# Config/settings.py
#
# Fuente única de configuración. Todos los módulos leen de aquí.
# Los valores pueden sobreescribirse mediante variables de entorno (útil en AWS).

import os
from pathlib import Path

from Services.Mundo.generacion_suelos import ParametrosGeneracion

# ── Modo de ejecución ─────────────────────────────────────────────────────────
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# ── Modo de arranque (true para ignorar snapshots) ────────────────────────────
FRESH: bool = os.getenv("FRESH", "false").lower() == "true"

# ── LOG LEVEL ────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

#
#
#
# ── Mundo ─────────────────────────────────────────────────────────────────────
#
MAX_VISION_DISTANCE = int(
    os.getenv("MAX_VISION_DISTANCE", 10)
)  # la distancia de vision es la maxima distancia de interaccion
#
#
# ---- ↓ SI SE MODIFICA, HAY QUE RETOCAR VARIABLES DEL CLIMA O SE ROMPE --------
ATMOSFERA_ESCALA: int = int(
    os.getenv("ATMOSFERA_ESCALA", 10)
)  # tamaño relativo del grid atmosferico respecto al grid del suelo
#
NUM_SECTORES_X = 6
NUM_SECTORES_Y = 6
#
# cantidad de celdas atmosfericas/sector (lado del cuadrado)
NUM_CELDAS_ATMOSFERA_POR_LADO_SECTOR = 2

#
#
#
SECTOR_SIZE = int(
    os.getenv(
        "SECTOR_SIZE",
        ATMOSFERA_ESCALA * ATMOSFERA_ESCALA * NUM_CELDAS_ATMOSFERA_POR_LADO_SECTOR,
    )
)
GRID_WIDTH = int(os.getenv("GRID_WIDTH", NUM_SECTORES_X * SECTOR_SIZE))
GRID_HEIGHT = int(os.getenv("GRID_HEIGHT", NUM_SECTORES_Y * SECTOR_SIZE))
#


#
SOUND_MAP_CELL_SIZE = int(os.getenv("SOUND_MAP_CELL_SIZE", 10))
MAX_SOUND_DISTANCE = int(os.getenv("MAX_SOUND_DISTANCE", 50))

# ── IDs especiales ────────────────────────────────────────────────────────
ID_CICLO_SOLAR: int = int(os.getenv("ID_CICLO_SOLAR", "1"))
ID_CICLO_LUNAR: int = int(os.getenv("ID_CICLO_LUNAR", "2"))
ID_RELOJ: int = int(os.getenv("ID_RELOJ", "3"))
ID_ESTACIONES: int = int(os.getenv("ID_ESTACIONES", "4"))
ID_LUZ_AMBIENTAL: int = int(os.getenv("ID_LUZ_AMBIENTAL", "5"))
ID_TEMPERATURA_ATMOSFERICA: int = int(os.getenv("ID_TEMPERATURA_ATMOSFERICA", "6"))
ID_PRESION: int = int(os.getenv("ID_PRESION", "7"))
ID_VIENTO: int = int(os.getenv("ID_VIENTO", "8"))
ID_HUMEDAD_ABSOLUTA: int = int(os.getenv("ID_HUMEDAD_ABSOLUTA", "9"))
ID_HUMEDAD_RELATIVA: int = int(os.getenv("ID_HUMEDAD_RELATIVA", "10"))
ID_CICLO_ANUAL: int = int(os.getenv("ID_CICLO_ANUAL", "11"))
ID_INVIERNO: int = int(os.getenv("ID_INVIERNO", "12"))
ID_PRIMAVERA: int = int(os.getenv("ID_PRIMAVERA", "13"))
ID_VERANO: int = int(os.getenv("ID_VERANO", "14"))
ID_OTONO: int = int(os.getenv("ID_OTONO", "15"))
ID_NUBE: int = int(os.getenv("ID_NUBE", "16"))
ID_LLUVIA: int = int(os.getenv("ID_LLUVIA", "17"))


