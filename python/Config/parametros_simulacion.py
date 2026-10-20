# Config/parametros_simulacion.py

from Config.settings import ATMOSFERA_ESCALA

# ---- Tiempo -----------------------------------------
# -----------------------------------------------------
SEGUNDOS_SIMULADOS_TICK = 1


# ---- Celdas -----------------------------------------
# -----------------------------------------------------
TAMANHO_CELDA_LOGICA = 1  # m, lado de una casilla
TAMANHO_CELDA_ATMOSFERICA = TAMANHO_CELDA_LOGICA * ATMOSFERA_ESCALA


# ---- Planeta -----------------------------------------
# ------------------------------------------------------
# Radiación máxima al mediodía en el ecuador, en W/m² (valor real aproximado
# de la constante solar en superficie).
RADIACION_MAXIMA: float = 1000.0

# Inclinación axial real de la Tierra -- ajustable si se quiere un
# planeta con estaciones más o menos marcadas.
INCLINACION_AXIAL_GRADOS: float = 23.44

# ---- Aire ---------------------------------------------
# -------------------------------------------------------
# Propiedades del aire a nivel del mar. SIN CALIBRAR.
CALOR_ESPECIFICO_AIRE: float = 1005.0  # J/(kg·K)
DENSIDAD_AIRE: float = 1.2  # kg/m³

# Capacidad térmica de la capa de aire de la celda, J/(m²·K). Antes estaba en
# temperatura_atmosferica; el suelo se cuenta aparte con su inercia.
C_AIRE: float = 1.0e6

# Altura equivalente de la capa de aire, m. DERIVADA de C_AIRE: así la
# capacidad térmica y el volumen de aire (para la humedad) no pueden divergir.
# 1e6 / (1005·1.2) ≈ 829 m.
ALTURA_CAPA_AIRE: float = C_AIRE / (CALOR_ESPECIFICO_AIRE * DENSIDAD_AIRE)

# ---- Agua ---------------------------------------------
# -------------------------------------------------------
# Calor latente de vaporización del agua, J/kg.
CALOR_LATENTE_VAPORIZACION: float = 2.45e6

# Evaporación tipo Dalton: E = (A + B·v)·(ρ_sat(T_agua) − ρ_vapor), con E en
# kg/(m²·s). A y B*v son velocidades de transferencia de masa, m/s. SIN CALIBRAR
# (con A = 2e-3 y agua a 25 °C con 50 % de humedad relativa salen ~3 mm/día en
# calma y ~6 mm/día con 5 m/s).
EVAPORACION_COEF_BASE: float = 2.0e-3  # A, m/s (aire en calma)
EVAPORACION_COEF_VIENTO: float = 1.0e-3  # B, adimensional (m/s por m/s de viento)
