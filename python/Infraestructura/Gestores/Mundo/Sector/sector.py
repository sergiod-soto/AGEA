# Infraestructura/Gestores/Mundo/Sector/sector.py

"""
Lógica principal de un sector del mundo.

Responsabilidades:
  - Mantener el estado de las celdas de su región en memoria (objetos deserializados)
  - Mantener el estado de las celdas de atmósfera de su región y
    avanzar su tick (ver _avanzar_atmosfera)
  - Ejecutar el tick de computación (solo si ACTIVO)
  - Gestionar ghost zones recibidas del Gestor_Mundo (terreno y atmósfera)
  - Procesar sonidos cross-border
  - Detectar y reportar migraciones de bots
  - Persistir su estado en S3 cuando recibe SaveSnapshot

La serialización/deserialización de elementos está desacoplada en
CeldaSectorStore (terreno) y CeldaAtmosferaStore (atmósfera).
Para cambiar la estrategia de almacenamiento, reimplementar esos
stores sin tocar este fichero.

Carpeta: Gestores/Mundo/Sector/

Configuración (Config.settings):
  SECTOR_COL, SECTOR_ROW
  SECTOR_SIZE
  ATMOSFERA_ESCALA
  S3_BUCKET, S3_PREFIX          (para snapshots)
"""

import json
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Optional

from vectors import Vector2

from Config.settings import (
    ATMOSFERA_ESCALA,
    S3_BUCKET,
    S3_PREFIX,
    SECTOR_COL,
    SECTOR_ROW,
    SECTOR_SIZE,
)
from Core.Entities.Elementos.elemento import Elemento
from Core.Entities.Elementos.registry import reconstruir_elemento

from Core.Entities.Mundo.Atmosfera import sistema_atmosferico
from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera
from Infraestructura.Gestores.Mundo.Sector.escala_atmosfera import (
    pos_terreno_a_atmosfera,
)
from Infraestructura.Gestores.Mundo.Sector.mutaciones import (
    CrearElemento,
    EliminarElemento,
    MoverElemento,
    Mutacion,
)
from Infraestructura.Gestores.Mundo.Sector.sector_mode import SectorMode
from Infraestructura.Gestores.Mundo.Sector.tick_context import TickContext

