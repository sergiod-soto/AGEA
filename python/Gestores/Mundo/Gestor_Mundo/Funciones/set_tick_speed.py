# Gestores/Mundo/Gestor_Mundo/funciones/set_tick_speed.py
from Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo, SystemState

NAME = "SetTickSpeed"
MAX_FACTOR = 10.0

async def handle(gestor: GestorMundo, request, context) -> pb.SetTickSpeedResponse:
    factor = request.speed_factor
    if factor < 0:
        return pb.SetTickSpeedResponse(
            ok=False,
            error="speed_factor no puede ser negativo.",
            effective_factor=gestor._speed_factor,
        )
    if factor == 0.0:
        await gestor.freeze()
        gestor._speed_factor = 0.0
        return pb.SetTickSpeedResponse(ok=True, effective_factor=0.0)

    effective = min(factor, MAX_FACTOR)
    gestor._speed_factor = effective
    if gestor._state == SystemState.PAUSED:
        await gestor.resume()
    return pb.SetTickSpeedResponse(ok=True, effective_factor=effective)