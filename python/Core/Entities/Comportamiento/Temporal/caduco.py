from abc import abstractmethod

from Core.Entities.Comportamiento.Temporal.temporal import Temporal


class Caduco(Temporal):
    """
    Durabilidad decae con el tiempo
    
    Parametros:
    
    - duracion_max: int
    
    - duracion_restante: int = None
    
    Metodos abstractos:
    
    - tick(self) -> None
    
    - desaparecer(self) -> None
    """

    def __init__(self, duracion_max: int, duracion_restante: int = None,**kwargs):
        super().__init__(**kwargs)
        self.duracion_max = duracion_max
        self.duracion_restante = duracion_restante or duracion_max

        @abstractmethod
        def tick(self) -> None: ...

        @abstractmethod
        def desaparecer(self) -> None: ...
