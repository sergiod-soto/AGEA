# Core/Entities/Mundo/Suelo/suelo_limite.py

from Core.Entities.Comportamiento.Terreno.terreno_bloqueante import Terreno_Bloqueante
from Core.Entities.Mundo.Suelo.suelo import Suelo

# Valores térmicos de Suelo_Piedra, para distorsionar lo mínimo la media de las
# celdas de atmósfera de borde (Suelo las exige y la celda las promedia).
# OJO: son copias. Si cambian en Suelo_Piedra, hay que cambiarlos aquí;
# test_suelo_limite.py lo comprueba.
TASA_CONVERSION_LIMITE: float = 75
INERCIA_TERMICA_LIMITE: float = 4e5


class Suelo_Limite(Suelo, Terreno_Bloqueante):
    """
    Frontera del mundo: anillo de 1 casilla en el borde del mapa. Es un Suelo
    (ocupa el slot 'suelo', no hay otro terreno debajo) y es invariable.

    - No admite ocupantes (admite_ocupantes = False): Sector._asignar_slot
      rechaza cualquier bot o elemento suelto en su casilla.
    - Bloquea el viento (lo aporta Terreno_Bloqueante; SUPUESTO sin comprobar:
      que ponga resistencia_viento = 1.0 y la flag cacheable). El bloqueo es
      booleano por celda de atmósfera: toda la celda de borde (10x10 casillas)
      queda sin transporte de viento.
    - Térmicamente se comporta como piedra: no se inventan valores propios.
    """

    admite_ocupantes = False

    def __init__(self, id_elemento, casilla, **kwargs):
        super().__init__(
            tipo=Suelo_Limite,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=TASA_CONVERSION_LIMITE,
            inercia_termica=INERCIA_TERMICA_LIMITE,
            **kwargs,
        )

    def tick_elemento(self, ctx): ...
