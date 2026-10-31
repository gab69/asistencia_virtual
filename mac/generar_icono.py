"""Genera icono.icns. Lo usa construir_mac.sh."""
from icono import crear_imagen

TAMANO_BASE_ICNS = 1024

if __name__ == "__main__":
    crear_imagen(TAMANO_BASE_ICNS).save("icono.icns")
    print("icono.icns generado")
