# Core/Entities/Comportamiento/Fisico/enterrable.py

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

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "_des_enterrable": self._des_enterrable,
            "_enterrado": self._enterrado,
        }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        seccion = data["comportamientos"][__class__.__name__]
        self._des_enterrable = seccion["_des_enterrable"]
        self._enterrado = seccion["_enterrado"]

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"enterrable": {}}
        return datos

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
        # Sin parámetros propios: el estado interno se inicializa solo.
        return []

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
