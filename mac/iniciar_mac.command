#!/bin/bash
# Modo desarrollo en Mac: ejecuta el programa desde el código fuente.
cd "$(dirname "$0")"
python3 -c "import customtkinter, AppKit" 2>/dev/null || python3 -m pip install --quiet -r requirements.txt
python3 principal.py
