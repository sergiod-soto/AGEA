from Core.Entities.Elementos.Simples.Etereo.etereo import Etereo

"""
estilo feromonas.

el bot deja un mensaje que le llega a modo de interrupcion a los bots que se acerquen lo suficiente.
es comun que un bot no sea capaz de entender el mensaje de otro bot.
"""


class Mensaje(Etereo):
    def __init__(
        self,
        tamanho,
        casilla,
        capa,
        rotacion=0,
        fuerza_sector_activo=False,
        fuerza_vecinos_activos=False,
        **kwargs
    ):
        super().__init__(
            Mensaje,
            tamanho,
            casilla,
            capa,
            rotacion,
            fuerza_sector_activo,
            fuerza_vecinos_activos,
            **kwargs
        )
