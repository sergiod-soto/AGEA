from Core.Entities.Comportamiento.Stats.Simples.temperatura import Temperatura
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Clima.clima import Clima
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Fenomenos.nubes import Nubes

from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.humedad_absoluta import Humedad_Absoluta
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.presion import Presion
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.radiacion import Radiacion
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.Sistema_Primario.viento import Viento
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)


class Atmosfera(Sistema_Atmosferico):

    def __init__(self, **kwargs):
        super().__init__(Atmosfera, **kwargs)

        self.radiacion = Radiacion()
        self.temperatura = Temperatura()
        self.presion = Presion()
        self.viento = Viento()
        self.humedad_absoluta = Humedad_Absoluta()
        self.nubes = Nubes()
        self.clima = Clima()

    def get(self, posicion: tuple[int, int]): ...  # TODO
