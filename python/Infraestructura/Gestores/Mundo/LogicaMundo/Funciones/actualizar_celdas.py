# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/actualizar_celdas.py
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

logger = logging.getLogger(__name__)
NAME = "ActualizarCeldas"


async def handle(logica, request, context):
    """
    Aplica el resultado de un tick de Sector (celdas cambiadas + movimientos
    externos) y devuelve los movimientos RECHAZADOS, para que Gestor_Mundo no
    migre esos bots. Cada rechazado es un RechazoMovimiento del .proto:
    id_elemento, eliminado y pos_devuelta. Se pasan como dicts (protobuf los
    convierte), así no hace falta importar el tipo del mensaje.
    """
    try:
        rechazados = await logica.actualizar_celdas(
            list(request.changed_cells), list(request.movimientos_externos)
        )
        return pb.ActualizarCeldasResponse(
            ok=True,
            rechazados=[
                {
                    "id_elemento": eid,
                    # pos None = no cupo ni en destino ni en origen y se
                    # eliminó: no hay posición a la que devolverlo.
                    "eliminado": pos is None,
                    **(
                        {}
                        if pos is None
                        else {"pos_devuelta": {"x": pos[0], "y": pos[1]}}
                    ),
                }
                for eid, pos in rechazados.items()
            ],
        )
    except Exception as e:
        logger.exception("Error en ActualizarCeldas")
        return pb.ActualizarCeldasResponse(ok=False, error=str(e))