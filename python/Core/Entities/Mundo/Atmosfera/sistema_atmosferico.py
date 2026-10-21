# Core/Entities/Mundo/Atmosfera/sistema_atmosferico.py

"""
Orquestador del tick atmosférico de UNA celda.

Con Temperatura, Presion, Viento, Humedad_Absoluta y Humedad_Relativa
llevando su propia lógica de cálculo (ver
Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/...), este módulo
se queda con dos responsabilidades:

  1) calcular la radiación entrante del tick (ver calcular_radiacion), y
  2) llamar a actualizar() de cada sistema de la celda en el ORDEN
     acordado: temperatura -> presion -> viento -> humedad_absoluta ->
     nube -> condensación -> lluvia -> humedad_relativa. La condensación es la única
     fase que toca varias magnitudes a la vez (vapor, nube, temperatura del
     aire) y va DESPUÉS del transporte, para que ninguna celda termine el tick
     sobresaturada.

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

Adyacencia: 4 vecinos cardinales por celda (decisión tomada); los bordes del
mundo son cerrados. Este módulo no construye esa lista -- la construye
Sector._vecinos_atmosfera, mezclando celdas propias y ghost zone.

IMPORTANTE: avanzar_celda() MUTA la celda que recibe (cada
Sistema_Atmosferico guarda su propio estado y actualizar() lo modifica
in-place) -- no devuelve ningún patch. Las cachés de Celda_Atmosfera no
viajan por proto: se reconstruyen desde el terreno en cada load_state del Sector.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from vectors import Vector2

from Config.parametros_simulacion import (
    ALTURA_CAPA_AIRE,
    CALENTAMIENTO_POR_CONDENSACION,
    INCLINACION_AXIAL_GRADOS,
    NUBE_CRITICA,
    OPACIDAD_MASICA_NUBE,
    RADIACION_MAXIMA,
    SEGUNDOS_SIMULADOS_TICK,
    TAU_LLUVIA,
)
from Config.settings import ATMOSFERA_ESCALA, GRID_HEIGHT
from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera
from Core.Fisica.termodinamica import ajuste_saturacion, autoconversion


@dataclass(frozen=True, kw_only=True)
class EstadoCelda:
    """
    Lo que un vecino necesita saber de una celda: copia INMUTABLE (floats) del
    estado del TICK ANTERIOR. Única definición de "qué se congela": una
    magnitud nueva se añade aquí y en las dos fábricas (desde_celda y
    celda_atmosfera_proto.estado_desde_proto), sin tuplas posicionales que
    puedan descolocarse en silencio.

    temperatura = la del AIRE (K). El viento va como componentes (m/s), que es
    lo que necesita la advección.
    """

    temperatura: float
    presion: float
    humedad_absoluta: float
    nube: float = 0.0
    viento_x: float = 0.0
    viento_y: float = 0.0

    @classmethod
    def desde_celda(cls, celda: Celda_Atmosfera) -> "EstadoCelda":
        return cls(
            temperatura=celda.temperatura.valor,
            presion=celda.presion.valor,
            humedad_absoluta=celda.humedad_absoluta.valor,
            nube=celda.nube.valor,
            viento_x=celda.viento.direccion.x * celda.viento.intensidad,
            viento_y=celda.viento.direccion.y * celda.viento.intensidad,
        )


@dataclass(frozen=True, kw_only=True)
class EstadoVecino(EstadoCelda):
    """
    EstadoCelda de una celda vecina más lo que depende de la celda que se
    calcula.

    direccion: vector unitario CARDINAL (±1,0)/(0,±1) que apunta DESDE la celda
    que se calcula HACIA este vecino. Lo pone Sector._vecinos_atmosfera.
    """

    direccion: Vector2
    bloqueo_total_viento: bool = False

    @classmethod
    def desde_estado(
        cls, estado: EstadoCelda, direccion: Vector2, bloqueo_total_viento: bool
    ) -> "EstadoVecino":
        # asdict copia los campos de EstadoCelda (todos floats).
        return cls(
            **asdict(estado),
            direccion=direccion,
            bloqueo_total_viento=bloqueo_total_viento,
        )


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
    factor = cos(latitud - declinación_solar): coseno del ángulo cenital
    al mediodía. La declinación oscila entre ±INCLINACION_AXIAL_GRADOS.

    FASE: progreso_anual = 0 es el inicio de Invierno, que coincide con el
    solsticio de invierno del hemisferio de y cercano a 0 (el de latitud
    positiva en _latitud_radianes). Por eso la declinación es -cos(...):
      0.00 -> -23.44° (solsticio de invierno)
      0.25 ->   0°    (equinoccio, empieza Primavera)
      0.50 -> +23.44° (solsticio de verano, empieza Verano)
      0.75 ->   0°    (equinoccio, empieza Otoño)
    Así coincide con el ciclo de Estaciones (4 pasos de 3 meses desde 0).
    El hemisferio opuesto queda invertido sin ningún if, porque su latitud
    es negativa.

    max(0, ...) recorta a 0 la noche polar (cos negativo: el sol queda por
    debajo del horizonte incluso al mediodía).
    """
    declinacion = -math.radians(INCLINACION_AXIAL_GRADOS) * math.cos(
        2 * math.pi * progreso_anual
    )
    latitud = _latitud_radianes(y)
    return max(0.0, math.cos(latitud - declinacion))


