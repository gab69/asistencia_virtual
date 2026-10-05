"""Dibujo del icono del programa (círculo azul con check)."""
from PIL import Image, ImageDraw

TAMANO_BASE = 64
COLOR_FONDO = (37, 99, 235)
_CIRCULO = (2, 2, 62, 62)
_CHECK = [(18, 33), (28, 44), (47, 21)]
_GROSOR_CHECK = 7


def crear_imagen(tamano: int = TAMANO_BASE) -> Image.Image:
    escala = tamano / TAMANO_BASE
    imagen = Image.new("RGBA", (tamano, tamano), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(imagen)
    dibujo.ellipse([c * escala for c in _CIRCULO], fill=COLOR_FONDO)
    dibujo.line(
        [(x * escala, y * escala) for x, y in _CHECK],
        fill="white", width=round(_GROSOR_CHECK * escala), joint="curve",
    )
    return imagen
