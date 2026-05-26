#!/bin/bash
# MiExt Launcher (command file — double-click to run in Terminal)
# Bypasses Gatekeeper by running inside trusted Terminal.app

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
EXEC="$APP_DIR/MiExt.app/Contents/MacOS/mi-ext"

if [ ! -x "$EXEC" ]; then
    echo "Error: Cannot find MiExt executable at $EXEC"
    read -p "Press Enter to exit..."
    exit 1
fi

exec "$EXEC" "$@"
