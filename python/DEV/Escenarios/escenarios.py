# Dev/Escenarios/escenarios.py

from __future__ import annotations

from typing import Callable

from Core.Entities.Mundo import datos
from Dev.Escenarios.serie_estados import Serie_Estados

# Cada función recibe la Serie_Estados a rellenar y no devuelve nada:
# su efecto es llamar a serie.add(...) las veces que haga falta.
TipoEscenario = Callable[[Serie_Estados], None]


def _escenario_dos_bots_test(serie: Serie_Estados) -> None:
    """
    Migrado de Serie_Estados.test(): "b0.test" alterna girando sobre
    sí mismo, "b3.test" recorre un cuadrado de 50x50 en pasos de 10
    y reinicia.

    Nota heredada del original: asume que "b0.test" y "b3.test" ya
    existen en datos.bots antes de cargar este escenario -- si no,
    fallará al primer acceso. No se corrige aquí porque no es parte
    del problema que se está resolviendo ahora mismo.
    """

    def girar():
        datos.bots["b0.test"].rotacion += 5
        serie.add([lambda: girar()])


    def mover_x():
        casilla = datos.bots["b3.test"].casilla
        if casilla[0] >= 50:
            serie.add([lambda: mover_y()])
        else:
            datos.bots["b3.test"].casilla = (casilla[0] + 10, casilla[1])
            serie.add([lambda: mover_x()])

    def mover_y():
        casilla = datos.bots["b3.test"].casilla
        if casilla[1] >= 50:
            serie.add([lambda: reiniciar()])
        else:
            datos.bots["b3.test"].casilla = (casilla[0], casilla[1] + 10)
            serie.add([lambda: mover_y()])

    def reiniciar():
        datos.bots["b3.test"].casilla = (15, 15)
        serie.add([lambda: mover_x()])

    girar()
    mover_x()


# Nombre -> función que puebla el escenario. Añadir uno nuevo es una
# línea aquí, no un cambio en Serie_Estados ni en cargar_escenario().
ESCENARIOS: dict[str, TipoEscenario] = {
    "dos_bots_test": _escenario_dos_bots_test,
}


def cargar_escenario(nombre: str, serie: Serie_Estados) -> None:
    """
    Punto de entrada único: busca `nombre` en el registro y lo aplica
    sobre `serie`. Lanza KeyError con los nombres válidos si no
    existe, en vez de arrancar en silencio con un escenario vacío
    (que sería mucho más difícil de diagnosticar).
    """
    escenario = ESCENARIOS.get(nombre)
    if escenario is None:
        raise KeyError(
            f"Escenario desconocido: '{nombre}'. Válidos: {list(ESCENARIOS)}"
        )
    escenario(serie)
