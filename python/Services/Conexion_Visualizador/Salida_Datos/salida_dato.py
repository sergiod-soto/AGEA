# Services/Conexion_Visualizador/Salida_Datos/salida_dato.py

from Services.Conexion_Visualizador.Salida_Datos.Entidades.salida_bot import salida_bot_full

_HANDLERS: dict = {
    "bot": salida_bot_full,
}


def salida_dato(shared_data, entrada: dict) -> dict | None:
    entity = entrada.get("entity")
    handler = _HANDLERS.get(entity)

    if handler is None:
        print(f"[SALIDA_DATO] Entidad desconocida: {entity!r}")
        return None

    dato = handler(shared_data, entrada)
    if dato is None:
        return None

    return {"tipo": "dato", entity: dato}
