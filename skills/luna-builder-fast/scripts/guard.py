#!/usr/bin/env python3
"""
guard.py — Auditor determinista de frontera de archivos para Luna Builder Fast.

Garantiza que un agente o proceso SOLO haya modificado los archivos autorizados
en su lista cerrada, tomando en cuenta:
- Modificaciones staged y unstaged
- Archivos untracked (nuevos)
- Borrados y renombrados
- Separación respecto a un snapshot baseline inicial
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run_git(cmd, cwd=None):
    res = subprocess.run(["git"] + cmd, cwd=cwd, capture_output=True, text=False)
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(cmd)} failed: {err}")
    return res.stdout


def get_git_status_porcelain(cwd=None):
    """
    Retorna diccionario de ruta normalizada -> estado status code (2 chars).
    Usa formato -z para manejar espacios y caracteres especiales de forma segura.
    """
    raw = run_git(["status", "--porcelain=v1", "-z"], cwd=cwd)
    entries = raw.split(b"\x00")
    status_map = {}
    i = 0
    while i < len(entries):
        entry = entries[i]
        if not entry:
            i += 1
            continue
        code = entry[:2].decode("utf-8", errors="replace")
        path_str = entry[3:].decode("utf-8", errors="replace")
        norm_path = os.path.normpath(path_str).replace("\\", "/")

        # En renombrados (R) o copias (C), el siguiente elemento en -z es el destino original
        if code.startswith("R") or code.startswith("C") or code[1:2] in ("R", "C"):
            if i + 1 < len(entries):
                i += 1
                dest_path = entries[i].decode("utf-8", errors="replace")
                norm_dest = os.path.normpath(dest_path).replace("\\", "/")
                status_map[norm_dest] = code
        status_map[norm_path] = code
        i += 1
    return status_map


def get_current_head(cwd=None):
    try:
        raw = run_git(["rev-parse", "HEAD"], cwd=cwd)
        return raw.decode("utf-8", errors="replace").strip()
    except Exception:
        return "NO_COMMIT"


def take_snapshot(snapshot_file, cwd=None):
    status_map = get_git_status_porcelain(cwd=cwd)
    head = get_current_head(cwd=cwd)
    data = {
        "head": head,
        "status": status_map
    }
    snap_path = Path(snapshot_file).resolve()
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[guard] Snapshot baseline guardado en: {snap_path}")
    print(f"[guard] Archivos sucios preexistentes: {len(status_map)}")


def normalize_allowlist(allowlist_items, cwd=None):
    allowed = set()
    repo_root = Path(run_git(["rev-parse", "--show-toplevel"], cwd=cwd).decode("utf-8", errors="replace").strip())
    for item in allowlist_items:
        clean = item.strip().strip("'\"")
        if not clean:
            continue
        p = Path(clean)
        if not p.is_absolute():
            p = (Path(cwd or ".").resolve() / p).resolve()
        else:
            p = p.resolve()
        try:
            rel = p.relative_to(repo_root)
            allowed.add(str(rel).replace("\\", "/"))
        except ValueError:
            allowed.add(clean.replace("\\", "/"))
    return allowed


def verify_changes(allowlist_items, snapshot_file=None, cwd=None):
    current_status = get_git_status_porcelain(cwd=cwd)
    baseline_status = {}
    if snapshot_file and os.path.exists(snapshot_file):
        try:
            data = json.loads(Path(snapshot_file).read_text(encoding="utf-8"))
            baseline_status = data.get("status", {})
        except Exception as e:
            print(f"[guard] Advertencia: no se pudo leer snapshot: {e}", file=sys.stderr)

    allowed_set = normalize_allowlist(allowlist_items, cwd=cwd)

    # Identificar cambios introducidos DESPUÉS del baseline
    touched_by_agent = {}
    for path, code in current_status.items():
        if path not in baseline_status or baseline_status[path] != code:
            touched_by_agent[path] = code

    # Archivos que estaban sucios y ahora están limpios (staged o restaurados)
    for path, code in baseline_status.items():
        if path not in current_status:
            touched_by_agent[path] = "RESTORED/COMMITTED"

    # Ignorar metadatos internos de luna (.luna/) y el propio archivo de snapshot
    snap_rel = None
    if snapshot_file:
        try:
            repo_root = Path(run_git(["rev-parse", "--show-toplevel"], cwd=cwd).decode("utf-8", errors="replace").strip())
            snap_rel = str(Path(snapshot_file).resolve().relative_to(repo_root)).replace("\\", "/")
        except Exception:
            pass

    filtered_touched = {}
    for path, code in touched_by_agent.items():
        if path.startswith(".luna/") or path == ".luna" or (snap_rel and path == snap_rel):
            continue
        filtered_touched[path] = code
    touched_by_agent = filtered_touched

    violations = []
    authorized = []

    for path, code in touched_by_agent.items():
        # Comprobar si path coincide con la lista permitida
        is_allowed = False
        for allowed in allowed_set:
            if path == allowed or path.endswith("/" + allowed) or allowed.endswith("/" + path):
                is_allowed = True
                break
        if is_allowed:
            authorized.append((path, code))
        else:
            violations.append((path, code))

    print("=" * 60)
    print("REPORTE DE AUDITORÍA DETERMINISTA (guard.py)")
    print("=" * 60)
    print(f"Archivos autorizados en contrato: {len(allowed_set)}")
    for a in sorted(allowed_set):
        print(f"  [PERMITIDO] {a}")
    print("-" * 60)
    print(f"Archivos modificados por el agente: {len(touched_by_agent)}")
    for p, c in authorized:
        print(f"  [OK]        ({c}) {p}")
    for p, c in violations:
        print(f"  [VIOLACIÓN] ({c}) {p}")
    print("=" * 60)

    if violations:
        print(f"[ERROR] GUARD FALLIDO: {len(violations)} archivo(s) modificado(s) fuera de la lista permitida.", file=sys.stderr)
        sys.exit(1)
    else:
        print("[ÉXITO] GUARD PASÓ: Todos los cambios están estrictamente dentro de la frontera.")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Auditor determinista de frontera de archivos")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando snapshot
    snap_p = subparsers.add_parser("snapshot", help="Toma un snapshot baseline del estado git")
    snap_p.add_argument("--file", "-f", required=True, help="Ruta del archivo json donde guardar snapshot")
    snap_p.add_argument("--cwd", help="Directorio del repositorio")

    # Subcomando check
    check_p = subparsers.add_parser("check", help="Comprueba que solo los archivos permitidos fueron tocados")
    check_p.add_argument("--allow", "-a", nargs="+", required=True, help="Lista de rutas permitidas")
    check_p.add_argument("--snapshot", "-s", help="Ruta del archivo json de baseline previo")
    check_p.add_argument("--cwd", help="Directorio del repositorio")

    args = parser.parse_args()
    if args.command == "snapshot":
        take_snapshot(args.file, cwd=args.cwd)
    elif args.command == "check":
        verify_changes(args.allow, snapshot_file=args.snapshot, cwd=args.cwd)


if __name__ == "__main__":
    main()
