# Core/Entities/Comportamiento/Fisico/empujable.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Fisico.fisico import Fisico
from Core.Entities.Elementos.elemento import Elemento


class Empujable(Fisico):
    """
    Parametros:

    - coste_empujar: float

    Metodos abstractos:

    - check_push(self, direccion) -> Elemento | True | False
    - push(self, direccion) -> bool
    """

    REQUIERE = {
        "coste_empujar: float",
    }
    ABSTRACTOS = {
        "def check_push(self, direccion) -> Elemento | bool",
        "def push(self, direccion) -> bool",
    }

    def __init__(self, coste_empujar: float, **kwargs):
        super().__init__(**kwargs)

        self.coste_empujar = coste_empujar  #   cuanta energia drena moverlo 1 ud.
        self.empujable: bool = True

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "coste_empujar": self.coste_empujar,
            "empujable": self.empujable,
        }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        seccion = data["comportamientos"][__class__.__name__]
        self.coste_empujar = seccion["coste_empujar"]
        self.empujable = seccion["empujable"]

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"empujable": {}}
        return datos

    @classmethod
    def _campos_internos(cls):
        return {"empujable"}

    def calcular_coste_empujar_en_cadena(self, direccion) -> float:
        """
        Compruebo el coste de mover algo. si no puede moverse, o choca contra
        algo que no puede ser movido, retorna -1.
        Si puede moverse y no choca, retorna el coste propio.
        Si puede moverse pero choca, retorna el coste sumado
        """

        check = self.check_push(direccion)
        if check is True:
            return self.coste_empujar
        if check is False:
            return -1.0
        if isinstance(check, Elemento):
            # choca, asi que en check debe haber un Elemento
            #
            # compruebo si tiene el comportamiento 'Empujable'
            if check.tiene_comportamiento(Empujable):
                return self.coste_empujar + check.calcular_coste_empujar_en_cadena(
                    direccion
                )
            else:
                return -1.0

    @abstractmethod
    def check_push(self, direccion) -> Elemento | bool:
        """
        Intenta mover la entidad una celda en 'direccion'.
        Devuelve un Elemento si choca contra algo, True si tendria exito o False si no puede.
        """
        ...

    @abstractmethod
    def push(self, direccion) -> bool: ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "coste_empujar",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Indica que es un Elemento empujable por otros.

Atributos:
\tcoste_empujar: float

Métodos:
\tcalcular_coste_empujar_en_cadena(self, direccion) -> float
\t--------------------------------------
\tCalcula la energia necesaria para mover el elemento tnato en 
\tcaso de que se mueva solo como que provoque un empuje en cadena.

\t@abstractmethod check_push(self, direccion) -> Elemento | bool
\t--------------------------------------
\tComprueba si el Elemento puede ser movido.

\t@abstractmethod push(self, direccion) -> bool
\t--------------------------------------
\tIntenta empujar el elemento el la dirección y con la fuerza dada.
\tSi choca contra un Elemento, lo retorna. 
\tSi logra moverlo, retorna True. En caso contrario, retorna False.
        """
