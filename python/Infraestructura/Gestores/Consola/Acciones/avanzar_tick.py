# Infraestructura/Gestores/Consola/Acciones/avanzar_tick.py
from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)


async def _handler(comunicaciones: ComunicacionesLocal) -> str:
    ok, error = await comunicaciones.avanza_tick()
    return "Tick avanzado." if ok else f"Error: {error}"


ACCION = AccionConsola(
    nombre="avanzar_tick",
    descripcion="Avanza exactamente un tick (requiere modo_paso activado antes).",
    handler=_handler,
)