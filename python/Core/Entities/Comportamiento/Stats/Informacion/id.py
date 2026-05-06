from Core.Entities.Comportamiento.Stats.Informacion.informacion import Informacion


class ID(Informacion):
    def __init__(self, id: int,**kwargs):
        super().__init__("ID", id,**kwargs)
