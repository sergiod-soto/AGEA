from Core.Entities.Comportamiento.Energetico.energetico import Energetico


class Termico(Energetico):
    """
    recomendable añadir sistema de cache en el que se precalcula la U
    con un elemento para no recalcularla en cada tick.

    Parametros:

    - self.temperatura_propia: float
    - self.tasa_transferencia: float
    - self.radio: float
    """

    def __init__(
        self, temperatura_propia: float, tasa_transferencia: float, radio: float
    ):
        super().__init__()
        self.temperatura_propia = temperatura_propia
        self.tasa_transferencia = tasa_transferencia
        self.radio = radio
        self.termico = True

    def tick(self, elementos: list[(float, float)]) -> float:
        """
        calculo del intercambio de temperaturas con el resto de elementos.

        list(temperatura, tasa)
        """

        delta = 0
        for neighbor_temp, neighbor_rate in elementos:
            U = (self.tasa_transferencia * neighbor_rate) / (
                self.tasa_transferencia + neighbor_rate
            )
            Q = U * (self.temperatura_propia - neighbor_temp)
            delta -= Q

        self.temperatura_propia += delta
