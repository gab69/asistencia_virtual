"""Lanza la desinstalación según el sistema operativo y la forma de ejecución."""
import shlex
import subprocess
from pathlib import Path

from configuracion import RUTA_CONFIGURACION
from entorno import carpeta_de_instalacion, esta_empaquetado, ruta_del_bundle_mac
from plataforma import ES_WINDOWS

DESINSTALADOR_WINDOWS = "unins000.exe"
ARGUMENTO_WINDOWS = "/SILENT"
SCRIPT_FUENTE_WINDOWS = Path(__file__).with_name("desinstalar.bat")
ARGUMENTO_FUENTE_WINDOWS = "/silencioso"
SEGUNDOS_DE_ESPERA_MAC = 2  # deja que el programa se cierre antes de borrarlo


def _comando_windows() -> list[str]:
    if esta_empaquetado():
        return [str(carpeta_de_instalacion() / DESINSTALADOR_WINDOWS), ARGUMENTO_WINDOWS]
    return ["cmd", "/c", str(SCRIPT_FUENTE_WINDOWS), ARGUMENTO_FUENTE_WINDOWS]


def _comando_mac() -> list[str]:
    from inicio_mac import RUTA_AGENTE

    rutas = [RUTA_AGENTE, RUTA_CONFIGURACION]
    aplicacion = ruta_del_bundle_mac()
    if esta_empaquetado() and aplicacion:
        rutas.append(aplicacion)
    a_borrar = " ".join(shlex.quote(str(ruta)) for ruta in rutas)
    return ["/bin/sh", "-c", f"sleep {SEGUNDOS_DE_ESPERA_MAC}; rm -rf {a_borrar}"]


def lanzar_desinstalacion() -> None:
    if ES_WINDOWS:
        subprocess.Popen(_comando_windows(), creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        subprocess.Popen(_comando_mac(), start_new_session=True)
