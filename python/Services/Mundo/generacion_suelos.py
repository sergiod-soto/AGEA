"""
generacion_suelos.py — Generación del mapa de suelos del mundo.

Genera un mapa de suelos COHERENTE (no ruido): continentes rodeados de
océano, cordilleras, ríos que bajan al mar, desiertos cálidos y secos,
polos con banquisa y hielo SOLO donde hace frío de verdad, y barro como
transición entre tierra húmeda y agua.

Los umbrales de mar/montaña NO son valores absolutos: se calculan por
CUANTILES sobre el ruido generado, así que las proporciones de terreno
son estables para cualquier seed (~68% de agua, ~15% de montaña sobre la
tierra...). Mismo seed + mismos parámetros = mundo idéntico.

Diseñado en CAPAS de procesado independientes y ordenadas, para poder
añadir capas nuevas a futuro (vegetación, minerales, cuevas...) sin tocar
las existentes: nueva clase + @registrar_capa("nombre") + insertar el
nombre en ORDEN_CAPAS (o pasarlo en `capas=[...]`).

No importa nada del proyecto salvo (opcionalmente) Config.settings para
los valores por defecto, así que el renderizador puede usarlo standalone.

Uso:
    mapa = generar_mapa_suelos()                     # dict {(x, y): "Suelo_X"}
    mapa = generar_mapa_suelos(seed=7, num_rios=20)   # con overrides
"""

from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass, field
from typing import Optional

# Nombres de clases TAL CUAL están en Core/Entities/Elementos/registry.py
SUELO_AGUA = "Suelo_Agua"
SUELO_ARENA = "Suelo_Arena"
SUELO_BARRO = "Suelo_Barro"
SUELO_CESPED = "Suelo_Cesped"
SUELO_GRAVA = "Suelo_Grava"
SUELO_HIELO = "Suelo_Hielo"
SUELO_OCEANO = "Suelo_Oceano"
SUELO_PIEDRA = "Suelo_Piedra"
SUELO_TIERRA = "Suelo_Tierra"
SUELO_LIMITE = "Suelo_Limite"

# Hidrología (no son clases de suelo: es METADATO de generación). El mar se
# deduce de la elevación (< nivel_mar), así que solo se etiquetan río y lago.
HIDRO_RIO = "rio"
HIDRO_LAGO = "lago"


# ── Ruido determinista (sin dependencias externas) ─────────────────────────────


def _hash_entero(x: int, y: int, seed: int) -> float:
    """Hash 2D -> [0, 1). Determinista: misma seed, mismo mundo."""
    h = (x * 374761393 + y * 668265263 + seed * 1013904223) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return h / 0xFFFFFFFF


def _suavizado(t: float) -> float:
    """smoothstep: elimina el aspecto de rejilla del value noise."""
    return t * t * (3.0 - 2.0 * t)


def _ruido_valor(x: float, y: float, seed: int) -> float:
    """Value noise: interpolación bilinear (suavizada) del hash en la rejilla."""
    xi, yi = math.floor(x), math.floor(y)
    fx, fy = _suavizado(x - xi), _suavizado(y - yi)
    h00 = _hash_entero(xi, yi, seed)
    h10 = _hash_entero(xi + 1, yi, seed)
    h01 = _hash_entero(xi, yi + 1, seed)
    h11 = _hash_entero(xi + 1, yi + 1, seed)
    return (
        h00 * (1 - fx) * (1 - fy)
        + h10 * fx * (1 - fy)
        + h01 * (1 - fx) * fy
        + h11 * fx * fy
    )


def _fbm(x: float, y: float, seed: int, octavas: int, escala: float) -> float:
    """Ruido fractal (suma de octavas). Devuelve [0, 1)."""
    frecuencia = 1.0 / escala
    amplitud = 1.0
    total = 0.0
    norma = 0.0
    for octava in range(octavas):
        total += amplitud * _ruido_valor(
            x * frecuencia, y * frecuencia, seed + octava * 101
        )
        norma += amplitud
        amplitud *= 0.5
        frecuencia *= 2.0
    return total / norma


def _cuantil(ordenados: list[float], q: float) -> float:
    """Valor en el cuantil q (0..1) de una lista YA ordenada."""
    if not ordenados:
        raise ValueError("_cuantil sobre lista vacía")
    idx = min(len(ordenados) - 1, int(q * len(ordenados)))
    return ordenados[idx]


# ── Estado del mundo durante la generación ────────────────────────────────────


@dataclass
class MapaMundo:
    """Estado intermedio entre capas. Las capas leen y escriben aquí."""

    ancho: int
    alto: int
    # Altura del terreno en [0, 1].
    elevacion: list[list[float]] = field(init=False)
    # Temperatura relativa en [0, 1]: 0 = polar, 1 = ecuatorial.
    temperatura: list[list[float]] = field(init=False)
    # Humedad relativa en [0, 1].
    humedad: list[list[float]] = field(init=False)
    # Suelo asignado por las capas, None = aún sin decidir.
    suelos: list[list[Optional[str]]] = field(init=False)
    # Hidrología: None o un dict por casilla de agua interior (el mar
    # /océano no se etiqueta). La simulación no distingue ríos de lagos
    # (todo es Suelo_Agua); esto es metadato para capas futuras y el
    # renderizador:
    #   río:  {"tipo": HIDRO_RIO, "id": int, "dir": (dx, dy)}  # dir = flujo
    #   lago: {"tipo": HIDRO_LAGO, "id": int, "capacidad_maxima": float,
    #          "fondo": float, "elev": float, "area": int}
    #     - capacidad_maxima: cota de desborde (la orilla).
    #     - fondo: cota más baja de la cuenca (la última gota al secarse).
    #     - elev: elevación de ESTA casilla (batimetría del lago).
    hidro: list[list[Optional[dict]]] = field(init=False)
    # Red hidrográfica (genealogía de ríos y lagos): la rellena la capa
    # "rios" (y "mares_interiores" para sus lagos) y la devuelve
    # generar_mapa_suelos como cuarto valor.
    red: dict = field(init=False)
    # La capa "rios" deja aquí su instancia para que capas posteriores
    # tracen desagües con la misma maquinaria (None si no se ejecutó).
    trazador_rios: object = field(init=False)
    # Umbrales calculados por la capa de orografía (por cuantiles) y leídos
    # por las capas siguientes. Congelados tras calcularse: todas las capas
    # ven el MISMO mar y la MISMA montaña.
    nivel_mar: float = 0.0
    umbral_montana: float = 1.0
    umbral_piedra: float = 1.0
    umbral_grava: float = 1.0
    # Fijados por las capas a partir de las cuotas (cuantiles).
    umbral_temp_hielo: float = 0.0
    umbral_sequia: float = float("inf")
    umbral_cesped: float = float("inf")

    def __post_init__(self) -> None:
        self.elevacion = [[0.0] * self.ancho for _ in range(self.alto)]
        self.temperatura = [[0.0] * self.ancho for _ in range(self.alto)]
        self.humedad = [[0.0] * self.ancho for _ in range(self.alto)]
        self.suelos = [[None] * self.ancho for _ in range(self.alto)]
        self.hidro = [[None] * self.ancho for _ in range(self.alto)]
        self.red = {"rios": {}, "lagos": {}}
        self.trazador_rios = None

    def en_limite(self, x: int, y: int) -> bool:
        return x == 0 or y == 0 or x == self.ancho - 1 or y == self.alto - 1

    def es_agua(self, x: int, y: int) -> bool:
        return self.elevacion[y][x] < self.nivel_mar

    def vecinos(self, x: int, y: int):
        """Vecinos de 8 direcciones que caen dentro del mapa."""
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.ancho and 0 <= ny < self.alto:
                    yield nx, ny


