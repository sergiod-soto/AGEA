# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/get_snapshot_info.py
COMPONENTE = "GESTOR_MUNDO"
OPERACION = "GetSnapshotInfo"


async def handle(clientes, payload: bytes) -> bytes:
    resp = await clientes.gestor_mundo.get_snapshot_info()
    return resp.SerializeToString()
