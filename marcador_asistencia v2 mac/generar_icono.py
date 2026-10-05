"""Genera icono.ico (Windows) e icono.icns (macOS). Lo usan los scripts de construcción."""
from icono import crear_imagen

TAMANOS_ICO = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
TAMANO_BASE_ICNS = 1024

if __name__ == "__main__":
    crear_imagen(256).save("icono.ico", sizes=TAMANOS_ICO)
    crear_imagen(TAMANO_BASE_ICNS).save("icono.icns")
    print("icono.ico e icono.icns generados")
