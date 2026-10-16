# Config/parametros_simulacion.py

from Config.settings import ATMOSFERA_ESCALA

# ---- Tiempo -----------------------------------------
SEGUNDOS_SIMULADOS_TICK = 1
TICKS_POR_DIA = round(
    60 * 60 * 24 / SEGUNDOS_SIMULADOS_TICK
)  # Cuantos ticks dura un dia simulado

# ---- Celdas -----------------------------------------
TAMANHO_CELDA_LOGICA = 1  # m, lado de una casilla
TAMANHO_CELDA_ATMOSFERICA = TAMANHO_CELDA_LOGICA * ATMOSFERA_ESCALA


# ---- Planeta -----------------------------------------
# Radiación máxima al mediodía en el ecuador, en W/m² (valor real aproximado
# de la constante solar en superficie).
RADIACION_MAXIMA: float = 1000.0

# Inclinación axial real de la Tierra -- ajustable si se quiere un
# planeta con estaciones más o menos marcadas.
INCLINACION_AXIAL_GRADOS: float = 23.44
