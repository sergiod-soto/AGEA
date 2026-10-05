# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/humedad_absoluta.py

from Config.parametros_simulacion import (
    SEGUNDOS_SIMULADOS_TICK,
    TAMANHO_CELDA_ATMOSFERICA,
)
from Config.settings import ID_HUMEDAD_ABSOLUTA
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)

# Difusividad de la humedad, m²/s. SIN CALIBRAR.
DIFUSIVIDAD_HUMEDAD: float = 5.0

# Fracción de la diferencia con CADA vecino que se iguala por segundo, 1/s
# (D/L²). Con L = 10 m da 0.05 1/s, igual que el valor anterior.
_COEFICIENTE_DIFUSION: float = DIFUSIVIDAD_HUMEDAD / TAMANHO_CELDA_ATMOSFERICA**2


class Humedad_Absoluta(Sistema_Atmosferico):
    def __init__(self, valor_inicial: float = 0.0, **kwargs):
        super().__init__(Humedad_Absoluta, ID_HUMEDAD_ABSOLUTA, **kwargs)
        # kg/m³ de vapor de agua en el aire (densidad de vapor). Es la unidad
        # que espera Humedad_Relativa para comparar con la saturación.
        self.valor: float = valor_inicial

    def actualizar(self, temperatura: float, vecinos: list) -> None:
        """
        TODO(modelo): sin evaporación todavía (depende de ríos/oasis y de la
        vegetación, ficheros aún vacíos). `temperatura` (K) ya está en la firma
        pero todavía NO se usa.

        De momento solo difunde con los vecinos (tick anterior, ghost zone).
        Mismo criterio de estabilidad que Presion: coeficiente * dt * n < 1.
        """
        # Segundos que avanza la simulación en este tick.
        dt = SEGUNDOS_SIMULADOS_TICK
        difusion = sum(
            (vecino.humedad_absoluta - self.valor) * _COEFICIENTE_DIFUSION * dt
            for vecino in vecinos
        )
        # max(): la humedad no puede ser negativa.
        self.valor = max(0.0, self.valor + difusion)
