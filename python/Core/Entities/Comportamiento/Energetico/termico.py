# Core/Entities/Comportamiento/Energetico/termico.py

from Core.Entities.Comportamiento.Energetico.energetico import Energetico


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

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "temperatura_propia": self.temperatura_propia,
            "tasa_transferencia_temperatura": self.tasa_transferencia_temperatura,
            "radio_termico": self.radio_termico,
        }
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"termico": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        seccion = data["comportamientos"][__class__.__name__]
        self.temperatura_propia = seccion["temperatura_propia"]
        self.tasa_transferencia_temperatura = seccion["tasa_transferencia_temperatura"]
        self.radio_termico = seccion["radio_termico"]

    @classmethod
    def _campos_internos(cls):
        return {
            "temperatura_propia",
            "tasa_transferencia_temperatura",
            "radio_termico",
        }

    def intercambiar_temperatura(
        self, elementos: list[tuple[float, float]], ctx
    ) -> None:
        """
        Intercambio de calor con vecinos: elementos = [(temperatura, tasa), ...].
        Si la temperatura cambia más de 1e-2, pide emitir
        'temperatura_cambiada_<id_elemento>' con la temperatura nueva. Es un
        evento de "estado actual": agrupable en el futuro.
        """
        temp_propia_inicial = self.temperatura_propia
        delta = 0
        for neighbor_temp, neighbor_rate in elementos:
            U = (self.tasa_transferencia_temperatura * neighbor_rate) / (
                self.tasa_transferencia_temperatura + neighbor_rate
            )
            delta -= U * (self.temperatura_propia - neighbor_temp)
        self.temperatura_propia += delta

        if abs(self.temperatura_propia - temp_propia_inicial) > 1e-2:
            ctx.emitir_evento(
                f"temperatura_cambiada_{self.id_elemento}",
                self.temperatura_propia,
                agrupable=True,
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
- El Elemento intercambia calor con su entorno.

Atributos:
\ttemperatura_propia: float
\ttasa_transferencia_temperatura: float
\tradio_termico: int = 0

Métodos:
\tintercambiar_temperatura(self, elementos: list[tuple[float, float]], ctx) -> None
\t--------------------------------------
\tCalcula el intercambio de calor con los vecinos (temperatura, tasa).
        """
