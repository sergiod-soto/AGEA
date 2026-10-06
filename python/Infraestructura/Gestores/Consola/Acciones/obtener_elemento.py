# Infraestructura/Gestores/Consola/Acciones/obtener_elemento.py
"""
obtener_elemento.py — Pide, por id, los datos de un elemento del
mundo. Sin especificar nada más que el id, devuelve el modo
"representacion" (lo mismo que se le manda a Unity); se puede pedir
explícitamente "serializacion" para la info completa (como en un
snapshot).
"""

import json

from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Consola.cuestionario import CampoCuestionario
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)


def _parse_tipo_datos(texto: str) -> str:
    valor = texto.strip().lower()
    if valor not in ("representacion", "serializacion"):
        raise ValueError("usa 'representacion' o 'serializacion'.")
    return valor


def _parse_lista_campos(texto: str) -> list[str]:
    return [c.strip() for c in texto.split(",") if c.strip()]


async def _handler(
    comunicaciones: ComunicacionesLocal,
    id_elemento: int,
    tipo_datos: str,
    incluir: list[str],
) -> str:
    ok, error, datos = await comunicaciones.obtener_elemento(
        element_id=id_elemento, tipo_datos=tipo_datos, incluir=incluir
    )
    if not ok:
        return f"Error: {error}"
    return json.dumps(json.loads(datos.decode()), indent=2, ensure_ascii=False)


ACCION = AccionConsola(
    num = 6,
    nombre="id",
    descripcion="Muestra los datos de un elemento, buscado por su id.",
    campos=[
        CampoCuestionario(nombre="id_elemento", prompt="ID del elemento", tipo=int),
        CampoCuestionario(
            nombre="tipo_datos",
            prompt="Tipo de datos ('representacion'/'serializacion')",
            tipo=_parse_tipo_datos,
            opcional=True,
            valor_por_defecto="representacion",
        ),
        CampoCuestionario(
            nombre="incluir",
            prompt="Campos a incluir, separados por coma",
            tipo=_parse_lista_campos,
            opcional=True,
            valor_por_defecto=[],
        ),
    ],
    handler=_handler,
)
