from math import sin
import math

from Core.Entities.Elementos.Abstractos.Informacion.informacion import Informacion


class Luz_Ambiental(Informacion):
    """
    Intensidad de la luz ambiental.
    
    Depende del ciclo solar, la densidad de nubes (y por
    ello, la posicion), y el 
    estado del ciclo lunar.
    """
    

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(Luz_Ambiental, **kwargs)
        self._factor = 1

    def get_intensidad_luz_ambiental(self) -> float:

        def _clamp(valor, minimo, maximo) -> float:
            return max(minimo, min(valor, maximo))

        hora = self.mundo.get_tiempo()

        amanecer = self.get_hora_amanecer()
        anochecer = self.get_hora_anochecer()
        tSol = (hora - self.amanecer) / (anochecer - amanecer)
        if tSol < 0 or tSol > 1:
            luzSolar = 0
        else:
            luzSolar = 100 * sin(math.pi * tSol) ** self._factor

        tLuna = (hora - anochecer) / (amanecer - anochecer)
        if tLuna < 0 or tLuna > 1:
            luzLuna = 0
        else:
            luzLuna = self.get_intensidad_luna() * sin(math.pi * tLuna) ** self._factor

        return _clamp((luzSolar + luzLuna) * factorNubes, 1, 100)
