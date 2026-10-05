"""Elige cómo se activa el inicio automático según el sistema operativo."""
from plataforma import ES_WINDOWS

if ES_WINDOWS:
    from inicio_windows import configurar_inicio_automatico
else:
    from inicio_mac import configurar_inicio_automatico

__all__ = ["configurar_inicio_automatico"]
