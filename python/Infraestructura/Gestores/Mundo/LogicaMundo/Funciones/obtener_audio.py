# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/obtener_audio.py


from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "ObtenerAudio"


async def handle(logica, request, context):
    ok, error, audio = await logica.obtener_audio(request.id_sonido)
    return pb.ObtenerAudioResponse(ok=ok, error=error, audio=audio)
