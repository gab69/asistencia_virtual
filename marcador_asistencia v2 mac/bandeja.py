"""Presencia en segundo plano: bandeja del sistema (Windows) o Dock (macOS)."""
import subprocess
import tkinter as tk
from typing import Callable

from icono import crear_imagen
from plataforma import ES_WINDOWS

NOMBRE_PROGRAMA = "Marcador de asistencia"
EVENTO_REABRIR_MAC = "tk::mac::ReopenApplication"


class IconoBandejaWindows:
    """Las acciones se ejecutan en un hilo aparte: quien las entregue debe
    encargarse de llevarlas al hilo principal de la interfaz."""

    def __init__(self, al_abrir: Callable[[], None], al_salir: Callable[[], None]):
        import pystray  # solo se usa (e instala) en Windows

        menu = pystray.Menu(
            pystray.MenuItem("Abrir configuración", lambda *_: al_abrir(), default=True),
            pystray.MenuItem("Salir", lambda *_: al_salir()),
        )
        self._icono = pystray.Icon("marcador_asistencia", crear_imagen(), NOMBRE_PROGRAMA, menu)

    def iniciar(self) -> None:
        self._icono.run_detached()

    def avisar(self, mensaje: str) -> None:
        self._icono.notify(mensaje, NOMBRE_PROGRAMA)

    def detener(self) -> None:
        self._icono.stop()


class IconoDock:
    """En macOS el Dock cumple el papel de la bandeja: al hacer clic en su
    icono se vuelve a mostrar la ventana de configuración."""

    def __init__(self, raiz: tk.Tk, al_abrir: Callable[[], None]):
        self._raiz = raiz
        self._al_abrir = al_abrir

    def iniciar(self) -> None:
        self._raiz.createcommand(EVENTO_REABRIR_MAC, self._al_abrir)

    def avisar(self, mensaje: str) -> None:
        script = f'display notification "{mensaje}" with title "{NOMBRE_PROGRAMA}"'
        subprocess.Popen(["osascript", "-e", script])

    def detener(self) -> None:
        """No hay nada que liberar: el Dock desaparece al cerrar el programa."""


def crear_icono_bandeja(raiz: tk.Tk, al_abrir: Callable[[], None], al_salir: Callable[[], None]):
    if ES_WINDOWS:
        return IconoBandejaWindows(al_abrir, al_salir)
    return IconoDock(raiz, al_abrir)
