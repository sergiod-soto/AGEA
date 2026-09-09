from Core.Entities.Comportamiento.Energetico.energetico import Energetico
from Core.Entities.Elementos.elemento import Elemento


class Termico(Energetico):
    """
    recomendable añadir sistema de cache en el que se precalcula la U
    con un elemento para no recalcularla en cada tick.

    Parametros:

    - temperatura_propia: float
    - tasa_transferencia_temperatura: float
    - radio_termico: float

    Metodos abstractos:

    -
    """

    REQUIERE = {
        "temperatura_propia: float",
        "tasa_transferencia_temperatura: float",
        "radio_termico: int = 0",
    }
    ABSTRACTOS = {}

    def __init__(
        self,
        temperatura_propia: float,
        tasa_transferencia_temperatura: float,
        radio_termico: int = 0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.temperatura_propia = temperatura_propia
        self.tasa_transferencia_temperatura = tasa_transferencia_temperatura
        self.radio_termico = radio_termico  # TODO: formula para calcular radio_termico

    @classmethod
    def _campos_internos(cls):
        return {
            "temperatura_propia",
            "tasa_transferencia_temperatura",
            "radio_termico",
        }

    def tick(self, elementos: list[(float, float)]) -> float:
        # TODO: comprobar que tick no machaque a super().tick()
        """
        calculo del intercambio de temperaturas con el resto de elementos.

        list(temperatura, tasa)
        """
        temp_propia_inicial = self.temperatura_propia
        delta = 0
        for neighbor_temp, neighbor_rate in elementos:
            U = (self.tasa_transferencia_temperatura * neighbor_rate) / (
                self.tasa_transferencia_temperatura + neighbor_rate
            )
            Q = U * (self.temperatura_propia - neighbor_temp)
            delta -= Q

        self.temperatura_propia += delta

        # emision del evento del cambio de temperatura
        if abs(self.temperatura_propia - temp_propia_inicial) > 1e-2:
            Elemento.mundo.bus.emitir(
                f"temperatura_cambiada_{id(self)}", self.temperatura_propia
            )

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "temperatura_propia",
            "tasa_transferencia_temperatura",
            "radio_termico",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Peso es la masa del elemento.

Atributos:
\tpeso: float

Métodos:
\ttick(self, elementos: list[(float, float)]) -> float
\t--------------------------------------
\tComputa el siguiente tick.
        """
