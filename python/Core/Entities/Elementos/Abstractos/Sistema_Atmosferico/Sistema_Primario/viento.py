# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/viento.py

from __future__ import annotations

import math

from vectors import Vector2

from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)

# Cuánto se acerca el viento a su objetivo de terreno (preferente +
# artificial) cada tick.
RELAJACION_VIENTO: float = 0.1

# Cuánta influencia tiene la diferencia de presión con cada vecino sobre
# el viento resultante (el viento sopla de más presión a menos presión).
FACTOR_GRADIENTE_PRESION: float = 0.02


class Viento(Sistema_Atmosferico):
    def __init__(
        self,
        intensidad_inicial: float = 0.0,
        direccion_inicial: Vector2 | None = None,
        **kwargs,
    ):
        super().__init__(Viento, **kwargs)
        self.intensidad: float = intensidad_inicial
        self.direccion: Vector2 = direccion_inicial or Vector2(0, 0)

    def get(
        self, posicion: tuple[int, int]
    ): ...  # TODO -- fuera del alcance de este cambio, se deja tal cual.

    def actualizar(self, celda, presion: float, vecinos: list) -> None:
        """
        Se trabaja el viento como un único vector (intensidad *
        dirección) para poder sumarle fuerzas cómodamente, y al final
        se descompone de nuevo en (intensidad, direccion).

        NOTA sobre Vector2: no se asume que soporte operadores
        aritméticos (+, *, normalize...) más allá de tener .x/.y y un
        constructor Vector2(x, y) -- es lo único que se ve usado en
        celda_atmosfera.py (`Vector2(0, 0)`). Si sí los soporta, esto se
        puede simplificar bastante.

        Fuerzas combinadas:
          1) Relajación hacia el viento "de terreno" de `celda`:
             direccion_preferente_viento + fuerza_viento (se tratan
             ambos como vectores y se suman -- revisar si fuerza_viento
             resulta ser en realidad solo una magnitud).
          2) Gradiente de presión: empuje hacia los vecinos con menor
             `presion` (la de ESTA celda, ya recalculada este tick por
             Presion.actualizar -- por eso se recibe como parámetro en
             vez de leerse de `celda`) y desde los de mayor presión,
             usando el vector `direccion` de cada EstadoVecino (del tick
             anterior, ghost zone).
          3) resistencia_viento del terreno amortigua el resultado final
             (0 = libre, 1 = bloqueado por completo).
        """
        vx = self.direccion.x * self.intensidad
        vy = self.direccion.y * self.intensidad

        objetivo_x = celda.direccion_preferente_viento.x + celda.fuerza_viento.x
        objetivo_y = celda.direccion_preferente_viento.y + celda.fuerza_viento.y
        vx += (objetivo_x - vx) * RELAJACION_VIENTO
        vy += (objetivo_y - vy) * RELAJACION_VIENTO

        for vecino in vecinos:
            diferencia_presion = presion - vecino.presion
            vx += vecino.direccion.x * diferencia_presion * FACTOR_GRADIENTE_PRESION
            vy += vecino.direccion.y * diferencia_presion * FACTOR_GRADIENTE_PRESION

        factor_libre = 1.0 - celda.resistencia_viento
        vx *= factor_libre
        vy *= factor_libre

        self.intensidad = math.hypot(vx, vy)
        self.direccion = (
            Vector2(vx / self.intensidad, vy / self.intensidad)
            if self.intensidad > 0
            else Vector2(0, 0)
        )
