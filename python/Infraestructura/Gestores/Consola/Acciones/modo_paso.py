# Infraestructura/Gestores/Consola/Acciones/modo_paso.py
from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Consola.cuestionario import CampoCuestionario, parse_bool
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)


async def _handler(comunicaciones: ComunicacionesLocal, activar: bool) -> str:
    ok, error = await comunicaciones.set_step_mode(activar)
    estado = "activado" if activar else "desactivado"
    return f"Modo paso {estado}." if ok else f"Error: {error}"


ACCION = AccionConsola(
    nombre="modo_paso",
    descripcion="Activa o desactiva el modo tick a tick.",
    campos=[
        CampoCuestionario(
            nombre="activar", prompt="Activar modo paso (s/n)", tipo=parse_bool
        )
    ],
    handler=_handler,
)