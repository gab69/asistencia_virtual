@echo off
setlocal
set "CARPETA=%~dp0"
if "%CARPETA:~-1%"=="\" set "CARPETA=%CARPETA:~0,-1%"
cd /d "%TEMP%"

if /i not "%~1"=="/silencioso" (
    choice /m "Desinstalar Marcador de asistencia y borrar su carpeta"
    if errorlevel 2 exit /b
)

rem 1. Cerrar el programa si esta en ejecucion
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -like ('*' + $env:CARPETA + '*principal.py*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

rem 2. Quitar el inicio automatico con Windows
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v MarcadorAsistencia /f >nul 2>&1

rem 3. Borrar la configuracion guardada
del /f /q "%USERPROFILE%\marcador_asistencia.json" >nul 2>&1

rem 4. Borrar la carpeta del programa (con unos segundos de espera)
start "" /min cmd /c "timeout /t 3 /nobreak >nul & rmdir /s /q "%CARPETA%""

if /i not "%~1"=="/silencioso" echo Desinstalacion completada.
if /i not "%~1"=="/silencioso" pause
