"""Sistema operativo en el que se ejecuta el programa."""
import sys

ES_WINDOWS = sys.platform == "win32"
ES_MAC = sys.platform == "darwin"
NOMBRE_SISTEMA = "Windows" if ES_WINDOWS else "macOS"
