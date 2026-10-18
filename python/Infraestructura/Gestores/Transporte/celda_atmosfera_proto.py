# Infraestructura/Gestores/Transporte/celda_atmosfera_proto.py

"""
Conversión entre Celda_Atmosfera (Core) y AtmosphereCell (proto).

Antes estaba repetida en Sector (CeldaAtmosferaStore) y en LogicaMundo
(a_proto, y la copia de estado de actualizar_celdas_atmosfera). Vive en
Infraestructura/Transporte y no en Core: Core no debe depender de los protos.

Qué viaja y qué no:
  - ESTADO SIMULADO (radiacion, temperatura, presion, viento, humedades):
    aplicar_estado_simulado() lo copia a una celda, nueva o existente.
  - TERRENO ESPEJADO (resistencia_viento, bloqueo_total_viento): solo lo
    copia aplicar_espejo_terreno(). Lo calcula el Sector desde sus cachés y
    Logica lo espeja sin cachés propias (decisión 1-A). El Sector, en cambio,
    NO lo restaura del proto: lo reconstruye desde el terreno en load_state.
  - Las cachés de Suelo (tasa, inercia) no viajan nunca.

Para añadir un campo nuevo al proto, solo hay que tocar este módulo.
"""

from vectors import Vector2

from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb


def _vector_a_proto(v: Vector2):
    return common_pb.Vector2(x=v.x, y=v.y)


def _vector_desde_proto(v) -> Vector2:
    return Vector2(v.x, v.y)


def a_proto(celda: Celda_Atmosfera):
    """Celda_Atmosfera -> AtmosphereCell, con todo lo que viaja (SI: K, Pa,
    m/s...). La posición sale de la propia celda (espacio de atmósfera)."""
    x, y = celda.posicion
    return common_pb.AtmosphereCell(
        pos=common_pb.Position(x=x, y=y),
        resistencia_viento=celda.resistencia_viento,
        bloqueo_total_viento=celda.bloqueo_total_viento,
        viento_objetivo=_vector_a_proto(celda.viento_objetivo),
        radiacion=celda.radiacion,
        temperatura=celda.temperatura.valor,
        presion=celda.presion.valor,
        viento_intensidad=celda.viento.intensidad,
        viento_direccion=_vector_a_proto(celda.viento.direccion),
        humedad_absoluta=celda.humedad_absoluta.valor,
        humedad_relativa=celda.humedad_relativa.valor,
        temperatura_suelo=celda.temperatura.valor_suelo,
    )


def aplicar_estado_simulado(cell, celda: Celda_Atmosfera) -> None:
    """Copia el estado simulado del proto sobre `celda` (in-place). Sirve para
    una celda recién construida y para una ya existente."""
    celda.radiacion = cell.radiacion
    celda.temperatura.valor = cell.temperatura
    celda.temperatura.valor_suelo = cell.temperatura_suelo
    celda.presion.valor = cell.presion
    celda.viento.intensidad = cell.viento_intensidad
    celda.viento.direccion = _vector_desde_proto(cell.viento_direccion)
    celda.humedad_absoluta.valor = cell.humedad_absoluta
    celda.humedad_relativa.valor = cell.humedad_relativa


def aplicar_espejo_terreno(cell, celda: Celda_Atmosfera) -> None:
    """Copia los dos campos de terreno que calcula el Sector. Solo para quien
    NO mantiene cachés (Logica). Con bloqueo total, resistencia_viento solo
    describe a los elementos no bloqueantes: se mira siempre el bloqueo antes."""
    celda.resistencia_viento = cell.resistencia_viento
    celda.bloqueo_total_viento = cell.bloqueo_total_viento


def desde_proto(cell) -> Celda_Atmosfera:
    """AtmosphereCell -> Celda_Atmosfera NUEVA. Se construye con los valores
    por defecto y se sobrescribe el estado simulado (si no, se perdería el
    estado real). Las cachés quedan vacías: las rellena quien corresponda."""
    celda = Celda_Atmosfera(
        posicion=(cell.pos.x, cell.pos.y),
        viento_objetivo=_vector_desde_proto(cell.viento_objetivo),
    )
    aplicar_estado_simulado(cell, celda)
    return celda
