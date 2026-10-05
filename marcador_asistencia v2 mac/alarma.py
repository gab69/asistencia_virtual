"""Alarma sonora que se repite mientras la pantalla está bloqueada."""
import subprocess
import threading

from plataforma import ES_WINDOWS

if ES_WINDOWS:
    import winsound

FRECUENCIA_HZ = 1000
DURACION_PITIDO_MS = 250
SONIDO_MAC = "/System/Library/Sounds/Sosumi.aiff"
PITIDOS_POR_RAFAGA = 3
PAUSA_ENTRE_PITIDOS_S = 0.1
PAUSA_ENTRE_RAFAGAS_S = 3.0


def _emitir_pitido() -> None:
    if ES_WINDOWS:
        winsound.Beep(FRECUENCIA_HZ, DURACION_PITIDO_MS)
    else:
        subprocess.run(["afplay", SONIDO_MAC], check=False)


def _emitir_rafaga(detener: threading.Event) -> None:
    for _ in range(PITIDOS_POR_RAFAGA):
        if detener.is_set():
            return
        _emitir_pitido()
        detener.wait(PAUSA_ENTRE_PITIDOS_S)


class Alarma:
    def __init__(self):
        self._detener = threading.Event()
        self._hilo: threading.Thread | None = None

    def iniciar(self) -> None:
        if self._hilo is not None:
            return
        self._detener.clear()
        self._hilo = threading.Thread(target=self._repetir, daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._detener.set()
        self._hilo = None

    def _repetir(self) -> None:
        while not self._detener.is_set():
            _emitir_rafaga(self._detener)
            self._detener.wait(PAUSA_ENTRE_RAFAGAS_S)


def probar_alarma() -> None:
    """Suena una sola ráfaga, para que el usuario compruebe el volumen."""
    threading.Thread(target=_emitir_rafaga, args=(threading.Event(),), daemon=True).start()