# ── Unity ────────────────────────────────────────────────────────
UNITY_HOST: str = os.getenv("UNITY_HOST", "127.0.0.1")
UNITY_PORT: int = int(os.getenv("UNITY_PORT", "5069" if DEBUG else "5001"))
UNITY_FRAME_EVERY_N_TICKS = int(os.getenv("UNITY_FRAME_EVERY_N_TICKS", 1))


# ── Conexión con comunicaciones_remoto_server ────────────────────────────────────────────────────────
COMUNICACIONES_REMOTO_HOST = os.getenv("COMUNICACIONES_REMOTO_HOST", "[::]")
COMUNICACIONES_REMOTO_PORT: int = int(os.getenv("COMUNICACIONES_REMOTO_PORT", 60500))
LOGICA_MUNDO_ADDRESS = os.getenv("LOGICA_MUNDO_ADDRESS", "localhost:60250")
GESTOR_MUNDO_ADDRESS = os.getenv("GESTOR_MUNDO_ADDRESS", "localhost:60200")
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
DEFAULT_HV_BUDGET = int(os.getenv("DEFAULT_HV_BUDGET", 100))


# ── Gestor Mundo ──────────────────────────────────────────────────────────────
GESTOR_MUNDO_HOST = os.getenv("GESTOR_MUNDO_HOST", "[::]")
SECTOR_BASE_PORT = int(os.getenv("SECTOR_BASE_PORT", 60100))
FALLOS_CONSECUTIVOS_SECTOR_CAIDO = int(os.getenv("FALLOS_CONSECUTIVOS_SECTOR_CAIDO", 3))
GESTOR_MUNDO_WORKERS = int(os.getenv("GESTOR_MUNDO_WORKERS", 4))
SNAPSHOT_MAX = int(os.getenv("SNAPSHOT_MAX", "20"))
TICK_TIMEOUT_MS = int(os.getenv("TICK_TIMEOUT_MS", 500))
TICKS_ANTES_DE_DORMIR = int(os.getenv("TICKS_ANTES_DE_DORMIR", 10))
GESTOR_MUNDO_PORT = int(os.getenv("GESTOR_MUNDO_PORT", 60200))


# ── Logica Mundo ──────────────────────────────────────────────────────────────
LOGICA_MUNDO_HOST = os.getenv("LOGICA_MUNDO_HOST", "[::]")
LOGICA_MUNDO_PORT = int(os.getenv("LOGICA_MUNDO_PORT", 60250))

# ── Sector Server ──────────────────────────────────────────────────────────────
SECTOR_COL = int(os.getenv("SECTOR_COL", 0))
SECTOR_ROW = int(os.getenv("SECTOR_ROW", 0))
SECTOR_HOST = os.getenv("SECTOR_HOST", "localhost")
SECTOR_PORT = int(os.getenv("SECTOR_PORT", 60100))
SECTOR_WORKERS = int(os.getenv("SECTOR_WORKERS", 4))


# ── Consola ──────────────────────────────────────────────────────────────
COMUNICACIONES_REMOTO_ADDRESS = os.getenv("COMUNICACIONES_REMOTO_ADDRESS")

# ── Loop principal ────────────────────────────────────────────────────────────
TICKS_PROCESADOS_SEGUNDO: int = int(os.getenv("TICKS_PROCESADOS_SEGUNDO", 1))

# ── Ficheros ──────────────────────────────────────────────────────────────────
NOMBRE_FICHERO_URLS: str = os.getenv("NOMBRE_FICHERO_URLS", "Urls.csv")
SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "/data/snapshots"))
SNAPSHOT_INTERVAL_TICKS = int(os.getenv("SNAPSHOT_INTERVAL_TICKS", 100))
DEEP_SAVE_INTERVAL_TICKS = int(os.getenv("DEEP_SAVE_INTERVAL_TICKS", 500))


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


# ── Generacion inicial suelos ────────────────────────────────────────────────
SEMILLA_MUNDO: int = 430

