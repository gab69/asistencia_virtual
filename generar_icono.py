"""Genera icono.ico (para el .exe y el instalador). Lo usa construir_instalador.bat."""
from icono import crear_imagen

TAMANOS = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

if __name__ == "__main__":
    crear_imagen(256).save("icono.ico", sizes=TAMANOS)
    print("icono.ico generado")
