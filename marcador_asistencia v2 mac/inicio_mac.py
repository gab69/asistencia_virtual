"""Inicio automático en macOS mediante un LaunchAgent (se ejecuta al iniciar sesión)."""
import plistlib
import sys
from pathlib import Path

from entorno import ARGUMENTO_MINIMIZADO, esta_empaquetado

ETIQUETA = "com.gabrc.marcadorasistencia"
RUTA_AGENTE = Path.home() / "Library" / "LaunchAgents" / f"{ETIQUETA}.plist"


def _argumentos_de_inicio() -> list[str]:
    if esta_empaquetado():
        return [sys.executable, ARGUMENTO_MINIMIZADO]
    script = Path(__file__).with_name("principal.py")
    return [sys.executable, str(script), ARGUMENTO_MINIMIZADO]


def configurar_inicio_automatico(activar: bool) -> None:
    if activar:
        _escribir_agente()
    else:
        RUTA_AGENTE.unlink(missing_ok=True)


def _escribir_agente() -> None:
    RUTA_AGENTE.parent.mkdir(parents=True, exist_ok=True)
    contenido = {
        "Label": ETIQUETA,
        "ProgramArguments": _argumentos_de_inicio(),
        "RunAtLoad": True,
    }
    with RUTA_AGENTE.open("wb") as archivo:
        plistlib.dump(contenido, archivo)
