"""Modelo de configuración y su persistencia en disco."""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

RUTA_CONFIGURACION = Path.home() / "marcador_asistencia.json"
DIAS_SEMANA = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")


@dataclass
class Marcacion:
    nombre: str
    hora: str  # formato "HH:MM"
    activa: bool = True


def _marcaciones_por_defecto() -> list[Marcacion]:
    return [
        Marcacion("Entrada", "08:00"),
        Marcacion("Salida a refrigerio", "13:00"),
        Marcacion("Regreso de refrigerio", "14:00"),
        Marcacion("Salida", "17:00"),
    ]


@dataclass
class Configuracion:
    url: str = "https://"
    palabras_titulo: str = ""  # separadas por coma
    permitir_navegador_completo: bool = True
    alarma_sonora: bool = True
    dias_laborales: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    limite_bloqueo_minutos: int = 15
    codigo_emergencia: str = "1234"
    iniciar_con_windows: bool = True
    marcaciones: list[Marcacion] = field(default_factory=_marcaciones_por_defecto)


def _migrar_formato_anterior(datos: dict) -> dict:
    if "palabra_titulo" in datos:
        datos["palabras_titulo"] = datos.pop("palabra_titulo")
    return datos


def cargar_configuracion() -> Configuracion:
    if not RUTA_CONFIGURACION.exists():
        return Configuracion()
    try:
        datos = _migrar_formato_anterior(
            json.loads(RUTA_CONFIGURACION.read_text(encoding="utf-8"))
        )
        datos["marcaciones"] = [Marcacion(**m) for m in datos["marcaciones"]]
        return Configuracion(**datos)
    except (ValueError, KeyError, TypeError):
        return Configuracion()


def guardar_configuracion(configuracion: Configuracion) -> None:
    contenido = json.dumps(asdict(configuracion), indent=2, ensure_ascii=False)
    RUTA_CONFIGURACION.write_text(contenido, encoding="utf-8")
