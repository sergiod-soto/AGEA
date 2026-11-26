# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/obtener_datos_hidrograficos.py
import json
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

logger = logging.getLogger(__name__)
NAME = "ObtenerDatosHidrograficos"


async def handle(logica, request, context):
    try:
        red_dict = logica.obtener_red_hidrografica()
        alturas_dict = {
            f"{x},{y}": h for (x, y), h in logica.obtener_alturas().items()
        }
        hidro_dict = {
            f"{x},{y}": d for (x, y), d in logica.obtener_hidrologia().items()
        }

        return pb.ObtenerDatosHidrograficosResponse(
            ok=True,
            error="",
            red_json=json.dumps(red_dict).encode("utf-8"),
            alturas_json=json.dumps(alturas_dict).encode("utf-8"),
            hidrologia_json=json.dumps(hidro_dict).encode("utf-8"),
        )
    except Exception as e:
        logger.exception("Error en ObtenerDatosHidrograficos")
        return pb.ObtenerDatosHidrograficosResponse(
            ok=False,
            error=str(e),
            red_json=b"",
            alturas_json=b"",
            hidrologia_json=b"",
        )
