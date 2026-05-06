from Core.Entities.Comportamiento.Stats.Informacion.informacion import Informacion


class Posicion(Informacion):
    def __init__(self, posicion: tuple[int, int],**kwargs):
        super().__init__("posicion", posicion,**kwargs)
