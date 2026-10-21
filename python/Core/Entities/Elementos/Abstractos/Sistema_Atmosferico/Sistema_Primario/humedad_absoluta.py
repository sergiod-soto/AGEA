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

    def actualizar(
        self,
        vecinos: list,
        velocidad: tuple[float, float],
        bloqueado: bool,
    ) -> None:
        """
        Difunde con los vecinos y se advecta con el viento (`velocidad` en m/s
        y `bloqueado` son los de ESTA celda al inicio del tick). Los vecinos
        son del tick anterior (ghost zone). Estabilidad: ver
        Config/validacion_simulacion.

        Las FUENTES y SUMIDEROS de vapor no entran aquí: la evaporación la
        aplica el Sector (Celda_Atmosfera.aplicar_evaporacion) y la
        condensación el orquestador (sistema_atmosferico._condensar), después
        del transporte.
        """
        dt = SEGUNDOS_SIMULADOS_TICK
        difusion = sum(
            (vecino.humedad_absoluta - self.valor) * _COEFICIENTE_DIFUSION * dt
            for vecino in vecinos
        )
        # kg/m³ que entran/salen con el viento (ya incluye dt).
        adveccion = sum(
            self.delta_advectivo(
                self.valor,
                vecino.humedad_absoluta,
                velocidad,
                (vecino.viento_x, vecino.viento_y),
                vecino.direccion,
                bloqueado or vecino.bloqueo_total_viento,
            )
            for vecino in vecinos
        )
        # max(): la humedad no puede ser negativa.
        self.valor = max(0.0, self.valor + difusion + adveccion)
