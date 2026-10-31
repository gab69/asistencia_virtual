"""Presencia en segundo plano: en macOS el Dock cumple el papel de la bandeja."""
import subprocess
import tkinter as tk
from typing import Callable

NOMBRE_PROGRAMA = "Marcador de asistencia"
EVENTO_REABRIR = "tk::mac::ReopenApplication"


class IconoDock:
    """Al hacer clic en el icono del Dock se vuelve a mostrar la configuración."""

    def __init__(self, raiz: tk.Tk, al_abrir: Callable[[], None]):
        self._raiz = raiz
        self._al_abrir = al_abrir

    def iniciar(self) -> None:
        self._raiz.createcommand(EVENTO_REABRIR, self._al_abrir)

    def avisar(self, mensaje: str) -> None:
        script = f'display notification "{mensaje}" with title "{NOMBRE_PROGRAMA}"'
        subprocess.Popen(["osascript", "-e", script])

    def detener(self) -> None:
        """No hay nada que liberar: el Dock desaparece al cerrar el programa."""