@dataclass
class ParametrosGeneracion:
    """Todos los parámetros ajustables de la generación.

    Las proporciones (`prop_*`) son CUANTILES: fracción del mapa bajo el
    mar, o fracción de la tierra por encima de cada umbral orográfico.
    Eso hace que seed 42 y seed 99999 produzcan mundos distintos pero con
    la MISMA mezcla de terrenos.
    """

    ancho: int = 600
    alto: int = 600
    seed: int = 42
    # Orografía
    proporcion_agua: float = 0.68  # fracción del mapa bajo el nivel del mar
    proporcion_montana: float = 0.85  # cuantil de tierra donde empieza montaña
    proporcion_piedra: float = 0.97  # cumbres altas
    banda_grava: float = 0.08  # piedemonte: montaña - banda
    ganancia_relieve: float = 2.0  # contraste del ruido de elevación
    octavas_orografia: int = 5
    # Tamaño de "continente" con fragmentacion = 0 (en celdas).
    escala_orografia: float = 80.0
    # 0.0 = una única masa continental (Pangea); 1.0 = mar lleno de
    # islitas. Ajusta la FRECUENCIA del ruido de elevación: a mayor
    # fragmentación, features más pequeños y tierra más troceada.
    fragmentacion: float = 0.5
    # Costas: fracción del lado menor que cae hacia el océano de borde.
    borde_oceano: float = 0.15
    # Altura del mapa: la elevación normalizada (0..1) se convierte a
    # METROS con 0 = nivel del mar. La cota más alta del mapa (elev=1)
    # queda a altura_maxima_metros; el fondo marino queda en negativo.
    altura_maxima_metros: float = 4000.0
    # Clima
    penalizacion_altitud: float = 1.2  # cuánto enfría la altitud
    octavas_clima: int = 3
    escala_clima: float = 150.0
    # Ríos. Nacen SOLO en la frontera de las zonas de Suelo_Piedra y
    # bajan SIN LÍMITE de longitud: solo terminan en el mar o al unirse a
    # otro río/lago. En un callejón sin salida forman un lago que, si su
    # cuenca desborda, da nacimiento a un río nuevo (el desagüe).
    num_rios: int = 14
    # Ancho de río. Los ríos NO tienen todos el mismo ancho: se engordan
    # por ANILLOS a partir del cauce, y el número de anillos se sortea en
    # función de la longitud REAL trazada: un río corto casi nunca se
    # ensancha; uno largo es muy PROBABLE que lo sea, pero no seguro.
    # - ancho_max_rio: anillos máximos extra (ancho máx = 1 + anillo).
    # - longitud_ref_rio_ancho: longitud (celdas) a la que la probabilidad
    #   de ensancharse cada anillo llega a 1.0; antes crece linealmente.
    ancho_max_rio: int = 3
    longitud_ref_rio_ancho: float = 400.0
    # Sinuosidad: cuánto se permite desviarse del descenso más directo.
    # 0.0 = siempre al vecino más bajo (líneas rectas/quebradas). Mayor
    # valor = el río elige entre TODOS los vecinos que bajan, con un
    # sorteo sesgado por la pendiente: aparecen meandros. En unidades de
    # elevación: 0.02-0.05 ya da curvas naturales.
    sinuosidad_rio: float = 0.03
    # Tope de seguridad: cuántos lagos puede encadenar un mismo
    # manantial (río -> lago -> desagüe -> lago -> ...) antes de que la
    # cadena se dé por muerta. Con cuencas normales no se llega, pero un
    # terreno muy raro podría patinar.
    max_lagos_por_rio: int = 8
    # Tamaño mínimo de lago en celdas. La cuenca real donde se atasca el
    # río suele ser diminuta (2-4 celdas) porque el terreno fBm es liso;
    # si el lago queda por debajo de este tamaño, el agua SIGUE subiendo
    # (tragándose las casillas de la orilla más bajas primero) hasta
    # alcanzarlo. El desborde sigue siendo el punto de fuga más bajo.
    tamano_min_lago: int = 16
    # Humedad: distancia máx. (celdas) al agua que sigue influyendo.
    alcance_humedad: int = 12
    bono_humedad_agua: float = 0.35
    # Cuotas de suelo: fracción de la TIERRA EMERGIDA que ocupa cada
    # bioma. Se cumplen por CANTILES + RANKING físico, así que son
    # exactas en cualquier seed y siguen siendo coherentes: el desierto
    # cae en lo más cálido y seco, el césped en lo más húmedo, el hielo
    # en los polos. Suelo_Tierra NO se configura: es el resto.
    proporcion_hielo: float = 0.12  # tundra polar + banquisa del mar
    proporcion_arena: float = 0.10  # desierto cálido y seco
    proporcion_cesped: float = 0.30  # praderas húmedas
    # Barro
    umbral_humedad_barro: float = 0.55


# ── Registro de capas ─────────────────────────────────────────────────────────

CAPAS: dict[str, type] = {}
ORDEN_CAPAS: list[str] = [
    "orografia",
    "mares_interiores",
    "rios",
    "biomas",
    "barro",
    "limite",
]


