"""
render_suelos.py — Pinta el mapa de suelos generado como una imagen.

Ejecutable standalone: genera el mundo con generacion_suelos (misma seed
que el servidor = mismo mundo) y escribe un PNG donde cada casilla es un
bloque de `--escala` píxeles del color de su suelo.

Sin dependencias externas: el PNG se escribe con zlib+struct directamente
(no hace falta Pillow). Si quieres un PNG, no un .ppm, esto ya lo es.

Uso:
    python Herramientas/render_suelos.py
    python Herramientas/render_suelos.py --seed 7 --escala 4 --salida mundo.png
    python Herramientas/render_suelos.py --ancho 300 --alto 300 --num_rios 20
"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

# Raíz del repo = padre de Herramientas/, para poder importar el generador
# tanto si se lanza desde la raíz como desde cualquier sitio.
_RAIZ = Path(__file__).resolve().parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from Services.Mundo.generacion_suelos import (
    HIDRO_LAGO,
    HIDRO_RIO,
    generar_mapa_suelos,
)

# Paleta fija: nombre de clase -> RGB. Añadir aquí cualquier suelo nuevo.
PALETA: dict[str, tuple[int, int, int]] = {
    "Suelo_Oceano": (26, 79, 138),
    "Suelo_Agua": (46, 134, 193),
    "Suelo_Hielo": (191, 227, 242),
    "Suelo_Arena": (232, 217, 160),
    "Suelo_Barro": (107, 74, 47),
    "Suelo_Cesped": (90, 160, 44),
    "Suelo_Grava": (154, 154, 146),
    "Suelo_Piedra": (125, 125, 120),
    "Suelo_Tierra": (139, 90, 43),
    "Suelo_Limite": (212, 0, 0),
}

# Sobrepintado hidrológico: distingue ríos y lagos del Suelo_Agua "plano".
# La hidrología llega como {(x, y): {"tipo": ...}}: ver generacion_suelos.
PALETA_HIDRO: dict[str, tuple[int, int, int]] = {
    HIDRO_RIO: (28, 90, 170),  # azul profundo: cauce
    HIDRO_LAGO: (110, 180, 220),  # azul claro: lámina de lago
}


def _chunk_png(tipo: bytes, datos: bytes) -> bytes:
    return (
        struct.pack(">I", len(datos))
        + tipo
        + datos
        + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
    )


def _rejilla_discontinua(
    filas: list[bytearray],
    celdas_x: int,
    celdas_y: int,
    escala: int,
    lado: int,
) -> None:
    """Sobreimpone líneas discontinuas NEGRAS formando cuadrados de
    `lado` celdas, alineados con la esquina INFERIOR IZQUIERDA: el borde
    inferior de cada cuadrado coincide con el borde exterior del
    Suelo_Limite inferior, y el izquierdo con el Suelo_Limite
    izquierdo. Patrón de guion: 3 celdas pintadas, 3 sin pintar."""
    if lado <= 0 or escala <= 0:
        return
    grosor = max(1, escala // 2)
    alto_px = celdas_y * escala
    ancho_px = celdas_x * escala

    def negro(px: int, py: int) -> None:
        for oy in range(grosor):
            for ox in range(grosor):
                X, Y = px + ox, py + oy
                if 0 <= X < ancho_px and 0 <= Y < alto_px:
                    base = 1 + X * 3
                    filas[Y][base: base + 3] = b"\x00\x00\x00"

    # Verticales: fronteras de celda en x = k*lado, desde el borde izq.
    for vx in range(0, celdas_x + 1, lado):
        px = vx * escala
        for cy in range(celdas_y):
            dist_abajo = celdas_y - 1 - cy
            if dist_abajo % 6 < 3:
                negro(px, cy * escala)

    # Horizontales: fronteras en y = celdas_y - k*lado, desde el borde inf.
    for hy in range(celdas_y, -1, -lado):
        py = hy * escala
        for cx in range(celdas_x):
            if cx % 6 < 3:  # distancia al borde izquierdo
                negro(cx * escala, py)


def guardar_png(
    mapa: dict[tuple[int, int], str],
    ancho: int,
    alto: int,
    escala: int,
    salida: Path,
    hidrologia: dict[tuple[int, int], dict] | None = None,
    lado_cuadricula: int = 0,
) -> dict[str, int]:
    """Escribe el PNG. Devuelve el recuento de casillas por suelo."""
    conteo: dict[str, int] = {}
    filas: list[bytes] = []
    for y in range(alto):
        # 1 fila de casillas -> escala filas de píxeles idénticas.
        fila_celdas = bytearray()
        for x in range(ancho):
            suelo = mapa[(x, y)]
            conteo[suelo] = conteo.get(suelo, 0) + 1
            rgb = PALETA.get(suelo)
            if rgb is None:
                raise ValueError(
                    f"Suelo '{suelo}' sin color asignado en PALETA; "
                    f"añádelo para poder renderizarlo."
                )
            # Sobrepintado hidrológico (río/lago), si existe: el valor es
            # un dict {"tipo": ..., "id": ..., ...}.
            info = hidrologia.get((x, y)) if hidrologia is not None else None
            if info is not None:
                rgb = PALETA_HIDRO.get(info.get("tipo", ""), rgb)
            fila_celdas += bytes(rgb) * escala
        for _ in range(escala):
            filas.append(bytearray(b"\x00" + bytes(fila_celdas)))

    _rejilla_discontinua(filas, ancho, alto, escala, lado_cuadricula)
    imagen = b"".join(bytes(f) for f in filas)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk_png(b"IHDR", struct.pack(">IIBBBBB", ancho * escala, alto * escala, 8, 2, 0, 0, 0))
        + _chunk_png(b"IDAT", zlib.compress(imagen, 9))
        + _chunk_png(b"IEND", b"")
    )
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(png)
    return conteo


def guardar_png_alturas(
    alturas: dict[tuple[int, int], int],
    ancho: int,
    alto: int,
    escala: int,
    salida: Path,
    lado_cuadricula: int = 0,
) -> tuple[int, int]:
    """Pinta el mapa de alturas en ESCALA DE GRISES: negro = más bajo,
    blanco = más elevado. El rango se normaliza al mínimo y máximo reales
    del mapa (el fondo marino también tiene alturas negativas), así que
    0 m de altitud NO es gris medio necesariamente. Devuelve (min, max)
    en metros, para poder imprimir la leyenda."""
    mn = min(alturas.values())
    mx = max(alturas.values())
    rango = max(1, mx - mn)

    filas: list[bytes] = []
    for y in range(alto):
        fila_celdas = bytearray()
        for x in range(ancho):
            gris = int(255 * (alturas[(x, y)] - mn) / rango)
            fila_celdas += bytes((gris, gris, gris)) * escala
        for _ in range(escala):
            filas.append(bytearray(b"\x00" + bytes(fila_celdas)))

    _rejilla_discontinua(filas, ancho, alto, escala, lado_cuadricula)
    imagen = b"".join(bytes(f) for f in filas)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk_png(b"IHDR", struct.pack(">IIBBBBB", ancho * escala, alto * escala, 8, 2, 0, 0, 0))
        + _chunk_png(b"IDAT", zlib.compress(imagen, 9))
        + _chunk_png(b"IEND", b"")
    )
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(png)
    return mn, mx


def guardar_png_rios(
    hidrologia: dict[tuple[int, int], dict],
    ancho: int,
    alto: int,
    escala: int,
    salida: Path,
    lado_cuadricula: int = 0,
) -> int:
    """Mapa de dirección de flujo de los ríos.

    Cada casilla de río se pinta según su `dir` (delta hacia aguas
    abajo). Cardinales (suponiendo fila 0 = norte del PNG):
        N (0,-1) amarillo   S (0,+1) cian
        E (+1,0) rojo       O (-1,0) azul
    Diagonales: mezcla PROPORCIONAL de las dos cardinales que
    componen el vector (p. ej. NE = 50% amarillo + 50% rojo).

    Fondo: tierra, lagos y mar en grises (el mapa es EXCLUSIVO de ríos:
    los lagos van en su propio PNG). Devuelve el nº de casillas de río
    pintadas.
    """
    COLOR_N = (255, 255, 0)
    COLOR_S = (0, 255, 255)
    COLOR_E = (255, 0, 0)
    COLOR_O = (0, 0, 255)
    FONDO_TIERRA = (45, 45, 45)
    FONDO_MAR = (20, 20, 20)
    COLOR_LAGO = (45, 45, 45)  # lagos disfrazados de tierra: mapa de RÍOS

    filas: list[bytes] = []
    pintadas = 0
    for y in range(alto):
        fila_celdas = bytearray()
        for x in range(ancho):
            info = hidrologia.get((x, y))
            if info is not None and info.get("tipo") == HIDRO_RIO:
                dx, dy = info.get("dir", (0, 0))
                adx, ady = abs(dx), abs(dy)
                if adx + ady == 0:
                    rgb = FONDO_TIERRA  # sin dirección: no debería pasar
                else:
                    # Mezcla proporcional: el peso de cada eje es su módulo.
                    horizontal = COLOR_E if dx > 0 else COLOR_O
                    vertical = COLOR_N if dy < 0 else COLOR_S
                    rgb = tuple(
                        (adx * horizontal[i] + ady * vertical[i]) // (adx + ady)
                        for i in range(3)
                    )
                pintadas += 1
            elif info is not None and info.get("tipo") == HIDRO_LAGO:
                rgb = COLOR_LAGO
            else:
                rgb = FONDO_TIERRA  # la tierra firme
            fila_celdas += bytes(rgb) * escala
        for _ in range(escala):
            filas.append(bytearray(b"\x00" + bytes(fila_celdas)))

    _rejilla_discontinua(filas, ancho, alto, escala, lado_cuadricula)
    imagen = b"".join(bytes(f) for f in filas)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk_png(b"IHDR", struct.pack(">IIBBBBB", ancho * escala, alto * escala, 8, 2, 0, 0, 0))
        + _chunk_png(b"IDAT", zlib.compress(imagen, 9))
        + _chunk_png(b"IEND", b"")
    )
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(png)
    return pintadas


def guardar_png_lagos(
    hidrologia: dict[tuple[int, int], dict],
    ancho: int,
    alto: int,
    escala: int,
    salida: Path,
    lado_cuadricula: int = 0,
) -> int:
    """Mapa de batimetría de lagos, NORMALIZADO POR LAGO.

    Cada lago se pinta en grises con SU propio rango:
    - negro = fondo (cota más baja de la cuenca): donde quedaría la
      última gota de agua si el lago se secara.
    - blanco = la orilla de desborde (capacidad_maxima).
    Dos lagos nunca comparten escala: cada uno muestra su propia forma
    de cubeta, independientemente de su altitud absoluta.

    Fondo: tierra, ríos y mar en grises (solo los lagos llevan color:
    el mapa es EXCLUSIVO de lagos). Devuelve el nº de casillas de lago
    pintadas."""
    FONDO_TIERRA = (45, 45, 45)
    FONDO_MAR = (20, 20, 20)
    COLOR_RIO = (45, 45, 45)  # ríos disfrazados de tierra: mapa de LAGOS

    filas: list[bytes] = []
    pintadas = 0
    for y in range(alto):
        fila_celdas = bytearray()
        for x in range(ancho):
            info = hidrologia.get((x, y))
            if info is not None and info.get("tipo") == HIDRO_LAGO:
                rango = info["capacidad_maxima"] - info["fondo"]
                if rango > 0:
                    t = (info["elev"] - info["fondo"]) / rango
                else:
                    t = 0.0  # lago de una celda: todo fondo
                gris = int(255 * max(0.0, min(1.0, t)))
                rgb = (gris, gris, gris)
                pintadas += 1
            elif info is not None and info.get("tipo") == HIDRO_RIO:
                rgb = COLOR_RIO
            else:
                rgb = FONDO_TIERRA
            fila_celdas += bytes(rgb) * escala
        for _ in range(escala):
            filas.append(bytearray(b"\x00" + bytes(fila_celdas)))

    _rejilla_discontinua(filas, ancho, alto, escala, lado_cuadricula)
    imagen = b"".join(bytes(f) for f in filas)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk_png(b"IHDR", struct.pack(">IIBBBBB", ancho * escala, alto * escala, 8, 2, 0, 0, 0))
        + _chunk_png(b"IDAT", zlib.compress(imagen, 9))
        + _chunk_png(b"IEND", b"")
    )
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(png)
    return pintadas


def main() -> int:
    parser = argparse.ArgumentParser(description="Render del mapa de suelos.")
    parser.add_argument("--seed", type=int, default=None, help="Semilla (default: Config.SEMILLA_MUNDO)")
    parser.add_argument("--ancho", type=int, default=None)
    parser.add_argument("--alto", type=int, default=None)
    parser.add_argument("--escala", type=int, default=4, help="Píxeles por casilla")
    parser.add_argument("--salida", type=Path, default=Path("mundo_suelos.png"))
    parser.add_argument("--capas", nargs="*", default=None, help="Pipeline (default: ORDEN_CAPAS)")
    # Pasar cualquier parámetro de ParametrosGeneracion: --num_rios 20 --nivel_mar 0.5
    args, extra = parser.parse_known_args()

    overrides = {}
    it = iter(extra)
    for tok in it:
        if not tok.startswith("--"):
            parser.error(f"Argumento no reconocido: {tok}")
        try:
            overrides[tok[2:]] = int(next(it))
        except ValueError:
            overrides[tok[2:]] = float(next(it))

    mapa, hidrologia, alturas = generar_mapa_suelos(
        seed=args.seed,
        ancho=args.ancho,
        alto=args.alto,
        capas=args.capas,
        **overrides,
    )
    ancho, alto = max(p[0] for p in mapa) + 1, max(p[1] for p in mapa) + 1

    conteo = guardar_png(mapa, ancho, alto, args.escala, args.salida, hidrologia)

    # Mapa de alturas: mismo mundo, un PNG aparte.
    salida_alturas = args.salida.with_name(
        args.salida.stem + "_alturas" + args.salida.suffix
    )
    guardar_png_alturas(alturas, ancho, alto, args.escala, salida_alturas)

    total = sum(conteo.values())
    print(f"Escrito: {args.salida} ({ancho * args.escala}x{alto * args.escala} px, {total} casillas)")
    print("Distribución de suelos:")
    for suelo in sorted(conteo, key=conteo.get, reverse=True):
        pct = 100.0 * conteo[suelo] / total
        print(f"  {suelo:<14} {conteo[suelo]:>7}  {pct:5.1f} %")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())