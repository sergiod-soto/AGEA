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

    REQUIERE = {}
    ABSTRACTOS = {
        "def check_enterrable(self) -> bool",
        "def check_desenterrable(self) -> bool",
        "def enterrar(self) -> bool",
        "def desenterrar(self) -> bool",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._des_enterrable: bool = True
        self._enterrado: bool = False

    @classmethod
    def _campos_internos(cls):
        return {"_des_enterrable", "_enterrado"}

    @abstractmethod
    def check_enterrable(self) -> bool: ...

    @abstractmethod
    def check_desenterrable(self) -> bool: ...

    @abstractmethod
    def enterrar(self) -> bool: ...

    @abstractmethod
    def desenterrar(self) -> bool: ...
