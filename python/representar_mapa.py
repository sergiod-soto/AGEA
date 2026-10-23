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

from Services.Mundo.generacion_suelos import (
    ParametrosGeneracion,
    generar_mapa_suelos,
)
from Services.Mundo.render_suelos import (
    guardar_png,
    guardar_png_alturas,
    guardar_png_lagos,
    guardar_png_rios,
)

# Preset del mundo. Los campos que no se fijan usan los defaults; seed,
# ancho y alto se toman de Config.settings si no se tocan aquí.
PARAMETROS_MUNDO = ParametrosGeneracion(
    ancho=3000,
    alto=3000,
    seed=42,
    # Orografía
    proporcion_agua=0.5,  # fracción del mapa bajo el nivel del mar
    proporcion_montana=0.95,  # cuantil de tierra donde empieza montaña
    proporcion_piedra=0.97,  # cumbres altas
    banda_grava=0.08,  # piedemonte: montaña - banda
    ganancia_relieve=2.2,  # contraste del ruido de elevación
    octavas_orografia=5,
    # Tamaño de "continente" con fragmentacion = 0 (en celdas).
    escala_orografia=200.0,
    # 0.0 = una única masa continental (Pangea); 1.0 = mar lleno de
    # islitas. Ajusta la FRECUENCIA del ruido de elevación: a mayor
    # fragmentación, features más pequeños y tierra más troceada.
    fragmentacion=0.4,
    # Costas: fracción del lado menor que cae hacia el océano de borde.
    borde_oceano=0.15,
    # Altura del mapa: la elevación normalizada (0..1) se convierte a
    # METROS con 0 = nivel del mar. La cota más alta del mapa (elev=1)
    # queda a altura_maxima_metros; el fondo marino queda en negativo.
    altura_maxima_metros=4500.0,
    # Clima
    penalizacion_altitud=1.2,  # cuánto enfría la altitud
    octavas_clima=3,
    escala_clima=150.0,
    # Ríos. Nacen SOLO en la frontera de las zonas de Suelo_Piedra y
    # bajan SIN LÍMITE de longitud: solo terminan en el mar o al unirse a
    # otro río/lago. En un callejón sin salida forman un lago que, si su
    # cuenca desborda, da nacimiento a un río nuevo (el desagüe).
    num_rios=20,
    # Ancho de río. Los ríos NO tienen todos el mismo ancho: se engordan
    # por ANILLOS a partir del cauce, y el número de anillos se sortea en
    # función de la longitud REAL trazada: un río corto casi nunca se
    # ensancha; uno largo es muy PROBABLE que lo sea, pero no seguro.
    # - ancho_max_rio: anillos máximos extra (ancho máx = 1 + anillo).
    # - longitud_ref_rio_ancho: longitud (celdas) a la que la probabilidad
    #   de ensancharse cada anillo llega a 1.0; antes crece linealmente.
    ancho_max_rio=3,
    longitud_ref_rio_ancho=400.0,
    # Sinuosidad: cuánto se permite desviarse del descenso más directo.
    # 0.0 = siempre al vecino más bajo (líneas rectas/quebradas). Mayor
    # valor = el río elige entre TODOS los vecinos que bajan, con un
    # sorteo sesgado por la pendiente: aparecen meandros. En unidades de
    # elevación: 0.02-0.05 ya da curvas naturales.
    sinuosidad_rio=0.03,
    # Tope de seguridad: cuántos lagos puede encadenar un mismo
    # manantial (río -> lago -> desagüe -> lago -> ...) antes de que la
    # cadena se dé por muerta. Con cuencas normales no se llega, pero un
    # terreno muy raro podría patinar.
    max_lagos_por_rio=99999,
    # Humedad: distancia máx. (celdas) al agua que sigue influyendo.
    alcance_humedad=12,
    bono_humedad_agua=0.35,
    # Cuotas de suelo: fracción de la TIERRA EMERGIDA que ocupa cada
    # bioma. Se cumplen por CANTILES + RANKING físico, así que son
    # exactas en cualquier seed y siguen siendo coherentes: el desierto
    # cae en lo más cálido y seco, el césped en lo más húmedo, el hielo
    # en los polos. Suelo_Tierra NO se configura: es el resto.
    proporcion_hielo=0.12,  # tundra polar + banquisa del mar
    proporcion_arena=0.10,  # desierto cálido y seco
    proporcion_cesped=0.30,  # praderas húmedas
    # Barro
    umbral_humedad_barro=0.55,
)


def main() -> int:
    import Config.settings as config

    print(
        # f"Generando mundo {config.GRID_WIDTH}x{config.GRID_HEIGHT} "
        f"Generando mundo {3000}x{3000}"
        f"(seed {config.SEMILLA_MUNDO})..."
    )
    suelos, hidrologia, alturas = generar_mapa_suelos(
        parametros=PARAMETROS_MUNDO,
        verbose=True,
    )

    # ancho, alto = config.GRID_WIDTH, config.GRID_HEIGHT
    ancho, alto = 3000, 3000
    salida = Path("SalidaMapas/mundo_suelos.png")
    escala = max(1, config.GRID_WIDTH // max(ancho, alto))  # imagen ~1200 px de lado
    escala = 1

    # 1) Mapa de suelos con hidrología.
    print(f"Renderizando suelos ({escala} px/casilla)...")
    conteo = guardar_png(suelos, ancho, alto, escala, salida, hidrologia)

    total = sum(conteo.values())
    print(f"Escrito: {salida} ({ancho * escala}x{alto * escala} px)")
    print("Distribución de suelos:")
    for suelo in sorted(conteo, key=conteo.get, reverse=True):
        pct = 100.0 * conteo[suelo] / total
        print(f"  {suelo:<14} {conteo[suelo]:>8}  {pct:5.1f} %")

    # 2) Mapa de alturas (grises: negro = bajo, blanco = alto).
    salida_alt = Path("SalidaMapas/mundo_alturas.png")
    print(f"Renderizando alturas ({escala} px/casilla)...")
    mn, mx = guardar_png_alturas(alturas, ancho, alto, escala, salida_alt)
    print(f"Escrito: {salida_alt} (negro = {mn} m, blanco = {mx} m)")

    # 3) Mapa de ríos: color = dirección de flujo (cardinales + mezclas).
    salida_rios = Path("SalidaMapas/mundo_rios.png")
    print(f"Renderizando ríos ({escala} px/casilla)...")
    pintadas = guardar_png_rios(hidrologia, ancho, alto, escala, salida_rios)
    print(f"Escrito: {salida_rios} ({pintadas} casillas de río)")

    # 4) Batimetría de lagos: negro = fondo (última gota al secarse),
    #    blanco = orilla de desborde. Escala independiente por lago.
    salida_lagos = Path("SalidaMapas/mundo_lagos.png")
    print(f"Renderizando lagos ({escala} px/casilla)...")
    lagos_px = guardar_png_lagos(hidrologia, ancho, alto, escala, salida_lagos)
    print(f"Escrito: {salida_lagos} ({lagos_px} casillas de lago)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
