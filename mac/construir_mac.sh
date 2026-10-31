#!/bin/bash
# Construye "Marcador de asistencia" para macOS: la app (.app) y su instalador (.dmg).
# Ejecutar UNA vez en un Mac:  ./construir_mac.sh
set -e
cd "$(dirname "$0")"

NOMBRE_APP="Marcador de asistencia"
CARPETA_SALIDA="Output"
APP="dist/$NOMBRE_APP.app"

echo "=== 1/5 Preparando herramientas ==="
if ! command -v python3 >/dev/null; then
    echo "Instala Python 3 desde https://www.python.org (incluye Tk) y vuelve a ejecutar."
    exit 1
fi
python3 -m venv .venv_build
source .venv_build/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt pyinstaller

echo "=== 2/5 Generando icono ==="
python generar_icono.py

echo "=== 3/5 Creando la aplicación (incluye Python, no hace falta instalarlo) ==="
pyinstaller --noconfirm --clean --windowed \
    --name "$NOMBRE_APP" \
    --icon icono.icns \
    --osx-bundle-identifier com.gabrc.marcadorasistencia \
    --collect-all customtkinter \
    --hidden-import AppKit --hidden-import Foundation \
    principal.py

echo "=== 4/5 Configurando permisos y firma ==="
plutil -replace NSAppleEventsUsageDescription -string \
    "Necesito controlar otras ventanas para recordarte marcar tu asistencia." \
    "$APP/Contents/Info.plist"
codesign --force --deep --sign - "$APP"

echo "=== 5/5 Creando el instalador (.dmg) ==="
rm -rf dmg_tmp "$CARPETA_SALIDA"
mkdir -p dmg_tmp "$CARPETA_SALIDA"
cp -R "$APP" dmg_tmp/
ln -s /Applications dmg_tmp/Applications
hdiutil create -volname "$NOMBRE_APP" -srcfolder dmg_tmp -ov -format UDZO \
    "$CARPETA_SALIDA/Instalador_MarcadorAsistencia_Mac.dmg"
rm -rf dmg_tmp

echo
echo "LISTO: $CARPETA_SALIDA/Instalador_MarcadorAsistencia_Mac.dmg"
open "$CARPETA_SALIDA"