from Infraestructura.Gestores.Transporte.Proto_Generated import (
    common_pb2 as common_pb,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Modo de sector
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
#  CeldaSectorStore (terreno)
# ─────────────────────────────────────────────


@dataclass
class CeldaSector:
    """Igual que Celda en logica_mundo, pero con objetos Elemento reales
    en vez de ids — es la copia de trabajo que usa el Sector durante el
    tick, no el estado gold (ese vive solo en Logica_Mundo)."""

    suelo: Optional[Any] = None
    bot: Optional[Any] = None
    resto: list = field(default_factory=list)


class CeldaSectorStore:
    """Almacén de celdas deserializadas del sector, reconstruido en cada
    LoadState a partir del delta de entrada — sin persistencia propia."""

    def __init__(self):
        self._celdas: dict[tuple[int, int], CeldaSector] = {}

    def __contains__(self, pos: tuple[int, int]) -> bool:
        return pos in self._celdas

    def __len__(self) -> int:
        return len(self._celdas)

    def get(self, x: int, y: int) -> Optional[CeldaSector]:
        return self._celdas.get((x, y))

    def get_or_create(self, x: int, y: int) -> "CeldaSector":
        """Como get(), pero crea una CeldaSector vacía si no existía —
        necesario para CrearElemento/MoverElemento cuando el destino cae
        en una posición sin celda registrada todavía."""
        pos = (x, y)
        if pos not in self._celdas:
            self._celdas[pos] = CeldaSector()
        return self._celdas[pos]

    def serializar_celda(self, x: int, y: int) -> "common_pb.Cell":
        """Serializa la celda en (x, y) tal como está AHORA en el store
        (tras resolver mutaciones), para construir cada Cell de
        changed_cells. Si no hay celda registrada, se trata como vacía —
        es una respuesta válida (p. ej. si el único elemento que había se
        acaba de eliminar y no queda nada más ahí)."""
        celda = self._celdas.get((x, y), CeldaSector())
        return common_pb.Cell(
            pos=common_pb.Position(x=x, y=y),
            suelo=self._serializar_slot(celda.suelo),
            bot=self._serializar_slot(celda.bot),
            resto=[self._serializar_slot(e) for e in celda.resto],
        )

    def items(self):
        return self._celdas.items()

    def from_proto_cell(self, cell) -> None:
        """Deserializa un Cell proto (suelo/bot/resto en bytes) a una
        CeldaSector con objetos Elemento reales, y la indexa por posición.
        Los elementos ya existentes llegan con su id real de siempre —
        reconstruir_elemento no necesita asignar nada aquí."""
        pos = (cell.pos.x, cell.pos.y)
        self._celdas[pos] = CeldaSector(
            suelo=self._deserializar_slot(cell.suelo),
            bot=self._deserializar_slot(cell.bot),
            resto=[
                e
                for e in (self._deserializar_slot(b) for b in cell.resto)
                if e is not None
            ],
        )

    def to_proto_cells(self) -> list:
        """Reserializa las celdas (con objetos Elemento reales) de vuelta a
        Cell proto. Usado por GetState (y por tanto por el healthcheck)."""
        result = []
        for (x, y), celda in self._celdas.items():
            result.append(
                common_pb.Cell(
                    pos=common_pb.Position(x=x, y=y),
                    suelo=self._serializar_slot(celda.suelo),
                    bot=self._serializar_slot(celda.bot),
                    resto=[self._serializar_slot(e) for e in celda.resto],
                )
            )
        return result

    @staticmethod
    def _serializar_slot(elemento) -> bytes:
        if elemento is None:
            return b""
        return json.dumps(elemento.serializar()).encode()

    @staticmethod
    def _deserializar_slot(blob: bytes):
        if not blob:
            return None
        return reconstruir_elemento(json.loads(blob.decode()))


# ─────────────────────────────────────────────
#  CeldaAtmosferaStore (atmósfera)
# ─────────────────────────────────────────────


class CeldaAtmosferaStore:
    """
    Análogo de CeldaSectorStore pero para celdas de atmósfera. A
    diferencia de CeldaSectorStore, aquí no hay slots (suelo/bot/resto):
    una celda de atmósfera no es un contenedor de elementos, es un único
    objeto con su propio estado (temperatura, presion, viento...). Cada
    posición -- en espacio de atmósfera, no de terreno; ver
    Mundo.pos_suelo_a_atmosfera -- mapea a UNA Celda_Atmosfera.

    Reconstruido en cada LoadState a partir de lo que envíe Gestor_Mundo,
    igual que CeldaSectorStore -- sin persistencia propia.
    """

    def __init__(self):
        self._celdas: dict[tuple[int, int], Celda_Atmosfera] = {}

    def __contains__(self, pos: tuple[int, int]) -> bool:
        return pos in self._celdas

    def __len__(self) -> int:
        return len(self._celdas)

    def get(self, x: int, y: int) -> Optional[Celda_Atmosfera]:
        return self._celdas.get((x, y))

    def set(self, x: int, y: int, celda: Celda_Atmosfera) -> None:
        """No hay equivalente a get_or_create(): a diferencia de una
        CeldaSector (que puede empezar vacía y rellenarse), una
        Celda_Atmosfera siempre llega completa desde quien la construya --
        no tiene sentido inventar una "a medias"."""
        self._celdas[(x, y)] = celda

    def items(self):
        return self._celdas.items()

    def from_proto_cell(self, cell) -> None:
        """
        Reconstruye una Celda_Atmosfera a partir de un AtmosphereCell
        proto, y la indexa por posición.

        Se reconstruye "a mano": Celda_Atmosfera.__init__ crea sus
        Sistema_Atmosferico con los valores iniciales por defecto de cada
        clase (K, Pa...) -- después de construirla hay que sobreescribir
        cada .valor con lo que realmente venía en el proto, o se perdería
        el estado real de la celda en cada LoadState.

        Las cachés (tasa/inercia de Suelo, resistencia y bloqueo de
        viento) NO se restauran del proto: se reconstruyen desde el
        terreno en Sector._sincronizar_atmosfera_desde_terreno.
        """
        pos = (cell.pos.x, cell.pos.y)

        celda = Celda_Atmosfera(
            posicion=pos,
            direccion_preferente_viento=Vector2(
                cell.direccion_preferente_viento.x,
                cell.direccion_preferente_viento.y,
            ),
            fuerza_viento=Vector2(cell.fuerza_viento.x, cell.fuerza_viento.y),
        )

        celda.radiacion = cell.radiacion
        celda.temperatura.valor = cell.temperatura  # K
        celda.presion.valor = cell.presion  # Pa
        celda.viento.intensidad = cell.viento_intensidad
        celda.viento.direccion = Vector2(
            cell.viento_direccion.x, cell.viento_direccion.y
        )
        celda.humedad_absoluta.valor = cell.humedad_absoluta
        celda.humedad_relativa.valor = cell.humedad_relativa

        self._celdas[pos] = celda

    def to_proto_cells(self) -> list:
        """Serializa todas las celdas propias a AtmosphereCell proto,
        volcando terreno y estado simulado actual (SI: K, Pa, m/s...)."""
        result = []
        for (x, y), celda in self._celdas.items():
            result.append(
                common_pb.AtmosphereCell(
                    pos=common_pb.Position(x=x, y=y),
                    resistencia_viento=celda.resistencia_viento,
                    bloqueo_total_viento=celda.bloqueo_total_viento,
                    direccion_preferente_viento=common_pb.Vector2(
                        x=celda.direccion_preferente_viento.x,
                        y=celda.direccion_preferente_viento.y,
                    ),
                    fuerza_viento=common_pb.Vector2(
                        x=celda.fuerza_viento.x, y=celda.fuerza_viento.y
                    ),
                    radiacion=celda.radiacion,
                    temperatura=celda.temperatura.valor,
                    presion=celda.presion.valor,
                    viento_intensidad=celda.viento.intensidad,
                    viento_direccion=common_pb.Vector2(
                        x=celda.viento.direccion.x, y=celda.viento.direccion.y
                    ),
                    humedad_absoluta=celda.humedad_absoluta.valor,
                    humedad_relativa=celda.humedad_relativa.valor,
                )
            )
        return result


# ─────────────────────────────────────────────
#  Delta de tick
# ─────────────────────────────────────────────


@dataclass
class TickDelta:
    """Resultado de la computación de un tick en un Sector."""

    tick_id: int

    # Registro interno/depuración de lo que pidieron los elementos.
    # YA NO viaja tal cual a Logica_Mundo (el Sector las resuelve él
    # mismo — ver Sector._resolver_mutaciones — para poder paralelizar
    # el tick del mundo sector-por-sector).
    mutaciones: list[Mutacion] = field(default_factory=list)

    # Celdas ya resueltas — esto es lo que de verdad viaja a
    # Logica_Mundo en GetDeltaResponse.changed_cells.
    changed_cells: list = field(default_factory=list)

    # bot_id (int, id del SCRIPT — no del avatar) de los bots cuyo
    # avatar ha sido eliminado este tick. Quien reciba el GetDelta debe
    # usarlo para ordenar la terminación del script correspondiente
    # (ver Logica_Mundo.matar_bot).
    dead_bot_ids: list[int] = field(default_factory=list)
    emitted_sounds: list = field(default_factory=list)

    # Celdas de atmósfera propias, YA avanzadas este tick -- se manda
    # el estado completo de todas las propias en vez de intentar
    # detectar "cuáles cambiaron" (con este modelo físico, virtualmente
    # todas cambian algo cada tick, así que filtrar no ahorraría nada
    # y sí añadiría código).
    changed_atmosphere_cells: list = field(default_factory=list)

    movimientos_salientes: list = field(default_factory=list)
    eventos: list = field(default_factory=list)


# ─────────────────────────────────────────────
#  Sector
# ─────────────────────────────────────────────


class Sector:

    def __init__(self):
        # La región del sector sale de Config.settings (valores fijados al
        # importar el módulo, no del entorno "vivo"). Para tests, parchear
        # Config.settings antes de importar este módulo.
        self._col = SECTOR_COL
        self._row = SECTOR_ROW
        self._size = SECTOR_SIZE

        self._validar_escala_atmosfera()

        self._mode = SectorMode.INACTIVO

        # Celdas propias del sector (terreno)
        self._celdas = CeldaSectorStore()

        # Celdas de atmósfera propias del sector -- qué posiciones
        # "pertenecen" a este Sector se calcula en
        # _posiciones_atmosfera_propias(), no aquí; esto solo
        # inicializa el almacén vacío.
        self._atmosfera = CeldaAtmosferaStore()

        # Ghost zone de terreno: celdas de sectores vecinos dentro de
        # MAX_VISION_DISTANCE. OJO: son Cell proto (con bytes), no
        # CeldaSector -- ver nota en TickContext.get_celda.
        self._ghost: dict[tuple[int, int], Any] = {}

        # Ghost zone de ATMÓSFERA: celdas de atmósfera de sectores
        # vecinos (adyacencia-8), de solo lectura, del tick anterior.
        # Separada de self._ghost -- ver set_ghost_zone_atmosfera.
        self._ghost_atmosfera: dict[tuple[int, int], Any] = {}

        # Sonidos cross-border recibidos para el tick actual
        self._sounds_pendientes: list = []

        # Progreso de los ciclos globales (solar, lunar, anual) para el
        # tick actual. Son los MISMOS para todos los Sectores -- se
        # guardan como float plano (no como instancias de
        # Ciclo_Solar/Ciclo_Lunar/Estacion, que dependen de Mundo/Reloj
        # y no existen en este proceso).
        self._progreso_solar: float = 0.0
        self._progreso_lunar: float = 0.0
        self._progreso_anual: float = 0.0

        # Delta del último tick completado — listo para GetDelta
        self._last_delta: Optional[TickDelta] = None

        # tick_id del último tick recibido
        self._current_tick_id: int = -1

        # Bots presentes en este sector: bot_id → BotSnapshot proto
        self._bots: dict[int, Any] = {}

        # Índice inverso: id_elemento (el avatar en el mundo) → bot_id (el
        # script). Son ids independientes — este índice es la única forma de
        # ir de uno a otro sin adivinar por posición. Se mantiene en
        # load_state / add_migrating_bot / _detectar_migraciones /
        # _resolver_mutaciones.
        self._elemento_a_bot: dict[int, int] = {}

    # ─────────────────────────────────────────
    #  Propiedades de región
    #  Derivadas de _col, _row, _size.
    # ─────────────────────────────────────────

    @property
    def _x0(self) -> int:
        return self._col * self._size

    @property
    def _y0(self) -> int:
        return self._row * self._size

    @property
    def _x1(self) -> int:
        return self._x0 + self._size

    @property
    def _y1(self) -> int:
        return self._y0 + self._size

    # ---- Región en espacio de atmósfera (bloques de ATMOSFERA_ESCALA
    # celdas de terreno) -- análogas a las de arriba, en unidades
    # distintas. Solo son exactas (ningún bloque a caballo entre
    # sectores) gracias a _validar_escala_atmosfera. ----

    @property
    def _atmosfera_x0(self) -> int:
        return self._x0 // ATMOSFERA_ESCALA

    @property
    def _atmosfera_y0(self) -> int:
        return self._y0 // ATMOSFERA_ESCALA

    @property
    def _atmosfera_x1(self) -> int:
        return self._x1 // ATMOSFERA_ESCALA

    @property
    def _atmosfera_y1(self) -> int:
        return self._y1 // ATMOSFERA_ESCALA

    def _posiciones_atmosfera_propias(self) -> list[tuple[int, int]]:
        """
        Posiciones (en espacio de atmósfera, no de terreno) que
        pertenecen a este Sector. Es un rectángulo exacto -- ninguna
        celda de atmósfera queda a caballo entre sectores -- porque
        _validar_escala_atmosfera ya impide que ATMOSFERA_ESCALA no
        divida SECTOR_SIZE. Si esa comprobación se quitara alguna vez,
        este método dejaría de ser correcto en los bordes.
        """
        return [
            (x, y)
            for x in range(self._atmosfera_x0, self._atmosfera_x1)
            for y in range(self._atmosfera_y0, self._atmosfera_y1)
        ]

    def _validar_escala_atmosfera(self) -> None:
        """
        Comprueba que ATMOSFERA_ESCALA divide exactamente a SECTOR_SIZE.

        Por qué es obligatorio y no solo deseable: Sectores y celdas de
        atmósfera parten el MISMO grid, ambos con origen en (0,0). Si
        ATMOSFERA_ESCALA no divide SECTOR_SIZE, habría celdas de
        atmósfera cuyo bloque de terreno cae parte en este Sector y
        parte en el Sector vecino -- ¿cuál de los dos la calcula? Con
        el reparto actual (cada Sector calcula sobre su propia región +
        ghost zone de solo lectura) eso no tiene respuesta correcta.

        Se falla rápido y explícito al arrancar el Sector, en vez de
        dejar que el problema aparezca más tarde como una celda de
        atmósfera duplicada o inconsistente en mitad de una partida.
        """
        if self._size % ATMOSFERA_ESCALA != 0:
            raise ValueError(
                f"ATMOSFERA_ESCALA ({ATMOSFERA_ESCALA}) debe ser divisor de "
                f"SECTOR_SIZE ({self._size}) -- si no, hay celdas de "
                "atmósfera repartidas entre dos Sectores sin ninguna regla "
                "de quién las calcula. Ajusta Config.settings."
            )

    def _en_region_propia(self, pos: tuple[int, int]) -> bool:
        """True si pos (espacio de terreno) cae dentro de la región de este
        Sector. Un Sector solo puede escribir celdas de su región."""
        x, y = pos
        return self._x0 <= x < self._x1 and self._y0 <= y < self._y1

    @staticmethod
    def _asignar_slot(celda: CeldaSector, slot: str, elemento: Any) -> bool:
        """Coloca 'elemento' en el slot de 'celda'. False, sin cambiar nada,
        si el slot es de ocupación única (suelo/bot) y ya está ocupado: así
        no se sobrescribe en silencio al ocupante anterior."""
        if slot == "suelo":
            if celda.suelo is not None:
                return False
            celda.suelo = elemento
        elif slot == "bot":
            if celda.bot is not None:
                return False
            celda.bot = elemento
        else:
            celda.resto.append(elemento)
        return True

    @staticmethod
    def _fijar_casilla(elemento, pos: tuple[int, int]) -> None:
        """El Sector es el ÚNICO que escribe `casilla`: solo él sabe si un
        movimiento se produjo, se rechazó (vuelve al origen) o aterrizó en
        otro sector. Los elementos no deben tocarla en su tick()."""
        if hasattr(elemento, "casilla"):
            elemento.casilla = pos

    def _registrar_movimiento_saliente(self, delta, mutacion, elemento, slot) -> None:
        """Declara un movimiento a una celda de otro Sector. Se serializa el
        elemento aquí (su estado pudo cambiar este tick). No se toca la celda
        de origen ni la posición del bot: eso solo ocurre en confirmar_salida."""
        ox, oy = mutacion.pos_origen
        dx, dy = mutacion.pos_destino
        mov = common_pb.MovimientoSaliente(
            id_elemento=mutacion.id_elemento,
            tipo_slot=slot,
            pos_origen=common_pb.Position(x=ox, y=oy),
            pos_destino=common_pb.Position(x=dx, y=dy),
            elemento=CeldaSectorStore._serializar_slot(elemento),
        )
        if slot == "bot":
            bot = self._bots.get(self._elemento_a_bot.get(mutacion.id_elemento))
            if bot is not None:
                mov.bot.CopyFrom(bot)
        delta.movimientos_salientes.append(mov)

    def recibir_elemento(self, mov) -> tuple[bool, str, Optional[Any]]:
        """
        Destino de un movimiento entre sectores: aloja el elemento si cabe.
        Devuelve (aceptado, motivo, celda_resultante). Todo o nada: se valida
        antes de tocar nada y el slot es el último paso que puede rechazar.
        """
        pos = (mov.pos_destino.x, mov.pos_destino.y)
        if not self._en_region_propia(pos):
            return False, f"{pos} cae fuera de la región de este sector", None
        elemento = CeldaSectorStore._deserializar_slot(mov.elemento)
        if elemento is None:
            raise ValueError("MovimientoSaliente sin elemento serializado.")

        celda = self._celdas.get_or_create(*pos)
        if not self._asignar_slot(celda, mov.tipo_slot, elemento):
            return False, f"slot '{mov.tipo_slot}' de {pos} ocupado", None

        self._fijar_casilla(elemento, pos)
        if elemento.tiene_flag(Elemento.Flags.RESISTENCIA_VIENTO_CACHEABLE):
            self._registrar_resistencia_viento(pos, elemento)
        if mov.HasField("bot"):
            bot = common_pb.BotSnapshot()
            bot.CopyFrom(mov.bot)
            bot.pos.x, bot.pos.y = pos
            self._bots[bot.bot_id] = bot
            self._elemento_a_bot[bot.id_elemento] = bot.bot_id
        return True, "", self._celdas.serializar_celda(*pos)

    def confirmar_salida(self, id_elemento: int, pos_origen: tuple[int, int]):
        """Origen de un movimiento ya aceptado: elimina el elemento de su celda
        y devuelve la celda resultante. ValueError si no está (divergencia)."""
        elemento, slot = self._quitar_de_celda(pos_origen, id_elemento)
        if elemento is None:
            raise ValueError(
                f"confirmar_salida: elemento {id_elemento} no está en {pos_origen}."
            )
        if elemento.tiene_flag(Elemento.Flags.RESISTENCIA_VIENTO_CACHEABLE):
            self._eliminar_resistencia_viento(pos_origen, id_elemento)
        if slot == "bot":
            bot_id = self._elemento_a_bot.pop(id_elemento, None)
            if bot_id is not None:
                self._bots.pop(bot_id, None)
        return self._celdas.serializar_celda(*pos_origen)

    def _localizar_en_celda(self, pos, id_elemento):
        """Como _quitar_de_celda, pero sin quitar: (elemento, slot) o (None, None)."""
        celda = self._celdas.get(*pos)
        if celda is None:
            return None, None
        if celda.suelo is not None and celda.suelo.id_elemento == id_elemento:
            return celda.suelo, "suelo"
        if celda.bot is not None and celda.bot.id_elemento == id_elemento:
            return celda.bot, "bot"
        for e in celda.resto:
            if e.id_elemento == id_elemento:
                return e, "resto"
        return None, None

    # ─────────────────────────────────────────
    #  Ciclo de vida
    # ─────────────────────────────────────────

    def set_mode(self, mode: SectorMode) -> None:
        if self._mode == mode:
            return
        logger.info(
            "Sector (%d,%d): %s → %s", self._col, self._row, self._mode.name, mode.name
        )
        self._mode = mode

    def load_state(self, cells: list, celdas_atmosfera: list, bots: list) -> None:
        """
        Carga el estado gold enviado por Gestor_Mundo: terreno,
        atmósfera y bots. Usado en arranque o tras recuperación de spot
        caído.

        AVISO DE RUPTURA: esta firma cambió respecto a la versión
        anterior (cells, bots) -- quien llame a esto (el servicer gRPC
        de LoadState) debe construir/pasar también celdas_atmosfera
        (request.atmosphere_cells).
        """
        self._celdas = CeldaSectorStore()
        for cell in cells:
            self._celdas.from_proto_cell(cell)

        self._atmosfera = CeldaAtmosferaStore()
        for cell_atm in celdas_atmosfera:
            self._atmosfera.from_proto_cell(cell_atm)

        # Las celdas de atmósfera recién deserializadas no traen cachés:
        # se reconstruyen desde el terreno.
        self._sincronizar_atmosfera_desde_terreno()

        self._bots = {bot.bot_id: bot for bot in bots}
        self._elemento_a_bot = {bot.id_elemento: bot.bot_id for bot in bots}
        logger.info(
            "Sector (%d,%d): estado cargado — %d celdas, %d celdas de "
            "atmósfera, %d bots",
            self._col,
            self._row,
            len(self._celdas),
            len(self._atmosfera),
            len(self._bots),
        )

    def _sincronizar_atmosfera_desde_terreno(self) -> None:
        """
        Recorre self._celdas (terreno propio, ya cargado) y registra en
        cada Celda_Atmosfera propia la tasa/inercia de su Suelo y la
        resistencia_viento de sus elementos estáticos. Necesario tras
        cada load_state, porque las Celda_Atmosfera recién deserializadas
        del proto no traen estas cachés (ver docstring de load_state).

        Solo cubre la región propia del sector -- no toca ghost zones
        (self._ghost/self._ghost_atmosfera son de solo lectura y no
        deben tener cachés propias).
        """
        for (x, y), celda in self._celdas.items():
            pos = (x, y)
            # pos_terreno_a_atmosfera devuelve una POSICIÓN (tupla), no la
            # celda: hay que buscarla en el store. (Antes se usaba la tupla
            # como si fuera la celda y reventaba con AttributeError.)
            celda_atmosfera = self._atmosfera.get(
                *pos_terreno_a_atmosfera(x, y, ATMOSFERA_ESCALA)
            )
            if celda_atmosfera is None:
                continue

            if celda.suelo is not None:
                celda_atmosfera.registrar_suelo(
                    pos,
                    celda.suelo.tasa_conversion_radiacion_calor,
                    celda.suelo.inercia_termica,
                )

            for elemento in celda.resto:
                if elemento.tiene_flag(Elemento.Flags.RESISTENCIA_VIENTO_CACHEABLE):
                    celda_atmosfera.registrar_resistencia_elemento(
                        elemento.id_elemento, elemento.resistencia_viento
                    )

    def get_state(self):
        """
        Devuelve el estado completo del sector (para GetState del
        servicer): terreno, atmósfera y bots.

        AVISO DE RUPTURA: mismo cambio de firma que load_state -- ahora
        devuelve una tupla de 3 elementos en vez de 2.
        """
        cells = self._celdas.to_proto_cells()
        celdas_atmosfera = self._atmosfera.to_proto_cells()
        bots = list(self._bots.values())
        return cells, celdas_atmosfera, bots

    # ─────────────────────────────────────────
    #  Cachés de atmósfera (sin ctx: no dependen del contexto del tick)
    # ─────────────────────────────────────────

    def _celda_atmosfera_de(self, pos: tuple[int, int]) -> Optional[Celda_Atmosfera]:
        """Celda_Atmosfera propia que cubre la posición de TERRENO 'pos'."""
        return self._atmosfera.get(
            *pos_terreno_a_atmosfera(pos[0], pos[1], ATMOSFERA_ESCALA)
        )

    def _sincronizar_atmosfera_de_suelo(self, pos, suelo) -> None:
        """Un Suelo solo se sustituye: se actualiza y, si no estaba (KeyError), se da de alta."""
        celda_atm = self._celda_atmosfera_de(pos)
        if celda_atm is None:
            logger.warning(
                "Sector (%d,%d): Suelo en %s sin Celda_Atmosfera.",
                self._col,
                self._row,
                pos,
            )
            return
        try:
            celda_atm.actualizar_suelo(
                pos, suelo.tasa_conversion_radiacion_calor, suelo.inercia_termica
            )
        except KeyError:
            celda_atm.registrar_suelo(
                pos, suelo.tasa_conversion_radiacion_calor, suelo.inercia_termica
            )

    def _registrar_resistencia_viento(self, pos, elemento) -> None:
        celda_atm = self._celda_atmosfera_de(pos)
        if celda_atm is None:
            logger.warning(
                "Sector (%d,%d): %s en %s sin Celda_Atmosfera.",
                self._col,
                self._row,
                elemento.id_elemento,
                pos,
            )
            return
        celda_atm.registrar_resistencia_elemento(
            elemento.id_elemento, elemento.resistencia_viento
        )

    def _eliminar_resistencia_viento(self, pos, id_elemento) -> None:
        celda_atm = self._celda_atmosfera_de(pos)
        if celda_atm is None:
            logger.warning(
                "Sector (%d,%d): baja de %s en %s sin Celda_Atmosfera.",
                self._col,
                self._row,
                id_elemento,
                pos,
            )
            return
        celda_atm.eliminar_resistencia_elemento(id_elemento)

    def _resolver_mutaciones(
        self, mutaciones: list[Mutacion], delta: TickDelta
    ) -> None:
        posiciones_cambiadas: set[tuple[int, int]] = set()

        for mutacion in mutaciones:
            if isinstance(mutacion, CrearElemento):
                # PENDIENTE (ids de elementos nacidos en tick(), aplazado): sin
                # id real, Logica rechazaría la celda y sería fatal.
                if not mutacion.elemento.id_elemento:
                    logger.error(
                        "Sector (%d,%d): creación en %s descartada, el elemento (%s) no tiene id.",
                        self._col,
                        self._row,
                        mutacion.pos,
                        type(mutacion.elemento).__name__,
                    )
                    continue
                celda = self._celdas.get_or_create(*mutacion.pos)
                if not self._asignar_slot(celda, mutacion.tipo_slot, mutacion.elemento):
                    logger.warning(
                        "Sector (%d,%d): creación descartada en %s, slot '%s' ocupado.",
                        self._col,
                        self._row,
                        mutacion.pos,
                        mutacion.tipo_slot,
                    )
                    continue
                posiciones_cambiadas.add(mutacion.pos)
                self._fijar_casilla(mutacion.elemento, mutacion.pos)
                if mutacion.tipo_slot == "suelo":
                    self._sincronizar_atmosfera_de_suelo(
                        mutacion.pos, mutacion.elemento
                    )
                if mutacion.elemento.tiene_flag(
                    Elemento.Flags.RESISTENCIA_VIENTO_CACHEABLE
                ):
                    self._registrar_resistencia_viento(mutacion.pos, mutacion.elemento)

            elif isinstance(mutacion, EliminarElemento):
                elemento, slot = self._quitar_de_celda(
                    mutacion.pos, mutacion.id_elemento
                )
                posiciones_cambiadas.add(mutacion.pos)
                # El Suelo no se da de baja de la caché: nunca se elimina, solo
                # se sustituye (lo cubre el CrearElemento que le sigue).
                if elemento is not None and elemento.tiene_flag(
                    Elemento.Flags.RESISTENCIA_VIENTO_CACHEABLE
                ):
                    self._eliminar_resistencia_viento(
                        mutacion.pos, mutacion.id_elemento
                    )
                # Un avatar eliminado consta como bot muerto: el Gestor ordena
                # terminar su script.
                if slot == "bot" and elemento is not None:
                    bot_id = self._elemento_a_bot.pop(mutacion.id_elemento, None)
                    if bot_id is not None:
                        self._bots.pop(bot_id, None)
                        delta.dead_bot_ids.append(bot_id)

            elif isinstance(mutacion, MoverElemento):
                if not self._en_region_propia(mutacion.pos_destino):
                    # Cruza a otro Sector: NO se toca el elemento aquí. Se
                    # declara y el Gestor resuelve (RecibirElemento/ConfirmarSalida).
                    elemento, slot = self._localizar_en_celda(
                        mutacion.pos_origen, mutacion.id_elemento
                    )
                    if elemento is not None:
                        self._registrar_movimiento_saliente(
                            delta, mutacion, elemento, slot
                        )
                    continue

                # Movimiento dentro de la región propia.
                elemento, slot = self._quitar_de_celda(
                    mutacion.pos_origen, mutacion.id_elemento
                )
                posiciones_cambiadas.add(mutacion.pos_origen)
                if elemento is None:
                    continue
                cacheable = elemento.tiene_flag(
                    Elemento.Flags.RESISTENCIA_VIENTO_CACHEABLE
                )
                if cacheable:
                    self._eliminar_resistencia_viento(
                        mutacion.pos_origen, mutacion.id_elemento
                    )

                celda_destino = self._celdas.get_or_create(*mutacion.pos_destino)
                if self._asignar_slot(celda_destino, slot, elemento):
                    posiciones_cambiadas.add(mutacion.pos_destino)
                    posicion_final = mutacion.pos_destino
                else:
                    logger.warning(
                        "Sector (%d,%d): movimiento de %s rechazado, slot '%s' de %s ocupado; vuelve a %s.",
                        self._col,
                        self._row,
                        mutacion.id_elemento,
                        slot,
                        mutacion.pos_destino,
                        mutacion.pos_origen,
                    )
                    self._asignar_slot(
                        self._celdas.get_or_create(*mutacion.pos_origen), slot, elemento
                    )
                    posicion_final = mutacion.pos_origen

                self._fijar_casilla(elemento, posicion_final)

                if cacheable:
                    self._registrar_resistencia_viento(posicion_final, elemento)
                # La posición del BotSnapshot sigue al avatar.
                if slot == "bot":
                    bot = self._bots.get(self._elemento_a_bot.get(mutacion.id_elemento))
                    if bot is not None:
                        bot.pos.x, bot.pos.y = posicion_final

        delta.changed_cells = [
            self._celdas.serializar_celda(x, y) for (x, y) in posiciones_cambiadas
        ]

    # ─────────────────────────────────────────
    #  FASE 0 — Preparación del tick
    # ─────────────────────────────────────────

    def set_ghost_zone(self, tick_id: int, ghost_cells: list) -> None:
        """Recibe y almacena la ghost zone de TERRENO para este tick."""
        self._ghost = {}
        for cell in ghost_cells:
            key = (cell.pos.x, cell.pos.y)
            self._ghost[key] = cell
        logger.debug(
            "Sector (%d,%d): ghost zone cargada — %d celdas (tick %d)",
            self._col,
            self._row,
            len(self._ghost),
            tick_id,
        )

    def set_ghost_zone_atmosfera(self, tick_id: int, ghost_cells: list) -> None:
        """Recibe y almacena la ghost zone de ATMÓSFERA (adyacencia-8,
        celdas de solo lectura del tick anterior) para este tick.
        Separada de self._ghost (terreno): son conceptos distintos que
        solo comparten el nombre por analogía -- ver sector_service.proto,
        SetAtmosphereGhostZone."""
        self._ghost_atmosfera = {}
        for cell in ghost_cells:
            key = (cell.pos.x, cell.pos.y)
            self._ghost_atmosfera[key] = cell
        logger.debug(
            "Sector (%d,%d): ghost zone de atmósfera cargada — %d celdas (tick %d)",
            self._col,
            self._row,
            len(self._ghost_atmosfera),
            tick_id,
        )

    def set_sounds(self, tick_id: int, sounds: list) -> None:
        """Recibe los sonidos cross-border para este tick."""
        self._sounds_pendientes = sounds
        logger.debug(
            "Sector (%d,%d): %d sonidos recibidos (tick %d)",
            self._col,
            self._row,
            len(sounds),
            tick_id,
        )

    def set_ciclos_globales(
        self,
        tick_id: int,
        progreso_solar: float,
        progreso_lunar: float,
        progreso_anual: float,
    ) -> None:
        """
        Recibe el progreso (0.0-1.0) de los ciclos solar/lunar/anual
        para este tick, ya calculado por quien tiene el Ciclo real
        (Reloj.Ciclo.tick_actual / duración -- en Logica_Mundo/Mundo,
        vía Gestor_Mundo). Sector no conoce ni necesita conocer cuántos
        ticks dura un día o un año, solo el ratio.

        progreso_lunar se guarda para cuando exista algún sistema que
        lo necesite -- hoy ningún Sistema_Atmosferico lo usa todavía.
        """
        self._progreso_solar = progreso_solar
        self._progreso_lunar = progreso_lunar
        self._progreso_anual = progreso_anual
        logger.debug(
            "Sector (%d,%d): ciclos globales actualizados -- solar=%.3f, "
            "lunar=%.3f, anual=%.3f (tick %d)",
            self._col,
            self._row,
            progreso_solar,
            progreso_lunar,
            progreso_anual,
            tick_id,
        )

    def add_migrating_bot(self, tick_id: int, bot, elemento: bytes = b"") -> None:
        """Registra un bot que llega a este sector y coloca su avatar en el
        store. Sin lo segundo el avatar no ejecutaría tick() aquí, y la
        próxima celda que este sector reporte en esa posición lo borraría de
        Mundo (actualizar_celda sustituye la celda entera).

        `elemento` es el avatar serializado (mismo formato que un slot de
        Cell). Por defecto vacío para no romper a los llamadores actuales:
        en ese caso solo se registra el bot, como antes."""
        self._bots[bot.bot_id] = bot
        self._elemento_a_bot[bot.id_elemento] = bot.bot_id

        if elemento:
            pos = (bot.pos.x, bot.pos.y)
            if not self._en_region_propia(pos):
                logger.warning(
                    "Sector (%d,%d): avatar %s llega a %s, fuera de su región.",
                    self._col,
                    self._row,
                    bot.id_elemento,
                    pos,
                )
            else:
                celda = self._celdas.get_or_create(*pos)
                if celda.bot is not None and celda.bot.id_elemento == bot.id_elemento:
                    # Ya cargado por un LoadState reciente (p. ej. la
                    # activación de un sector INACTIVO, que carga antes de
                    # recibir al bot): la operación es idempotente.
                    pass
                elif not self._asignar_slot(
                    celda, "bot", CeldaSectorStore._deserializar_slot(elemento)
                ):
                    logger.error(
                        "Sector (%d,%d): slot bot de %s ocupado al recibir %s.",
                        self._col,
                        self._row,
                        pos,
                        bot.id_elemento,
                    )

        logger.debug(
            "Sector (%d,%d): bot %s migrado (tick %d)",
            self._col,
            self._row,
            bot.bot_id,
            tick_id,
        )

    # ─────────────────────────────────────────
    #  FASE 1 — Computación del tick
    # ─────────────────────────────────────────

    def compute_tick(self, tick_id: int) -> TickDelta:
        """
        Ejecuta tick() de cada elemento propio (solo si el sector está ACTIVO),
        resuelve las mutaciones que pidieron, avanza la atmósfera propia y deja
        el TickDelta listo para GetDelta.
        """
        self._current_tick_id = tick_id
        delta = TickDelta(tick_id=tick_id)

        if self._mode != SectorMode.ACTIVO:
            self._last_delta = delta
            return delta

        ctx = TickContext(
            celdas_inicio_tick=self._celdas,
            ghost=self._ghost,
            x0=self._x0,
            y0=self._y0,
            x1=self._x1,
            y1=self._y1,
            atmosfera=self._atmosfera,
            ghost_atmosfera=self._ghost_atmosfera,
            escala_atmosfera=ATMOSFERA_ESCALA,
            tick_id=tick_id,
        )

        self._procesar_sonidos(ctx)

        # Los elementos solo ACUMULAN mutaciones en ctx (escritura diferida): el
        # resultado no depende del orden de este bucle.
        for (x, y), celda in list(self._celdas.items()):
            for elemento in (celda.suelo, celda.bot, *celda.resto):
                if elemento is None:
                    continue
                try:
                    elemento.tick(ctx)
                except Exception:
                    # Se registra QUÉ elemento falló y se relanza: el tick aborta
                    # (StartTick ok=False -> ErrorSincronizacion en el Gestor).
                    logger.exception(
                        "Sector (%d,%d) tick %d: tick() de %s (id=%s) en (%d,%d) falló.",
                        self._col,
                        self._row,
                        tick_id,
                        type(elemento).__name__,
                        elemento.id_elemento,
                        x,
                        y,
                    )
                    raise

        delta.mutaciones = ctx.obtener_mutaciones()
        delta.eventos = self._consolidar_eventos(ctx.obtener_eventos())

        # Desde aquí el Sector ya modifica su copia: si algo lanza, el delta se
        # pierde y Logica no vería esos cambios. Se registra y se relanza.
        try:
            self._resolver_mutaciones(delta.mutaciones, delta)
            delta.emitted_sounds = []  # TODO: junto con _procesar_sonidos
            self._avanzar_atmosfera(tick_id)
            delta.changed_atmosphere_cells = self._atmosfera.to_proto_cells()
        except Exception:
            logger.exception(
                "Sector (%d,%d) tick %d: excepción tras aplicar mutaciones; "
                "el delta se PIERDE (el Sector ya modificó su copia).",
                self._col,
                self._row,
                tick_id,
            )
            raise

        self._last_delta = delta
        return delta

    def _avanzar_atmosfera(self, tick_id: int) -> None:
        """Avanza un tick cada celda de atmósfera propia. Los vecinos se
        leen SIEMPRE del tick anterior (modelo acordado)."""
        posiciones_propias = self._posiciones_atmosfera_propias()

        # Se congelan ANTES de mutar nada los únicos valores que leen los
        # vecinos. Son floats (inmutables), así que la copia es real.
        # Guardar las celdas en un dict NO congelaba nada: avanzar_celda las
        # muta in-place y el dict apuntaba a los mismos objetos, con lo que
        # el resultado dependía del orden del bucle.
        estados_previos: dict[tuple[int, int], tuple[float, float, float]] = {}
        for pos in posiciones_propias:
            celda = self._atmosfera.get(*pos)
            if celda is not None:
                estados_previos[pos] = (
                    celda.temperatura.valor,
                    celda.presion.valor,
                    celda.humedad_absoluta.valor,
                )

        for pos in posiciones_propias:
            celda = self._atmosfera.get(*pos)
            if celda is None:
                continue  # bloque aún sin crear (mundo recién arrancado)
            vecinos = self._vecinos_atmosfera(pos, estados_previos)
            sistema_atmosferico.avanzar_celda(
                celda, self._progreso_solar, self._progreso_anual, vecinos
            )

    def _vecinos_atmosfera(
        self,
        pos: tuple[int, int],
        estados_previos: dict[tuple[int, int], tuple[float, float, float]],
    ) -> list[sistema_atmosferico.EstadoVecino]:
        """
        Lista de EstadoVecino (adyacencia-8) de la celda en 'pos', con los
        valores del TICK ANTERIOR: los vecinos propios salen de
        'estados_previos' (congelados) y los de otro Sector, de la ghost
        zone. Los vecinos que no existen en ninguna de las dos (borde del
        mundo) se omiten: el borde es adiabático.

        (Estaba definido DENTRO de _avanzar_atmosfera, tras el bucle, así
        que self._vecinos_atmosfera no existía.)
        """
        x, y = pos
        vecinos: list[sistema_atmosferico.EstadoVecino] = []

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                vecino_pos = (x + dx, y + dy)

                estado = estados_previos.get(vecino_pos)
                if estado is not None:
                    temperatura, presion, humedad_absoluta = estado
                    # Vecino propio: bloqueo_total_viento no lo muta
                    # avanzar_celda, así que se lee en vivo del store propio
                    # -- no hace falta congelarlo como el resto.
                    celda_vecina = self._atmosfera.get(*vecino_pos)
                    bloqueo_total_viento = (
                        celda_vecina.bloqueo_total_viento
                        if celda_vecina is not None
                        else False
                    )
                else:
                    vecino_proto = self._ghost_atmosfera.get(vecino_pos)
                    if vecino_proto is None:
                        continue
                    temperatura = vecino_proto.temperatura
                    presion = vecino_proto.presion
                    humedad_absoluta = vecino_proto.humedad_absoluta
                    # Vecino de GHOST ZONE (otro Sector): su bloqueo viaja en
                    # el proto (AtmosphereCell.bloqueo_total_viento). Ojo: lo
                    # rellena Logica_Mundo desde SU Celda_Atmosfera, cuyas
                    # cachés hoy nadie mantiene (pendiente de la fase de
                    # cachés) -- hasta entonces valdrá siempre False.
                    bloqueo_total_viento = vecino_proto.bloqueo_total_viento

                distancia = math.hypot(dx, dy)
                vecinos.append(
                    sistema_atmosferico.EstadoVecino(
                        temperatura=temperatura,
                        presion=presion,
                        humedad_absoluta=humedad_absoluta,
                        direccion=Vector2(dx / distancia, dy / distancia),
                        bloqueo_total_viento=bloqueo_total_viento,
                    )
                )
        return vecinos

    def _sincronizar_atmosfera_de_suelo(
        self, ctx: TickContext, mutacion: CrearElemento
    ) -> None:
        """
        Refleja en la Celda_Atmosfera la tasa/inercia de un Suelo recién
        creado. Un Suelo solo se sustituye (nunca se elimina), así que lo
        normal es que la posición ya esté registrada: se actualiza y, si no
        lo estaba (KeyError), se da de alta.

        PROVISIONAL: este método no existía (los hooks de CrearElemento lo
        llamaban y reventaban con AttributeError). Es el mínimo coherente
        con las decisiones cerradas; la regla definitiva de las cachés
        (dónde vive, upsert...) queda para la fase de cachés.
        """
        x, y = mutacion.pos
        celda_atmosfera = ctx.get_atmosfera(x, y)
        if celda_atmosfera is None:
            logger.warning(
                "Sector (%d,%d): Suelo en %s sin Celda_Atmosfera "
                "correspondiente -- no se registra su tasa/inercia.",
                self._col,
                self._row,
                mutacion.pos,
            )
            return
        suelo = mutacion.elemento
        try:
            celda_atmosfera.actualizar_suelo(
                mutacion.pos,
                suelo.tasa_conversion_radiacion_calor,
                suelo.inercia_termica,
            )
        except KeyError:
            celda_atmosfera.registrar_suelo(
                mutacion.pos,
                suelo.tasa_conversion_radiacion_calor,
                suelo.inercia_termica,
            )

    def _registrar_resistencia_viento(
        self, ctx: TickContext, pos: tuple[int, int], elemento: Any
    ) -> None:
        """Da de alta la contribución de 'elemento' a resistencia_viento
        en la Celda_Atmosfera que cubre 'pos'. No falla si la celda no
        existe (borde del mundo / bloque aún sin crear) -- solo avisa."""
        x, y = pos
        celda_atmosfera = ctx.get_atmosfera(x, y)
        if celda_atmosfera is None:
            logger.warning(
                "Sector (%d,%d): elemento %s (estático-viento) en %s sin "
                "Celda_Atmosfera correspondiente -- no se registra su "
                "resistencia_viento.",
                self._col,
                self._row,
                elemento.id_elemento,
                pos,
            )
            return
        celda_atmosfera.registrar_resistencia_elemento(
            elemento.id_elemento, elemento.resistencia_viento
        )

    def _eliminar_resistencia_viento(
        self, ctx: TickContext, pos: tuple[int, int], id_elemento: int
    ) -> None:
        """Da de baja la contribución de id_elemento a resistencia_viento
        en la Celda_Atmosfera que cubre 'pos'."""
        x, y = pos
        celda_atmosfera = ctx.get_atmosfera(x, y)
        if celda_atmosfera is None:
            logger.warning(
                "Sector (%d,%d): baja de resistencia_viento de %s en %s "
                "sin Celda_Atmosfera correspondiente -- ignorada.",
                self._col,
                self._row,
                id_elemento,
                pos,
            )
            return
        celda_atmosfera.eliminar_resistencia_elemento(id_elemento)

    def _quitar_de_celda(
        self, pos: tuple[int, int], id_elemento: int
    ) -> tuple[Optional[Any], Optional[str]]:
        """Busca id_elemento en la celda de pos (suelo/bot/resto) y lo
        quita de ahí. (None, None) si no se encontró."""
        celda = self._celdas.get(*pos)
        if celda is None:
            return None, None
        if celda.suelo is not None and celda.suelo.id_elemento == id_elemento:
            elemento, celda.suelo = celda.suelo, None
            return elemento, "suelo"
        if celda.bot is not None and celda.bot.id_elemento == id_elemento:
            elemento, celda.bot = celda.bot, None
            return elemento, "bot"
        for i, e in enumerate(celda.resto):
            if e.id_elemento == id_elemento:
                return celda.resto.pop(i), "resto"
        return None, None

    @staticmethod
    def _consolidar_eventos(eventos: list) -> list:
        """
        ÚNICO punto por el que pasan los eventos del tick hacia el delta.
        Hoy los envía TODOS, tal cual, en orden de emisión.

        Para agrupar en el futuro basta cambiar el cuerpo de esta función: para
        los EventoPedido con agrupable=True, quedarse solo con el último de cada
        `tipo` (conservando el orden de la última aparición) y dejar intactos los
        no agrupables. Nada más cambia: ni protos, ni Gestor, ni Logica.
        """
        return [
            common_pb.EventoMundo(tipo=e.tipo, payload=e.payload, agrupable=e.agrupable)
            for e in eventos
        ]

    def _procesar_sonidos(self, ctx: TickContext) -> None:
        """Aplica los efectos de los sonidos cross-border recibidos.
        TODO: implementar cuando la API de sonido esté definida — probablemente
        también a través de ctx, si un sonido puede disparar mutaciones."""
        for sound in self._sounds_pendientes:
            pass
        self._sounds_pendientes = []

    def _detectar_migraciones(self, delta: TickDelta) -> None:
        """
        Comprueba qué bots han salido de la región del sector
        y los añade a delta.outgoing_bots.
        """
        from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2 import (
            MigratingBot,
        )

        x0, y0, x1, y1 = self._x0, self._y0, self._x1, self._y1

        bots_fuera = []
        for bot_id, bot in self._bots.items():
            x, y = bot.pos.x, bot.pos.y
            if not (x0 <= x < x1 and y0 <= y < y1):
                delta.outgoing_bots.append(
                    MigratingBot(
                        bot=bot,
                        target_pos=common_pb.Position(x=x, y=y),
                    )
                )
                bots_fuera.append(bot_id)

        for bot_id in bots_fuera:
            self._elemento_a_bot.pop(self._bots[bot_id].id_elemento, None)
            del self._bots[bot_id]

    # ─────────────────────────────────────────
    #  FASE 2 — GetDelta
    # ─────────────────────────────────────────

    def get_delta(self, tick_id: int) -> Optional[TickDelta]:
        """
        Devuelve el delta del tick solicitado.
        Si tick_id no coincide con el último tick computado, devuelve None.
        """
        if self._last_delta is None or self._last_delta.tick_id != tick_id:
            logger.warning(
                "Sector (%d,%d): GetDelta tick_id=%d pero último tick=%s",
                self._col,
                self._row,
                tick_id,
                self._last_delta.tick_id if self._last_delta else "None",
            )
            return None
        return self._last_delta

    # ─────────────────────────────────────────
    #  Snapshot (S3)
    # ─────────────────────────────────────────

    async def save_snapshot(self, snapshot_id: str) -> None:
        """
        Persiste el estado del sector en S3 con el snapshot_id dado.
        TODO: implementar con aioboto3 cuando se decida el cliente AWS.
        """
        cells_raw = []
        for (x, y), elemento in self._celdas.items():
            cells_raw.append({"x": x, "y": y, "element": ""})

        bots_raw = []
        for bot_id, bot in self._bots.items():
            bots_raw.append({"bot_id": bot_id})

        data = {
            "snapshot_id": snapshot_id,
            "col": self._col,
            "row": self._row,
            "mode": self._mode.value,
            "tick_id": self._current_tick_id,
            "cells": cells_raw,
            "bots": bots_raw,
        }

        key = f"{S3_PREFIX}/sector_{self._col}_{self._row}/{snapshot_id}.json"

        logger.info(
            "TODO: snapshot sector (%d,%d) → s3://%s/%s (snapshot_id=%s)",
            self._col,
            self._row,
            S3_BUCKET,
            key,
            snapshot_id,
        )

    async def restore_snapshot(self, snapshot_id: str) -> None:
        """
        Restaura el estado del sector desde S3.
        TODO: implementar con aioboto3.
        """
        logger.info(
            "TODO: restore sector (%d,%d) desde s3://%s/%s/%s",
            self._col,
            self._row,
            S3_BUCKET,
            S3_PREFIX,
            snapshot_id,
        )
