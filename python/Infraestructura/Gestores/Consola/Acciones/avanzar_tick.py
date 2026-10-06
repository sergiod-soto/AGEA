# Infraestructura/Gestores/Consola/Acciones/avanzar_tick.py
from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)


async def _handler(comunicaciones: ComunicacionesLocal) -> str:
    ok, error = await comunicaciones.avanza_tick()
    return "Tick avanzado." if ok else f"Error: {error}"


ACCION = AccionConsola(
    num = 1,
    nombre="tick",
    descripcion="Avanza un tick del servidor (requiere modo_paso activado antes).",
    handler=_handler,
)