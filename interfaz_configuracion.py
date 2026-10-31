"""Ventana moderna (CustomTkinter): todo visible en dos columnas, sin desplazarse."""
from dataclasses import dataclass
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from componentes import FilaMarcacion, Tarjeta, campo_texto, nota
from configuracion import DIAS_SEMANA, Configuracion

MARGEN = 16
OPCIONES_LIMITE = ["5", "10", "15", "20", "30", "45", "60"]
COLOR_PELIGRO = "#c62828"
COLOR_PELIGRO_HOVER = "#8e0000"
COLOR_NEUTRO = "#555555"
COLOR_NEUTRO_HOVER = "#3d3d3d"
CREDITO = "Desarrollado por @GabRec"


@dataclass
class Acciones:
    guardar: Callable[[Configuracion], None]
    probar: Callable[[Configuracion], None]
    probar_sonido: Callable[[], None]
    desinstalar: Callable[[], None]
    salir: Callable[[], None]


class VentanaConfiguracion:
    def __init__(self, raiz: ctk.CTk, configuracion: Configuracion, acciones: Acciones):
        self._raiz = raiz
        self._acciones = acciones
        self._construir_encabezado()
        self._construir_botones()
        izquierda, derecha = self._crear_columnas()
        self._construir_seccion_pagina(izquierda, configuracion)
        self._construir_seccion_seguridad(izquierda, configuracion)
        self._construir_seccion_horarios(derecha, configuracion)
        self._construir_seccion_dias(derecha, configuracion)
        self._construir_seccion_sistema(derecha, configuracion)

    # ---------- estructura ----------
    def _construir_encabezado(self) -> None:
        encabezado = ctk.CTkFrame(self._raiz, fg_color="transparent")
        encabezado.pack(fill="x", padx=20, pady=(16, 8))
        textos = ctk.CTkFrame(encabezado, fg_color="transparent")
        textos.pack(side="left")
        ctk.CTkLabel(
            textos, text="Marcador de asistencia",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            textos, text="Nunca más olvides marcar tu entrada y salida.",
            text_color="gray",
        ).pack(anchor="w")
        ctk.CTkLabel(
            encabezado, text=CREDITO, text_color="gray",
            font=ctk.CTkFont(size=12, slant="italic"),
        ).pack(side="right", anchor="s")

    def _construir_botones(self) -> None:
        contenedor = ctk.CTkFrame(self._raiz, fg_color="transparent")
        contenedor.pack(side="bottom", fill="x", padx=20, pady=12)
        ctk.CTkButton(
            contenedor, text="Guardar", height=40, command=self._guardar
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            contenedor, text="Probar bloqueo", height=40, command=self._probar,
            fg_color=COLOR_NEUTRO, hover_color=COLOR_NEUTRO_HOVER,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _crear_columnas(self) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
        contenedor = ctk.CTkFrame(self._raiz, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=MARGEN // 2)
        contenedor.grid_columnconfigure((0, 1), weight=1, uniform="columnas")
        contenedor.grid_rowconfigure(0, weight=1)
        izquierda = ctk.CTkFrame(contenedor, fg_color="transparent")
        derecha = ctk.CTkFrame(contenedor, fg_color="transparent")
        izquierda.grid(row=0, column=0, sticky="nsew")
        derecha.grid(row=0, column=1, sticky="nsew")
        return izquierda, derecha

    @staticmethod
    def _nueva_tarjeta(columna: ctk.CTkFrame, titulo: str) -> Tarjeta:
        tarjeta = Tarjeta(columna, titulo)
        tarjeta.pack(fill="x", padx=MARGEN // 2, pady=5)
        return tarjeta

    # ---------- columna izquierda ----------
    def _construir_seccion_pagina(self, columna, configuracion: Configuracion) -> None:
        tarjeta = self._nueva_tarjeta(columna, "🌐  Página de asistencia")
        self._url = campo_texto(tarjeta, "Dirección (URL)", configuracion.url)
        self._palabras = campo_texto(
            tarjeta, "Palabras del título de la pestaña (separadas por coma)",
            configuracion.palabras_titulo,
        )
        self._navegador_completo = ctk.CTkSwitch(
            tarjeta.contenido, text="Permitir todo el navegador (para iniciar sesión)"
        )
        if configuracion.permitir_navegador_completo:
            self._navegador_completo.select()
        self._navegador_completo.pack(anchor="w", pady=(4, 2))
        nota(
            tarjeta,
            "Desactívalo para bloquear también otras pestañas. En ese caso, agrega arriba "
            "el título de la página de login (por ejemplo: Asistencia, Iniciar sesión).",
        )

    def _construir_seccion_seguridad(self, columna, configuracion: Configuracion) -> None:
        tarjeta = self._nueva_tarjeta(columna, "🔒  Seguridad y alarma")
        self._construir_fila_alarma(tarjeta, configuracion)
        ctk.CTkLabel(tarjeta.contenido, text="Liberar automáticamente tras (minutos)", anchor="w").pack(fill="x")
        self._limite = ctk.CTkOptionMenu(tarjeta.contenido, values=OPCIONES_LIMITE, width=90)
        self._limite.set(str(configuracion.limite_bloqueo_minutos))
        self._limite.pack(anchor="w", pady=(2, 8))
        self._codigo = campo_texto(
            tarjeta, "Código de emergencia", configuracion.codigo_emergencia, oculto=True
        )

    def _construir_fila_alarma(self, tarjeta: Tarjeta, configuracion: Configuracion) -> None:
        fila = ctk.CTkFrame(tarjeta.contenido, fg_color="transparent")
        fila.pack(fill="x", pady=(0, 10))
        self._alarma = ctk.CTkSwitch(fila, text="Alarma sonora al bloquear")
        if configuracion.alarma_sonora:
            self._alarma.select()
        self._alarma.pack(side="left")
        ctk.CTkButton(
            fila, text="🔊 Probar", width=90, command=self._acciones.probar_sonido,
            fg_color=COLOR_NEUTRO, hover_color=COLOR_NEUTRO_HOVER,
        ).pack(side="right")

    # ---------- columna derecha ----------
    def _construir_seccion_horarios(self, columna, configuracion: Configuracion) -> None:
        tarjeta = self._nueva_tarjeta(columna, "⏰  Horarios de marcación")
        self._filas = []
        for marcacion in configuracion.marcaciones:
            fila = FilaMarcacion(tarjeta.contenido, marcacion)
            fila.pack(fill="x", pady=4)
            self._filas.append(fila)

    def _construir_seccion_dias(self, columna, configuracion: Configuracion) -> None:
        tarjeta = self._nueva_tarjeta(columna, "📅  Días laborales")
        fila = ctk.CTkFrame(tarjeta.contenido, fg_color="transparent")
        fila.pack(fill="x")
        self._dias = []
        for indice, nombre in enumerate(DIAS_SEMANA):
            caja = ctk.CTkCheckBox(fila, text=nombre, width=54, checkbox_width=20, checkbox_height=20)
            if indice in configuracion.dias_laborales:
                caja.select()
            caja.pack(side="left")
            self._dias.append(caja)

    def _construir_seccion_sistema(self, columna, configuracion: Configuracion) -> None:
        tarjeta = self._nueva_tarjeta(columna, "⚙️  Sistema")
        self._inicio_windows = ctk.CTkSwitch(tarjeta.contenido, text="Iniciar con Windows")
        if configuracion.iniciar_con_windows:
            self._inicio_windows.select()
        self._inicio_windows.pack(anchor="w", pady=(0, 10))
        fila = ctk.CTkFrame(tarjeta.contenido, fg_color="transparent")
        fila.pack(fill="x")
        ctk.CTkButton(
            fila, text="Salir del programa", command=self._acciones.salir,
            fg_color=COLOR_NEUTRO, hover_color=COLOR_NEUTRO_HOVER,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            fila, text="Desinstalar", command=self._confirmar_desinstalacion,
            fg_color=COLOR_PELIGRO, hover_color=COLOR_PELIGRO_HOVER,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    # ---------- lectura y validación ----------
    def _leer_configuracion(self) -> Configuracion:
        return Configuracion(
            url=self._url.get().strip(),
            palabras_titulo=self._palabras.get().strip(),
            permitir_navegador_completo=bool(self._navegador_completo.get()),
            alarma_sonora=bool(self._alarma.get()),
            dias_laborales=[i for i, caja in enumerate(self._dias) if caja.get()],
            limite_bloqueo_minutos=int(self._limite.get()),
            codigo_emergencia=self._codigo.get(),
            iniciar_con_windows=bool(self._inicio_windows.get()),
            marcaciones=[fila.a_marcacion() for fila in self._filas],
        )

    @staticmethod
    def _buscar_error(configuracion: Configuracion) -> str | None:
        if not configuracion.url.startswith(("http://", "https://")):
            return "La dirección debe empezar con http:// o https://"
        if not configuracion.permitir_navegador_completo and not configuracion.palabras_titulo:
            return "Escribe al menos una palabra del título, o permite todo el navegador."
        if not configuracion.dias_laborales:
            return "Selecciona al menos un día laboral."
        if not configuracion.codigo_emergencia:
            return "Define un código de emergencia."
        return None

    def _configuracion_valida(self) -> Configuracion | None:
        configuracion = self._leer_configuracion()
        error = self._buscar_error(configuracion)
        if error:
            messagebox.showwarning("Revisa los datos", error)
            return None
        return configuracion

    # ---------- acciones ----------
    def _guardar(self) -> None:
        configuracion = self._configuracion_valida()
        if configuracion:
            self._acciones.guardar(configuracion)
            messagebox.showinfo("Listo", "Configuración guardada.")

    def _probar(self) -> None:
        configuracion = self._configuracion_valida()
        if configuracion:
            self._acciones.probar(configuracion)

    def _confirmar_desinstalacion(self) -> None:
        mensaje = (
            "Se cerrará el programa, se quitará el inicio automático y se borrarán "
            "el programa y tu configuración.\n\n¿Deseas continuar?"
        )
        if messagebox.askyesno("Desinstalar", mensaje):
            self._acciones.desinstalar()