def registrar_capa(nombre: str):
    """Clase-decorador: registra la capa bajo `nombre`.

    Para añadir una capa nueva a futuro: crear la clase (hereda de Capa),
    decorarla con @registrar_capa("nombre") e insertar el nombre en
    ORDEN_CAPAS en la posición que toque (o pasarlo explícito en
    `capas=[...]` al llamar a generar_mapa_suelos).
    """

    def _decorar(clase: type) -> type:
        CAPAS[nombre] = clase
        return clase

    return _decorar


class Capa:
    """Base de las capas de procesado. NO registrada directamente."""

    def aplicar(
        self, mapa: MapaMundo, p: ParametrosGeneracion, rng: random.Random
    ) -> None:
        raise NotImplementedError


# ── Capa 1: orografía + clima base ──────────────────────────────────────────


@registrar_capa("orografia")
class CapaOrografia(Capa):
    """Elevación (fBm con contraste + caída hacia los bordes para que el
    mundo sea tierra rodeada de océano), umbrales de mar/montaña por
    CUANTILES, temperatura por LATITUD (polos arriba y abajo) y humedad
    base por ruido independiente."""

    def aplicar(
        self, mapa: MapaMundo, p: ParametrosGeneracion, rng: random.Random
    ) -> None:
        lado_menor = min(mapa.ancho, mapa.alto)
        caida = p.borde_oceano * lado_menor
        todas: list[float] = []

        for y in range(mapa.alto):
            # Latitud 0 en el centro (ecuador), 1 en los polos (filas 0 y alto-1).
            lat = abs(y - (mapa.alto - 1) / 2) / max(1.0, (mapa.alto - 1) / 2)
            for x in range(mapa.ancho):
                # Fragmentación: escala efectiva del ruido. A 0, features
                # grandes (una única masa); a 1, pequeños (archipiélago).
                escala = p.escala_orografia * (1.0 - 0.7 * p.fragmentacion)
                raw = _fbm(x, y, p.seed, p.octavas_orografia, escala)
                elev = 0.5 + (raw - 0.5) * p.ganancia_relieve
                elev = max(0.0, min(1.0, elev))

                # Cae hacia los bordes: océano garantizado alrededor.
                dist_borde = min(x, y, mapa.ancho - 1 - x, mapa.alto - 1 - y)
                factor = min(1.0, dist_borde / caida) if caida > 0 else 1.0
                elev *= factor
                mapa.elevacion[y][x] = elev
                todas.append(elev)

                # Temperatura: latitud + ruido suave - altitud.
                temp = 1.0 - lat**1.6
                temp += (
                    _fbm(x, y, p.seed + 7, p.octavas_clima, p.escala_clima) - 0.5
                ) * 0.25
                temp -= max(0.0, elev - 0.5) * p.penalizacion_altitud
                mapa.temperatura[y][x] = max(0.0, min(1.0, temp))

                hum = _fbm(x, y, p.seed + 13, p.octavas_clima, p.escala_clima)
                mapa.humedad[y][x] = 0.5 + (hum - 0.5) * 0.8  # [0.1, 0.9]

        # Umbrales por cuantil: mar sobre TODO el mapa; el resto sobre la
        # tierra emergida SIN el hielo polar (en los polos el clima gana a
        # la orografía: una cumbre polar es hielo, no montaña).
        todas.sort()
        mapa.nivel_mar = _cuantil(todas, p.proporcion_agua)
        tierra_idx = [
            (x, y)
            for y in range(mapa.alto)
            for x in range(mapa.ancho)
            if mapa.elevacion[y][x] >= mapa.nivel_mar
        ]
        temps = sorted(mapa.temperatura[y][x] for x, y in tierra_idx)
        mapa.umbral_temp_hielo = _cuantil(temps, p.proporcion_hielo)
        sin_hielo = sorted(
            mapa.elevacion[y][x]
            for x, y in tierra_idx
            if mapa.temperatura[y][x] >= mapa.umbral_temp_hielo
        )
        mapa.umbral_montana = _cuantil(sin_hielo, p.proporcion_montana)
        mapa.umbral_piedra = _cuantil(sin_hielo, p.proporcion_piedra)
        mapa.umbral_grava = _cuantil(
            sin_hielo, max(0.0, p.proporcion_montana - p.banda_grava)
        )


