# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/humedad_absoluta.py

from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)

DIFUSION_HUMEDAD: float = 0.05


class Humedad_Absoluta(Sistema_Atmosferico):
    def __init__(self, valor_inicial: float = 0.0, **kwargs):
        super().__init__(Humedad_Absoluta, **kwargs)
        self.valor: float = valor_inicial

    def actualizar(self, temperatura: float, vecinos: list) -> None:
        """
        TODO(modelo): sin evaporación todavía -- depende de ríos/oasis
        (rio.py, oasis.py) y probablemente de vegetación (bosque.py,
        selva.py, taiga.py, comida.py), todos ellos vacíos por ahora.
        `temperatura` se recibe ya en la firma (la evaporación depende
        de ella en cualquier modelo razonable) pero todavía NO se usa.

        De momento solo difunde con los vecinos (tick anterior, ghost
        zone), para no dejarla completamente estática mientras existe
        el resto de sistemas de los que depende.
        """
        difusion = sum(
            (vecino.humedad_absoluta - self.valor) * DIFUSION_HUMEDAD
            for vecino in vecinos
        )
        self.valor = max(0.0, self.valor + difusion)
