"""Barra siempre visible que obliga a permanecer en la página de asistencia."""
import time
import tkinter as tk
import webbrowser

import customtkinter as ctk

import ventanas
from alarma import Alarma
from configuracion import Configuracion, Marcacion
from dialogo_emergencia import DialogoEmergencia

INTERVALO_VIGILANCIA_MS = 1000
SEGUNDOS_DE_GRACIA_AL_ABRIR = 8      # tiempo para que cargue la página sin molestarte
SEGUNDOS_ENTRE_APERTURAS = 10
ALTURA_MINIMA_BARRA = 60
COLOR_BARRA = "#c62828"
COLOR_CONFIRMAR = "#2e7d32"
COLOR_CONFIRMAR_HOVER = "#1b5e20"


class Bloqueador:
    def __init__(self, raiz: tk.Tk, configuracion: Configuracion, marcacion: Marcacion):
        self._raiz = raiz
        self._configuracion = configuracion
        self._marcacion = marcacion
        self._palabras = self._separar_palabras(configuracion.palabras_titulo)
        self._inicio = time.monotonic()
        self._ultima_apertura = float("-inf")
        self._pagina_maximizada = False
        self._dialogo: DialogoEmergencia | None = None
        self._alarma = Alarma()
        self.activo = True
        self._barra = self._crear_barra()
        if configuracion.alarma_sonora:
            self._alarma.iniciar()
        self._abrir_pagina()
        self._vigilar()

    @staticmethod
    def _separar_palabras(texto: str) -> list[str]:
        return [p.strip().lower() for p in texto.split(",") if p.strip()]

    # ---------- barra superior ----------
    def _crear_barra(self) -> tk.Toplevel:
        barra = tk.Toplevel(self._raiz)
        barra.overrideredirect(True)
        barra.attributes("-topmost", True)
        barra.configure(bg=COLOR_BARRA)
        self._agregar_mensaje(barra)
        self._agregar_boton(barra, "Ya marqué ✔", self.liberar, COLOR_CONFIRMAR, COLOR_CONFIRMAR_HOVER)
        self._agregar_boton(barra, "Emergencia", self._pedir_codigo_emergencia, "transparent", "#8e0000", borde=True)
        self._extender_de_lado_a_lado(barra)
        return barra

    @staticmethod
    def _extender_de_lado_a_lado(barra: tk.Toplevel) -> None:
        barra.update_idletasks()
        ancho = ventanas.ancho_de_pantalla()
        alto = max(ALTURA_MINIMA_BARRA, barra.winfo_reqheight())
        barra.geometry(f"{ancho}x{alto}+0+0")
        barra.update()
        ventanas.fijar_arriba_y_encima(barra, ancho, alto)

    def _agregar_mensaje(self, barra: tk.Toplevel) -> None:
        texto = f"⏰  Marca tu {self._marcacion.nombre.lower()} ahora. Mientras tanto, otras ventanas quedan bloqueadas."
        ctk.CTkLabel(
            barra, text=texto, text_color="white",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=20)

    @staticmethod
    def _agregar_boton(barra, texto, comando, color, color_hover, borde=False) -> None:
        ctk.CTkButton(
            barra, text=texto, command=comando, width=130, height=36,
            corner_radius=18, fg_color=color, hover_color=color_hover,
            bg_color=COLOR_BARRA, border_width=2 if borde else 0, border_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="right", padx=8, pady=12)

    # ---------- vigilancia ----------
    def _vigilar(self) -> None:
        if not self.activo:
            return
        if self._tiempo_agotado():
            self.liberar()
            return
        if self._debe_vigilar():
            self._mantener_en_pagina_de_asistencia()
        self._barra.attributes("-topmost", True)
        self._raiz.after(INTERVALO_VIGILANCIA_MS, self._vigilar)

    def _debe_vigilar(self) -> bool:
        """No se interviene mientras carga la página ni mientras se escribe el código."""
        return not self._esta_cargando_pagina() and self._dialogo is None

    def _tiempo_agotado(self) -> bool:
        limite_segundos = self._configuracion.limite_bloqueo_minutos * 60
        return time.monotonic() - self._inicio > limite_segundos

    def _esta_cargando_pagina(self) -> bool:
        return time.monotonic() - self._ultima_apertura < SEGUNDOS_DE_GRACIA_AL_ABRIR

    def _mantener_en_pagina_de_asistencia(self) -> None:
        en_primer_plano = ventanas.ventana_en_primer_plano()
        permitida = self._esta_permitida(en_primer_plano)
        if not permitida:
            ventanas.minimizar(en_primer_plano)
        destino = self._buscar_ventana_de_asistencia()
        if destino is None:
            self._abrir_pagina()
        elif self._debe_traer_al_frente(destino, permitida):
            ventanas.traer_al_frente_maximizada(destino)
            self._pagina_maximizada = True

    def _debe_traer_al_frente(self, pagina: int, ventana_actual_permitida: bool) -> bool:
        return (
            not ventana_actual_permitida
            or ventanas.esta_minimizada(pagina)
            or not self._pagina_maximizada
        )

    def _esta_permitida(self, ventana: int) -> bool:
        titulo = ventanas.titulo_de(ventana)
        return (
            not titulo.strip()
            or ventanas.es_ventana_propia(ventana)
            or self._coincide_con_palabras(titulo)
            or self._es_navegador_permitido(ventana)
        )

    def _es_navegador_permitido(self, ventana: int) -> bool:
        return (
            self._configuracion.permitir_navegador_completo
            and ventanas.es_ventana_de_navegador(ventana)
        )

    def _coincide_con_palabras(self, titulo: str) -> bool:
        titulo = titulo.lower()
        return any(palabra in titulo for palabra in self._palabras)

    def _buscar_ventana_de_asistencia(self) -> int | None:
        por_titulo = ventanas.buscar_ventana(
            lambda v: self._coincide_con_palabras(ventanas.titulo_de(v))
        )
        if por_titulo or not self._configuracion.permitir_navegador_completo:
            return por_titulo
        return ventanas.buscar_ventana(ventanas.es_ventana_de_navegador)

    def _abrir_pagina(self) -> None:
        if time.monotonic() - self._ultima_apertura < SEGUNDOS_ENTRE_APERTURAS:
            return
        webbrowser.open(self._configuracion.url)
        self._ultima_apertura = time.monotonic()
        self._pagina_maximizada = False  # se maximizará al terminar de cargar

    # ---------- salida ----------
    def _pedir_codigo_emergencia(self) -> None:
        if self._dialogo is not None:
            return
        self._dialogo = DialogoEmergencia(
            self._raiz,
            self._configuracion.codigo_emergencia,
            al_aceptar=self.liberar,
            al_cerrar=self._al_cerrar_dialogo,
        )

    def _al_cerrar_dialogo(self) -> None:
        self._dialogo = None

    def _cerrar_dialogo(self) -> None:
        if self._dialogo is None:
            return
        try:
            self._dialogo.destroy()
        except tk.TclError:
            pass  # ya estaba cerrado
        self._dialogo = None

    def liberar(self) -> None:
        self.activo = False
        self._alarma.detener()
        self._cerrar_dialogo()
        self._barra.destroy()