@registrar_capa("rios")
class CapaRios(Capa):
    """Red fluvial con GENEALOGÍA: manantial -> río -> lago -> desagüe...

    Ríos que nacen SOLO en la frontera de las zonas de Suelo_Piedra y
    bajan SIN LÍMITE de longitud. Reglas de vida y muerte de un río:
    - muere en el OCÉANO sin crear nada más (fin de la red);
    - muere en un LAGO (le llega por fuera): el lago no crea nada nuevo
      por él;
    - en un CALLEJÓN SIN SALIDA crea un lago; si el lago desborda, el
      DESAGÜE es un río nuevo (el lago guarda la referencia);
    - cuando DOS RÍOS CONVERGEN, ambos mueren y nace un río nuevo que
      continúa por el cauce aguas abajo: el tramo receptor se PARTE en
      ese punto, y ambos ríos guardan referencia al nuevo.

    La red completa queda en mapa.red["rios"] y mapa.red["lagos"]:
      ríos:  {"nace_de": ("manantial", (x, y)) | ("lago", id_lago) |
                       ("confluencia", (x, y)),
              "muere_en": ("mar", None) | ("lago", id_lago) |
                       ("confluencia", id_rio) | ("seca", None),
              "camino": [(x, y), ...]}
      lagos: {"nace_de_rio": id_rio | None, "desagua_en_rio": id | None,
              "capacidad_maxima": float, "fondo": float, "area": int}
    (Los lagos de mares_interiores también se registran, con nace_de_rio
    None porque no nacen de ningún río.)

    En la hidrología por casilla, cada celda de río sigue llevando su
    {"tipo", "id", "dir"}: el id es del río al que pertenece AHORA
    (tras posibles particiones por confluencia).
    """

    def aplicar(
        self, mapa: MapaMundo, p: ParametrosGeneracion, rng: random.Random
    ) -> None:
        # Fuentes: SOLO en la FRONTERA de las zonas de Suelo_Piedra: celdas
        # de piedra (>= umbral_piedra) que tocan al menos una celda NO
        # piedra. Nacer en el interior de un macizo rocoso está prohibido:
        # el río no puede atravesar la piedra, así que desde ahí solo
        # podría volver a subir, y eso no es un río.
        candidatas = [
            (x, y)
            for y in range(mapa.alto)
            for x in range(mapa.ancho)
            if mapa.elevacion[y][x] >= mapa.umbral_piedra
            and any(
                mapa.elevacion[ny][nx] < mapa.umbral_piedra
                for nx, ny in mapa.vecinos(x, y)
            )
        ]
        if not candidatas:
            return
        fuentes = rng.sample(candidatas, min(p.num_rios, len(candidatas)))

        # Espacios de ids: sobran de sobra (4 celdas por casilla).
        self._ids_rio = iter(range(1, 4 * mapa.ancho * mapa.alto + 1))
        self._ids_lago = iter(range(1, 4 * mapa.ancho * mapa.alto + 1))
        # Índice celda -> (id_rio, posición en el camino): permite partir
        # el cauce receptor en una confluencia.
        self._indice: dict[tuple[int, int], tuple[int, int]] = {}

        for fx, fy in fuentes:
            self._trazar(mapa, p, rng, fx, fy)
        # Deja el trazador accesible: capas posteriores (mares_interiores)
        # pueden trazar desagües de sus lagos con la MISMA maquinaria
        # (ids, índice de cauces, confluencias, lagos encadenados).
        mapa.trazador_rios = self

    def _nuevo_rio(self, mapa: MapaMundo, nace_de) -> int:
        id_rio = next(self._ids_rio)
        mapa.red["rios"][id_rio] = {"nace_de": nace_de, "muere_en": None, "camino": []}
        return id_rio

    def _trazar(
        self,
        mapa: MapaMundo,
        p: ParametrosGeneracion,
        rng: random.Random,
        fx: int,
        fy: int,
        nace_de: Optional[tuple] = None,
    ) -> int:
        """Traza la cadena completa de un punto de nacimiento: segmentos
        de río (posiblemente varios, separados por lagos o nacidos de
        confluencias ajenas) hasta morir en mar, lago o confluencia.
        Devuelve el id del PRIMER río de la cadena.

        nace_de: origen del primer río; None = manantial en (fx, fy).
        Otras capas (mares_interiores) lo usan con ("lago", id) para
        trazar los desagües de sus lagos."""
        id_rio = self._nuevo_rio(mapa, nace_de or ("manantial", (fx, fy)))
        x, y = fx, fy
        visitadas: set[tuple[int, int]] = {(x, y)}
        camino: list[tuple[int, int]] = []  # cauce de TODA la cadena (para ensanchar)
        lagos = 0

        while True:
            # ── Fin de la cadena: mar, borde, lago ajeno o confluencia ──
            if mapa.es_agua(x, y) or mapa.en_limite(x, y):
                mapa.red["rios"][id_rio]["muere_en"] = ("mar", None)
                break
            if (x, y) not in visitadas and mapa.suelos[y][x] == SUELO_AGUA:
                info = mapa.hidro[y][x]
                if info is not None and info.get("tipo") == HIDRO_RIO:
                    self._confluencia(mapa, id_rio, info["id"], (x, y))
                elif info is not None and info.get("tipo") == HIDRO_LAGO:
                    mapa.red["rios"][id_rio]["muere_en"] = ("lago", info["id"])
                else:  # agua sin etiqueta (no debería existir aquí): mar
                    mapa.red["rios"][id_rio]["muere_en"] = ("mar", None)
                break

            # ── Siguiente paso: descenso con meandro (igual que siempre) ──
            mejor = None
            elev_actual = mapa.elevacion[y][x]
            mejor_coste = float("inf")
            for nx, ny in mapa.vecinos(x, y):
                if (nx, ny) in visitadas:
                    continue
                if (nx, ny) != (fx, fy) and mapa.elevacion[ny][
                    nx
                ] >= mapa.umbral_piedra:
                    continue  # pared de piedra
                e = mapa.elevacion[ny][nx]
                if e >= elev_actual:
                    continue  # solo se baja (garantiza progreso)
                coste = e + rng.uniform(0.0, max(0.0, p.sinuosidad_rio))
                if coste < mejor_coste:
                    mejor_coste = coste
                    mejor = (nx, ny)

            if mejor is None:
                # Callejón sin salida: lago, y si desborda, nuevo río.
                lagos += 1
                if lagos > p.max_lagos_por_rio:
                    mapa.red["rios"][id_rio]["muere_en"] = ("seca", None)
                    break  # seguridad: cadena patológica
                id_lago = next(self._ids_lago)
                desborde, celdas_lago = self._hacer_lago(
                    mapa, p, x, y, id_lago, id_rio, visitadas
                )
                # CORRECCIÓN CLAVE: las celdas del lago pasan a visitadas,
                # si no, el desagüe desciende "bajando" hacia su propio
                # lago y muere en él al primer paso.
                for cx, cy, _ in celdas_lago:
                    visitadas.add((cx, cy))
                if desborde is None:
                    mapa.red["rios"][id_rio]["muere_en"] = ("lago", id_lago)
                    break  # lago terminal
                # El desagüe del lago es un río nuevo.
                id_rio = self._nuevo_rio(mapa, ("lago", id_lago))
                mapa.red["lagos"][id_lago]["desagua_en_rio"] = id_rio
                x, y = desborde
                visitadas.add((x, y))
                continue

            # Registrar la casilla actual como río, con su dirección de
            # flujo (delta hacia la casilla siguiente, aguas abajo).
            nx, ny = mejor
            mapa.suelos[y][x] = SUELO_AGUA
            mapa.hidro[y][x] = {
                "tipo": HIDRO_RIO,
                "id": id_rio,
                "dir": (nx - x, ny - y),
            }
            registro = mapa.red["rios"][id_rio]
            registro["camino"].append((x, y))
            self._indice[(x, y)] = (id_rio, len(registro["camino"]) - 1)
            camino.append((x, y))
            x, y = mejor
            visitadas.add((x, y))

        self._ensanchar(mapa, p, rng, camino)

    def _confluencia(
        self,
        mapa: MapaMundo,
        id_llega: int,
        id_recibe: int,
        celda: tuple[int, int],
    ) -> None:
        """El río id_llega alcanza el cauce de id_recibe en `celda`:
        ambos mueren y nace un río NUEVO que continúa por el cauce
        receptor aguas abajo. El tramo receptor se PARTE: id_recibe
        conserva solo lo que hay ANTES de la confluencia; el nuevo río
        hereda el resto del camino y el destino que tuviera (mar, lago o
        otra confluencia). Así la genealogía se encadena: A -> N -> Y.
        """
        id_nuevo = self._nuevo_rio(mapa, ("confluencia", celda))
        registro = mapa.red["rios"][id_recibe]
        # Destino del cauce receptor ANTES de partirlo: el tramo que
        # hereda el nuevo río ya sabía adónde iba (mar, lago u otra
        # confluencia). El receptor muere aquí, en la confluencia.
        destino_viejo = registro["muere_en"]
        registro["muere_en"] = ("confluencia", id_nuevo)
        mapa.red["rios"][id_llega]["muere_en"] = ("confluencia", id_nuevo)

        # Partir el cauce receptor en el punto de confluencia: el nuevo
        # río se queda el tramo aguas abajo y re-etiqueta sus celdas.
        if celda in self._indice:
            id_owner, k = self._indice[celda]
            if id_owner == id_recibe:
                camino_recibe = registro["camino"]
                heredado = camino_recibe[k:]
                registro["camino"] = camino_recibe[:k]
                nuevo = mapa.red["rios"][id_nuevo]
                nuevo["camino"] = heredado
                for i, (cx, cy) in enumerate(heredado):
                    mapa.hidro[cy][cx]["id"] = id_nuevo
                    self._indice[(cx, cy)] = (id_nuevo, i)

        # El nuevo río hereda el destino que tenía el tramo receptor.
        mapa.red["rios"][id_nuevo]["muere_en"] = destino_viejo

    def _ensanchar(
        self,
        mapa: MapaMundo,
        p: ParametrosGeneracion,
        rng: random.Random,
        camino: list[tuple[int, int]],
    ) -> None:
        """Engorda el cauce por anillos (como siempre). Las celdas del
        anillo heredan tipo/id/dir del cauce vecino más próximo, y se
        registran en el índice apuntando a esa celda del cauce: así una
        confluencia posterior sobre un anillo parte el cauce por su
        dueño."""
        if not camino or p.ancho_max_rio <= 1:
            return
        prob = min(1.0, len(camino) / max(1.0, p.longitud_ref_rio_ancho))

        cauce = set(camino)
        for _ in range(p.ancho_max_rio - 1):
            if rng.random() >= prob:
                break

            anillo = set()
            for x, y in cauce:
                for nx, ny in mapa.vecinos(x, y):
                    if (nx, ny) in cauce or mapa.es_agua(nx, ny):
                        continue
                    if mapa.en_limite(nx, ny):
                        continue
                    if mapa.elevacion[ny][nx] >= mapa.umbral_piedra:
                        continue
                    anillo.add((nx, ny))
            if not anillo:
                break
            for nx, ny in anillo:
                cx, cy = min(cauce, key=lambda c: (c[0] - nx) ** 2 + (c[1] - ny) ** 2)
                mapa.suelos[ny][nx] = SUELO_AGUA
                mapa.hidro[ny][nx] = dict(mapa.hidro[cy][cx])
                if (cx, cy) in self._indice:
                    self._indice[(nx, ny)] = self._indice[(cx, cy)]
            cauce |= anillo

    def _hacer_lago(
        self,
        mapa: MapaMundo,
        p: ParametrosGeneracion,
        x: int,
        y: int,
        id_lago: int,
        id_rio: int,
        visitadas: set[tuple[int, int]],
    ):
        """Llena la cuenca del callejón por inundación creciente (priority
        flood) y localiza el punto de DESBORDE real. Registra el lago en
        la red con la referencia al río que lo creó.

        El desborde NO es "la primera celda por encima del nivel": es la
        primera celda del lago con un vecino EXTERIOR (tierra no vista
        por la inundación, no piedra, más BAJA que ella): el único sitio
        por donde el agua escapa de verdad (el umbral/sill de la cuenca).
        Solo se acepta si el lago ya alcanza tamano_min_lago; antes de
        eso el agua sigue subiendo.

        Devuelve (desborde, celdas): la casilla donde nacerá el río
        desagüe (o None si el lago es terminal) y las celdas anegadas,
        para que _trazar las marque como visitadas y el desagüe no
        re entre en su propio lago."""
        frontera: list[tuple[float, int, int]] = []
        en_cola: set[tuple[int, int]] = set()
        for vx, vy in list(mapa.vecinos(x, y)) + [(x, y)]:
            en_cola.add((vx, vy))
            heapq.heappush(frontera, (mapa.elevacion[vy][vx], vx, vy))

        nivel = -1.0
        celdas_lago: list[tuple[int, int, float]] = []
        desborde = None

        while frontera:
            e, cx, cy = heapq.heappop(frontera)
            propia = (cx, cy) in visitadas
            ajena = not propia and (
                mapa.es_agua(cx, cy) or mapa.suelos[cy][cx] == SUELO_AGUA
            )

            if ajena:
                # El lago conectó con agua exterior: la cadena muere aquí.
                desborde = None
                break

            if not propia and mapa.en_limite(cx, cy):
                continue  # el anillo del borde no se encharca ni desborda

            if not propia:
                # ¿Escape real? Vecino exterior: tierra no vista por la
                # inundación, más baja que esta celda, no pared de piedra.
                escape = any(
                    (nx, ny) not in en_cola
                    and (nx, ny) not in visitadas
                    and not mapa.es_agua(nx, ny)
                    and mapa.suelos[ny][nx] != SUELO_AGUA
                    and mapa.elevacion[ny][nx] < e
                    and mapa.elevacion[ny][nx] < mapa.umbral_piedra
                    for nx, ny in mapa.vecinos(cx, cy)
                )
                if escape and len(celdas_lago) >= p.tamano_min_lago:
                    nivel = e
                    desborde = (cx, cy)
                    break

            # Casilla de la cuenca (o agua propia): se anega.
            nivel = max(nivel, e)
            mapa.suelos[cy][cx] = SUELO_AGUA
            celdas_lago.append((cx, cy, e))
            for nx, ny in mapa.vecinos(cx, cy):
                if (nx, ny) not in en_cola:
                    en_cola.add((nx, ny))
                    heapq.heappush(frontera, (mapa.elevacion[ny][nx], nx, ny))

        fondo = min(e for _, _, e in celdas_lago) if celdas_lago else nivel
        for lx, ly, le in celdas_lago:
            mapa.hidro[ly][lx] = {
                "tipo": HIDRO_LAGO,
                "id": id_lago,
                "capacidad_maxima": nivel,
                "fondo": fondo,
                "elev": le,
                "area": len(celdas_lago),
            }
        mapa.red["lagos"][id_lago] = {
            "nace_de_rio": id_rio,
            "desagua_en_rio": None,  # lo fija _trazar si desborda
            "capacidad_maxima": nivel,
            "fondo": fondo,
            "area": len(celdas_lago),
        }
        return desborde, celdas_lago


