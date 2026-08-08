# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/obtener_audio.py


import json
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "ObtenerAudio"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.ObtenerAudioRequest()
    req.ParseFromString(payload)

    audio = await clientes.logica_mundo.obtener_audio(req.id_sonido)
    if audio is None:
        # LogicaMundoClient.obtener_audio ya devuelve None tanto si el id
        # no existe como si falla la llamada -- no se distingue aquí
        # porque el cliente ya logueó el motivo concreto.
        resp = pb.ObtenerAudioResponse(
            ok=False, error="Audio no encontrado.", audio=b""
        )
    else:
        resp = pb.ObtenerAudioResponse(
            ok=True, error="", audio=json.dumps(audio).encode()
        )
    return resp.SerializeToString()
