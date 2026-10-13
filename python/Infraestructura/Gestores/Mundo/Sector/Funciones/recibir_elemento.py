# Infraestructura/Gestores/Mundo/Sector/Funciones/recibir_elemento.py
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as pb,
)
from Infraestructura.Gestores.Mundo.Sector.sector import Sector

logger = logging.getLogger(__name__)
NAME = "RecibirElemento"


async def handle(sector: Sector, request, context) -> pb.RecibirElementoResponse:
    """
    Paso 1 del movimiento entre sectores: "¿puedes alojar este elemento?" y,
    si cabe, lo aloja en el mismo acto (un solo RPC; el Gestor procesa los
    movimientos en serie, así que entre preguntar y crear no puede ocurrir
    nada).

    Dos tipos de resultado, que el Gestor distingue:
      - ok=True, aceptado=False -> RECHAZO normal (slot ocupado...). No es un
        error: el elemento se queda en su sector de origen.
      - ok=False                -> fallo real (excepción). El Gestor lo trata
        como fatal: no se sabe en qué estado quedó este sector.
    """
    try:
        aceptado, motivo, celda = sector.recibir_elemento(request.movimiento)
        if not aceptado:
            return pb.RecibirElementoResponse(
                ok=True, aceptado=False, motivo_rechazo=motivo
            )
        return pb.RecibirElementoResponse(ok=True, aceptado=True, celda_destino=celda)
    except Exception as e:
        logger.exception("Error en RecibirElemento")
        return pb.RecibirElementoResponse(ok=False, error=str(e))