# ── Capa 3: biomas ────────────────────────────────────────────────────────────


@registrar_capa("biomas")
class CapaBiomas(Capa):
    """Asigna el suelo de TODAS las casillas aún sin decidir.

    Las cuotas (proporcion_hielo/arena/cesped) se cumplen por CANTILES
    con RANKING físico: se ordenan las casillas por el criterio real de
    cada bioma (el desierto en lo más cálido y seco, el césped en lo más
    húmedo, el hielo en lo más frío) y el umbral se fija justo donde se
    agota la cuota. Así la CANTIDAD es exacta en cualquier seed, pero el
    MAPA sigue siendo coherente con el mundo real: nunca verás un desierto
    pegado al hielo polar.

    Precedencia (lo primero gana): agua/banquisa -> hielo -> montaña ->
    arena -> césped -> tierra (resto).
    """

    def aplicar(
        self, mapa: MapaMundo, p: ParametrosGeneracion, rng: random.Random
    ) -> None:
        self._refinar_humedad(mapa, p)
        self._calcular_cuotas_llanura(mapa, p)

        for y in range(mapa.alto):
            for x in range(mapa.ancho):
                if mapa.suelos[y][x] is None:
                    mapa.suelos[y][x] = self._bioma(mapa, p, x, y)

    def _calcular_cuotas_llanura(
        self, mapa: MapaMundo, p: ParametrosGeneracion
    ) -> None:
        """Fija umbral_sequia/umbral_cesped por cuantil sobre la LLANURA:
        tierra emergida, sin hielo, sin montaña/grava y sin ríos."""
        llanura = [
            (x, y)
            for y in range(mapa.alto)
            for x in range(mapa.ancho)
            if mapa.suelos[y][x] is None
            and not mapa.es_agua(x, y)
            and mapa.elevacion[y][x] < mapa.umbral_grava
            and mapa.temperatura[y][x] >= mapa.umbral_temp_hielo
        ]
        if not llanura:  # mundo todo agua/hielo/montaña: nada que repartir
            return

        # Desierto: la fracción más cálida y seca de la llanura.
        sequia = sorted(mapa.temperatura[y][x] - mapa.humedad[y][x] for x, y in llanura)
        mapa.umbral_sequia = _cuantil(sequia, 1.0 - p.proporcion_arena)

        # Césped: la fracción más húmeda de lo que queda tras el desierto.
        resto = [
            (x, y)
            for x, y in llanura
            if mapa.temperatura[y][x] - mapa.humedad[y][x] < mapa.umbral_sequia
        ]
        if resto:
            hums = sorted(mapa.humedad[y][x] for x, y in resto)
            mapa.umbral_cesped = _cuantil(hums, 1.0 - p.proporcion_cesped)

    def _refinar_humedad(self, mapa: MapaMundo, p: ParametrosGeneracion) -> None:
        """BFS multi-fuente desde toda casilla de agua (mar o río): la
        humedad sube cerca del agua y decae con la distancia."""
        alcance = max(1, p.alcance_humedad)
        distancia: dict[tuple[int, int], int] = {}
        pendientes: list[tuple[int, int, int]] = []
        for y in range(mapa.alto):
            for x in range(mapa.ancho):
                if mapa.es_agua(x, y) or mapa.suelos[y][x] == SUELO_AGUA:
                    distancia[(x, y)] = 0
                    pendientes.append((x, y, 0))

        cabeza = 0
        while cabeza < len(pendientes):
            x, y, d = pendientes[cabeza]
            cabeza += 1
            if d >= alcance:
                continue
            for nx, ny in mapa.vecinos(x, y):
                if (nx, ny) not in distancia:
                    distancia[(nx, ny)] = d + 1
                    pendientes.append((nx, ny, d + 1))

        for (x, y), d in distancia.items():
            bono = (1.0 - d / alcance) * p.bono_humedad_agua
            mapa.humedad[y][x] = min(1.0, mapa.humedad[y][x] + bono)

    @staticmethod
    def _bioma(mapa: MapaMundo, p: ParametrosGeneracion, x: int, y: int) -> str:
        elev = mapa.elevacion[y][x]
        temp = mapa.temperatura[y][x]
        hum = mapa.humedad[y][x]
        helado = temp < mapa.umbral_temp_hielo

        # Agua: océano profundo vs. agua costera/somera. En los polos el
        # mar se congela: banquisa de hielo.
        if elev < mapa.nivel_mar - 0.08:
            return SUELO_HIELO if helado else SUELO_OCEANO
        if elev < mapa.nivel_mar:
            return SUELO_HIELO if helado else SUELO_AGUA

        # Hielo continental: tundra polar.
        if helado:
            return SUELO_HIELO

        # Montaña: cumbres de roca (grava en las laderas más secas).
        if elev >= mapa.umbral_piedra:
            return SUELO_PIEDRA
        if elev >= mapa.umbral_montana:
            return SUELO_GRAVA if hum < 0.45 else SUELO_PIEDRA
        if elev >= mapa.umbral_grava and hum < 0.45:
            return SUELO_GRAVA

        # Llanuras por cuota: desierto en lo más cálido y seco, césped en
        # lo más húmedo, tierra en el resto.
        if (temp - hum) >= mapa.umbral_sequia:
            return SUELO_ARENA
        if hum >= mapa.umbral_cesped:
            return SUELO_CESPED
        return SUELO_TIERRA


