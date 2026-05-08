from Core.Entities.Comportamiento.Energetico.energetico import Energetico
from Core.Entities.Elementos.elemento import Elemento


class Termico(Energetico):
    """
    recomendable añadir sistema de cache en el que se precalcula la U
    con un elemento para no recalcularla en cada tick.

    Parametros:

    - temperatura_propia: float
    - tasa_transferencia: float
    - radio_termico: float

    Metodos abstractos:

    -
    """

    def __init__(
        self,
        temperatura_propia: float,
        tasa_transferencia: float,
        radio_termico: float,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.temperatura_propia = temperatura_propia
        self.tasa_transferencia = tasa_transferencia
        self.radio_termico = radio_termico
        self.termico: bool = True

    def tick(self, elementos: list[(float, float)]) -> float:
        """
        calculo del intercambio de temperaturas con el resto de elementos.

        list(temperatura, tasa)
        """
        temp_propia_inicial = self.temperatura_propia
        delta = 0
        for neighbor_temp, neighbor_rate in elementos:
            U = (self.tasa_transferencia * neighbor_rate) / (
                self.tasa_transferencia + neighbor_rate
            )
            Q = U * (self.temperatura_propia - neighbor_temp)
            delta -= Q

        self.temperatura_propia += delta
        
        # emision del evento del cambio de temperatura
        if abs(self.temperatura_propia - temp_propia_inicial) > 1e-2:
            Elemento.mundo.bus.emitir(
                f"temperatura_cambiada_{id(self)}", self.temperatura_propia
            )