def calcular_radiacion(
    y: int, progreso_solar: float, progreso_anual: float, factor_nubes: float = 1.0
) -> float:
    """
    Radiación de un tick = curva día/noche x factor estacional+latitud x
    factor_nubes (transmitancia de la nube, ver _factor_nubes). La sombra de
    árboles se podrá aplicar igual, como otro factor más, cuando exista.
    """
    base_diaria = max(0.0, math.sin(2 * math.pi * progreso_solar))
    factor_estacional = _factor_estacional_y_latitud(y, progreso_anual)
    return RADIACION_MAXIMA * base_diaria * factor_estacional * factor_nubes


def _factor_nubes(nube: float) -> float:
    """
    Transmitancia de la celda, en (0, 1]: Beer-Lambert sobre el agua líquida de
    la columna (nube · ALTURA_CAPA_AIRE, kg/m²). Continua: sin nube vale 1 y
    baja suavemente al crecer, sin saltos de umbral. Una sola magnitud (la
    nube); la opacidad se deriva, no se guarda.
    """
    return math.exp(-OPACIDAD_MASICA_NUBE * nube * ALTURA_CAPA_AIRE)


def _condensar(celda: Celda_Atmosfera) -> None:
    """
    Aplica el cambio de fase de ajuste_saturacion (función pura):
    vapor + nube se conserva, y el calor latente va al AIRE de la celda
    (condensar lo calienta, evaporar la nube lo enfría). Se ejecuta tras el
    transporte, sobre el estado ya mezclado.
    """
    delta = ajuste_saturacion(
        celda.humedad_absoluta.valor, celda.nube.valor, celda.temperatura.valor
    )
    celda.humedad_absoluta.valor -= delta
    celda.nube.valor += delta
    celda.temperatura.valor += CALENTAMIENTO_POR_CONDENSACION * delta


def _precipitar(celda: Celda_Atmosfera) -> None:
    """
    Convierte parte de la nube en lluvia (autoconversión, función pura en
    termodinamica.autoconversion). Va tras _condensar, para precipitar sobre la
    nube ya formada este tick, y antes de humedad_relativa.

    - La nube baja lo convertido (kg/m³ de aire).
    - lluvia = lo convertido · ALTURA_CAPA_AIRE (kg/m² de celda). Se ASIGNA, no
      se suma: vale 0 en un tick sin lluvia.
    - Sin calor latente nuevo: el que se liberó al condensar ya está en el aire.
    - El vapor no se toca, así que no hay re-evaporación de la lluvia al caer.
    """
    llovido = autoconversion(
        celda.nube.valor, NUBE_CRITICA, TAU_LLUVIA, SEGUNDOS_SIMULADOS_TICK
    )
    celda.nube.valor -= llovido
    celda.lluvia.valor = llovido * ALTURA_CAPA_AIRE


def avanzar_celda(
    celda: Celda_Atmosfera,
    progreso_solar: float,
    progreso_anual: float,
    vecinos: list[EstadoVecino],
) -> None:
    """
    Avanza `celda` un tick. Muta `celda` in-place.

    celda.posicion está en espacio de atmósfera (bloques de ATMOSFERA_ESCALA
    celdas de terreno) -- para la latitud se usa el centro del bloque en
    coordenadas de terreno, no el índice de bloque.
    """
    _, y_bloque = celda.posicion
    y_terreno = y_bloque * ATMOSFERA_ESCALA + ATMOSFERA_ESCALA // 2

    # La nube que ve la radiación es la del TICK ANTERIOR (la celda aún no la
    # ha actualizado): retraso de 1 s, inocuo, y la realimentación es negativa
    # (más nube -> suelo más frío -> menos evaporación).
    celda.radiacion = calcular_radiacion(
        y_terreno,
        progreso_solar,
        progreso_anual,
        _factor_nubes(celda.nube.valor),
    )

    # Velocidad del viento al INICIO del tick (la del tick anterior). Se captura
    # antes de viento.actualizar porque la advección de las caras debe usar el
    # mismo valor que ven los vecinos: así el flujo de cada cara coincide en
    # sus dos lados y se conserva la cantidad. Humedad y nube, que se calculan
    # DESPUÉS del viento, también usan esta velocidad.
    velocidad = (
        celda.viento.direccion.x * celda.viento.intensidad,
        celda.viento.direccion.y * celda.viento.intensidad,
    )

    celda.temperatura.actualizar(
        celda.tasa_conversion_radiacion_calor,
        celda.inercia_termica,
        celda.radiacion,
        vecinos,
        velocidad,
        celda.bloqueo_total_viento,
    )
    celda.presion.actualizar(celda.temperatura.valor, vecinos)
    celda.viento.actualizar(celda, celda.presion.valor, vecinos)
    celda.humedad_absoluta.actualizar(vecinos, velocidad, celda.bloqueo_total_viento)
    celda.nube.actualizar(vecinos, velocidad, celda.bloqueo_total_viento)
    # Tras el transporte: cambio de fase y calor latente sobre el estado mezclado.
    _condensar(celda)
    # Autoconversión de la nube ya formada: la lluvia caída se publica en la
    # celda y los elementos la leen el tick siguiente.
    _precipitar(celda)
    celda.humedad_relativa.actualizar(
        celda.humedad_absoluta.valor, celda.temperatura.valor
    )
