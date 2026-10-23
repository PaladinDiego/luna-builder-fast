#!/usr/bin/env python3
"""
hook_pretool.py — Hook de ultrabaja latencia para PreToolUse en Luna Builder Fast.
Ejecuta en < 30ms. Si LUNA_GUARD_ALLOW no está activo, autoriza inmediatamente.
Si está activo, verifica que el archivo a modificar esté en la lista permitida.
"""

import json
import os
import sys

def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    allowlist_env = os.environ.get("LUNA_GUARD_ALLOW", "")
    if not allowlist_env:
        # Modo pasivo: cero overhead
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    target_path = args.get("Path") or args.get("path")
    if not target_path:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # Normalizar rutas
    norm_target = os.path.normpath(target_path).replace("\\", "/").lower()
    allowed_list = [os.path.normpath(a.strip()).replace("\\", "/").lower() for a in allowlist_env.split(";") if a.strip()]

    matched = False
    for allowed in allowed_list:
        if norm_target == allowed or norm_target.endswith("/" + allowed) or allowed.endswith("/" + norm_target):
            matched = True
            break

    if matched:
        print(json.dumps({"decision": "allow"}))
    else:
        reason = f"[LUNA GUARD] Acceso bloqueado: '{target_path}' no está en la lista autorizada ({allowlist_env})"
        print(json.dumps({"decision": "deny", "reason": reason}))

if __name__ == "__main__":
    main()
