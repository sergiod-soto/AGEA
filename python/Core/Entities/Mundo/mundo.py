# Core/Entities/Mundo/mundo.py
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
from vectors import Vector2

from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.Estacion.estaciones import (
    Estaciones,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.ciclo_anual import (
    Ciclo_Anual,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.ciclo_lunar import (
    Ciclo_Lunar,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.ciclo_solar import (
    Ciclo_Solar,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj
from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera
from Core.Entities.Mundo.Suelo.celda import Celda
from Core.Entities.Mundo.bus_eventos import BusEventos


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
        self.elementos: dict[int, Any] = {}

        # posición -> Celda (ids de suelo/bot/resto en esa posición).
        # Antes Logica_Mundo._gold_cells.
        self.malla_terreno: dict[tuple[int, int], Celda] = {}

        # posición EN ESPACIO DE ATMÓSFERA -> Celda_Atmosfera.
        # Antes Logica_Mundo._gold_atmosfera.
        self.malla_atmosfera: dict[tuple[int, int], Celda_Atmosfera] = {}

        # Celdas de atmósfera cuyo terreno (viento_objetivo) cambió desde el
        # último tick, en espacio de atmósfera. Las toma el Gestor en la fase 0
        # (tomar_parches_atmosfera) para enviarlas al Sector. Estado TRANSITORIO:
        # no se persiste en snapshots, porque el valor ya está en la celda.
        self._parches_atmosfera: set[tuple[int, int]] = set()

        # id_elemento -> posición. Único índice de posición por id --
        # sustituye a Logica_Mundo._bot_positions (que solo indexaba
        # bots, y por su stat "id" externo, no por id_elemento).
        self.ids: dict[int, tuple[int, int]] = {}

        # bot_id (stat "id" del Bot, externo -- lo usan los scripts y la
        # API de matar/eliminar avatar) -> id_elemento (interno, la clave
        # real en self.elementos/self.ids). Es la única pieza que sigue
        # distinguiendo "id externo del bot" de "id interno del mundo":
        # eliminar_avatar_bot/matar_bot reciben bot_id, no id_elemento,
        # y no hay forma de unificar eso sin cambiar esas dos APIs.
        # Deliberadamente pequeña (solo bots), no un segundo mapa de
        # posiciones.
        self.bots: dict[int, int] = {}

        # Reloj encargado de controlar los eventos guiados por el tiempo.
        self.reloj = Reloj()

        # Ciclos astrales
        self.ciclo_solar = Ciclo_Solar(self)
        self.ciclo_lunar = Ciclo_Lunar(self)
        self.ciclo_anual = Ciclo_Anual(self)

        # Estaciones
        self.estaciones = Estaciones(self)

    # ---- Elementos: alta / baja / movimiento ----

    def crear_elemento(
        self,
        eid: int,
        pos: tuple[int, int],
        tipo_slot: str,
        elemento: Any,
        bot_id: Optional[int] = None,
    ) -> None:
        """Registra 'elemento' bajo 'eid', lo coloca en 'pos' según
        'tipo_slot', e indexa su posición. 'bot_id' es opcional -- solo
        se pasa cuando el elemento es un bot y se conoce su id externo."""
        if eid in self.elementos:
            raise ValueError(f"El id {eid} ya está registrado.")
        if self._slot_ocupado(pos, tipo_slot):
            raise ValueError(f"El slot '{tipo_slot}' de {pos} ya está ocupado.")
        self.elementos[eid] = elemento
        celda = self.malla_terreno.setdefault(pos, Celda())
        celda.put_elemento(eid, tipo_slot)
        self.ids[eid] = pos
        if bot_id is not None:
            self.bots[bot_id] = eid

    def eliminar_elemento(self, eid: int, bot_id: Optional[int] = None) -> bool:
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

    def _slot_ocupado(self, pos: tuple[int, int], tipo_slot: str) -> bool:
        """True si el slot es de ocupación única (suelo/bot) y ya tiene ocupante.
        Celda.put_elemento sobrescribe sin avisar y dejaría huérfano al anterior."""
        celda = self.malla_terreno.get(pos)
        return (
            celda is not None
            and tipo_slot in ("suelo", "bot")
            and getattr(celda, tipo_slot) is not None
        )

    # ---- Consultas ----

    def obtener_elemento(self, eid: int) -> Optional[Any]:
        return self.elementos.get(eid)

    def obtener_posicion(self, eid: int) -> Optional[tuple[int, int]]:
        return self.ids.get(eid)

    def obtener_celda(self, pos: tuple[int, int]) -> Optional[Celda]:
        return self.malla_terreno.get(pos)

    def contiene(self, pos: tuple[int, int], eid: int) -> bool:
        celda = self.malla_terreno.get(pos)
        return celda is not None and celda.contiene(eid)

    def id_elemento_de_bot(self, bot_id: int) -> Optional[int]:
        return self.bots.get(bot_id)

    def registrar_elemento_reconstruido(self, eid: int, elemento: Any) -> None:
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

    def celdas_atmosfera_en_region(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        excluir_min: Optional[tuple[int, int]] = None,
        excluir_max: Optional[tuple[int, int]] = None,
    ) -> list[tuple[tuple[int, int], Celda_Atmosfera]]:
        """
        Análogo a celdas_en_region, pero sobre malla_atmosfera. A
        diferencia de esa, min_pos/max_pos ya están en espacio de
        atmósfera (no hace falta convertir) -- quien llama
        (Gestor_Mundo, calculando el rectángulo de un Sector) ya sabe
        convertir.
        """
        x0, y0 = min_pos
        x1, y1 = max_pos
        tiene_exclusion = excluir_min is not None and excluir_max is not None
        if tiene_exclusion:
            ex0, ey0 = excluir_min  # type: ignore
            ex1, ey1 = excluir_max  # type: ignore

        resultado = []
        for (x, y), celda in self.malla_atmosfera.items():
            if not (x0 <= x < x1 and y0 <= y < y1):
                continue
            if tiene_exclusion and (ex0 <= x < ex1 and ey0 <= y < ey1):
                continue
            resultado.append(((x, y), celda))
        return resultado

    def actualizar_celda(self, pos: tuple[int, int], celda: Celda) -> set[int]:
        """
        Reemplaza la celda completa en 'pos' (sincronización con otro
        proceso/sector). Sincroniza 'ids' para los elementos de la celda
        nueva y libera el índice de los que ya no están.

        Devuelve los ids que SALIERON de esta celda. No se puede saber aquí
        si se eliminaron o solo se movieron a otra celda del mismo lote (el
        orden de llegada es arbitrario), así que quien llama decide cuando
        haya aplicado todo el lote (ver Logica_Mundo.actualizar_celdas).
        """
        anterior = self.malla_terreno.get(pos)
        ids_anteriores = (
            {anterior.suelo, anterior.bot, *anterior.resto} - {None}
            if anterior is not None
            else set()
        )
        ids_nuevos = {celda.suelo, celda.bot, *celda.resto} - {None}

        salientes = ids_anteriores - ids_nuevos
        for eid in salientes:

            if self.ids.get(eid) == pos:
                self.ids.pop(eid, None)

        if celda.vacia():
            self.malla_terreno.pop(pos, None)
        else:
            self.malla_terreno[pos] = celda
            for eid in ids_nuevos:
                self.ids[eid] = pos

        return salientes

    def olvidar_elemento(self, eid: int, bot_id: Optional[int] = None) -> None:
        """Borra el objeto y su entrada en 'bots' SIN tocar malla ni 'ids'
        (ya sincronizados por actualizar_celda). Para elementos eliminados
        por un Sector, cuya baja llega como "la celda ya no lo contiene"."""
        self.elementos.pop(eid, None)
        if bot_id is not None:
            self.bots.pop(bot_id, None)

    # ---- Atmósfera ----

    def crear_atmosfera(
        self, pos_atmosfera: tuple[int, int], viento_objetivo: Vector2
    ) -> None:
        """Alta de una Celda_Atmosfera. `pos_atmosfera` está en espacio de
        ATMÓSFERA (no de suelo). ValueError si ya existe: sobrescribir en
        silencio perdería el estado simulado y el viento_objetivo (que el
        espejo no restaura) sin avisar al Sector. Para cambiar el viento de
        una celda existente se usa actualizar_atmosfera (parche)."""
        if pos_atmosfera in self.malla_atmosfera:
            raise ValueError(f"Ya existe una celda de atmósfera en {pos_atmosfera}.")
        self.malla_atmosfera[pos_atmosfera] = Celda_Atmosfera(
            posicion=pos_atmosfera, viento_objetivo=viento_objetivo
        )

    def obtener_atmosfera(
        self, pos_atmosfera: tuple[int, int]
    ) -> Optional[Celda_Atmosfera]:
        """Celda_Atmosfera VIVA en `pos_atmosfera` (espacio de atmósfera), o
        None. Sin lock: quien llame desde código async debe tomar el de Logica."""
        return self.malla_atmosfera.get(pos_atmosfera)

    def actualizar_atmosfera(self, pos_atmosfera: tuple[int, int], patch: dict) -> None:
        """
        Aplica un parche de terreno a la celda y la marca pendiente de envío al
        Sector (fase 0). `pos_atmosfera` en espacio de ATMÓSFERA.
          - KeyError si no hay celda en esa posición.
          - ValueError si el parche es inválido (lo valida Celda_Atmosfera).
        La marca se añade DESPUÉS de aplicar: un parche rechazado no deja
        ninguna celda marcada.
        """
        celda = self.malla_atmosfera.get(pos_atmosfera)
        if celda is None:
            raise KeyError(f"No hay celda de atmósfera en {pos_atmosfera}.")
        celda.aplicar_patch(patch)
        self._parches_atmosfera.add(pos_atmosfera)

    def tomar_parches_atmosfera(self) -> list[Celda_Atmosfera]:
        """
        Celdas parcheadas desde la última llamada, ordenadas por posición (orden
        determinista), y VACÍA la lista de pendientes. Si la entrega al Sector
        falla es fatal, así que no se reencola: el valor ya está en la celda.
        """
        posiciones = sorted(self._parches_atmosfera)
        self._parches_atmosfera.clear()
        return [
            self.malla_atmosfera[p] for p in posiciones if p in self.malla_atmosfera
        ]

    def descartar_parches_atmosfera(self) -> None:
        """Olvida los parches pendientes (p. ej. tras restaurar un snapshot,
        que ya sustituye toda la malla y deja obsoletas las marcas)."""
        self._parches_atmosfera.clear()
