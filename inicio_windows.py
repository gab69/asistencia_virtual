"""Activa o desactiva el inicio automático del programa con Windows."""
import sys
import winreg
from pathlib import Path

from entorno import esta_empaquetado

CLAVE_INICIO = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOMBRE_ENTRADA = "MarcadorAsistencia"
ARGUMENTO_MINIMIZADO = "--minimizado"


def _comando_de_inicio() -> str:
    if esta_empaquetado():
        return f'"{sys.executable}" {ARGUMENTO_MINIMIZADO}'
    interprete = Path(sys.executable).with_name("pythonw.exe")
    script = Path(__file__).with_name("principal.py")
    return f'"{interprete}" "{script}" {ARGUMENTO_MINIMIZADO}'


def configurar_inicio_automatico(activar: bool) -> None:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, CLAVE_INICIO, 0, winreg.KEY_SET_VALUE
    ) as clave:
        if activar:
            winreg.SetValueEx(clave, NOMBRE_ENTRADA, 0, winreg.REG_SZ, _comando_de_inicio())
        else:
            _borrar_entrada(clave)


def _borrar_entrada(clave) -> None:
    try:
        winreg.DeleteValue(clave, NOMBRE_ENTRADA)
    except FileNotFoundError:
        pass
