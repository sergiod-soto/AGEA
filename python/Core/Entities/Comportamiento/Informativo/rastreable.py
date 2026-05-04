from Core.Entities.Comportamiento.Informativo.informativo import Informativo
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Abstractos.Marcadores.Espaciales.rastro import Rastro


class Rastreable(Informativo):
    """
    Al moverse deja rastros dependiendo de condiciones.

    Los rastros tienen una intensidad (%) en funcion del terreno.

    Los stats del rastro dependen de las caracteristicas del Elemento que las produjo
    """

    def __init__(
        self,
        condiciones_rastro: list[tuple[list[Condicion], float]] = None,
    ):
        super().__init__()
        self.condiciones_rastro = condiciones_rastro or []

    def dejar_rastro(self, terreno) -> Rastro | None:
        for condiciones, intensidad_base in self.condiciones_rastro:
            if all(c.evaluar() for c in condiciones):
                return Rastro(
                    origen=self,
                    intensidad=intensidad_base * terreno.calcular_intensidad(self),
                )
        return None
