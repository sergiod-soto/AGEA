from abc import abstractmethod

from Core.Entities.Comportamiento.Temporal.temporal import Temporal


class Caduco(Temporal):
    """
    Durabilidad decae con el tiempo
    
    Parametros:
    
    - duracion_max_caduco: int    
    - duracion_restante_caduco: int = None
    
    Metodos abstractos:
    
    - tick() -> None    
    - desaparecer() -> None
    """

    def __init__(self, duracion_max_caduco: int, duracion_restante_caduco: int = None,**kwargs):
        super().__init__(**kwargs)
        self.duracion_max_caduco = duracion_max_caduco
        self.duracion_restante_caduco = duracion_restante_caduco or duracion_max_caduco

        @abstractmethod
        def tick(self) -> None: ...

        @abstractmethod
        def desaparecer(self) -> None: ...
