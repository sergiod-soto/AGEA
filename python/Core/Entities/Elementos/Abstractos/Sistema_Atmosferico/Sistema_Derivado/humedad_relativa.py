# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Derivado/humedad_relativa.py

import math

from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)


def _capacidad_maxima(temperatura: float) -> float:
    """
    Aproximación de Magnus-Tetens de la presión de vapor de saturación
    (fórmula meteorológica estándar), usada aquí como FORMA de curva --
    no como magnitud física exacta, porque no conocemos en qué unidades
    está humedad_absoluta en este juego. Lo importante que aporta: el
    aire más caliente admite más humedad antes de "saturarse", y lo hace
    de forma no lineal (crece cada vez más rápido con la temperatura),
    igual que en la realidad.

    Si humedad_absoluta acaba usando otra escala/unidades, este
    resultado necesitará un factor de escala para casar con ella -- eso
    no se puede saber hasta que Humedad_Absoluta tenga su modelo real
    (ver TODO en humedad_absoluta.py).
    """
    return 6.112 * math.exp((17.62 * temperatura) / (243.12 + temperatura))


class Humedad_Relativa(Sistema_Atmosferico):
    def __init__(self, valor_inicial: float = 0.0, **kwargs):
        super().__init__(Humedad_Relativa, **kwargs)
        self.valor: float = valor_inicial  # porcentaje, 0-100

    def actualizar(self, humedad_absoluta: float, temperatura: float) -> None:
        """
        Derivada: no difunde ni mira vecinos (por eso no recibe
        `vecinos`) -- se calcula solo a partir de humedad_absoluta y
        temperatura YA actualizadas de esta misma celda, en este mismo
        tick (de ahí el orden: temperatura -> ... -> humedad_absoluta ->
        humedad_relativa).
        """
        capacidad_maxima = _capacidad_maxima(temperatura)
        if capacidad_maxima <= 0:
            self.valor = 0.0
            return
        self.valor = max(0.0, min(100.0, (humedad_absoluta / capacidad_maxima) * 100.0))
