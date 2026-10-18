# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/viento.py

from __future__ import annotations

import math

from vectors import Vector2

from Config.parametros_simulacion import (
    TAMANHO_CELDA_ATMOSFERICA,
    SEGUNDOS_SIMULADOS_TICK,
)
from Config.settings import ID_VIENTO
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)

# Constante específica del aire seco, J/(kg·K). Sirve para sacar la
# densidad del aire de su presión y temperatura (gas ideal): rho = p/(R*T).
CONSTANTE_GAS_AIRE_SECO: float = 287.05

# Fracción de la distancia al viento "objetivo" del terreno que se recorre
# por segundo (1/s). Hace de rozamiento: sin ella el viento aceleraría sin
# límite bajo un gradiente de presión. SIN CALIBRAR (antes 0.1 por tick).
RELAJACION_VIENTO: float = 0.1


class Viento(Sistema_Atmosferico):
    def __init__(
        self,
        intensidad_inicial: float = 0.0,
        direccion_inicial: Vector2 | None = None,
        **kwargs,
    ):
        super().__init__(Viento, ID_VIENTO, **kwargs)
        # m/s. La dirección es un vector unitario.
        self.intensidad: float = intensidad_inicial
        self.direccion: Vector2 = direccion_inicial or Vector2(0, 0)

    def get(
        self, posicion: tuple[int, int]
    ): ...  # TODO -- fuera del alcance de este cambio, se deja tal cual.

    def actualizar(self, celda, presion: float, vecinos: list) -> None:
        """
        El viento se trabaja como un único vector de velocidad (m/s) para
        poder sumarle fuerzas, y al final se descompone en (intensidad,
        direccion). Un tick dura SEGUNDOS_SIMULADOS_TICK segundos.

        Fuerzas combinadas:
          1) Relajación hacia el viento objetivo del terreno (rozamiento).
          2) Gradiente de presión con diferencias centradas sobre los 4
             vecinos cardinales: a_x = (p_oeste - p_este) / (2·rho·L).
             Cada vecino aporta (p - p_vecino)/(2·rho·L) en su dirección; el
             2 sale de que la distancia entre oeste y este es 2L. `presion` es
             la de ESTA celda recién recalculada este tick; la de los vecinos
             es del tick anterior (ghost zone).
          3) Bordes cerrados: si no hay vecino en una dirección (borde del
             mundo), se anula la componente que empuja hacia fuera.
          4) resistencia_viento del terreno amortigua el resultado:
             - Con celda.bloqueo_total_viento el viento se detiene por
               completo SIN mirar resistencia_viento (se consulta siempre la
               flag primero).
             - Si no, se amortigua con (1 - resistencia_viento)^dt.
        """
        dt = SEGUNDOS_SIMULADOS_TICK

        vx = self.direccion.x * self.intensidad
        vy = self.direccion.y * self.intensidad

        # m/s. Velocidad objetivo del terreno hacia la que relaja el viento.
        objetivo_x = celda.viento_objetivo.x
        objetivo_y = celda.viento_objetivo.y
        vx += (objetivo_x - vx) * RELAJACION_VIENTO * dt
        vy += (objetivo_y - vy) * RELAJACION_VIENTO * dt

        # kg/m³. La temperatura ya está validada (> 0 K) por
        # Temperatura.actualizar, que corre antes en el mismo tick.
        densidad_aire = presion / (CONSTANTE_GAS_AIRE_SECO * celda.temperatura.valor)

        for vecino in vecinos:
            aceleracion = (presion - vecino.presion) / (
                2.0 * densidad_aire * TAMANHO_CELDA_ATMOSFERICA
            )
            vx += vecino.direccion.x * aceleracion * dt
            vy += vecino.direccion.y * aceleracion * dt

        # PLACEHOLDER -- redirección de viento por bloqueo total (punto #5
        # aparcado): hoy no redirige nada.
        dx_redireccion, dy_redireccion = self._calcular_redireccion(vecinos)
        vx += dx_redireccion
        vy += dy_redireccion

        # Bordes cerrados. Las direcciones de los vecinos son exactamente
        # (±1,0)/(0,±1), así que se pueden comparar por igualdad.
        presentes = {(v.direccion.x, v.direccion.y) for v in vecinos}
        if (1.0, 0.0) not in presentes:
            vx = min(vx, 0.0)  # sin vecino al este: no puede salir hacia él
        if (-1.0, 0.0) not in presentes:
            vx = max(vx, 0.0)
        if (0.0, 1.0) not in presentes:
            vy = min(vy, 0.0)
        if (0.0, -1.0) not in presentes:
            vy = max(vy, 0.0)

        factor_libre = (
            0.0
            if celda.bloqueo_total_viento
            else (1.0 - celda.resistencia_viento) ** dt
        )
        vx *= factor_libre
        vy *= factor_libre

        self.intensidad = math.hypot(vx, vy)
        self.direccion = (
            Vector2(vx / self.intensidad, vy / self.intensidad)
            if self.intensidad > 0
            else Vector2(0, 0)
        )

    @staticmethod
    def _calcular_redireccion(vecinos: list) -> tuple[float, float]:
        """
        PLACEHOLDER -- sin implementar. Devuelve (0.0, 0.0), sin efecto.
        """
        return 0.0, 0.0
