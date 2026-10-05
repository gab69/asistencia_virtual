"""Funciones de bajo nivel para manipular ventanas en Windows."""
import ctypes
import os
import tkinter as tk
from ctypes import wintypes
from typing import Callable

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

_kernel32.OpenProcess.restype = ctypes.c_void_p
_kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
_user32.GetParent.argtypes = [ctypes.c_void_p]
_user32.GetParent.restype = ctypes.c_void_p
_user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.RECT)]
_user32.SystemParametersInfoW.argtypes = [
    ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint,
]
_user32.SetWindowPos.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint,
]

_SW_MINIMIZE = 6
_SW_SHOWMAXIMIZED = 3
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_SM_CXSCREEN = 0
_SPI_GETWORKAREA = 0x0030
_HWND_TOPMOST = -1
_SWP_NOSIZE = 0x0001
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_SWP_SHOWWINDOW = 0x0040
_TAMANO_MAXIMO_RUTA = 1024

_NAVEGADORES = {
    "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe",
    "opera.exe", "vivaldi.exe", "iexplore.exe",
}


# ---------- consulta ----------
def ventana_en_primer_plano() -> int:
    return _user32.GetForegroundWindow()


def titulo_de(ventana: int) -> str:
    largo = _user32.GetWindowTextLengthW(ventana)
    buffer = ctypes.create_unicode_buffer(largo + 1)
    _user32.GetWindowTextW(ventana, buffer, largo + 1)
    return buffer.value


def esta_minimizada(ventana: int) -> bool:
    return bool(_user32.IsIconic(ventana))


def _proceso_de(ventana: int) -> int:
    proceso = ctypes.c_ulong()
    _user32.GetWindowThreadProcessId(ventana, ctypes.byref(proceso))
    return proceso.value


def _hilo_de(ventana: int) -> int:
    return _user32.GetWindowThreadProcessId(ventana, None)


def es_ventana_propia(ventana: int) -> bool:
    return _proceso_de(ventana) == os.getpid()


def _nombre_de_programa(ventana: int) -> str:
    manejador = _kernel32.OpenProcess(
        _PROCESS_QUERY_LIMITED_INFORMATION, False, _proceso_de(ventana)
    )
    if not manejador:
        return ""
    try:
        ruta = ctypes.create_unicode_buffer(_TAMANO_MAXIMO_RUTA)
        largo = ctypes.c_ulong(_TAMANO_MAXIMO_RUTA)
        if _kernel32.QueryFullProcessImageNameW(manejador, 0, ruta, ctypes.byref(largo)):
            return os.path.basename(ruta.value).lower()
        return ""
    finally:
        _kernel32.CloseHandle(manejador)


def es_ventana_de_navegador(ventana: int) -> bool:
    return _nombre_de_programa(ventana) in _NAVEGADORES


def buscar_ventana(condicion: Callable[[int], bool]) -> int | None:
    """Primera ventana visible, con título, de otro programa que cumpla la condición."""
    encontradas: list[int] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def revisar(ventana, _):
        if _es_ventana_ajena_con_titulo(ventana) and condicion(ventana):
            encontradas.append(ventana)
        return True

    _user32.EnumWindows(revisar, 0)
    return encontradas[0] if encontradas else None


def _es_ventana_ajena_con_titulo(ventana: int) -> bool:
    return (
        bool(_user32.IsWindowVisible(ventana))
        and bool(titulo_de(ventana).strip())
        and not es_ventana_propia(ventana)
    )


# ---------- acciones sobre ventanas ----------
def minimizar(ventana: int) -> None:
    _user32.ShowWindow(ventana, _SW_MINIMIZE)


def traer_al_frente_maximizada(ventana: int) -> None:
    """Muestra la ventana a pantalla completa (maximizada) y le da el foco.

    Se acopla temporalmente al hilo de la ventana activa porque Windows
    impide que un programa en segundo plano robe el foco sin ese permiso.
    """
    activa = _user32.GetForegroundWindow()
    hilo_propio = _kernel32.GetCurrentThreadId()
    hilo_activo = _hilo_de(activa) if activa else 0
    acoplado = bool(hilo_activo) and hilo_activo != hilo_propio and bool(
        _user32.AttachThreadInput(hilo_propio, hilo_activo, True)
    )
    try:
        _user32.ShowWindow(ventana, _SW_SHOWMAXIMIZED)
        _user32.BringWindowToTop(ventana)
        _user32.SetForegroundWindow(ventana)
    finally:
        if acoplado:
            _user32.AttachThreadInput(hilo_propio, hilo_activo, False)


# ---------- posición y tamaño ----------
def ancho_de_pantalla() -> int:
    """Ancho real del monitor principal, en los mismos píxeles que usa Windows."""
    return _user32.GetSystemMetrics(_SM_CXSCREEN)


def _area_de_trabajo() -> wintypes.RECT:
    """Zona del monitor principal sin la barra de tareas."""
    area = wintypes.RECT()
    _user32.SystemParametersInfoW(_SPI_GETWORKAREA, 0, ctypes.byref(area), 0)
    return area


def centrar_ventana(ventana_tk: tk.Misc) -> None:
    identificador = ventana_tk.winfo_id()
    ventana = _user32.GetParent(identificador) or identificador
    marco = wintypes.RECT()
    _user32.GetWindowRect(ventana, ctypes.byref(marco))
    area = _area_de_trabajo()
    ancho, alto = marco.right - marco.left, marco.bottom - marco.top
    x = area.left + (area.right - area.left - ancho) // 2
    y = area.top + (area.bottom - area.top - alto) // 2
    _user32.SetWindowPos(
        ventana, None, max(x, area.left), max(y, area.top), 0, 0,
        _SWP_NOSIZE | _SWP_NOZORDER,
    )


def fijar_arriba_y_encima(ventana_tk: tk.Misc, ancho: int, alto: int) -> None:
    """Coloca la ventana en la esquina superior izquierda, con ese tamaño, sobre todas las demás."""
    identificador = ventana_tk.winfo_id()
    ventana = _user32.GetParent(identificador) or identificador
    _user32.SetWindowPos(
        ventana, _HWND_TOPMOST, 0, 0, ancho, alto, _SWP_NOACTIVATE | _SWP_SHOWWINDOW
    )


def activar_aplicacion_propia() -> None:
    """En Windows basta con `focus_force` de Tk; existe por compatibilidad con macOS."""
