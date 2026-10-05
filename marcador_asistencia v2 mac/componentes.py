"""Componentes visuales reutilizables (CustomTkinter)."""
import customtkinter as ctk

from configuracion import Marcacion

RADIO_TARJETA = 14
MARGEN_TARJETA = 16


class Tarjeta(ctk.CTkFrame):
    """Panel redondeado con título; los widgets se agregan en `contenido`."""

    def __init__(self, padre, titulo: str):
        super().__init__(padre, corner_radius=RADIO_TARJETA)
        ctk.CTkLabel(
            self, text=titulo, font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=MARGEN_TARJETA, pady=(12, 6))
        self.contenido = ctk.CTkFrame(self, fg_color="transparent")
        self.contenido.pack(fill="x", padx=MARGEN_TARJETA, pady=(0, 12))


def campo_texto(tarjeta: Tarjeta, etiqueta: str, valor: str, oculto: bool = False) -> ctk.StringVar:
    variable = ctk.StringVar(value=valor)
    ctk.CTkLabel(tarjeta.contenido, text=etiqueta, anchor="w").pack(fill="x")
    ctk.CTkEntry(
        tarjeta.contenido, textvariable=variable, show="•" if oculto else ""
    ).pack(fill="x", pady=(2, 8))
    return variable


def nota(tarjeta: Tarjeta, texto: str) -> None:
    ctk.CTkLabel(
        tarjeta.contenido, text=texto, text_color="gray", anchor="w",
        justify="left", wraplength=400, font=ctk.CTkFont(size=12),
    ).pack(fill="x", pady=(0, 6))


class SelectorHora(ctk.CTkFrame):
    """Menús de horas y minutos: imposible escribir una hora inválida."""

    def __init__(self, padre, hora_inicial: str):
        super().__init__(padre, fg_color="transparent")
        horas, minutos = hora_inicial.split(":")
        self._horas = self._crear_menu(range(24), horas)
        ctk.CTkLabel(self, text=":").pack(side="left", padx=2)
        self._minutos = self._crear_menu(range(60), minutos)

    def _crear_menu(self, rango, valor_inicial: str) -> ctk.CTkOptionMenu:
        menu = ctk.CTkOptionMenu(self, values=[f"{n:02d}" for n in rango], width=70)
        menu.set(valor_inicial)
        menu.pack(side="left")
        return menu

    @property
    def valor(self) -> str:
        return f"{self._horas.get()}:{self._minutos.get()}"


class FilaMarcacion(ctk.CTkFrame):
    """Interruptor para activar la marcación + selector de hora."""

    def __init__(self, padre, marcacion: Marcacion):
        super().__init__(padre, fg_color="transparent")
        self._nombre = marcacion.nombre
        self._interruptor = ctk.CTkSwitch(self, text=marcacion.nombre)
        if marcacion.activa:
            self._interruptor.select()
        self._interruptor.pack(side="left")
        self._selector = SelectorHora(self, marcacion.hora)
        self._selector.pack(side="right")

    def a_marcacion(self) -> Marcacion:
        return Marcacion(self._nombre, self._selector.valor, bool(self._interruptor.get()))
