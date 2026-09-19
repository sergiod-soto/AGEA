# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/presion.py

from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)

# Fracción de la diferencia de presión con cada vecino que se transfiere
# en un tick.
DIFUSION_PRESION: float = 0.05


class Presion(Sistema_Atmosferico):
    def __init__(self, valor_inicial: float = 1000.0, **kwargs):
        super().__init__(Presion, **kwargs)
        self.bares: float = valor_inicial

    def actualizar(self, temperatura: float, vecinos: list) -> None:
        """
        TODO(modelo): falta la relación real presión<->temperatura (a
        grandes rasgos, aire más caliente = menos denso = menos presión
        a igual volumen). No hay constantes de bioma ni datos para
        fijar esa relación sin inventarla, así que `temperatura` se
        recibe (ya en la firma, lista para cuando se decida el modelo)
        pero todavía NO se usa.

        De momento la presión solo difunde con sus vecinos (tick
        anterior, ghost zone), para no dejarla completamente estática
        mientras se resuelve el modelo real.
        """
        difusion = sum(
            (vecino.presion - self.bares) * DIFUSION_PRESION for vecino in vecinos
        )
        self.bares += difusion
