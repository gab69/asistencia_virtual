"""Elige la implementación de manejo de ventanas según el sistema operativo."""
from plataforma import ES_WINDOWS

if ES_WINDOWS:
    from ventanas_windows import (
        activar_aplicacion_propia, ancho_de_pantalla, buscar_ventana, centrar_ventana,
        es_ventana_de_navegador, es_ventana_propia, esta_minimizada,
        fijar_arriba_y_encima, minimizar, titulo_de, traer_al_frente_maximizada,
        ventana_en_primer_plano,
    )
else:
    from ventanas_mac import (
        activar_aplicacion_propia, ancho_de_pantalla, buscar_ventana, centrar_ventana,
        es_ventana_de_navegador, es_ventana_propia, esta_minimizada,
        fijar_arriba_y_encima, minimizar, titulo_de, traer_al_frente_maximizada,
        ventana_en_primer_plano,
    )

__all__ = [
    "activar_aplicacion_propia", "ancho_de_pantalla", "buscar_ventana", "centrar_ventana",
    "es_ventana_de_navegador", "es_ventana_propia", "esta_minimizada",
    "fijar_arriba_y_encima", "minimizar", "titulo_de", "traer_al_frente_maximizada",
    "ventana_en_primer_plano",
]
