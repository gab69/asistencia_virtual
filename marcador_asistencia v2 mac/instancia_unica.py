"""Evita que el programa se ejecute dos veces a la vez."""
import subprocess
from pathlib import Path

from plataforma import ES_WINDOWS

TITULO = "Marcador de asistencia"
MENSAJE_WINDOWS = (
    "El marcador ya está en ejecución.\n\n"
    "Búscalo en los iconos junto al reloj (flecha ^) y haz clic en él."
)
MENSAJE_MAC = (
    "El marcador ya está en ejecución.\n\n"
    "Haz clic en su icono del Dock para abrir la configuración."
)

_NOMBRE_MUTEX = "Local\\MarcadorAsistencia"
_ERROR_YA_EXISTE = 183
_ICONO_INFORMACION = 0x40
_RUTA_BLOQUEO = Path.home() / ".marcador_asistencia.lock"
_recurso_bloqueado = None  # se conserva mientras viva el programa


def es_primera_instancia() -> bool:
    return _adquirir_en_windows() if ES_WINDOWS else _adquirir_en_unix()


def _adquirir_en_windows() -> bool:
    import ctypes

    global _recurso_bloqueado
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _recurso_bloqueado = kernel32.CreateMutexW(None, False, _NOMBRE_MUTEX)
    return ctypes.get_last_error() != _ERROR_YA_EXISTE


def _adquirir_en_unix() -> bool:
    import fcntl

    global _recurso_bloqueado
    _recurso_bloqueado = _RUTA_BLOQUEO.open("w")
    try:
        fcntl.flock(_recurso_bloqueado, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def avisar_que_ya_esta_ejecutando() -> None:
    if ES_WINDOWS:
        _avisar_en_windows()
    else:
        _avisar_en_mac()


def _avisar_en_windows() -> None:
    import ctypes

    ctypes.windll.user32.MessageBoxW(0, MENSAJE_WINDOWS, TITULO, _ICONO_INFORMACION)


def _avisar_en_mac() -> None:
    script = (
        f'display dialog "{MENSAJE_MAC}" with title "{TITULO}" '
        'buttons {"Entendido"} default button 1 with icon note'
    )
    subprocess.run(["osascript", "-e", script], check=False)
