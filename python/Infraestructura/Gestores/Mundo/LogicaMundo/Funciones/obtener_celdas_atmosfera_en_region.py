# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/obtener_celdas_atmosfera_en_region.py
"""
obtener_celdas_atmosfera_en_region.py — Implementación del RPC
ObtenerCeldasAtmosferaEnRegion.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "ObtenerCeldasAtmosferaEnRegion"


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

    cells = await logica.obtener_celdas_atmosfera_en_region(
        min_pos=(request.min.x, request.min.y),
        max_pos=(request.max.x, request.max.y),
        excluir_min=excluir_min,
        excluir_max=excluir_max,
    )
    return pb.ObtenerCeldasAtmosferaEnRegionResponse(ok=True, error="", cells=cells)
