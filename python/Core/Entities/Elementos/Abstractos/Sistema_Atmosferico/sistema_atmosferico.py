# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/sistema_atmosferico.py

from Config.parametros_simulacion import (
    SEGUNDOS_SIMULADOS_TICK,
    TAMANHO_CELDA_ATMOSFERICA,
)
from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto

# Fracción máxima del contenido de una celda que puede cruzar UNA cara en un
# tick. Con 4 caras de salida: 4 · 0.2 = 0.8, y el 0.2 restante es la difusión
# (0.05·1·4). Así la suma de todo lo que sale de una celda nunca pasa de 1 y
# el esquema explícito no puede dejarla negativa (ver validacion_simulacion).
# Equivale a ~2 m/s por eje con L = 10 m y dt = 1 s.
FRACCION_MAXIMA_ADVECCION: float = 0.2


class Sistema_Atmosferico(Elemento_Abstracto):
    """Base de las magnitudes atmosféricas. Aporta el cálculo de advección que
    comparten las que viajan con el viento (temperatura del aire y humedad)."""

    def __init__(self, tipo: type, id_elemento, **kwargs):
        super().__init__(tipo, id_elemento, **kwargs)

    @staticmethod
    def delta_advectivo(
        valor_propio: float,
        valor_vecino: float,
        velocidad_propia: tuple[float, float],
        velocidad_vecino: tuple[float, float],
        direccion,
        bloqueado: bool,
    ) -> float:
        """
        Cambio (ya multiplicado por dt) del valor propio por el flujo a través
        de UNA cara. `direccion` es el vector unitario cardinal hacia el vecino.

        - Velocidad de la cara: media de las dos celdas proyectada sobre la
          dirección. Las dos celdas de una cara obtienen u con signo opuesto,
          y el mismo tope, así que lo que sale de una entra en la otra: se
          conserva la cantidad total, también entre Sectores.
        - Upwind: si u > 0 (sale hacia el vecino) se pierde f·valor_propio; si
          u < 0 (llega del vecino) se gana |f|·valor_vecino.
        - Con bloqueo total en cualquiera de los dos lados, el flujo es 0.
        - Pura: usa valores del tick anterior (los vecinos ya lo son).
        """
        if bloqueado:
            return 0.0
        u = 0.5 * (
            (velocidad_propia[0] + velocidad_vecino[0]) * direccion.x
            + (velocidad_propia[1] + velocidad_vecino[1]) * direccion.y
        )
        f = u * SEGUNDOS_SIMULADOS_TICK / TAMANHO_CELDA_ATMOSFERICA
        f = max(-FRACCION_MAXIMA_ADVECCION, min(FRACCION_MAXIMA_ADVECCION, f))
        origen = valor_propio if f > 0 else valor_vecino
        return -f * origen
