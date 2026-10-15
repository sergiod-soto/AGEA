# Core/Entities/Mundo/Atmosfera/sistema_atmosferico.py

"""
Orquestador del tick atmosférico de UNA celda. VERSIÓN FINAL de esta
ronda de diseño -- sustituye cualquier versión anterior (la que usaba
Estacion/progreso_estacional para la radiación ya no aplica).

Con Temperatura, Presion, Viento, Humedad_Absoluta y Humedad_Relativa
llevando su propia lógica de cálculo (ver
Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/...), este módulo
se queda con dos responsabilidades:

  1) calcular la radiación entrante del tick (ver calcular_radiacion), y
  2) llamar a actualizar() de cada sistema de la celda en el ORDEN
     acordado: temperatura -> presion -> viento -> humedad_absoluta ->
     humedad_relativa.

Modelo de radiación (decisión final): en vez de un multiplicador
estacional discreto por Estacion/Verano/Invierno..., se usa la fórmula
astronómica estándar del ángulo cenital solar al mediodía:

    factor = cos(latitud - declinación_solar(progreso_anual))

Esto da, sin código especial: poca variación estacional en el ecuador,
variación extrema cerca de los polos, y estaciones invertidas en el
hemisferio sur de forma automática (declinación positiva + latitud
negativa = factor bajo = invierno austral, sin ningún if).

La clasificación categórica de Estacion (Verano/Invierno/Primavera/Otono
como ETIQUETA para otros sistemas, no para radiación) sigue existiendo
por separado -- ver Core/Entities/.../Marcadores/Temporales/Estaciones/.

Convención de coordenadas (decisión tomada): el ecuador está en
GRID_HEIGHT/2, no en y=0 literal -- así encaja con que Gestor_Mundo hoy
solo crea sectores para coordenadas no negativas (0..GRID_WIDTH,
0..GRID_HEIGHT). Un polo queda en y=0, el otro en y=GRID_HEIGHT.

Modelo "híbrido" (decisión tomada, no inventada aquí):
  - DENTRO de una misma celda, el cálculo es secuencial: cada paso ve
    ya el valor actualizado de los pasos anteriores de ESTA celda en
    ESTE tick.
  - Los VECINOS (EstadoVecino) que usa cada paso son siempre del TICK
    ANTERIOR -- llegan como snapshot congelado tipo "ghost zone" (mismo
    patrón que Gestor_Mundo usa con los Sectores para terreno). Esto es
    obligatorio: los vecinos pueden vivir en otro Sector calculando en
    paralelo.

Adyacencia: 8 vecinos por celda (decisión tomada). Este módulo no
construye esa lista -- la construye Sector._avanzar_atmosfera /
Sector._vecinos_atmosfera, mezclando celdas propias y ghost zone.

IMPORTANTE: avanzar_celda() MUTA la celda que recibe (cada
Sistema_Atmosferico guarda su propio estado y actualizar() lo modifica
in-place) -- no devuelve ningún patch. Las cachés de Celda_Atmosfera no
viajan por proto: se reconstruyen desde el terreno en cada load_state del Sector.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from vectors import Vector2

from Config.parametros_simulacion import INCLINACION_AXIAL_GRADOS, RADIACION_MAXIMA
from Config.settings import ATMOSFERA_ESCALA, GRID_HEIGHT
from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera


@dataclass(frozen=True)
class EstadoVecino:
    """
    Copia de solo lectura del estado de una celda de atmósfera vecina
    (una "ghost cell"), tomada del TICK ANTERIOR.

    direccion: vector unitario (x, y) que apunta DESDE la celda que se
    está calculando HACIA este vecino. Lo calcula quien construya la
    lista (Sector._vecinos_atmosfera); este módulo no asume nada sobre
    la topología de la malla de atmósfera, solo usa el vector que le
    dan.
    """

    temperatura: float
    presion: float
    humedad_absoluta: float
    direccion: Vector2
    bloqueo_total_viento: bool = False


def _latitud_radianes(y: int) -> float:
    """
    Convierte la coordenada y del mundo en una latitud aproximada.
    Convención (decisión tomada): el ecuador está en GRID_HEIGHT/2. Un
    polo queda en y=0 (latitud +90°), el otro en y=GRID_HEIGHT (latitud
    -90°); qué lado es "norte" es arbitrario, solo debe ser consistente
    en todo el sistema.
    """
    ecuador_y = GRID_HEIGHT / 2
    distancia_al_polo = GRID_HEIGHT / 2
    distancia_ecuador = ecuador_y - y  # positivo hacia y=0
    latitud_grados = max(-1.0, min(1.0, distancia_ecuador / distancia_al_polo)) * 90.0
    return math.radians(latitud_grados)


def _factor_estacional_y_latitud(y: int, progreso_anual: float) -> float:
    """
    factor = cos(latitud - declinación_solar). declinación_solar oscila
    entre ±INCLINACION_AXIAL_GRADOS a lo largo del año.

    progreso_anual=0 se toma como el equinoccio (declinación 0);
    progreso_anual=0.25 -> declinación máxima ("verano" del hemisferio
    donde y está cerca de 0, según _latitud_radianes). Es una
    convención de FASE, ajustable sin tocar la forma de la curva.

    max(0, ...) recorta a 0 los casos de "noche polar" (cos negativo,
    sol por debajo del horizonte incluso al mediodía).
    """
    declinacion = math.radians(INCLINACION_AXIAL_GRADOS) * math.sin(
        2 * math.pi * progreso_anual
    )
    latitud = _latitud_radianes(y)
    return max(0.0, math.cos(latitud - declinacion))


def calcular_radiacion(
    y: int, progreso_solar: float, progreso_anual: float, factor_nubes: float = 1.0
) -> float:
    """
    Radiación de un tick = curva día/noche x factor estacional+latitud x
    nubes. factor_nubes queda en 1.0 (neutro) hasta que exista un
    sistema de nubes real -- la sombra de árboles se podrá aplicar
    igual, como otro factor más, cuando exista.
    """
    base_diaria = max(0.0, math.sin(2 * math.pi * progreso_solar))
    factor_estacional = _factor_estacional_y_latitud(y, progreso_anual)
    return RADIACION_MAXIMA * base_diaria * factor_estacional * factor_nubes


def avanzar_celda(
    celda: Celda_Atmosfera,
    progreso_solar: float,
    progreso_anual: float,
    vecinos: list[EstadoVecino],
) -> None:
    """
    Avanza `celda` un tick. Muta `celda` in-place.

    celda.posicion está en espacio de atmósfera (bloques de
    ATMOSFERA_ESCALA celdas de terreno) -- para la latitud se usa el
    centro del bloque en coordenadas de terreno, no el índice de
    bloque (error despreciable salvo que ATMOSFERA_ESCALA sea enorme
    frente al tamaño del mapa).
    """
    _, y_bloque = celda.posicion
    y_terreno = y_bloque * ATMOSFERA_ESCALA + ATMOSFERA_ESCALA // 2

    celda.radiacion = calcular_radiacion(y_terreno, progreso_solar, progreso_anual)

    celda.temperatura.actualizar(
        celda.tasa_conversion_radiacion_calor,
        celda.inercia_termica,
        celda.radiacion,
        vecinos,
    )
    celda.presion.actualizar(celda.temperatura.valor, vecinos)
    celda.viento.actualizar(celda, celda.presion.valor, vecinos)
    celda.humedad_absoluta.actualizar(celda.temperatura.valor, vecinos)
    celda.humedad_relativa.actualizar(
        celda.humedad_absoluta.valor, celda.temperatura.valor
    )
