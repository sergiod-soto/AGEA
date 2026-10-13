# Infraestructura/Gestores/Mundo/Sector/Funciones/confirmar_salida.py
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as pb,
)
from Infraestructura.Gestores.Mundo.Sector.sector import Sector

logger = logging.getLogger(__name__)
NAME = "ConfirmarSalida"


async def handle(sector: Sector, request, context) -> pb.ConfirmarSalidaResponse:
    """
    Paso 2 del movimiento entre sectores: el destino ya aceptó el elemento, así
    que el sector ORIGEN lo elimina de su copia. Devuelve la celda de origen ya
    sin él, para que el Gestor se la pase a Logica_Mundo.

    Cualquier fallo (p. ej. el elemento ya no está en la celda) devuelve
    ok=False: el elemento estaría duplicado o perdido, y el Gestor lo trata
    como fatal.
    """
    try:
        celda = sector.confirmar_salida(
            request.id_elemento, (request.pos_origen.x, request.pos_origen.y)
        )
        return pb.ConfirmarSalidaResponse(ok=True, celda_origen=celda)
    except Exception as e:
        logger.exception("Error en ConfirmarSalida")
        return pb.ConfirmarSalidaResponse(ok=False, error=str(e))
