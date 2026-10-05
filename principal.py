"""Punto de entrada: conecta configuración, horario, bloqueo, bandeja e interfaz."""
import ctypes
import sys
from datetime import datetime
from typing import Callable

import customtkinter as ctk

import ventanas_windows as ventanas
from alarma import probar_alarma
from bandeja import IconoBandeja
from bloqueador import Bloqueador
from configuracion import (
    Configuracion,
    Marcacion,
    cargar_configuracion,
    guardar_configuracion,
)
from desinstalador import lanzar_desinstalacion
from inicio_windows import ARGUMENTO_MINIMIZADO, configurar_inicio_automatico
from instancia_unica import es_primera_instancia
from interfaz_configuracion import Acciones, VentanaConfiguracion
from programador import Programador

INTERVALO_REVISION_MS = 5000
RETRASO_OCULTAR_MS = 300
RETRASO_CENTRADO_MS = 250
TITULO_VENTANA = "Marcador de asistencia"
TAMANO_VENTANA = "1000x720"
MENSAJE_EN_BANDEJA = "Sigo activo en segundo plano. Haz clic en este icono para configurarme."
MENSAJE_YA_EJECUTANDO = (
    "El marcador ya está en ejecución.\n\n"
    "Búscalo en los iconos junto al reloj (flecha ^) y haz clic en él."
)


class Aplicacion:
    def __init__(self, iniciar_oculta: bool):
        self._configuracion = cargar_configuracion()
        self._programador = Programador(self._configuracion)
        self._bloqueador: Bloqueador | None = None
        self._aviso_bandeja_mostrado = False
        self._raiz = self._crear_ventana_principal()
        VentanaConfiguracion(
            self._raiz,
            self._configuracion,
            Acciones(
                guardar=self._guardar,
                probar=self._probar,
                probar_sonido=probar_alarma,
                desinstalar=self._desinstalar,
                salir=self._salir,
            ),
        )
        self._bandeja = IconoBandeja(
            al_abrir=self._en_hilo_principal(self._mostrar_ventana),
            al_salir=self._en_hilo_principal(self._salir),
        )
        self._bandeja.iniciar()
        if iniciar_oculta:
            self._raiz.after(RETRASO_OCULTAR_MS, self._raiz.withdraw)
        else:
            self._raiz.after(RETRASO_CENTRADO_MS, self._centrar_ventana)
        self._revisar_horario()

    def _crear_ventana_principal(self) -> ctk.CTk:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        raiz = ctk.CTk()
        raiz.title(TITULO_VENTANA)
        raiz.geometry(TAMANO_VENTANA)
        raiz.minsize(940, 680)
        raiz.protocol("WM_DELETE_WINDOW", self._ocultar_ventana)
        return raiz

    def ejecutar(self) -> None:
        self._raiz.mainloop()

    # ---------- ventana y bandeja ----------
    def _en_hilo_principal(self, accion: Callable[[], None]) -> Callable[[], None]:
        return lambda: self._raiz.after(0, accion)

    def _mostrar_ventana(self) -> None:
        self._raiz.deiconify()
        self._centrar_ventana()
        self._raiz.lift()
        self._raiz.focus_force()

    def _centrar_ventana(self) -> None:
        self._raiz.update()
        ventanas.centrar_ventana(self._raiz.winfo_id())

    def _ocultar_ventana(self) -> None:
        self._raiz.withdraw()
        if not self._aviso_bandeja_mostrado:
            self._aviso_bandeja_mostrado = True
            self._bandeja.avisar(MENSAJE_EN_BANDEJA)

    def _salir(self) -> None:
        self._bandeja.detener()
        self._raiz.destroy()

    # ---------- acciones de la interfaz ----------
    def _guardar(self, nueva: Configuracion) -> None:
        self._configuracion = nueva
        guardar_configuracion(nueva)
        self._programador.actualizar_configuracion(nueva)
        configurar_inicio_automatico(nueva.iniciar_con_windows)

    def _probar(self, configuracion: Configuracion) -> None:
        self._iniciar_bloqueo(configuracion, Marcacion("Prueba", "--:--"))

    def _desinstalar(self) -> None:
        lanzar_desinstalacion()
        self._salir()

    # ---------- ciclo principal ----------
    def _revisar_horario(self) -> None:
        if not self._hay_bloqueo_activo():
            marcacion = self._programador.marcacion_pendiente(datetime.now())
            if marcacion:
                self._iniciar_bloqueo(self._configuracion, marcacion)
        self._raiz.after(INTERVALO_REVISION_MS, self._revisar_horario)

    def _hay_bloqueo_activo(self) -> bool:
        return self._bloqueador is not None and self._bloqueador.activo

    def _iniciar_bloqueo(self, configuracion: Configuracion, marcacion: Marcacion) -> None:
        if not self._hay_bloqueo_activo():
            self._bloqueador = Bloqueador(self._raiz, configuracion, marcacion)


def _avisar_que_ya_esta_ejecutando() -> None:
    ctypes.windll.user32.MessageBoxW(0, MENSAJE_YA_EJECUTANDO, TITULO_VENTANA, 0x40)


def main() -> None:
    if sys.platform != "win32":
        sys.exit("Este programa usa funciones de Windows.")
    if not es_primera_instancia():
        _avisar_que_ya_esta_ejecutando()
        return
    Aplicacion(iniciar_oculta=ARGUMENTO_MINIMIZADO in sys.argv).ejecutar()


if __name__ == "__main__":
    main()
