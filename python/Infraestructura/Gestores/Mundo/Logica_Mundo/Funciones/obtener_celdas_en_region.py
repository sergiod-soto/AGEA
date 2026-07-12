# Infraestructura/Gestores/Mundo/Logica_Mundo/Funciones/obtener_celdas_en_region.py
"""
obtener_celdas_en_region.py — Implementación del RPC ObtenerCeldasEnRegion.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "ObtenerCeldasEnRegion"


async def handle(logica, request, context):
    excluir_min = (
        (request.excluir_min.x, request.excluir_min.y)
        if request.tiene_exclusion
        else None
    )
    excluir_max = (
        (request.excluir_max.x, request.excluir_max.y)
        if request.tiene_exclusion
        else None
    )

    # logica.obtener_celdas_en_region ya devuelve directamente una lista
    # de common_pb2.Cell (la traducción Celda→Cell ocurre dentro de
    # logica_mundo.py porque necesita self._elements/_lock).
    cells = await logica.obtener_celdas_en_region(
        min_pos=(request.min.x, request.min.y),
        max_pos=(request.max.x, request.max.y),
        excluir_min=excluir_min,
        excluir_max=excluir_max,
    )
    return pb.ObtenerCeldasEnRegionResponse(ok=True, error="", cells=cells)
