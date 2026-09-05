# Infraestructura/Gestores/Consola/Acciones/tick_rate.py
from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Consola.cuestionario import CampoCuestionario
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)


async def _handler(comunicaciones: ComunicacionesLocal, ticks_per_second: int) -> str:
    ok, error = await comunicaciones.set_tick_rate(ticks_per_second)
    if not ok:
        return f"Error: {error}"
    return (
        "Cadencia fijada a sin límite."
        if ticks_per_second <= 0
        else f"Cadencia fijada a {ticks_per_second}/s."
    )


ACCION = AccionConsola(
    nombre="tick_rate",
    descripcion="Fija la cadencia de ticks por segundo (0 = sin límite).",
    campos=[
        CampoCuestionario(
            nombre="ticks_per_second", prompt="Ticks por segundo", tipo=int
        )
    ],
    handler=_handler,
)