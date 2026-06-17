# Gestores/Mundo/Gestor_Mundo/funciones/get_global_state.py
import json
from Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo

NAME = "GetGlobalState"

async def handle(gestor: GestorMundo, request, context) -> pb.GetGlobalStateResponse:
    elementos = [
        pb.GlobalElementState(
            name=elem.__class__.__name__,
            state=json.dumps(elem.to_snapshot()).encode(),
        )
        for elem in gestor._elementos_globales
    ]
    return pb.GetGlobalStateResponse(
        ok=True,
        tick_id=gestor._tick_id,
        snapshot_id=gestor._snapshot_id,
        elementos_globales=elementos,
    )