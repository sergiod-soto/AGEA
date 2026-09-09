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

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Indica que el Elemento puede ser enterrado.

Atributos:

\t-

Métodos:
\t@abstractmethod check_enterrable(self) -> bool
\t--------------------------------------
\tComprueba si es enterrable.

\t@abstractmethod check_desenterrable(self) -> bool
\t--------------------------------------
\tComprueba si es desenterrable.

\t@abstractmethod enterrar(self) -> bool
\t--------------------------------------
\tEntierra al Elemento.

\t@abstractmethod desenterrar(self) -> bool
\t--------------------------------------
\tDesentierra al Elemento.
            """
