# Core/Mundo/mundo.py
"""
Este Mundo es El Mundo.
Es el mapa que es dividido en chunks.

Dueño único del estado espacial: qué hay en cada celda de terreno, qué
hay en cada celda de atmósfera, y dónde está cada elemento por su id.
No sabe nada de locks, snapshots, red o scripts de bots -- eso sigue
siendo responsabilidad de Logica_Mundo, que posee una instancia de
Mundo y la usa bajo su propio lock async. Mundo en sí es síncrono a
propósito: es solo estructura de datos + operaciones básicas sobre
ella, sin condiciones de carrera que gestionar por sí mismo.
"""

from __future__ import annotations

from typing import Any, Optional

from numpy import uint64

import Config.settings as config
from Core.Entities.Mundo.Celda.celda import Celda
from Core.Entities.Mundo.Celda.celda_atmosfera import Celda_Atmosfera
from Core.Entities.Elementos.elemento import Elemento
from Infraestructura.Gestores.Mundo.Bus_Eventos.bus import BusEventos


class Mundo:
    """
    Orden actualizacion metereologia:
    - 1) radiacion
    - 2) temperatura
    - 3) presion
    - 4) viento
    - 5) humedad_absoluta
    - 6) nubes
    """

    def __init__(self) -> None:
        self.bus_eventos = BusEventos()

        # id_elemento -> objeto real. Antes Logica_Mundo._elements.
        self.elementos: dict[uint64, Any] = {}

        # posición -> Celda (ids de suelo/bot/resto en esa posición).
        # Antes Logica_Mundo._gold_cells.
        self.malla_terreno: dict[tuple[int, int], Celda] = {}

        # posición EN ESPACIO DE ATMÓSFERA -> Celda_Atmosfera.
        # Antes Logica_Mundo._gold_atmosfera.
        self.malla_atmosfera: dict[tuple[int, int], Celda_Atmosfera] = {}

        # id_elemento -> posición. Único índice de posición por id --
        # sustituye a Logica_Mundo._bot_positions (que solo indexaba
        # bots, y por su stat "id" externo, no por id_elemento).
        self.ids: dict[uint64, tuple[int, int]] = {}

        # bot_id (stat "id" del Bot, externo -- lo usan los scripts y la
        # API de matar/eliminar avatar) -> id_elemento (interno, la clave
        # real en self.elementos/self.ids). Es la única pieza que sigue
        # distinguiendo "id externo del bot" de "id interno del mundo":
        # eliminar_avatar_bot/matar_bot reciben bot_id, no id_elemento,
        # y no hay forma de unificar eso sin cambiar esas dos APIs.
        # Deliberadamente pequeña (solo bots), no un segundo mapa de
        # posiciones.
        self.bots: dict[int, uint64] = {}

        # Cuántas celdas de suelo (por lado) cubre una celda de
        # atmósfera. Con escala 2, una Celda_Atmosfera engloba un bloque
        # de 2x2 celdas de suelo (mismo origen 0,0 en ambos grids).
        self.escala_atmosfera: int = config.ATMOSFERA_ESCALA

    # ---- Elementos: alta / baja / movimiento ----

    def crear_elemento(
        self,
        eid: uint64,
        pos: tuple[int, int],
        tipo_slot: str,
        elemento: Any,
        bot_id: Optional[int] = None,
    ) -> None:
        """Registra 'elemento' bajo 'eid', lo coloca en 'pos' según
        'tipo_slot', e indexa su posición. 'bot_id' es opcional -- solo
        se pasa cuando el elemento es un bot y se conoce su id externo."""
        self.elementos[eid] = elemento
        celda = self.malla_terreno.setdefault(pos, Celda())
        celda.put_elemento(eid, tipo_slot)
        self.ids[eid] = pos
        if bot_id is not None:
            self.bots[bot_id] = eid

    def eliminar_elemento(self, eid: uint64, bot_id: Optional[int] = None) -> bool:
        """Quita 'eid' de la malla, del registro de objetos y del índice
        de posición. 'bot_id' se pasa si se conoce, para limpiar también
        la tabla bot_id -> id_elemento. False si 'eid' no estaba."""
        pos = self.ids.get(eid)
        if pos is None:
            return False
        celda = self.malla_terreno.get(pos)
        if celda is None or not celda.remove_elemento(eid):
            return False

        if celda.vacia():
            self.malla_terreno.pop(pos, None)
        self.elementos.pop(eid, None)
        self.ids.pop(eid, None)
        if bot_id is not None:
            self.bots.pop(bot_id, None)
        return True

    def mover_elemento(self, eid: uint64, pos_destino: tuple[int, int]) -> bool:
        """Mueve 'eid' a 'pos_destino', conservando su slot. No hace
        falta tocar 'bots': esa tabla apunta a id_elemento, no a
        posición, así que sigue siendo válida tras el movimiento."""
        pos_origen = self.ids.get(eid)
        if pos_origen is None:
            return False
        celda_origen = self.malla_terreno.get(pos_origen)
        if celda_origen is None:
            return False

        tipo_slot = celda_origen.tipo_slot_de(eid)
        if tipo_slot is None:
            return False
        celda_origen.remove_elemento(eid)
        if celda_origen.vacia():
            self.malla_terreno.pop(pos_origen, None)

        celda_destino = self.malla_terreno.setdefault(pos_destino, Celda())
        celda_destino.put_elemento(eid, tipo_slot)
        self.ids[eid] = pos_destino
        return True

    # ---- Consultas ----

    def obtener_elemento(self, eid: uint64) -> Optional[Any]:
        return self.elementos.get(eid)

    def obtener_posicion(self, eid: uint64) -> Optional[tuple[int, int]]:
        return self.ids.get(eid)

    def obtener_celda(self, pos: tuple[int, int]) -> Optional[Celda]:
        return self.malla_terreno.get(pos)

    def contiene(self, pos: tuple[int, int], eid: uint64) -> bool:
        celda = self.malla_terreno.get(pos)
        return celda is not None and celda.contiene(eid)

    def id_elemento_de_bot(self, bot_id: int) -> Optional[uint64]:
        return self.bots.get(bot_id)

    def registrar_elemento_reconstruido(self, eid: uint64, elemento: Any) -> None:
        """Guarda un elemento ya deserializado sin tocar malla ni
        posición -- lo usa Logica_Mundo._slot_bytes_a_id, que solo
        necesita tener el objeto disponible por id, todavía sin saber en
        qué celda va (eso lo decide quien llame después)."""
        self.elementos[eid] = elemento

    def celdas_en_region(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        excluir_min: Optional[tuple[int, int]] = None,
        excluir_max: Optional[tuple[int, int]] = None,
    ) -> list[tuple[tuple[int, int], Celda]]:
        x0, y0 = min_pos
        x1, y1 = max_pos
        tiene_exclusion = excluir_min is not None and excluir_max is not None
        if tiene_exclusion:
            ex0, ey0 = excluir_min  # type: ignore
            ex1, ey1 = excluir_max  # type: ignore

        resultado = []
        for (x, y), celda in self.malla_terreno.items():
            if not (x0 <= x < x1 and y0 <= y < y1):
                continue
            if tiene_exclusion and (ex0 <= x < ex1 and ey0 <= y < ey1):
                continue
            resultado.append(((x, y), celda))
        return resultado

    def actualizar_celda(self, pos: tuple[int, int], celda: Celda) -> None:
        """
        Reemplaza la celda completa en 'pos' (sincronización con otro
        proceso/sector). Sincroniza 'ids' para todos los elementos de la
        celda nueva, y libera las entradas de 'ids' que apuntaban a
        'pos' para elementos que ya no están en la celda que llega --
        necesario porque 'ids' es ahora el único índice de posición: si
        no se sincroniza aquí, un elemento introducido por esta vía
        quedaría con posición en la malla pero sin entrada en 'ids'.
        """
        anterior = self.malla_terreno.get(pos)
        ids_anteriores = (
            {anterior.suelo, anterior.bot, *anterior.resto} - {None}
            if anterior is not None
            else set()
        )
        ids_nuevos = {celda.suelo, celda.bot, *celda.resto} - {None}

        for eid in ids_anteriores - ids_nuevos:
            self.ids.pop(eid, None)

        if celda.vacia():
            self.malla_terreno.pop(pos, None)
        else:
            self.malla_terreno[pos] = celda
            for eid in ids_nuevos:
                self.ids[eid] = pos

    # ---- Atmósfera ----

    def pos_suelo_a_atmosfera(self, pos_suelo: tuple[int, int]) -> tuple[int, int]:
        """// (floor division), no /, para que las coordenadas negativas
        agrupen bien: con escala 2, -1 y -2 caen en el mismo bloque."""
        x, y = pos_suelo
        escala = self.escala_atmosfera
        return (x // escala, y // escala)

    def crear_atmosfera(
        self,
        pos_atmosfera: tuple[int, int],
        resistencia_viento: float,
        direccion_preferente_viento: Any,
        fuerza_viento: Any,
        bioma: Any,
    ) -> None:
        self.malla_atmosfera[pos_atmosfera] = Celda_Atmosfera(
            posicion=pos_atmosfera,
            resistencia_viento=resistencia_viento,
            direccion_preferente_viento=direccion_preferente_viento,
            fuerza_viento=fuerza_viento,
            bioma=bioma,
        )

    def obtener_atmosfera(
        self, pos_atmosfera: tuple[int, int]
    ) -> Optional[Celda_Atmosfera]:
        return self.malla_atmosfera.get(pos_atmosfera)

    # ---- API por objeto (TODO -- ver nota en la respuesta) ----

    def eliminar_elemento_obj(self, elemento: Elemento):
        raise NotImplementedError  # TODO

    def agregar_elemento(self, elemento: Elemento):
        elemento.mundo = self
        # TODO: resto de agregar_elemento() en mundo.py
