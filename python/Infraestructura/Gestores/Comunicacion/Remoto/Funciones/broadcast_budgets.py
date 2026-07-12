# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/broadcast_budgets.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as pb,
)

COMPONENTE = "GESTOR_BOTS"
OPERACION = "BroadcastBudgets"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.BroadcastBudgetsRequest()
    req.ParseFromString(payload)

    overrides = {entry.bot_id: entry.budget for entry in req.overrides}
    ok = await clientes.gestor_bots.broadcast_budgets(
        default_budget=req.default_budget, overrides=overrides
    )
    resp = common_pb2.Ack(ok=ok, error="" if ok else "broadcast_budgets falló")
    return resp.SerializeToString()
