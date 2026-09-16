# Config/settings.py
#
# Fuente única de configuración. Todos los módulos leen de aquí.
# Los valores pueden sobreescribirse mediante variables de entorno (útil en AWS).

import os
from pathlib import Path

# ── Modo de ejecución ─────────────────────────────────────────────────────────
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# ── Modo de arranque (true para ignorar snapshots) ────────────────────────────
FRESH: bool = os.getenv("FRESH", "false").lower() == "true"

# ── LOG LEVEL ────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Conexión con Unity ────────────────────────────────────────────────────────
UNITY_HOST: str = os.getenv("UNITY_HOST", "127.0.0.1")
UNITY_PORT: int = int(os.getenv("UNITY_PORT", "5069" if DEBUG else "5001"))

# ── Conexión con comunicaciones_remoto_server ────────────────────────────────────────────────────────
COMUNICACIONES_REMOTO_HOST = os.getenv("COMUNICACIONES_REMOTO_HOST", "[::]")
COMUNICACIONES_REMOTO_PORT: int = int(os.getenv("COMUNICACIONES_REMOTO_PORT", 50500))
LOGICA_MUNDO_ADDRESS = os.getenv("LOGICA_MUNDO_ADDRESS", "localhost:50250")
GESTOR_MUNDO_ADDRESS = os.getenv("GESTOR_MUNDO_ADDRESS", "localhost:50200")
GESTOR_BOTS_ADDRESS = os.getenv("GESTOR_BOTS_ADDRESS", "localhost:50051")
LOG_LEVEL_REMOTE_SERVER = os.getenv("LOG_LEVEL_REMOTE_SERVER", "INFO")


# ── Bots ────────────────────────────────────────────────────────
GESTOR_BOTS_HOST = os.getenv("GESTOR_BOTS_HOST", "[::]")
GESTOR_BOTS_PORT: int = int(os.getenv("GESTOR_BOTS_PORT", 50051))
GESTOR_BOTS_WORKERS: int = int(os.getenv("GESTOR_BOTS_WORKERS", 10))
BOTS_POR_HYPERVISOR: int = int(os.getenv("BOTS_POR_HYPERVISOR", 100))
UMBRAL_HV_CAIDO_SEGUNDOS = float(os.getenv("UMBRAL_HV_CAIDO_SEGUNDOS", 90))
HYPERVISOR_ID = os.getenv("HYPERVISOR_ID", "hv_00")
HYPERVISOR_HOST = os.getenv("HYPERVISOR_HOST", "localhost")
HYPERVISOR_PORT = int(os.getenv("HYPERVISOR_PORT", 50300))
HYPERVISOR_PROXY_PORT = int(os.getenv("HYPERVISOR_PROXY_PORT", 50400))
HYPERVISOR_CAPACITY = int(os.getenv("HYPERVISOR_CAPACITY", 32))
HYPERVISOR_COUNT = int(os.getenv("HYPERVISOR_COUNT", 1))
HYPERVISOR_PROXY_BASE_PORT = int(os.getenv("HYPERVISOR_PROXY_BASE_PORT", 50400))

# ── Mundo ─────────────────────────────────────────────────────────────────────
MAX_VISION_DISTANCE = int(
    os.getenv("MAX_VISION_DISTANCE", 50)
)  # la distancia de vision es la maxima distancia de interaccion
GRID_WIDTH = int(os.getenv("GRID_WIDTH", 100))
GRID_HEIGHT = int(os.getenv("GRID_HEIGHT", 100))
SECTOR_SIZE = int(os.getenv("SECTOR_SIZE", 100))
ATMOSFERA_ESCALA: int = int(os.getenv(
    "ATMOSFERA_ESCALA", 2
))  # tamaño relativo del grid atmosferico respecto al grid del suelo

SOUND_MAP_CELL_SIZE = int(os.getenv("SOUND_MAP_CELL_SIZE", 10))
TICK_TIMEOUT_MS = int(os.getenv("TICK_TIMEOUT_MS", 500))
TICKS_ANTES_DE_DORMIR = int(os.getenv("TICKS_ANTES_DE_DORMIR", 10))
UNITY_FRAME_EVERY_N_TICKS = int(os.getenv("UNITY_FRAME_EVERY_N_TICKS", 1))
SNAPSHOT_INTERVAL_TICKS = int(os.getenv("SNAPSHOT_INTERVAL_TICKS", 100))
DEEP_SAVE_INTERVAL_TICKS = int(os.getenv("DEEP_SAVE_INTERVAL_TICKS", 500))
SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "/data/snapshots"))
GESTOR_MUNDO_PORT = int(os.getenv("GESTOR_MUNDO_PORT", 50200))
DEFAULT_HV_BUDGET = int(os.getenv("DEFAULT_HV_BUDGET", 100))

# ── Gestor Mundo ──────────────────────────────────────────────────────────────
DEFAULT_TICK_RATE: int = int(os.getenv("DEFAULT_TICK_RATE", 2))  # 0 = sin límite
GESTOR_MUNDO_HOST = os.getenv("GESTOR_MUNDO_HOST", "[::]")
SECTOR_BASE_PORT = int(os.getenv("SECTOR_BASE_PORT", 50100))
FALLOS_CONSECUTIVOS_SECTOR_CAIDO = int(os.getenv("FALLOS_CONSECUTIVOS_SECTOR_CAIDO", 3))
GESTOR_MUNDO_WORKERS = int(os.getenv("GESTOR_MUNDO_WORKERS", 4))
SNAPSHOT_MAX = int(os.getenv("SNAPSHOT_MAX", "20"))

# ── Logica Mundo ──────────────────────────────────────────────────────────────
LOGICA_MUNDO_HOST = os.getenv("LOGICA_MUNDO_HOST", "[::]")
LOGICA_MUNDO_PORT = int(os.getenv("LOGICA_MUNDO_PORT", 50250))

# ── Sector Server ──────────────────────────────────────────────────────────────
SECTOR_COL = int(os.getenv("SECTOR_COL", 0))
SECTOR_ROW = int(os.getenv("SECTOR_ROW", 0))
SECTOR_HOST = os.getenv("SECTOR_HOST", "localhost")
SECTOR_PORT = int(os.getenv("SECTOR_PORT", 50100))
SECTOR_WORKERS = int(os.getenv("SECTOR_WORKERS", 4))


# ── Consola ──────────────────────────────────────────────────────────────
COMUNICACIONES_REMOTO_ADDRESS = os.getenv("COMUNICACIONES_REMOTO_ADDRESS")

# ── Loop principal ────────────────────────────────────────────────────────────
MS_POR_FRAME: int = int(os.getenv("MS_POR_FRAME", "32"))

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

# ── S3 ────────────────────────────────────────────────
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_PREFIX = os.getenv("S3_PREFIX", "snapshots/sectores")
