# Config/settings.py
#
# Fuente única de configuración. Todos los módulos leen de aquí.
# Los valores pueden sobreescribirse mediante variables de entorno (útil en AWS).

import os

# ── Modo de ejecución ─────────────────────────────────────────────────────────
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# ── Conexión con Unity ────────────────────────────────────────────────────────
UNITY_HOST: str = os.getenv("UNITY_HOST", "127.0.0.1")
UNITY_PORT: int = int(os.getenv("UNITY_PORT", "5069" if DEBUG else "5001"))

# ── Mundo ─────────────────────────────────────────────────────────────────────
ANCHO: int = int(os.getenv("ANCHO", "1000"))
ALTO: int = int(os.getenv("ALTO", "1000"))
MAX_VISION_DISTANCE: int = int(os.getenv("MAX_VISION_DISTANCE", "50"))

# ── Loop principal ────────────────────────────────────────────────────────────
MS_POR_FRAME: int = int(os.getenv("MS_POR_FRAME", "500"))

# ── Perfiles ──────────────────────────────────────────────────────────────────
NUM_PERFILES: int = int(os.getenv("NUM_PERFILES", "6"))

# ── Ficheros ──────────────────────────────────────────────────────────────────
NOMBRE_FICHERO_URLS: str = os.getenv("NOMBRE_FICHERO_URLS", "Urls.csv")
