# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/presion.py

from Config.parametros_simulacion import (
    SEGUNDOS_SIMULADOS_TICK,
    TAMANHO_CELDA_ATMOSFERICA,
)
from Config.settings import ID_PRESION
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)

# Difusividad de la presión, m²/s. SIN CALIBRAR.
DIFUSIVIDAD_PRESION: float = 5.0

# Fracción de la diferencia con CADA vecino que se iguala por segundo, 1/s.
# Es D/L²: así, cambiar el tamaño de celda cambia la física de forma coherente
# en vez de exigir retocar un número mágico. Con L = 10 m da 0.05 1/s.
_COEFICIENTE_DIFUSION: float = DIFUSIVIDAD_PRESION / TAMANHO_CELDA_ATMOSFERICA**2

# Presión atmosférica estándar al nivel del mar, en pascales (Pa).
PRESION_ESTANDAR_PA: float = 101325.0


class Presion(Sistema_Atmosferico):
    def __init__(self, valor_inicial: float = PRESION_ESTANDAR_PA, **kwargs):
        super().__init__(Presion, ID_PRESION, **kwargs)
        # Pascales (Pa). Todo lo que lea .valor (viento, proto, snapshots) lo
        # recibe en Pa.
        self.valor: float = valor_inicial

    def actualizar(self, temperatura: float, vecinos: list) -> None:
        """
        TODO(modelo): falta la relación real presión<->temperatura (aire más
        caliente = menos denso). `temperatura` (K) ya está en la firma pero
        todavía NO se usa. Tampoco hay fuente de presión: con todas las celdas
        a 101325 Pa, la difusión no hace nada y no habrá viento por gradiente.

        De momento solo difunde con los vecinos (tick anterior, ghost zone).

        ESTABILIDAD: esquema explícito; hace falta
            _COEFICIENTE_DIFUSION * dt * n_vecinos < 1
        (4 vecinos cardinales, dt = 1 s: 0.05 * 1 * 4 = 0.2, correcto). Si se
        sube dt o se baja el tamaño de celda, hay que revisarlo.
        """
        dt = SEGUNDOS_SIMULADOS_TICK  # s simulados que avanza este tick
        difusion = sum(
            (vecino.presion - self.valor) * _COEFICIENTE_DIFUSION * dt
            for vecino in vecinos
        )
        self.valor += difusion
