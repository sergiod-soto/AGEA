# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Derivado/humedad_relativa.py

import math

from Config.settings import ID_HUMEDAD_RELATIVA
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.temperatura_atmosferica import (
    kelvin_a_celsius,
)

# Constante específica del vapor de agua, J/(kg·K).
CONSTANTE_GAS_VAPOR_AGUA: float = 461.5


def _capacidad_maxima(temperatura_k: float) -> float:
    """
    Densidad de vapor de agua de SATURACIÓN, en kg/m³ (misma unidad que
    humedad_absoluta), a la temperatura dada en kelvin.

    Dos pasos estándar:
      1) Magnus-Tetens (coeficientes de Sonntag) da la presión de vapor de
         saturación e_s en Pa. Magnus trabaja en °C, de ahí
         kelvin_a_celsius(). Válida aprox. entre -45 y 60 °C.
      2) Ley de los gases ideales para el vapor: rho = e_s / (R_v * T).

    Ejemplo de comprobación: a 20 °C da ~0.0173 kg/m³ (17.3 g/m³), el valor
    de las tablas. Con esto la humedad relativa ya no depende de ningún
    factor de escala inventado (resuelve la duda que había sobre unidades).
    """
    temperatura_c = kelvin_a_celsius(temperatura_k)
    presion_saturacion_pa = 611.2 * math.exp(
        (17.62 * temperatura_c) / (243.12 + temperatura_c)
    )
    return presion_saturacion_pa / (CONSTANTE_GAS_VAPOR_AGUA * temperatura_k)


class Humedad_Relativa(Sistema_Atmosferico):
    def __init__(self, valor_inicial: float = 0.0, **kwargs):
        super().__init__(Humedad_Relativa, ID_HUMEDAD_RELATIVA, **kwargs)
        self.valor: float = valor_inicial  # porcentaje, 0-100 (adimensional)

    def actualizar(self, humedad_absoluta: float, temperatura: float) -> None:
        """
        Derivada: no difunde ni mira vecinos -- se calcula solo a partir de
        humedad_absoluta (kg/m³) y temperatura (K) YA actualizadas de esta
        misma celda, en este mismo tick (de ahí el orden: temperatura ->
        ... -> humedad_absoluta -> humedad_relativa).
        """
        if temperatura <= 0:
            self.valor = 0.0
            return
        capacidad_maxima = _capacidad_maxima(temperatura)
        if capacidad_maxima <= 0:
            self.valor = 0.0
            return
        self.valor = max(0.0, min(100.0, (humedad_absoluta / capacidad_maxima) * 100.0))
