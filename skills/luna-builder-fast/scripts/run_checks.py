#!/usr/bin/env python3
"""
run_checks.py — Ejecutor y orquestador determinista de comprobaciones para Luna Builder Fast.

Diseñado para reemplazar cadenas de shell frágiles (como '&&' no soportado en PowerShell 5.1).
- Ejecuta comandos de comprobación/tests por separado.
- Guarda los logs completos en disco para diagnóstico profundo.
- Trunca y formatea el resumen observable en stdout (evita inundar la ventana de contexto).
- Ejecuta opcionalmente la auditoría de guard.py de frontera.
"""

import argparse
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path


def execute_step(name, command, log_file, cwd=None, timeout=120):
    start = time.perf_counter()
    p = subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    output_lines = []
    try:
        stdout, _ = p.communicate(timeout=timeout)
        output_lines = stdout.splitlines()
    except subprocess.TimeoutExpired:
        p.kill()
        output_lines = ["\n[run_checks] ERROR: Tiempo de espera agotado (timeout {}s)".format(timeout)]

    elapsed = time.perf_counter() - start
    code = p.returncode

    # Guardar log completo a disco
    log_path = Path(log_file).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"=== CHECK: {name} ===\n")
        f.write(f"COMMAND: {command}\n")
        f.write(f"EXIT CODE: {code}\n")
        f.write(f"ELAPSED: {elapsed:.2f}s\n")
        f.write(f"TIMESTAMP: {datetime.datetime.now().isoformat()}\n")
        f.write("=== LOG OUTPUT ===\n")
        f.write("\n".join(output_lines))

    # Generar extracto observable (≤ 12 líneas clave)
    if code == 0:
        summary_lines = output_lines[-5:] if len(output_lines) > 5 else output_lines
    else:
        # En caso de error, mostrar últimas 12 líneas del traceback
        summary_lines = output_lines[-12:] if len(output_lines) > 12 else output_lines

    return {
        "name": name,
        "command": command,
        "code": code,
        "elapsed": elapsed,
        "log_file": str(log_path),
        "summary": summary_lines
    }


def main():
    parser = argparse.ArgumentParser(description="Ejecutor determinista de comprobaciones y tests")
    parser.add_argument("--check", "-c", action="append", required=True, help="Nombre y comando en formato 'Nombre:Comando'")
    parser.add_argument("--run-id", default=None, help="Identificador de la corrida para logs")
    parser.add_argument("--cwd", default=".", help="Directorio de trabajo")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout por comando en segundos")
    parser.add_argument("--guard-allow", nargs="*", help="Si se especifica, ejecuta guard.py con esta lista permitida")
    parser.add_argument("--guard-snapshot", help="Archivo de baseline para guard.py")

    args = parser.parse_args()

    run_id = args.run_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_dir = Path(args.cwd) / ".luna" / "runs" / run_id

    results = []
    all_passed = True

    print("=" * 65)
    print(f"LUNA BUILDER FAST — VERIFICACIÓN DETERMINISTA (Run ID: {run_id})")
    print("=" * 65)

    for idx, item in enumerate(args.check, 1):
        if ":" in item:
            name, cmd = item.split(":", 1)
        else:
            name, cmd = f"check_{idx}", item

        name = name.strip()
        cmd = cmd.strip()
        log_file = runs_dir / f"{name}.log"

        print(f"[{idx}/{len(args.check)}] Ejecutando: {name} ... ", end="", flush=True)
        res = execute_step(name, cmd, log_file, cwd=args.cwd, timeout=args.timeout)
        results.append(res)

        if res["code"] == 0:
            print(f"PASS ({res['elapsed']:.2f}s)")
        else:
            print(f"FAIL (code {res['code']} en {res['elapsed']:.2f}s)")
            all_passed = False
            # Imprimir extracto del fallo inmediatamente
            print("  --- Extracto del error (ver log completo en {}) ---".format(res["log_file"]))
            for line in res["summary"]:
                print(f"  | {line}")
            print("  -------------------------------------------------------------")
            # Detener ejecución si una prueba crítica falló
            break

    # Si todos los checks pasaron y se solicitó guard, ejecutar guard
    if all_passed and args.guard_allow is not None:
        guard_script = Path(__file__).parent / "guard.py"
        guard_cmd = f"python \"{guard_script}\" check --allow {' '.join(args.guard_allow)} --cwd \"{args.cwd}\""
        if args.guard_snapshot:
            guard_cmd += f" --snapshot \"{args.guard_snapshot}\""

        print(f"[GUARD] Verificando frontera de archivos ... ", end="", flush=True)
        guard_log = runs_dir / "guard_verification.log"
        g_res = execute_step("guard", guard_cmd, guard_log, cwd=args.cwd, timeout=30)
        results.append(g_res)

        if g_res["code"] == 0:
            print(f"PASS ({g_res['elapsed']:.2f}s)")
        else:
            print(f"FAIL (Violación de frontera detectada)")
            for line in g_res["summary"]:
                print(f"  | {line}")
            all_passed = False

    print("=" * 65)
    total_time = sum(r["elapsed"] for r in results)
    status_str = "EXITOSO (PASS)" if all_passed else "FALLIDO (FAIL)"
    print(f"RESULTADO GLOBAL: {status_str} | Tiempo total: {total_time:.2f}s")
    print(f"Detalle de logs archivado en: {runs_dir.resolve()}")
    print("=" * 65)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
