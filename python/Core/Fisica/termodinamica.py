# Core/Fisica/termodinamica.py

"""
Funciones termodinámicas compartidas por varias magnitudes y comportamientos.

Por qué existe: la saturación del aire la necesitan Humedad_Relativa,
Acuoso (evaporación) y la condensación (ajuste_saturacion). Vive aquí para que
un módulo primario o un comportamiento no dependa de uno derivado.

Módulo puro (sin estado). Solo importa constantes de Config: no hay ciclos.
"""

import math

from Config.parametros_simulacion import CALENTAMIENTO_POR_CONDENSACION

# Constante específica del vapor de agua, J/(kg·K).
CONSTANTE_GAS_VAPOR_AGUA: float = 461.5

# Coeficientes de Magnus-Tetens (Sonntag): e_s = 611.2·exp(A·T/(B+T)), T en °C.
_PRESION_SATURACION_0C: float = 611.2  # Pa
_MAGNUS_A: float = 17.62
_MAGNUS_B: float = 243.12  # °C

# Rango de validez de Magnus-Tetens, en °C. Fuera de él la fórmula deja de ser
# fiable y, cerca de -243 °C, el denominador se anula.
_MAGNUS_MIN_C: float = -45.0
_MAGNUS_MAX_C: float = 60.0

# Diferencia entre las escalas Celsius y kelvin.
_KELVIN_EN_CERO_CELSIUS: float = 273.15


def densidad_vapor_saturacion(temperatura_k: float) -> float:
    """
    Densidad de vapor de agua de SATURACIÓN, en kg/m³ (misma unidad que
    humedad_absoluta), a la temperatura dada en kelvin. Precondición: > 0 K.

    Dos pasos estándar:
      1) Magnus-Tetens da la presión de vapor de saturación e_s en Pa. La
         temperatura se recorta al rango de validez solo para ESTE cálculo;
         el denominador del paso 2 usa la temperatura real.
      2) Gas ideal para el vapor: rho = e_s / (R_v · T).
    """
    temperatura_c = max(
        _MAGNUS_MIN_C, min(_MAGNUS_MAX_C, kelvin_a_celsius(temperatura_k))
    )
    presion_saturacion_pa = _PRESION_SATURACION_0C * math.exp(
        (_MAGNUS_A * temperatura_c) / (_MAGNUS_B + temperatura_c)
    )
    return presion_saturacion_pa / (CONSTANTE_GAS_VAPOR_AGUA * temperatura_k)


def derivada_densidad_vapor_saturacion(temperatura_k: float) -> float:
    """
    d(rho_sat)/dT en kg/(m³·K). Analítica, coherente con
    densidad_vapor_saturacion.

    rho = e_s/(R_v·T)  =>  d(ln rho)/dT = d(ln e_s)/dT - 1/T, con
    d(ln e_s)/dT = A·B/(B+T_c)² (Magnus). Fuera del rango de validez la
    saturación se recorta (e_s constante), así que solo queda el término -1/T.
    """
    temperatura_c = kelvin_a_celsius(temperatura_k)
    if _MAGNUS_MIN_C <= temperatura_c <= _MAGNUS_MAX_C:
        dln_es = _MAGNUS_A * _MAGNUS_B / (_MAGNUS_B + temperatura_c) ** 2
    else:
        dln_es = 0.0
    return densidad_vapor_saturacion(temperatura_k) * (dln_es - 1.0 / temperatura_k)


def ajuste_saturacion(vapor: float, nube: float, temperatura_k: float) -> float:
    """
    Masa que cambia de fase en una celda, en kg/m³ de aire. POSITIVA =
    condensa (vapor -> nube, el aire se calienta); NEGATIVA = la nube se
    evapora (nube -> vapor, el aire se enfría). Función pura: no muta nada;
    quien la llama aplica el resultado (ver sistema_atmosferico._condensar).

    Cómo: se busca delta tal que, tras mover delta de vapor a nube y calentar
    el aire k·delta (k = CALENTAMIENTO_POR_CONDENSACION), el vapor restante
    iguale la saturación a la NUEVA temperatura. Linealizando rho_sat:

        vapor - delta = rho_sat + rho_sat'·k·delta
        delta = (vapor - rho_sat) / (1 + k·rho_sat')

    Un solo paso, sin iterar. El denominador (>= 1) es la realimentación del
    calor latente: condensar calienta, y el aire más cálido admite más vapor.

    Límites: no se condensa más vapor del que hay (delta <= vapor) ni se
    evapora más nube de la que hay (delta >= -nube). Con aire subsaturado y
    sin nube, delta = 0.

    ValueError si temperatura_k <= 0 (la saturación no está definida).
    """
    if temperatura_k <= 0:
        raise ValueError(f"temperatura_k debe ser > 0 K (recibido {temperatura_k}).")
    exceso = vapor - densidad_vapor_saturacion(temperatura_k)
    realimentacion = 1.0 + CALENTAMIENTO_POR_CONDENSACION * (
        derivada_densidad_vapor_saturacion(temperatura_k)
    )
    delta = exceso / realimentacion
    return max(-nube, min(vapor, delta))


def celsius_a_kelvin(celsius: float) -> float:
    """°C -> K. Para fijar valores iniciales legibles (p. ej. 15 °C)."""
    return celsius + _KELVIN_EN_CERO_CELSIUS


def kelvin_a_celsius(kelvin: float) -> float:
    """K -> °C. Solo para mostrar o para fórmulas que trabajen en °C."""
    return kelvin - _KELVIN_EN_CERO_CELSIUS


def autoconversion(nube: float, nube_critica: float, tau: float, dt: float) -> float:
    """
    Autoconversión de nube a lluvia (tipo Kessler). Función PURA.

    Devuelve los kg/m³ de nube que se convierten en lluvia en este tick:
        max(0, nube − nube_critica) · dt / tau
    Requiere 0 < dt/tau <= 1 (lo garantiza validar_estabilidad). El min() final
    es una red de seguridad frente al redondeo: nunca se retira más nube de la
    que hay.
    """
    exceso = nube - nube_critica
    if exceso <= 0.0:
        return 0.0
    return min(nube, exceso * dt / tau)
