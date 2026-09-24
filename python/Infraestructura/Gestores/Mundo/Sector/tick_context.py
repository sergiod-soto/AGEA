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
        celdas_inicio_tick,
        ghost: dict,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        atmosfera=None,  # CeldaAtmosferaStore propio del Sector
        ghost_atmosfera: dict = None,
        escala_atmosfera: int = 1,
    ):
        self._celdas = celdas_inicio_tick
        self._ghost = ghost
        self._x0, self._y0, self._x1, self._y1 = x0, y0, x1, y1
        self._atmosfera = atmosfera
        self._ghost_atmosfera = ghost_atmosfera or {}
        self._escala_atmosfera = escala_atmosfera
        self._mutaciones: list[Mutacion] = []
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

    def get_atmosfera(self, x: int, y: int):
        """
        Devuelve la Celda_Atmosfera que cubre la posición de TERRENO (x, y)
        -- quien llama no necesita conocer ATMOSFERA_ESCALA, la conversión
        se hace aquí (igual que Mundo.pos_suelo_a_atmosfera).

        Devuelve la celda VIVA (no una copia): en compute_tick, tick() de
        los elementos corre ANTES de _avanzar_atmosfera, así que esto ya
        es consistente con leer "estado de inicio de tick" sin necesidad
        de congelar nada. No mutar lo que devuelve este método.

        None si la posición no está en la malla propia del Sector.

        LIMITACIÓN CONOCIDA, sin resolver a propósito: la ghost zone de
        atmósfera (self._ghost_atmosfera) solo tiene margen de 1 bloque,
        y además guarda AtmosphereCell (proto), no Celda_Atmosfera -- un
        tipo distinto al que se devuelve para la malla propia. Hoy no hace
        falta resolverlo: el único consumidor (Suelo.tick, vía
        Transformable) siempre consulta su PROPIA posición, que por
        definición cae dentro de la malla propia del Sector, nunca en la
        ghost zone. Si en el futuro algo (p.ej. un bot con visión) necesita
        consultar atmósfera fuera de su propio bloque, esto habrá que
        revisarlo: o se unifica el tipo devuelto, o se documenta que
        get_atmosfera solo sirve para "mi propia celda".
        """
        pos_atmosfera = (x // self._escala_atmosfera, y // self._escala_atmosfera)
        if self._atmosfera is None:
            return None
        return self._atmosfera.get(*pos_atmosfera)

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

    def eliminar_elemento(
        self,
        id_elemento: int,
        pos: tuple[int, int],
        bot_id: Optional[int] = None,
    ) -> None:
        self._mutaciones.append(
            EliminarElemento(
                id_elemento=id_elemento,
                pos=pos,
                bot_id=bot_id,
            )
        )

    # ─────────────────────────────────────────
    #  Cierre del tick
    # ─────────────────────────────────────────

    def obtener_mutaciones(self) -> list[Mutacion]:
        """Llamado por Sector al terminar de ejecutar tick() de todos sus
        elementos, para construir el TickDelta que se envía a Logica_Mundo."""
        return self._mutaciones
