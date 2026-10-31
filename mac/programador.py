"""Decide qué marcación corresponde en un momento dado."""
from datetime import date, datetime

from configuracion import Configuracion, Marcacion


class Programador:
    def __init__(self, configuracion: Configuracion):
        self._configuracion = configuracion
        self._ya_disparadas: set[tuple[date, str]] = set()

    def actualizar_configuracion(self, configuracion: Configuracion) -> None:
        self._configuracion = configuracion

    def marcacion_pendiente(self, ahora: datetime) -> Marcacion | None:
        if ahora.weekday() not in self._configuracion.dias_laborales:
            return None
        hora_actual = ahora.strftime("%H:%M")
        for marcacion in self._configuracion.marcaciones:
            if self._corresponde(marcacion, ahora.date(), hora_actual):
                self._ya_disparadas.add((ahora.date(), marcacion.nombre))
                return marcacion
        return None

    def _corresponde(self, marcacion: Marcacion, dia: date, hora_actual: str) -> bool:
        ya_fue_disparada = (dia, marcacion.nombre) in self._ya_disparadas
        return marcacion.activa and marcacion.hora == hora_actual and not ya_fue_disparada
