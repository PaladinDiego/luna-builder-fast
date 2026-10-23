#!/usr/bin/env python3
"""
install.py — Instalador multiplataforma de Luna Builder Fast para Google Antigravity.

Permite instalar Luna Builder Fast de forma instantánea en cualquier máquina
(Windows, macOS, Linux) en dos modalidades:
  1. Global (--global, default): ~/.gemini/config/plugins/luna-builder-fast
  2. Workspace (--workspace <path>): <path>/.agents/ o plugin de proyecto

Uso:
  python scripts/install.py
  python scripts/install.py --workspace /ruta/a/tu/proyecto
  python scripts/install.py --uninstall
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# Configurar stdout para evitar errores de codificación en consolas heredadas de Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_default_global_dir():
    home = Path.home()
    return home / ".gemini" / "config" / "plugins" / "luna-builder-fast"


def install_plugin(dest_dir, is_workspace=False):
    repo_root = Path(__file__).resolve().parent.parent
    dest = Path(dest_dir).resolve()

    print("=" * 65)
    print("INSTALADOR DE LUNA BUILDER FAST PARA GOOGLE ANTIGRAVITY")
    print("=" * 65)
    print(f"Origen del repositorio:  {repo_root}")
    print(f"Destino de instalacion:  {dest}")
    print(f"Modalidad:               {'Espacio de Trabajo (Workspace)' if is_workspace else 'Plugin Global (~/.gemini)'}")
    print("-" * 65)

    dest.mkdir(parents=True, exist_ok=True)

    # Lista de elementos a instalar
    items_to_copy = [
        ("plugin.json", dest / "plugin.json", False),
        ("hooks.json", dest / "hooks.json", False),
        ("README.md", dest / "README.md", False),
        ("agents", dest / "agents", True),
        ("rules", dest / "rules", True),
        ("skills", dest / "skills", True),
    ]

    for src_rel, target_path, is_dir in items_to_copy:
        src = repo_root / src_rel
        if not src.exists():
            print(f"[!] Advertencia: {src} no encontrado, omitiendo.")
            continue

        if is_dir:
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(src, target_path)
            print(f"[+] Carpeta sincronizada:  {src_rel}/ -> {target_path.relative_to(dest)}/")
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target_path)
            print(f"[+] Archivo copiado:       {src_rel} -> {target_path.relative_to(dest)}")

    # Verificacion de hooks.json
    hooks_target = dest / "hooks.json"
    if hooks_target.exists():
        try:
            json.loads(hooks_target.read_text(encoding="utf-8"))
            print("[+] Configuracion de hooks verificada para ejecucion relativa portable.")
        except Exception as e:
            print(f"[!] Error al verificar hooks.json: {e}")

    print("-" * 65)
    print("[OK] INSTALACION COMPLETADA EXITOSAMENTE!")
    print("=" * 65)
    if not is_workspace:
        print("IMPORTANTE: Para activar el plugin global en una sesion activa de Antigravity:")
        print("  1. Reinicia Antigravity para descubrir el nuevo directorio del plugin.")
        print("  2. Luna Builder Fast se activara automaticamente al solicitar en el chat:")
        print("     - 'Ejecuta esta tarea con luna fast'")
        print("     - 'Aplica este cambio en modo express'")
        print("     - 'Ejecuta estas tareas independientes en fan-out con luna fast'")
    else:
        print("Luna Builder Fast ha sido vinculado en tu espacio de trabajo.")
    print("=" * 65)


def uninstall_plugin(dest_dir):
    dest = Path(dest_dir).resolve()
    print("=" * 65)
    print("DESINSTALADOR DE LUNA BUILDER FAST")
    print("=" * 65)
    print(f"Directorio a desinstalar: {dest}")

    if not dest.exists():
        print("[-] El directorio no existe o ya ha sido removido.")
        sys.exit(0)

    try:
        shutil.rmtree(dest)
        print("[OK] Plugin desinstalado y archivos eliminados con exito.")
    except Exception as e:
        print(f"[!] Error al desinstalar: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Instalador de Luna Builder Fast para Google Antigravity")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--global", dest="is_global", action="store_true", default=True, help="Instalar como plugin global (default)")
    group.add_argument("--workspace", "-w", help="Ruta al proyecto/workspace para instalar localmente")
    parser.add_argument("--dest", "-d", help="Ruta de destino personalizada")
    parser.add_argument("--uninstall", "-u", action="store_true", help="Desinstalar el plugin del destino")

    args = parser.parse_args()

    if args.dest:
        target = Path(args.dest)
        is_ws = False
    elif args.workspace:
        target = Path(args.workspace) / ".agents" / "plugins" / "luna-builder-fast"
        is_ws = True
    else:
        target = get_default_global_dir()
        is_ws = False

    if args.uninstall:
        uninstall_plugin(target)
    else:
        install_plugin(target, is_workspace=is_ws)


if __name__ == "__main__":
    main()