# ── Capa 4: mares interiores -> agua interior ─────────────────────────────────
@registrar_capa("mares_interiores")
class CapaMaresInteriores(Capa):
    """RELLENA DE TIERRA los mares interiores, ANTES de trazar ríos.

    El mar PRINCIPAL es todo el Suelo_Oceano conectado con el borde del
    mapa. Cualquier masa de océano que no llega al borde es un mar
    interior cerrado (tipo mar Caspio): se convierte en TIERRA — el
    agua no lo vuelve a tocar — para que los ríos que se atasquen en su
    cuenca formen sus propios lagos desde cero, sin lagos previos
    heredados del relleno del océano.

    La conversión es suave: la cota se sube a nivel_mar + margen,
    conservando la FORMA relativa de la cubeta (lo más profundo queda
    algo más bajo), así el terreno es creíble y los ríos encuentran
    desniveles naturales donde atascarse y crear lagos.
    """

    # Cuánto se eleva el fondo del mar interior sobre el nivel del mar.
    MARGEN_RELLENO = 0.005
    VARIACION_RELLENO = 0.02

    def aplicar(
        self, mapa: MapaMundo, p: ParametrosGeneracion, rng: random.Random
    ) -> None:
        # OJO: esta capa corre ANTES de biomas, así que los SUELOS aún no
        # existen (son todos None). La detección es por ELEVACIÓN: agua =
        # celda bajo el nivel del mar.
        mar_principal = self._mar_principal(mapa)

        visitadas = set(mar_principal)
        for y in range(mapa.alto):
            for x in range(mapa.ancho):
                if (x, y) in visitadas or not mapa.es_agua(x, y):
                    continue
                # Masa de océano cerrada: tierra.
                # CORTE DE SEGURIDAD: el flood se corta en `visitadas`
                # (mar principal + masas ya rellenadas).
                componente = self._componente(mapa, x, y, visitadas)
                visitadas |= componente
                celdas = list(componente)
                if not celdas:
                    continue

                # Forma relativa de la cubeta: 0 = lo más profundo,
                # 1 = lo más alto de la masa.
                cotas = [mapa.elevacion[cy][cx] for cx, cy in celdas]
                mn, mx = min(cotas), max(cotas)
                for cx, cy in celdas:
                    rel = (mapa.elevacion[cy][cx] - mn) / max(1e-9, mx - mn)
                    # Elevar por ENCIMA del nivel del mar: desde ahora ya
                    # no es agua (es_agua lee la elevación) y biomas le
                    # asignará un suelo de llanura.
                    mapa.elevacion[cy][cx] = (
                        mapa.nivel_mar
                        + self.MARGEN_RELLENO
                        + self.VARIACION_RELLENO * rel
                    )

    @staticmethod
    def _componente(
        mapa: MapaMundo,
        x: int,
        y: int,
        barrera: set[tuple[int, int]],
    ) -> set[tuple[int, int]]:
        """Flood fill (8-dir) del agua (por ELEVACIÓN) conectada a
        (x, y), que NUNCA atraviesa `barrera` (mar principal y masas ya
        tratadas)."""
        pendientes = [(x, y)]
        visitadas = {(x, y)}
        cabeza = 0
        while cabeza < len(pendientes):
            cx, cy = pendientes[cabeza]
            cabeza += 1
            for nx, ny in mapa.vecinos(cx, cy):
                if (nx, ny) in visitadas or (nx, ny) in barrera:
                    continue
                if mapa.es_agua(nx, ny):
                    visitadas.add((nx, ny))
                    pendientes.append((nx, ny))
        return visitadas

    @staticmethod
    def _mar_principal(mapa: MapaMundo) -> set[tuple[int, int]]:
        """Flood fill (8-dir) desde el agua ELEVACIÓN-bajo-el-mar del
        BORDE: todo el océano conectado con el exterior del mapa."""
        pendientes: list[tuple[int, int]] = []
        for x in range(mapa.ancho):
            for y in (0, mapa.alto - 1):
                if mapa.es_agua(x, y):
                    pendientes.append((x, y))
        for y in range(mapa.alto):
            for x in (0, mapa.ancho - 1):
                if mapa.es_agua(x, y):
                    pendientes.append((x, y))

        visitadas: set[tuple[int, int]] = set(pendientes)
        cabeza = 0
        while cabeza < len(pendientes):
            x, y = pendientes[cabeza]
            cabeza += 1
            for nx, ny in mapa.vecinos(x, y):
                if (nx, ny) not in visitadas and mapa.es_agua(nx, ny):
                    visitadas.add((nx, ny))
                    pendientes.append((nx, ny))
        return visitadas


