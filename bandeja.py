"""Icono en la bandeja del sistema (junto al reloj de Windows)."""
from typing import Callable

import pystray

from icono import crear_imagen

NOMBRE_PROGRAMA = "Marcador de asistencia"


class IconoBandeja:
    """Las acciones se ejecutan en un hilo aparte: quien las entregue debe
    encargarse de llevarlas al hilo principal de la interfaz."""

    def __init__(self, al_abrir: Callable[[], None], al_salir: Callable[[], None]):
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
