# Infraestructura/Gestores/Consola/Acciones/pausar.py
from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)


async def _handler(comunicaciones: ComunicacionesLocal) -> str:
    ok, error = await comunicaciones.pause()
    return "Mundo pausado." if ok else f"Error al pausar: {error}"


ACCION = AccionConsola(
    nombre="pausar",
    descripcion="Congela todo el sistema (sectores + bots).",
    handler=_handler,
)
