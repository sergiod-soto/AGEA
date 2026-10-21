# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/nube.py

"""
Agua líquida en suspensión de una celda de atmósfera (la nube), en kg/m³ de aire.

Es una magnitud primaria y distinta del vapor: el vapor (Humedad_Absoluta) pasa
a nube y viceversa por la condensación, que NO vive aquí sino en el orquestador
(sistema_atmosferico._condensar), porque toca tres magnitudes (vapor, nube y
temperatura del aire) y ninguna debe modificar a otra.

Aquí solo hay TRANSPORTE: la nube viaja con el viento (advección upwind, la
misma de temperatura y humedad), sin difusión propia. El upwind de primer
orden ya suaviza los bordes por difusión numérica. Como la advección conserva
la cantidad (lo que sale de una celda entra en la vecina, también entre
Sectores), la nube total solo cambia por condensación o evaporación.
"""

from Config.settings import ID_NUBE
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)


class Nube(Sistema_Atmosferico):

    def __init__(self, valor_inicial: float = 0.0, **kwargs):
        super().__init__(Nube, ID_NUBE, **kwargs)
        # kg/m³ de agua líquida en el aire de la celda.
        self.valor: float = valor_inicial

    def actualizar(
        self,
        vecinos: list,
        velocidad: tuple[float, float],
        bloqueado: bool,
    ) -> None:
        """
        Advecta con el viento (`velocidad` en m/s y `bloqueado` son los de ESTA
        celda al inicio del tick; los vecinos, del tick anterior). Estabilidad:
        ver Config/validacion_simulacion (sin difusión: 4·0.2 = 0.8 <= 1).
        """
        # kg/m³ que entran/salen con el viento (ya incluye dt).
        adveccion = sum(
            self.delta_advectivo(
                self.valor,
                vecino.nube,
                velocidad,
                (vecino.viento_x, vecino.viento_y),
                vecino.direccion,
                bloqueado or vecino.bloqueo_total_viento,
            )
            for vecino in vecinos
        )
        # max(): protege del redondeo; la nube no puede ser negativa.
        self.valor = max(0.0, self.valor + adveccion)
