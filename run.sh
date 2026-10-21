#!/bin/sh
# Запуск эмулятора: ./run.sh [--vfs PATH] [--script PATH]
cd "$(dirname "$0")" || exit 1
exec python3 src/emulator.py "$@"
