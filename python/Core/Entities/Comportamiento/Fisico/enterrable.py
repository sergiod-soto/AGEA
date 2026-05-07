from abc import abstractmethod

from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Enterrable(Fisico):
    """
    Parametros:

    -

    Metodos abstractos:

    - check_enterrable(self) -> bool
    - check_desenterrable(self) -> bool
    - enterrar(self)
    - desenterrar(self)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._enterrable: bool = True
        self._enterrado = False

    @abstractmethod
    def check_enterrable(self) -> bool:
        pass

    @abstractmethod
    def check_desenterrable(self) -> bool:
        pass

    @abstractmethod
    def enterrar(self):
        pass

    @abstractmethod
    def desenterrar(self):
        pass


Enterrable