# ── Capa 5: barro (transición tierra/agua) ────────────────────────────────────


@registrar_capa("barro")
class CapaBarro(Capa):
    """El barro es una TRANSICIÓN: tierra húmeda en contacto directo con
    agua. La simulación ya se encarga de que se seque hacia Suelo_Tierra
    (ver suelo_barro.py); aquí solo se siembra."""

    def aplicar(
        self, mapa: MapaMundo, p: ParametrosGeneracion, rng: random.Random
    ) -> None:
        agua_o_mar = (SUELO_AGUA, SUELO_OCEANO)
        for y in range(mapa.alto):
            for x in range(mapa.ancho):
                if mapa.suelos[y][x] not in (SUELO_TIERRA, SUELO_CESPED):
                    continue
                if mapa.humedad[y][x] < p.umbral_humedad_barro:
                    continue
                if any(
                    mapa.suelos[ny][nx] in agua_o_mar or mapa.es_agua(nx, ny)
                    for nx, ny in mapa.vecinos(x, y)
                ):
                    mapa.suelos[y][x] = SUELO_BARRO


# ── Capa 6: límite del mundo ──────────────────────────────────────────────────


@registrar_capa("limite")
class CapaLimite(Capa):
    """Anillo de 1 casilla en el borde: Suelo_Limite SIEMPRE, pisando lo
    que hubiera (es la frontera del mundo, ver docstring de Suelo_Limite)."""

    def aplicar(
        self, mapa: MapaMundo, p: ParametrosGeneracion, rng: random.Random
    ) -> None:
        for x in range(mapa.ancho):
            mapa.suelos[0][x] = SUELO_LIMITE
            mapa.suelos[mapa.alto - 1][x] = SUELO_LIMITE
        for y in range(mapa.alto):
            mapa.suelos[y][0] = SUELO_LIMITE
            mapa.suelos[y][mapa.ancho - 1] = SUELO_LIMITE


# ── Punto de entrada ──────────────────────────────────────────────────────────


