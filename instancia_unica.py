"""Evita que el programa se ejecute dos veces a la vez."""
import ctypes

_NOMBRE_MUTEX = "Local\\MarcadorAsistencia"
_ERROR_YA_EXISTE = 183

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_manejador = None  # se conserva mientras viva el programa


def es_primera_instancia() -> bool:
    global _manejador
    _manejador = _kernel32.CreateMutexW(None, False, _NOMBRE_MUTEX)
    return ctypes.get_last_error() != _ERROR_YA_EXISTE
