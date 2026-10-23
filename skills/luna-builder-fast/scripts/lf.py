#!/usr/bin/env python3
"""
lf.py — Despachador y planificador ligero de dependencias para Luna Builder Fast.

Orquesta un grafo de tareas (DAG) optimizando la ruta crítica, ejecutando tareas listas
en concurrencia controlada, e integrando incrementalmente.
"""

import argparse
import concurrent.futures
import datetime
import json
import os
import subprocess
import sys
import time
from collections import defaultdict, deque
from pathlib import Path


def load_tasks(tasks_file):
    p = Path(tasks_file)
    if not p.exists():
        raise FileNotFoundError(f"Archivo de tareas no encontrado: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    tasks_map = {}
    for t in data:
        tid = t["id"]
        tasks_map[tid] = {
            "id": tid,
            "depends_on": set(t.get("depends_on", [])),
            "property": t.get("property", []),
            "prompt": t.get("prompt", ""),
            "acceptance": t.get("acceptance", ""),
            "mode": t.get("mode", "fast"),
            "effort": t.get("effort", "medium"),
            "status": "pending",  # pending, running, completed, failed, blocked
            "error": None,
            "duration": 0.0
        }
    return tasks_map


def validate_dag(tasks_map):
    # Detección de ciclos mediante algoritmo de Kahn
    in_degree = {tid: len(t["depends_on"]) for tid, t in tasks_map.items()}
    # Verificar que las dependencias existan
    for tid, t in tasks_map.items():
        for dep in t["depends_on"]:
            if dep not in tasks_map:
                raise ValueError(f"Tarea '{tid}' depende de '{dep}' que no existe en el archivo de tareas.")

    queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
    visited = 0
    while queue:
        curr = queue.popleft()
        visited += 1
        for tid, t in tasks_map.items():
            if curr in t["depends_on"]:
                in_degree[tid] -= 1
                if in_degree[tid] == 0:
                    queue.append(tid)

    if visited != len(tasks_map):
        raise ValueError("El grafo de tareas contiene ciclos o dependencias circulares.")


def run_task_worker(task, cwd, runs_dir):
    tid = task["id"]
    t_start = time.perf_counter()
    log_file = runs_dir / f"task_{tid}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"[lf] -> Iniciando {tid} (Modo: {task['mode']}, Esfuerzo: {task['effort']})")

    # Si hay comando de aceptación sin prompt de LLM (ej. codemod determinista)
    if task["mode"] == "codemod" or not task["prompt"]:
        cmd = task["acceptance"]
        res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        elapsed = time.perf_counter() - t_start
        log_file.write_text(f"CODE: {res.returncode}\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}", encoding="utf-8")
        return tid, (res.returncode == 0), elapsed, res.stderr if res.returncode != 0 else ""

    # Ejecución vía agy headless
    prompt = task["prompt"]
    if task["acceptance"]:
        prompt += f"\n\nComando de aceptación que DEBES ejecutar y verificar:\n{task['acceptance']}"

    cmd = [
        "agy", "-p", prompt,
        "--effort", task["effort"],
        "--output-format", "json"
    ]

    env = os.environ.copy()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=300)
        elapsed = time.perf_counter() - t_start
        output = p.stdout.strip()
        log_file.write_text(f"EXIT CODE: {p.returncode}\nOUT:\n{output}\nERR:\n{p.stderr}", encoding="utf-8")

        success = (p.returncode == 0)
        # Verificar aceptación si se estipuló
        if success and task["acceptance"]:
            c_res = subprocess.run(task["acceptance"], shell=True, cwd=cwd, capture_output=True, text=True)
            if c_res.returncode != 0:
                success = False
                error_msg = f"Aceptación fallida: {c_res.stderr or c_res.stdout}"
            else:
                error_msg = ""
        else:
            error_msg = p.stderr if not success else ""

        return tid, success, elapsed, error_msg

    except Exception as e:
        elapsed = time.perf_counter() - t_start
        return tid, False, elapsed, str(e)