PARAMETROS_MUNDO = ParametrosGeneracion(
    seed=SEMILLA_MUNDO,
    # Orografía
    proporcion_agua=0.4,  # fracción del mapa bajo el nivel del mar
    proporcion_montana=0.85,  # cuantil de tierra donde empieza montaña
    proporcion_piedra=0.97,  # cumbres altas
    banda_grava=0.08,  # piedemonte: montaña - banda
    ganancia_relieve=2.0,  # contraste del ruido de elevación
    octavas_orografia=5,
    # Tamaño de "continente" con fragmentacion = 0 (en celdas).
    escala_orografia=200.0,
    # 0.0 = una única masa continental (Pangea); 1.0 = mar lleno de
    # islitas. Ajusta la FRECUENCIA del ruido de elevación: a mayor
    # fragmentación, features más pequeños y tierra más troceada.
    fragmentacion=0.8,
    # Costas: fracción del lado menor que cae hacia el océano de borde.
    borde_oceano=0.15,
    # Altura del mapa: la elevación normalizada (0..1) se convierte a
    # METROS con 0 = nivel del mar. La cota más alta del mapa (elev=1)
    # queda a altura_maxima_metros; el fondo marino se aplana a 0.
    altura_maxima_metros=4500.0,
    # Clima
    penalizacion_altitud=1.2,  # cuánto enfría la altitud
    octavas_clima=3,
    escala_clima=150.0,
    # Ríos. Nacen SOLO en la frontera de las zonas de Suelo_Piedra y
    # bajan SIN LÍMITE de longitud: solo terminan en el mar o al unirse a
    # otro río. En un callejón sin salida forman un lago que, si su
    # cuenca desborda, da nacimiento a un río nuevo (el desagüe).
    num_rios=20,
    # Ancho de río. Los ríos NO tienen todos el mismo ancho: se engordan
    # por ANILLOS a partir del cauce, y el número de anillos se sortea en
    # función de la longitud REAL recorrida por el agua hasta ese tramo
    # (acumulada aguas arriba, ver CapaRios): un río corto casi nunca se
    # ensancha; uno largo es muy PROBABLE que lo sea, pero no seguro.
    # - ancho_max_rio: anillos máximos extra (ancho máx = 1 + anillo).
    # - longitud_ref_rio_ancho: longitud (celdas) a la que la probabilidad
    #   de ensancharse cada anillo llega a 1.0; antes crece linealmente.
    ancho_max_rio=20,
    longitud_ref_rio_ancho=4000.0,
    # Sinuosidad: cuánto se permite desviarse del descenso más directo.
    # 0.0 = siempre al vecino más bajo (líneas rectas/quebradas). Mayor
    # valor = el río elige entre TODOS los vecinos que bajan, con un
    # sorteo sesgado por la pendiente: aparecen meandros. En unidades de
    # elevación: 0.02-0.05 ya da curvas naturales.
    sinuosidad_rio=0.03,
    # Tope de seguridad: cuántos lagos puede encadenar un mismo
    # manantial (río -> lago -> desagüe -> lago -> ...) antes de que la
    # cadena se dé por muerta. Con cuencas normales no se llega, pero un
    # terreno muy raro podría patinar.
    max_lagos_por_rio=99999,
    # Tamaño mínimo de lago en celdas. La cuenca real donde se atasca el
    # río suele ser diminuta (2-4 celdas) porque el terreno fBm es liso;
    # si el lago queda por debajo de este tamaño, el agua SIGUE subiendo
    # (tragándose las casillas de la orilla más bajas primero) hasta
    # alcanzarlo. El desborde sigue siendo el punto de fuga más bajo.
    tamano_min_lago=16,
    # Humedad: distancia máx. (celdas) al agua que sigue influyendo.
    alcance_humedad=15,
    bono_humedad_agua=0.35,
    # Cuotas de suelo: fracción de la TIERRA EMERGIDA que ocupa cada
    # bioma. Se cumplen por CUANTILES + RANKING físico, así que son
    # exactas en cualquier seed y siguen siendo coherentes: el desierto
    # cae en lo más cálido y seco, el césped en lo más húmedo, el hielo
    # en los polos. Suelo_Tierra NO se configura: es el resto.
    proporcion_hielo=0.12,  # tundra polar + banquisa del mar
    proporcion_arena=0.10,  # desierto cálido y seco
    proporcion_cesped=0.30,  # praderas húmedas
    # Barro
    umbral_humedad_barro=0.55,
)

LADO_CUADRICULA: int = 200