def generar_mapa_suelos(
    seed: Optional[int] = None,
    ancho: Optional[int] = None,
    alto: Optional[int] = None,
    capas: Optional[list[str]] = None,
    parametros: Optional["ParametrosGeneracion | dict"] = None,
    verbose: bool = False,
    **overrides,
):
    """Ejecuta el pipeline de capas y devuelve {(x, y): nombre_clase} para
    TODAS las casillas del mundo (clave faltante = bug: LogicaMundo debe
    reventar explícito, no rellenar en silencio).

    Prioridad de configuración (de menor a mayor):
      1. Defaults de ParametrosGeneracion.
      2. Config.settings (seed/ancho/alto).
      3. `parametros`: un ParametrosGeneracion COMPLETO (todos sus campos
         sobrescriben lo anterior) o un dict {campo: valor} (solo los
         campos presentes sobrescriben). Es el modo cómodo para guardar
         presets: PARAMETROS_MUNDO = ParametrosGeneracion(fragmentacion=0.7,
         ...) en Config y pasarlo entero.
      4. `**overrides` y seed/ancho/alto explícitos: lo más específico.

    - capas: orden del pipeline; None = ORDEN_CAPAS por defecto.
    """
    try:
        import Config.settings as config

        ancho_def = config.GRID_WIDTH
        alto_def = config.GRID_HEIGHT
        seed_def = getattr(config, "SEMILLA_MUNDO", 42)
    except Exception:  # standalone (p.ej. renderizador sin repo importable)
        ancho_def, alto_def, seed_def = 600, 600, 42

    if isinstance(parametros, ParametrosGeneracion):
        p = ParametrosGeneracion(**parametros.__dict__)
    elif parametros:  # dict no vacío
        p = ParametrosGeneracion(**{**parametros})
    else:
        p = ParametrosGeneracion()

    # Fuentes 4: explícitos pisan lo que haya venido en `parametros`.
    if ancho is not None:
        p.ancho = ancho
    if alto is not None:
        p.alto = alto
    if seed is not None:
        p.seed = seed
    # Default solo si nadie lo fijó (ni preset ni Config).
    if p.ancho == ParametrosGeneracion.ancho:
        p.ancho = ancho_def
    if p.alto == ParametrosGeneracion.alto:
        p.alto = alto_def
    if p.seed == ParametrosGeneracion.seed:
        p.seed = seed_def

    for clave, valor in overrides.items():
        if clave not in p.__dataclass_fields__:
            raise ValueError(
                f"Parámetro de generación desconocido: '{clave}' "
                f"(campos válidos: {', '.join(sorted(p.__dataclass_fields__))})"
            )
        setattr(p, clave, valor)

    if p.ancho < 3 or p.alto < 3:
        raise ValueError(f"Mundo demasiado pequeño: {p.ancho}x{p.alto} (mínimo 3x3).")

    if not 0.0 <= p.fragmentacion <= 1.0:
        raise ValueError(
            f"fragmentacion debe estar en [0, 1]; recibida {p.fragmentacion!r}"
        )

    cuotas = (
        "proporcion_agua",
        "proporcion_hielo",
        "proporcion_arena",
        "proporcion_cesped",
        "proporcion_montana",
        "proporcion_piedra",
    )
    for cuota in cuotas:
        valor = getattr(p, cuota)
        if not 0.0 <= valor <= 1.0:
            raise ValueError(f"{cuota} debe estar en [0, 1]; recibido {valor!r}")
    if p.proporcion_arena + p.proporcion_cesped > 1.0:
        raise ValueError(
            f"proporcion_arena ({p.proporcion_arena}) + proporcion_cesped "
            f"({p.proporcion_cesped}) > 1.0: no queda llanura para Suelo_Tierra."
        )

    orden = list(capas) if capas is not None else list(ORDEN_CAPAS)
    for nombre in orden:
        if nombre not in CAPAS:
            raise ValueError(
                f"Capa de generación desconocida: '{nombre}' "
                f"(registradas: {', '.join(sorted(CAPAS))})"
            )

    mapa = MapaMundo(ancho=p.ancho, alto=p.alto)
    rng = random.Random(p.seed)

    def _informe(capa: str, t_capa: float) -> None:
        """Línea de progreso de una capa: qué tocó y cuánto tardó."""
        asig = sum(
            1
            for y in range(mapa.alto)
            for x in range(mapa.ancho)
            if mapa.suelos[y][x] is not None
        )
        hidro = sum(
            1
            for y in range(mapa.alto)
            for x in range(mapa.ancho)
            if mapa.hidro[y][x] is not None
        )
        pct = 100.0 * asig / (mapa.ancho * mapa.alto)
        extra = f" | hidrología: {hidro} celdas" if hidro else ""
        print(
            f"  [capa {capa:<16}] {asig:>8}/{mapa.ancho * mapa.alto} suelos "
            f"({pct:5.1f} %){extra} — {t_capa:.2f} s"
        )

    if verbose:
        total = p.ancho * p.alto
        print(
            f"Generando mundo {p.ancho}x{p.alto} ({total:,} casillas), "
            f"seed={p.seed}, capas: {', '.join(orden)}"
        )

    import time

    t_total = time.perf_counter()
    for nombre in orden:
        if verbose:
            print(f"  [capa {nombre:<16}] ...", flush=True)
        t_capa = time.perf_counter()
        CAPAS[nombre]().aplicar(mapa, p, rng)
        t_capa = time.perf_counter() - t_capa
        if verbose:
            _informe(nombre, t_capa)
    t_total = time.perf_counter() - t_total

    resultado: dict[tuple[int, int], str] = {}
    hidrologia: dict[tuple[int, int], dict] = {}
    alturas: dict[tuple[int, int], int] = {}
    for y in range(p.alto):
        for x in range(p.ancho):
            suelo = mapa.suelos[y][x]
            if suelo is None:
                raise RuntimeError(
                    f"El pipeline dejó la casilla ({x}, {y}) sin suelo; "
                    f"revisa el orden de capas: {orden}"
                )
            resultado[(x, y)] = suelo
            if mapa.hidro[y][x] is not None:
                hidrologia[(x, y)] = mapa.hidro[y][x]
            # Mapa de alturas en METROS: 0 = nivel del mar, paso 1 = 1 m.
            # TODO el mar se aplana a 0 m (altura uniforme): la batimetría
            # no se genera, solo la topografía emergida. La normalización
            # es lineal: elev=1 (cota máxima del mapa) ->
            # altura_maxima_metros.
            if mapa.elevacion[y][x] < mapa.nivel_mar:
                alturas[(x, y)] = 0
            else:
                factor = p.altura_maxima_metros / max(1e-9, 1.0 - mapa.nivel_mar)
                alturas[(x, y)] = int(
                    round((mapa.elevacion[y][x] - mapa.nivel_mar) * factor)
                )

    if verbose:
        print(f"Generación completada en {t_total:.2f} s")
        conteo: dict[str, int] = {}
        for suelo in resultado.values():
            conteo[suelo] = conteo.get(suelo, 0) + 1
        for suelo in sorted(conteo, key=conteo.get, reverse=True):
            pct = 100.0 * conteo[suelo] / len(resultado)
            print(f"  {suelo:<14} {conteo[suelo]:>8}  {pct:5.1f} %")
        print(
            f"Alturas: mín {min(alturas.values())} m, " f"máx {max(alturas.values())} m"
        )

    return resultado, hidrologia, alturas, mapa.red
