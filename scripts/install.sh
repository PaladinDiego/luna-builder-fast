#!/usr/bin/env bash
# ==============================================================================
# install.sh — Instalador de Luna Builder Fast para Google Antigravity (Linux/macOS)
# ==============================================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE=""
UNINSTALL=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -w|--workspace) WORKSPACE="$2"; shift ;;
        -u|--uninstall) UNINSTALL=true ;;
        -h|--help)
            echo "Uso: $0 [OPCIONES]"
            echo "  -w, --workspace DIR   Instalar localmente en el directorio del proyecto (.agents/)"
            echo "  -u, --uninstall       Desinstalar el plugin"
            exit 0
            ;;
        *) echo "Opción desconocida: $1"; exit 1 ;;
    esac
    shift
done

if [ -n "$WORKSPACE" ]; then
    TARGET_DIR="$WORKSPACE/.agents/plugins/luna-builder-fast"
    IS_WORKSPACE=true
else
    TARGET_DIR="$HOME/.gemini/config/plugins/luna-builder-fast"
    IS_WORKSPACE=false
fi

echo "================================================================="
echo "  INSTALADOR DE LUNA BUILDER FAST PARA GOOGLE ANTIGRAVITY"
echo "================================================================="
echo "Repositorio: $REPO_ROOT"
echo "Destino:     $TARGET_DIR"
echo "-----------------------------------------------------------------"

if [ "$UNINSTALL" = true ]; then
    if [ -d "$TARGET_DIR" ]; then
        rm -rf "$TARGET_DIR"
        echo "[✓] Plugin desinstalado correctamente de $TARGET_DIR"
    else
        echo "[-] El directorio de destino no existe."
    fi
    exit 0
fi

mkdir -p "$TARGET_DIR"

ITEMS=("plugin.json" "hooks.json" "README.md" "agents" "rules" "skills")

for item in "${ITEMS[@]}"; do
    SRC="$REPO_ROOT/$item"
    DEST="$TARGET_DIR/$item"
    if [ -e "$SRC" ]; then
        cp -R "$SRC" "$DEST"
        echo "[+] Copiado: $item"
    else
        echo "[!] Advertencia: $item no encontrado en el repo"
    fi
done

echo "-----------------------------------------------------------------"
echo "[✓] ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!"
echo "================================================================="
if [ "$IS_WORKSPACE" = false ]; then
    echo "Para activar los cambios:"
    echo "  1. Reinicia Antigravity para descubrir el plugin global."
    echo "  2. Pide en el chat: 'Ejecuta esta tarea con luna fast'"
fi
