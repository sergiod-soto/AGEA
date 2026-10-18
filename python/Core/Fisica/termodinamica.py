# Core/Entities/Mundo/Atmosfera/termodinamica.py

"""
Funciones termodinámicas compartidas por varias magnitudes y comportamientos.

Por qué existe: la saturación del aire la necesitan Humedad_Relativa (derivada),
y a futuro Humedad_Absoluta (condensación) y Acuoso (evaporación). Antes vivía
como función privada en humedad_relativa; importarla desde ahí obligaba a un
módulo primario o a un comportamiento a depender de uno derivado.

Este módulo es puro (sin estado). Solo importa kelvin_a_celsius, que no depende
de nada de aquí, así que no hay ciclos.
"""

import math


# Constante específica del vapor de agua, J/(kg·K).
CONSTANTE_GAS_VAPOR_AGUA: float = 461.5

# Rango de validez de Magnus-Tetens (Sonntag), en °C. Fuera de él la fórmula
# deja de ser fiable y, cerca de -243 °C, el denominador se anula.
_MAGNUS_MIN_C: float = -45.0
_MAGNUS_MAX_C: float = 60.0

# Diferencia entre las escalas Celsius y kelvin.
_KELVIN_EN_CERO_CELSIUS: float = 273.15


def densidad_vapor_saturacion(temperatura_k: float) -> float:
    """
    Densidad de vapor de agua de SATURACIÓN, en kg/m³ (misma unidad que
    humedad_absoluta), a la temperatura dada en kelvin. Precondición: > 0 K.

    Dos pasos estándar:
      1) Magnus-Tetens (coeficientes de Sonntag) da la presión de vapor de
         saturación e_s en Pa. Magnus trabaja en °C, de ahí kelvin_a_celsius().
         La temperatura se recorta al rango de validez (-45 a 60 °C) solo para
         ESTE cálculo; el denominador de abajo usa la temperatura real.
      2) Ley de los gases ideales para el vapor: rho = e_s / (R_v * T).
    """
    temperatura_c = max(
        _MAGNUS_MIN_C, min(_MAGNUS_MAX_C, kelvin_a_celsius(temperatura_k))
    )
    presion_saturacion_pa = 611.2 * math.exp(
        (17.62 * temperatura_c) / (243.12 + temperatura_c)
    )
    return presion_saturacion_pa / (CONSTANTE_GAS_VAPOR_AGUA * temperatura_k)


def celsius_a_kelvin(celsius: float) -> float:
    """°C -> K. Para fijar valores iniciales legibles (p. ej. 15 °C)."""
    return celsius + _KELVIN_EN_CERO_CELSIUS


def kelvin_a_celsius(kelvin: float) -> float:
    """K -> °C. Solo para mostrar o para fórmulas que trabajen en °C."""
    return kelvin - _KELVIN_EN_CERO_CELSIUS
