# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Derivado/humedad_relativa.py

from Config.settings import ID_HUMEDAD_RELATIVA
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)
from Core.Entities.Mundo.Atmosfera.termodinamica import densidad_vapor_saturacion


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
        capacidad_maxima = densidad_vapor_saturacion(temperatura)
        if capacidad_maxima <= 0:
            self.valor = 0.0
            return
        self.valor = max(0.0, min(100.0, (humedad_absoluta / capacidad_maxima) * 100.0))
