@echo off
cd /d "%~dp0"
python -c "import customtkinter, pystray, PIL" >nul 2>&1 || python -m pip install --quiet -r "%~dp0requirements.txt"
start "" pythonw "%~dp0principal.py"
