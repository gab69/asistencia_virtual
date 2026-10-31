"""Evita que el programa se ejecute dos veces a la vez."""
import fcntl
import subprocess
from pathlib import Path

TITULO = "Marcador de asistencia"
MENSAJE = (
    "El marcador ya está en ejecución.\n\n"
    "Haz clic en su icono del Dock para abrir la configuración."
)

RUTA_BLOQUEO = Path.home() / ".marcador_asistencia.lock"
_recurso_bloqueado = None  # se conserva mientras viva el programa


def es_primera_instancia() -> bool:
    global _recurso_bloqueado
    _recurso_bloqueado = RUTA_BLOQUEO.open("w")
    try:
        fcntl.flock(_recurso_bloqueado, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def avisar_que_ya_esta_ejecutando() -> None:
    script = (
        f'display dialog "{MENSAJE}" with title "{TITULO}" '
        'buttons {"Entendido"} default button 1 with icon note'
    )
    subprocess.run(["osascript", "-e", script], check=False)
