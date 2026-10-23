"""
representar_mapa.py — Genera el mundo y lo pinta como PNGs.

Escribe dos imágenes:
- mundo_suelos.png:    mapa de suelos con hidrología sobrepintada
                       (ríos azul profundo, lagos azul claro).
- mundo_alturas.png:    mapa de alturas en escala de grises: negro = lo
                       más bajo (fondo marino), blanco = lo más elevado.

La generación SIEMPRE devuelve (suelos, hidrologia, alturas).
"""

from __future__ import annotations

from pathlib import Path

from Config import settings
from Services.Mundo.generacion_suelos import (
    generar_mapa_suelos,
)
from Services.Mundo.render_suelos import (
    guardar_png,
    guardar_png_alturas,
    guardar_png_lagos,
    guardar_png_rios,
)

# Lado de los cuadrados de la rejilla discontinua (en CELDAS), alineada
# con la esquina inferior izquierda. 0 = sin rejilla.
LADO_CUADRICULA = settings.LADO_CUADRICULA

# Preset del mundo. Los campos que no se fijan usan los defaults; seed,
# ancho y alto se toman de Config.settings si no se tocan aquí.
PARAMETROS_MUNDO = settings.PARAMETROS_MUNDO


def verificar_mares_interiores(suelos, ancho, alto):
    # Semilla: anillo INTERIOR (el borde es Suelo_Limite)
    frontera = set()
    for x in range(ancho):
        for y in (1, alto - 2):
            if suelos[(x, y)] == "Suelo_Oceano":
                frontera.add((x, y))
    for y in range(alto):
        for x in (1, ancho - 2):
            if suelos[(x, y)] == "Suelo_Oceano":
                frontera.add((x, y))

    mar_principal = set(frontera)
    pendientes = list(frontera)
    while pendientes:
        cx, cy = pendientes.pop()
        for nx, ny in (
            (cx - 1, cy),
            (cx + 1, cy),
            (cx, cy - 1),
            (cx, cy + 1),
            (cx - 1, cy - 1),
            (cx + 1, cy - 1),
            (cx - 1, cy + 1),
            (cx + 1, cy + 1),
        ):
            if (nx, ny) in mar_principal or not (0 <= nx < ancho and 0 <= ny < alto):
                continue
            if suelos[(nx, ny)] == "Suelo_Oceano":
                mar_principal.add((nx, ny))
                pendientes.append((nx, ny))

    interiores = [
        (x, y)
        for (x, y), s in suelos.items()
        if s == "Suelo_Oceano" and (x, y) not in mar_principal
    ]
    print(f"Celdas de mar principal: {len(mar_principal)}")
    print(
        f"AVISO: {len(interiores)} celdas de océano interior SIN tratar"
        if interiores
        else "OK: no hay mares interiores"
    )
    return interiores


def main() -> int:
    import Config.settings as config

    print(
        f"Generando mundo {config.GRID_WIDTH}x{config.GRID_HEIGHT} "
        f"(seed {config.SEMILLA_MUNDO})..."
    )
    suelos, hidrologia, alturas, red = generar_mapa_suelos(
        parametros=PARAMETROS_MUNDO,
        verbose=True,
    )

    verificar_mares_interiores(suelos, config.GRID_HEIGHT, config.GRID_WIDTH)

    ancho, alto = config.GRID_WIDTH, config.GRID_HEIGHT
    # Salidas en el directorio SalidaMapas/ (relativo a donde se ejecute).
    salida = Path(
        f"SalidaMapas/{config.SEMILLA_MUNDO}/mundo_suelos_{config.SEMILLA_MUNDO}.png"
    )
    escala = max(1, 1200 // max(ancho, alto))  # imagen ~1200 px de lado
    escala = 1

    # 1) Mapa de suelos con hidrología.
    print(f"Renderizando suelos ({escala} px/casilla)...")
    conteo = guardar_png(
        suelos, ancho, alto, escala, salida, hidrologia, LADO_CUADRICULA
    )

    total = sum(conteo.values())
    print(f"Escrito: {salida} ({ancho * escala}x{alto * escala} px)")
    print("Distribución de suelos:")
    for suelo in sorted(conteo, key=conteo.get, reverse=True):
        pct = 100.0 * conteo[suelo] / total
        print(f"  {suelo:<14} {conteo[suelo]:>8}  {pct:5.1f} %")

    # 2) Mapa de alturas (grises: negro = bajo, blanco = alto).
    salida_alt = Path(
        f"SalidaMapas/{config.SEMILLA_MUNDO}/mundo_alturas_{config.SEMILLA_MUNDO}.png"
    )
    print(f"Renderizando alturas ({escala} px/casilla)...")
    mn, mx = guardar_png_alturas(
        alturas, ancho, alto, escala, salida_alt, LADO_CUADRICULA
    )
    print(f"Escrito: {salida_alt} (negro = {mn} m, blanco = {mx} m)")

    # 3) Mapa de ríos: color = dirección de flujo (cardinales + mezclas).
    salida_rios = Path(
        f"SalidaMapas/{config.SEMILLA_MUNDO}/mundo_rios_{config.SEMILLA_MUNDO}.png"
    )
    print(f"Renderizando ríos ({escala} px/casilla)...")
    pintadas = guardar_png_rios(
        hidrologia, ancho, alto, escala, salida_rios, LADO_CUADRICULA
    )
    print(f"Escrito: {salida_rios} ({pintadas} casillas de río)")

    # 4) Batimetría de lagos: negro = fondo (última gota al secarse),
    #    blanco = orilla de desborde. Escala independiente por lago.
    salida_lagos = Path(
        f"SalidaMapas/{config.SEMILLA_MUNDO}/mundo_lagos_{config.SEMILLA_MUNDO}.png"
    )
    print(f"Renderizando lagos ({escala} px/casilla)...")
    lagos_px = guardar_png_lagos(
        hidrologia, ancho, alto, escala, salida_lagos, LADO_CUADRICULA
    )
    print(f"Escrito: {salida_lagos} ({lagos_px} casillas de lago)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
