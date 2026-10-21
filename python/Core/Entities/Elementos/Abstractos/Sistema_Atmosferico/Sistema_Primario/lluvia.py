# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Sistema_Primario/lluvia.py

"""
Lluvia caída en una celda de atmósfera durante el ÚLTIMO tick, en kg/m² de
celda (columna de agua).

Es una magnitud transitoria: se SUSTITUYE en cada tick (no se acumula) y no
viaja con el viento, por eso no está en EstadoCelda. La lógica que la calcula
(autoconversión de nube a lluvia) NO vive aquí sino en el orquestador
(sistema_atmosferico._precipitar), igual que la condensación: toca dos
magnitudes (nube y lluvia) y ninguna debe modificar a otra.

Los elementos la leen con ctx.get_atmosfera(...).lluvia.valor en el tick
SIGUIENTE (el agua llega con un tick de retraso) y deciden qué hacer con ella
(el barro se moja, la piedra no).

Es intensiva (kg/m² de celda): cada casilla de las ATMOSFERA_ESCALA² que cubre
la celda ve el mismo valor, a diferencia de Evaporar, que sí se reparte.

TODO (decisión 2, aplazada): el reparto del agua a las casillas y el destino
del agua que nadie absorbe. Hoy el agua no absorbida se pierde: el agua total
del mundo NO se conserva.
"""

from Config.settings import ID_LLUVIA
from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)


class Lluvia(Sistema_Atmosferico):

    def __init__(self, valor_inicial: float = 0.0, **kwargs):
        super().__init__(Lluvia, ID_LLUVIA, **kwargs)
        # kg/m² de celda caídos en el último tick.
        self.valor: float = valor_inicial
