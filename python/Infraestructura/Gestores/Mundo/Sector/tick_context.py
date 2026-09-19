# Infraestructura/Gestores/Mundo/Sector/tick_context.py
"""
Contexto que se pasa a tick() de cada elemento durante la computación
de un Sector.

Dos responsabilidades, deliberadamente separadas:

  1. LECTURA — get_celda()/en_region_propia(). Siempre devuelven el estado
     con el que empezó el tick (instantánea recibida en el delta de entrada
     + ghost zone de los vecinos), nunca el resultado de una mutación ya
     pedida por otro elemento en este mismo tick. Es una decisión de diseño
     explícita: prioriza determinismo y simplicidad (el resultado de un
     tick no depende del orden en que se computan los elementos dentro del
     sector) por encima de permitir "ver" cambios a medias dentro del tick.

  2. ESCRITURA — guardar_elemento()/eliminar_elemento()/mover_elemento().
     No aplican nada: acumulan la petición en una lista. Sector, al
     terminar de ejecutar tick() de todos sus elementos, usa
     obtener_mutaciones() para construir el TickDelta que manda a
     Logica_Mundo — quien es el único que aplica los cambios de verdad
     sobre el estado real del mundo (_gold_cells / _elements).

Por qué escritura diferida y no directa:
  Sector no tiene el estado real del mundo, solo una copia de trabajo para
  este tick (sin persistencia propia). Escribir "directamente" no tendría
  dónde persistir el cambio más allá del propio tick.
"""

from typing import Any, Optional

from Infraestructura.Gestores.Mundo.Sector.mutaciones import (
    CrearElemento,
    EliminarElemento,
    MoverElemento,
    Mutacion,
)


class TickContext:

    def __init__(
        self,
        celdas_inicio_tick,  # CeldaSectorStore (o equivalente) — instantánea de este tick, no se modifica
        ghost: dict,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
    ):
        # Estado de solo lectura: instantánea de comienzo de tick.
        # get_celda nunca refleja mutaciones pedidas durante este mismo tick.
        self._celdas = celdas_inicio_tick
        self._ghost = ghost
        self._x0, self._y0, self._x1, self._y1 = x0, y0, x1, y1

        # Mutaciones pedidas durante este tick, en el orden en que se pidieron.
        # Sector las traduce al TickDelta al terminar; aquí no se aplican.
        self._mutaciones: list[Mutacion] = []

        # Contador para generar marcadores locales únicos dentro de este tick,
        # necesario porque un mismo sector puede crear varios elementos a la vez.
        self._contador_nuevos = 0

    # ─────────────────────────────────────────
    #  Lectura (siempre estado de inicio de tick)
    # ─────────────────────────────────────────

    def get_celda(self, x: int, y: int) -> Optional[Any]:
        """Devuelve la celda en (x, y): de la región propia si cae dentro
        de los límites del sector, o de la ghost zone si es de un vecino.
        None si no hay nada en esa celda."""
        if self.en_region_propia(x, y):
            return self._celdas.get(x, y)
        return self._ghost.get((x, y))

    def en_region_propia(self, x: int, y: int) -> bool:
        return self._x0 <= x < self._x1 and self._y0 <= y < self._y1

    # ─────────────────────────────────────────
    #  Escritura (diferida — solo se acumula, no se aplica aquí)
    # ─────────────────────────────────────────

    def guardar_elemento(
        self,
        pos: tuple[int, int],
        tipo_slot: str,
        elemento: Any,
        bot_id: Optional[int] = None,
    ) -> str:

        marcador = f"nuevo_{self._contador_nuevos}"
        self._contador_nuevos += 1
        self._mutaciones.append(
            CrearElemento(
                marcador_local=marcador,
                pos=pos,
                tipo_slot=tipo_slot,
                elemento=elemento,
                bot_id=bot_id,
            )
        )
        return marcador

    def mover_elemento(
        self,
        id_elemento: int,
        pos_origen: tuple[int, int],
        pos_destino: tuple[int, int],
        bot_id: Optional[int] = None,
    ) -> None:
        self._mutaciones.append(
            MoverElemento(
                id_elemento=id_elemento,
                pos_origen=pos_origen,
                pos_destino=pos_destino,
                bot_id=bot_id,
            )
        )

    def mover_elemento(
        self,
        id_elemento: int,
        pos_origen: tuple[int, int],
        pos_destino: tuple[int, int],
    ) -> None:
        """Pide mover un elemento existente. Si pos_destino cae fuera de
        este sector, Logica_Mundo se encarga de la migración al aplicar
        la mutación — este método no necesita saberlo."""
        self._mutaciones.append(
            MoverElemento(
                id_elemento=id_elemento,
                pos_origen=pos_origen,
                pos_destino=pos_destino,
            )
        )

    # ─────────────────────────────────────────
    #  Cierre del tick
    # ─────────────────────────────────────────

    def obtener_mutaciones(self) -> list[Mutacion]:
        """Llamado por Sector al terminar de ejecutar tick() de todos sus
        elementos, para construir el TickDelta que se envía a Logica_Mundo."""
        return self._mutaciones
