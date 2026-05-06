from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Combinable(Material):
    """
    Un elemento es Combinable si puede ser juntado con otro elemento iguale, resultando en superior -caracteristica-

    Parametros:

    - elemento: Elemento (el Elemento al cual se le quiere añadir lo original)

    - cantidad_max: float = None

    Metodos abstractos:

    - combinar(self, elemento: Elemento) -> Elemento
    """

    def __init__(self, elemento: Elemento, cantidad_max: float = None,**kwargs):
        super().__init__(**kwargs)
        self.elemento = elemento
        self.cantidad_max = cantidad_max or float("inf")

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
