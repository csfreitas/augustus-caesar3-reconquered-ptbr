#!/bin/sh
set -eu
if [ "$#" -ne 1 ] || [ -z "$1" ]; then
    printf 'Uso: %s "/caminho/Reconquered Campaign"\n' "$0" >&2
    exit 2
fi
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -f "$SCRIPT_DIR/reconquered_ptbr_native_media.py" ]; then
    printf 'Instalador nativo ausente. Extraia o pacote RC3 completo.\n' >&2
    exit 1
fi
if ! command -v python3 >/dev/null 2>&1 ||
    ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
    printf 'Python 3.11 ou superior nao encontrado. Disponibilize python3 no PATH.\n' >&2
    exit 1
fi
exec python3 "$SCRIPT_DIR/reconquered_ptbr_native_media.py" uninstall "$1"
