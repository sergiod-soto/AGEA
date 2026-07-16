# Config/settings.py
#
# Fuente única de configuración. Todos los módulos leen de aquí.
# Los valores pueden sobreescribirse mediante variables de entorno (útil en AWS).

import os

# ── Modo de ejecución ─────────────────────────────────────────────────────────
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# ── Modo de arranque (true para ignorar snapshots) ────────────────────────────
FRESH: bool = os.getenv("FRESH", "false").lower() == "true"

# ── Conexión con Unity ────────────────────────────────────────────────────────
UNITY_HOST: str = os.getenv("UNITY_HOST", "127.0.0.1")
UNITY_PORT: int = int(os.getenv("UNITY_PORT", "5069" if DEBUG else "5001"))

# ── Mundo ─────────────────────────────────────────────────────────────────────
ANCHO: int = int(os.getenv("ANCHO", "1000"))
ALTO: int = int(os.getenv("ALTO", "1000"))
MAX_VISION_DISTANCE: int = int(os.getenv("MAX_VISION_DISTANCE", "50"))

# ── Gestor Mundo ──────────────────────────────────────────────────────────────
DEFAULT_TICK_RATE: int = int(os.getenv("DEFAULT_TICK_RATE", 0))  # 0 = sin límite

# ── Loop principal ────────────────────────────────────────────────────────────
MS_POR_FRAME: int = int(os.getenv("MS_POR_FRAME", "500"))

# ── Perfiles ──────────────────────────────────────────────────────────────────
NUM_PERFILES: int = int(os.getenv("NUM_PERFILES", "6"))

# ── Ficheros ──────────────────────────────────────────────────────────────────
NOMBRE_FICHERO_URLS: str = os.getenv("NOMBRE_FICHERO_URLS", "Urls.csv")

# ── Directorio raíz de logs ────────────────────────────────────────────────
LOG_DIR: str = os.getenv("LOG_DIR", "Logs/")

# ── Modo de arranque: "local" o "remoto"/"produccion" ─────────────────────────
# Lo fija main.py al lanzar cada subproceso (mismo mecanismo que FRESH: se
# hereda vía os.environ.copy(), sin pasar argumentos por línea de comandos).
# Cada _server.py lo usa para decidir si loguea directo a fichero (local,
# sin red) o acumula en buffer + expone PullLogs (remoto, sin conexión
# entrante hacia el ordenador local).
MODO: str = os.getenv("MODO", "local")

# ── Intervalo de polling de logs en modo remoto (segundos) ────────────────────
# main.py, en modo remoto, pregunta a cada componente cada este intervalo.
LOG_PULL_INTERVAL_SEGUNDOS: int = int(os.getenv("LOG_PULL_INTERVAL_SEGUNDOS", 5))

