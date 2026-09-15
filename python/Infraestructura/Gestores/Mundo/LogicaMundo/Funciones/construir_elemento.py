# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/construir_elemento.py
"""
construir_elemento.py — Implementación del RPC ConstruirElemento.

A diferencia de CrearElemento (que reensambla un elemento ya
construido en otro proceso, sin pasar por __init__ -- ver
LogicaMundo.crear_elemento), este RPC es la vía para que un elemento
empiece a existir por primera vez: 'campos' llega como JSON de valores
primitivos (recopilados por consola vía campos_para_creacion()), y es
LogicaMundo.construir_elemento() quien llama al constructor real de la
clase (ver Core.Entities.Elementos.registry.construir_elemento) y
asigna el id -- por eso 'campos' NO trae id_elemento, y por eso la
respuesta sí lo devuelve: quien llama lo necesita para poder
modificar/eliminar este elemento más adelante.
"""

import json
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

logger = logging.getLogger(__name__)
NAME = "ConstruirElemento"


async def handle(logica, request, context):
    pos = (request.pos.x, request.pos.y)
    try:
        campos = json.loads(request.campos.decode()) if request.campos else {}
    except json.JSONDecodeError as exc:
        logger.warning("ConstruirElemento: campos inválidos: %s", exc)
        return pb.ConstruirElementoResponse(
            ok=False, error=f"Campos inválidos: {exc}", id_elemento=0
        )

    ok, error, id_elemento = await logica.construir_elemento(
        pos, request.nombre_clase, campos
    )
    return pb.ConstruirElementoResponse(
        ok=ok,
        error=error,
        # uint64 del proto no acepta None ni numpy.uint64 directamente
        # en todos los bindings -- se normaliza a int plano.
        id_elemento=int(id_elemento) if id_elemento is not None else 0,
    )
