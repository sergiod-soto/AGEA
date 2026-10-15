# Core/Entities/Comportamiento/Material/combinable.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Combinable(Material):
    """
    Un elemento es Combinable si puede ser juntado con otro elemento iguale, resultando en superior -caracteristica-

    Parametros:

    - cantidad_max_combinable: float = None (None = infinito)

    Metodos abstractos:

    - combinar(self, elemento: Elemento) -> Elemento
    """

    REQUIERE = {"cantidad_max_combinable: float = None"}
    ABSTRACTOS = {"def combinar(self, elemento: Elemento) -> Elemento"}

    def __init__(self, cantidad_max_combinable: float = None, **kwargs):
        super().__init__(**kwargs)
        self.cantidad_max_combinable = cantidad_max_combinable or float("inf")

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"combinable": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"combinable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @abstractmethod
    def combinar(self, elemento: Elemento) -> Elemento:
        """
        Intenta combinar 2 Elementos combinables iguales.

        En caso de lograrlo sin problemas, retorna None.

        Si no se pueden combinar, retorna el Elemento original.

        Si se pueden combinar, pero el resultado supera el maximo, el
        Elemento objetivo se pone al maximo y se retorna el original con
        la cantidad sobrante
        """
        ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "cantidad_max_combinable",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser combinado, eliminando tanto ese Elemento como
el Elemento target, y creando un Elemento resultado de
cantidad igual a la suma de ambos.

Atributos:
\tcantidad_max_combinable: float = None

Métodos:
\t@abstractmethod combinar(self, elemento: Elemento) -> Elemento
\t--------------------------------------
\tConsume carga de energía.
            """
