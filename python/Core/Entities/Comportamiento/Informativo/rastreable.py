from abc import abstractmethod

from Core.Entities.Comportamiento.Informativo.informativo import Informativo
from Core.Entities.Comportamiento.Terreno.terreno import Terreno
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Abstractos.Marcadores.Espaciales.rastro import Rastro


class Rastreable(Informativo):
    """
    Al moverse deja rastros dependiendo de condiciones.

    Los rastros tienen una intensidad (%: float) en funcion del terreno.

    El codigo del rastro depende de las caracteristicas del Elemento que las produjo

    Parametros:

    - condiciones_rastro: list[tuple[list[Condicion], float]] = None

    Metodos abstractos:

    - dejar_rastro(self, terreno: Terreno) -> Rastro | None:
    """

    def __init__(
        self, condiciones_rastro: list[tuple[list[Condicion], float]] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.condiciones_rastro = condiciones_rastro or []

    @abstractmethod
    def dejar_rastro(self, terreno: Terreno) -> Rastro | None: ...