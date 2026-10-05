"""Distingue si el programa corre instalado (.exe) o desde el código fuente."""
import sys
from pathlib import Path


def esta_empaquetado() -> bool:
    return getattr(sys, "frozen", False)


def carpeta_de_instalacion() -> Path:
    return Path(sys.executable).parent
