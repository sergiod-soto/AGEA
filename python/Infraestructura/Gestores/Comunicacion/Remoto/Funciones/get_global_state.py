# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/get_global_state.py
COMPONENTE = "GESTOR_MUNDO"
OPERACION = "GetGlobalState"


async def handle(clientes, payload: bytes) -> bytes:
    resp = await clientes.gestor_mundo.get_global_state()
    return resp.SerializeToString()
