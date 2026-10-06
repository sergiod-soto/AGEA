# Infraestructura/Gestores/Consola/Acciones/reanudar.py
from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)


async def _handler(comunicaciones: ComunicacionesLocal) -> str:
    ok, error = await comunicaciones.resume()
    return "Mundo reanudado." if ok else f"Error al reanudar: {error}"


ACCION = AccionConsola(
    num = 8,
    nombre="reanudar",
    descripcion="Reanuda el sistema tras un pausar.",
    handler=_handler,
)