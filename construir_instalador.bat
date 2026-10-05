@echo off
setlocal
cd /d "%~dp0"
title Construyendo instalador - Marcador de asistencia

echo === 1/4 Preparando herramientas ===
python --version >nul 2>&1
if errorlevel 1 goto :sin_python
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo === 2/4 Generando icono ===
python generar_icono.py
if errorlevel 1 goto :error

echo === 3/4 Creando el programa (incluye Python, no hace falta instalarlo) ===
python -m PyInstaller --noconfirm --clean --windowed --name MarcadorAsistencia --icon icono.ico --collect-all customtkinter --hidden-import pystray._win32 principal.py
if errorlevel 1 goto :error

echo === 4/4 Creando el instalador ===
call :buscar_iscc
if not defined ISCC (
    echo Instalando Inno Setup, espera un momento...
    winget install -e --id JRSoftware.InnoSetup --silent --accept-package-agreements --accept-source-agreements
    call :buscar_iscc
)
if not defined ISCC goto :sin_inno
"%ISCC%" instalador.iss
if errorlevel 1 goto :error

echo.
echo LISTO. Tu instalador esta en:  %~dp0Output\Instalador_MarcadorAsistencia.exe
explorer "%~dp0Output"
pause
exit /b 0

:buscar_iscc
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
exit /b 0

:sin_python
echo No se encontro Python. Instalalo desde https://www.python.org (marca "Add Python to PATH") y vuelve a ejecutar.
pause
exit /b 1

:sin_inno
echo No se pudo instalar Inno Setup automaticamente. Descargalo desde https://jrsoftware.org/isdl.php, instalalo y vuelve a ejecutar.
pause
exit /b 1

:error
echo.
echo Ocurrio un error. Revisa los mensajes de arriba.
pause
exit /b 1
