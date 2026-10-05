"""Ventana modal, centrada y siempre al frente, para ingresar el código de emergencia."""
from typing import Callable

import customtkinter as ctk

import ventanas

TAMANO = "460x290"
RETRASO_ENFOQUE_MS = 250
COLOR_ERROR = "#ef5350"
COLOR_NEUTRO = "#555555"
COLOR_NEUTRO_HOVER = "#3d3d3d"
COLOR_DESBLOQUEAR = "#2e7d32"
COLOR_DESBLOQUEAR_HOVER = "#1b5e20"
MENSAJE_ERROR = "Código incorrecto. Inténtalo de nuevo."


class DialogoEmergencia(ctk.CTkToplevel):
    def __init__(
        self,
        raiz: ctk.CTk,
        codigo_correcto: str,
        al_aceptar: Callable[[], None],
        al_cerrar: Callable[[], None],
    ):
        super().__init__(raiz)
        self._codigo_correcto = codigo_correcto
        self._al_aceptar = al_aceptar
        self._al_cerrar = al_cerrar
        self.title("Código de emergencia")
        self.geometry(TAMANO)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        self._construir()
        self.update_idletasks()
        ventanas.centrar_ventana(self)
        self.after(RETRASO_ENFOQUE_MS, self._traer_al_frente)

    # ---------- construcción ----------
    def _construir(self) -> None:
        marco = ctk.CTkFrame(self, fg_color="transparent")
        marco.pack(fill="both", expand=True, padx=28, pady=22)
        ctk.CTkLabel(
            marco, text="🔒  Código de emergencia",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            marco, text="Ingresa tu código para desbloquear la pantalla.", text_color="gray",
        ).pack(anchor="w", pady=(2, 14))
        self._campo = ctk.CTkEntry(marco, show="•", height=42, font=ctk.CTkFont(size=16))
        self._campo.pack(fill="x")
        self._campo.bind("<Return>", lambda _: self._aceptar())
        self._error = ctk.CTkLabel(marco, text=" ", text_color=COLOR_ERROR)
        self._error.pack(anchor="w", pady=(6, 0))
        self._construir_botones(marco)

    def _construir_botones(self, marco: ctk.CTkFrame) -> None:
        fila = ctk.CTkFrame(marco, fg_color="transparent")
        fila.pack(side="bottom", fill="x")
        ctk.CTkButton(
            fila, text="Cancelar", height=40, command=self._cancelar,
            fg_color=COLOR_NEUTRO, hover_color=COLOR_NEUTRO_HOVER,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            fila, text="Desbloquear", height=40, command=self._aceptar,
            fg_color=COLOR_DESBLOQUEAR, hover_color=COLOR_DESBLOQUEAR_HOVER,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    # ---------- comportamiento ----------
    def _traer_al_frente(self) -> None:
        ventanas.activar_aplicacion_propia()
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()
        self._campo.focus_set()

    def _aceptar(self) -> None:
        if self._campo.get() == self._codigo_correcto:
            self.destroy()
            self._al_aceptar()
            return
        self._error.configure(text=MENSAJE_ERROR)
        self._campo.delete(0, "end")
        self._campo.focus_set()

    def _cancelar(self) -> None:
        self.destroy()
        self._al_cerrar()
