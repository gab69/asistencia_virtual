"""Distingue si el programa corre instalado (empaquetado) o desde el código fuente."""
import sys
from pathlib import Path

ARGUMENTO_MINIMIZADO = "--minimizado"


def esta_empaquetado() -> bool:
    return getattr(sys, "frozen", False)


def ruta_del_bundle_mac() -> Path | None:
    """Carpeta 'Nombre.app' que contiene el ejecutable, si existe."""
    for carpeta in Path(sys.executable).parents:
        if carpeta.suffix == ".app":
            return carpeta
    return None
