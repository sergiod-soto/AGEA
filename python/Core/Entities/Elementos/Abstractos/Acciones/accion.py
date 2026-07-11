from abc import abstractmethod

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Accion(Elemento_Abstracto):
    """
    Parametros

    - nombre: str

    Metodos abstractos:

    - ejecutar()
    """

    def __init__(self, tipo: type, nombre: str, **kwargs):
        super().__init__(tipo, **kwargs)
        self.nombre = nombre

    @abstractmethod
    def ejecutar(self): ...
