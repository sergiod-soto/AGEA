# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/trigger_deep_save.py
COMPONENTE = "GESTOR_MUNDO"
OPERACION = "TriggerDeepSave"


async def handle(clientes, payload: bytes) -> bytes:
    # trigger_deep_save() ya devuelve el proto Response completo — se
    # reenvía sin reinterpretarlo (patrón opaco, igual que Cell).
    resp = await clientes.gestor_mundo.trigger_deep_save()
    return resp.SerializeToString()
