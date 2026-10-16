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

        Unidades: velocidad m/s; presión Pa; densidad kg/m³; aceleración
        m/s². `celda.direccion_preferente_viento + celda.fuerza_viento` es
        el viento objetivo del terreno, AHORA EN m/s.

        Fuerzas combinadas:
          1) Relajación hacia el viento objetivo del terreno (rozamiento).
          2) Gradiente de presión: la aceleración hacia cada vecino es
                 a = (p_celda - p_vecino) / (rho * L)        [m/s²]
             con rho la densidad del aire de ESTA celda y L el lado de la
             celda de atmósfera (TAMANHO_CELDA_ATMOSFERICA) como distancia al
             vecino. Se ignora que los vecinos diagonales están a L*raíz(2):
             error pequeño, acepto por simplicidad. Es física: ya no hay
             un factor mágico, solo cambiar el tamaño de celda la modifica.
             `presion` es la de ESTA celda recién recalculada este tick
             (por eso llega como parámetro); la de los vecinos es del tick
             anterior (ghost zone).
          3) resistencia_viento del terreno amortigua el resultado:
             - Si celda.bloqueo_total_viento es True, el viento se detiene
               por completo SIN mirar celda.resistencia_viento (mientras haya
               bloqueo total ese valor solo describe a los elementos no
               bloqueantes). Se consulta siempre la flag primero.
             - Si no, se amortigua con (1 - resistencia_viento).

        TODO(modelo): el sumatorio sobre 8 vecinos con dirección unitaria sobreestima
        el gradiente ~4.8x frente a -(1/rho)*grad(p). Corregir antes de añadir una
        fuente de presión: a = sum((p - p_i) * n_i * L_i) / (6 * L**2 * rho), con
        L_i = L en ejes y L*raiz(2) en diagonales.
        """

        vx = self.direccion.x * self.intensidad
        vy = self.direccion.y * self.intensidad

        objetivo_x = celda.direccion_preferente_viento.x + celda.fuerza_viento.x
        objetivo_y = celda.direccion_preferente_viento.y + celda.fuerza_viento.y
        vx += (objetivo_x - vx) * RELAJACION_VIENTO * SEGUNDOS_SIMULADOS_TICK
        vy += (objetivo_y - vy) * RELAJACION_VIENTO * SEGUNDOS_SIMULADOS_TICK

        # kg/m³. La temperatura ya está validada (> 0 K) por
        # Temperatura.actualizar, que corre antes en el mismo tick.
        densidad_aire = presion / (CONSTANTE_GAS_AIRE_SECO * celda.temperatura.valor)

        for vecino in vecinos:
            aceleracion = (presion - vecino.presion) / (
                densidad_aire * TAMANHO_CELDA_ATMOSFERICA
            )
            vx += vecino.direccion.x * aceleracion * SEGUNDOS_SIMULADOS_TICK
            vy += vecino.direccion.y * aceleracion * SEGUNDOS_SIMULADOS_TICK

        # PLACEHOLDER -- redirección de viento por bloqueo total (montaña,
        # etc.; punto #5 aparcado). Hoy no redirige nada hacia los lados
        # del bloqueo: eso requiere geometría de vectores entre celdas.
        dx_redireccion, dy_redireccion = self._calcular_redireccion(vecinos)
        vx += dx_redireccion
        vy += dy_redireccion

        factor_libre = (
            0.0
            if celda.bloqueo_total_viento
            else (1.0 - celda.resistencia_viento) ** SEGUNDOS_SIMULADOS_TICK
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