def dispatch_dag(tasks_file, cwd=".", max_workers=2, integration_check=None):
    tasks_map = load_tasks(tasks_file)
    validate_dag(tasks_map)

    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_dir = Path(cwd) / ".luna" / "runs" / f"dag_{run_id}"
    runs_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print(f"LUNA BUILDER FAST — PLANIFICADOR DAG (Run ID: {run_id})")
    print(f"Total de tareas: {len(tasks_map)} | Concurrencia máxima: {max_workers}")
    print("=" * 65)

    wall_start = time.perf_counter()
    completed_tasks = set()
    failed_tasks = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        active_futures = {}  # future -> tid

        while len(completed_tasks) + len(failed_tasks) < len(tasks_map):
            # Identificar tareas listas para ejecutar
            ready_to_launch = []
            for tid, t in tasks_map.items():
                if t["status"] == "pending":
                    # Si alguna dependencia falló, marcar como bloqueada
                    if any(dep in failed_tasks for dep in t["depends_on"]):
                        t["status"] = "blocked"
                        failed_tasks.add(tid)
                        print(f"[lf] [BLOQUEO] Tarea {tid} cancelada porque su dependencia falló.")
                    elif all(dep in completed_tasks for dep in t["depends_on"]):
                        ready_to_launch.append(t)

            # Lanzar tareas listas respetando max_workers
            for t in ready_to_launch:
                if len(active_futures) < max_workers:
                    t["status"] = "running"
                    fut = executor.submit(run_task_worker, t, cwd, runs_dir)
                    active_futures[fut] = t["id"]

            if not active_futures:
                # Si no hay tareas activas y quedan pendientes sin desbloquear, salir
                break

            # Esperar a que al menos una tarea termine
            done, _ = concurrent.futures.wait(active_futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED)

            for fut in done:
                tid = active_futures.pop(fut)
                t = tasks_map[tid]
                try:
                    _, success, elapsed, err = fut.result()
                    t["duration"] = elapsed
                    if success:
                        t["status"] = "completed"
                        completed_tasks.add(tid)
                        print(f"[lf] [OK] Tarea {tid} completada con éxito ({elapsed:.2f}s)")

                        # Verificación de integración incremental
                        if integration_check:
                            print(f"[lf] Verificando integración incremental tras {tid}...")
                            ires = subprocess.run(integration_check, shell=True, cwd=cwd, capture_output=True, text=True)
                            if ires.returncode != 0:
                                print(f"[lf] [ERROR INTEGRACIÓN] Conflicto tras finalizar {tid}!", file=sys.stderr)
                                t["status"] = "failed"
                                t["error"] = "Fallo de integración incremental"
                                completed_tasks.remove(tid)
                                failed_tasks.add(tid)
                    else:
                        t["status"] = "failed"
                        t["error"] = err
                        failed_tasks.add(tid)
                        print(f"[lf] [FALLO] Tarea {tid} falló tras {elapsed:.2f}s: {err}")

                except Exception as ex:
                    t["status"] = "failed"
                    t["error"] = str(ex)
                    failed_tasks.add(tid)
                    print(f"[lf] [ERROR] Excepción en {tid}: {ex}")

    total_wall_time = time.perf_counter() - wall_start
    print("=" * 65)
    print("RESUMEN DE EJECUCIÓN DEL GRAFO (TTVD)")
    print(f"Tiempo de pared (Wall-Clock): {total_wall_time:.2f}s")
    print(f"Tareas completadas: {len(completed_tasks)}/{len(tasks_map)}")
    print(f"Tareas fallidas o bloqueadas: {len(failed_tasks)}/{len(tasks_map)}")
    print("=" * 65)

    all_ok = (len(completed_tasks) == len(tasks_map))
    sys.exit(0 if all_ok else 1)


def main():
    parser = argparse.ArgumentParser(description="Despachador DAG ligero para Luna Builder Fast")
    parser.add_argument("tasks", help="Archivo JSON con la definición del DAG de tareas")
    parser.add_argument("--cwd", default=".", help="Directorio raíz del proyecto")
    parser.add_argument("--workers", "-w", type=int, default=2, help="Concurrencia máxima (default: 2)")
    parser.add_argument("--integration-check", "-i", help="Comando de suite cruzada / integración incremental")

    args = parser.parse_args()
    dispatch_dag(args.tasks, cwd=args.cwd, max_workers=args.workers, integration_check=args.integration_check)


if __name__ == "__main__":
    main()
