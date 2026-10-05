"""Lanza la desinstalación: el desinstalador del instalador, o el .bat en modo código fuente."""
import subprocess
from pathlib import Path

from entorno import carpeta_de_instalacion, esta_empaquetado

DESINSTALADOR_INSTALADO = "unins000.exe"
ARGUMENTO_INSTALADO = "/SILENT"
SCRIPT_FUENTE = Path(__file__).with_name("desinstalar.bat")
ARGUMENTO_FUENTE = "/silencioso"


def _comando() -> list[str]:
    if esta_empaquetado():
        return [str(carpeta_de_instalacion() / DESINSTALADOR_INSTALADO), ARGUMENTO_INSTALADO]
    return ["cmd", "/c", str(SCRIPT_FUENTE), ARGUMENTO_FUENTE]


def lanzar_desinstalacion() -> None:
    subprocess.Popen(_comando(), creationflags=subprocess.CREATE_NO_WINDOW)
