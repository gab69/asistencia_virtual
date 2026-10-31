"""Borra la app, el inicio automático y los datos del usuario."""
import shlex
import subprocess

from configuracion import RUTA_CONFIGURACION
from entorno import esta_empaquetado, ruta_del_bundle_mac
from inicio_mac import RUTA_AGENTE
from instancia_unica import RUTA_BLOQUEO

SEGUNDOS_DE_ESPERA = 2  # deja que el programa se cierre antes de borrarlo


def _comando() -> list[str]:
    rutas = [RUTA_AGENTE, RUTA_CONFIGURACION, RUTA_BLOQUEO]
    aplicacion = ruta_del_bundle_mac()
    if esta_empaquetado() and aplicacion:
        rutas.append(aplicacion)
    a_borrar = " ".join(shlex.quote(str(ruta)) for ruta in rutas)
    return ["/bin/sh", "-c", f"sleep {SEGUNDOS_DE_ESPERA}; rm -rf {a_borrar}"]


def lanzar_desinstalacion() -> None:
    subprocess.Popen(_comando(), start_new_session=True)
