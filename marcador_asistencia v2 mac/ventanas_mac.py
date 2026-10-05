"""Manejo de aplicaciones y ventanas en macOS.

En macOS el bloqueo trabaja por aplicación: una "ventana" se identifica por el
id de proceso (pid) de su aplicación. Ocultar y activar aplicaciones no requiere
permisos; ajustar el tamaño de la ventana del navegador sí requiere el permiso
de Accesibilidad.
"""
import os
import subprocess
import tkinter as tk
from typing import Callable

from AppKit import (
    NSApplication,
    NSApplicationActivateIgnoringOtherApps,
    NSApplicationActivationPolicyRegular,
    NSRunningApplication,
    NSScreen,
    NSWorkspace,
)

_NAVEGADORES = {
    "com.google.Chrome", "com.apple.Safari", "org.mozilla.firefox",
    "com.microsoft.edgemac", "com.brave.Browser", "com.operasoftware.Opera",
    "com.vivaldi.Vivaldi", "company.thebrowser.Browser",
}


def _aplicacion(pid: int):
    return NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)


def _es_aplicacion_normal(aplicacion) -> bool:
    return aplicacion.activationPolicy() == NSApplicationActivationPolicyRegular


# ---------- consulta ----------
def ventana_en_primer_plano() -> int:
    aplicacion = NSWorkspace.sharedWorkspace().frontmostApplication()
    return aplicacion.processIdentifier() if aplicacion else 0


def titulo_de(pid: int) -> str:
    """Nombre de la aplicación; vacío para servicios del sistema (Dock, Spotlight...)."""
    aplicacion = _aplicacion(pid)
    if aplicacion is None or not _es_aplicacion_normal(aplicacion):
        return ""
    return aplicacion.localizedName() or ""


def esta_minimizada(pid: int) -> bool:
    aplicacion = _aplicacion(pid)
    return aplicacion is not None and bool(aplicacion.isHidden())


def es_ventana_propia(pid: int) -> bool:
    return pid == os.getpid()


def es_ventana_de_navegador(pid: int) -> bool:
    aplicacion = _aplicacion(pid)
    return aplicacion is not None and aplicacion.bundleIdentifier() in _NAVEGADORES


def buscar_ventana(condicion: Callable[[int], bool]) -> int | None:
    """Primera aplicación normal, distinta de esta, que cumpla la condición."""
    for aplicacion in NSWorkspace.sharedWorkspace().runningApplications():
        pid = aplicacion.processIdentifier()
        if _es_aplicacion_normal(aplicacion) and pid != os.getpid() and condicion(pid):
            return pid
    return None


# ---------- acciones ----------
def minimizar(pid: int) -> None:
    aplicacion = _aplicacion(pid)
    if aplicacion is not None:
        aplicacion.hide()


def traer_al_frente_maximizada(pid: int) -> None:
    aplicacion = _aplicacion(pid)
    if aplicacion is None:
        return
    aplicacion.unhide()
    aplicacion.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
    _ajustar_primera_ventana_a_la_pantalla(pid)


def _ajustar_primera_ventana_a_la_pantalla(pid: int) -> None:
    """Restaura y ocupa toda el área visible. Necesita permiso de Accesibilidad."""
    x, y, ancho, alto = _area_visible()
    script = f"""
    tell application "System Events"
        set proceso to first process whose unix id is {pid}
        set frontmost of proceso to true
        tell proceso
            if (count of windows) > 0 then
                try
                    set value of attribute "AXMinimized" of window 1 to false
                end try
                set position of window 1 to {{{x}, {y}}}
                set size of window 1 to {{{ancho}, {alto}}}
            end if
        end tell
    end tell
    """
    subprocess.Popen(
        ["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def activar_aplicacion_propia() -> None:
    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)


# ---------- posición y tamaño ----------
def _area_visible() -> tuple[int, int, int, int]:
    """(x, y, ancho, alto) sin Dock ni barra de menús, con el origen arriba a la izquierda."""
    pantalla = NSScreen.mainScreen()
    marco, visible = pantalla.frame(), pantalla.visibleFrame()
    x = int(visible.origin.x)
    y = int(marco.size.height - visible.origin.y - visible.size.height)
    return x, y, int(visible.size.width), int(visible.size.height)


def ancho_de_pantalla() -> int:
    return int(NSScreen.mainScreen().frame().size.width)


def centrar_ventana(ventana: tk.Misc) -> None:
    ventana.update_idletasks()
    x0, y0, ancho_area, alto_area = _area_visible()
    x = x0 + (ancho_area - ventana.winfo_width()) // 2
    y = y0 + (alto_area - ventana.winfo_height()) // 2
    ventana.wm_geometry(f"+{max(x, x0)}+{max(y, y0)}")


def fijar_arriba_y_encima(ventana: tk.Misc, ancho: int, alto: int) -> None:
    ventana.geometry(f"{ancho}x{alto}+0+0")
    ventana.attributes("-topmost", True)
