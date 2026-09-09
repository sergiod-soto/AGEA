# Infraestructura/Gestores/Consola/Acciones/crear_elemento.py
"""
crear_elemento.py — Acción de consola para crear un elemento nuevo.

Solo pide el nombre de la clase como campo "fijo" del cuestionario
inicial (AccionConsola.campos) porque el RESTO de campos depende de
QUÉ clase se elija -- no se puede saber de antemano. Por eso el propio
handler, una vez conoce la clase, arma un segundo cuestionario dinámico
a partir de clase.campos_para_creacion() + CATALOGO_CAMPOS y lo
ejecuta él mismo.

La posición (pos) que se manda a construir_elemento() es la MISMA
'casilla' que se le pide al usuario como campo del elemento -- no se
pregunta dos veces: pedirla por separado arriesgaría que el operador
diera dos valores distintos y el elemento quedara mal indexado en el
mundo respecto a su propio atributo 'casilla'.
"""

import json

from Core.Entities.Elementos.registry import ELEMENTOS
from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Consola.catalogo_campos import CATALOGO_CAMPOS
from Infraestructura.Gestores.Consola.cuestionario import (
    CampoCuestionario,
    ejecutar_cuestionario,
    parse_nombre_clase,
)
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)


async def _handler(comunicaciones: ComunicacionesLocal, nombre_clase: str) -> str:
    clase = ELEMENTOS[nombre_clase]  # ya validado por parse_nombre_clase

    nombres_campos = clase.campos_para_creacion()
    campos_cuestionario = []
    for nombre in nombres_campos:
        campo = CATALOGO_CAMPOS.get(nombre)
        if campo is None:
            return (
                f"Error: '{nombre_clase}' necesita el campo '{nombre}' para "
                "crearse, pero no está dado de alta en catalogo_campos.py."
            )
        campos_cuestionario.append(campo)

    valores = await ejecutar_cuestionario(campos_cuestionario)

    if "casilla" not in valores:
        return (
            f"Error: '{nombre_clase}' no declara 'casilla' en "
            "campos_para_creacion() -- no se sabe dónde colocarlo en el mundo."
        )
    pos = valores["casilla"]

    campos_json = json.dumps(valores).encode()
    ok, error, id_elemento = await comunicaciones.construir_elemento(
        pos, nombre_clase, campos_json
    )
    if not ok:
        return f"Error: {error}"
    return f"'{nombre_clase}' creado con id {id_elemento} en {pos}."


ACCION = AccionConsola(
    nombre="crear_elemento",
    descripcion="Crea un elemento nuevo.",
    campos=[
        CampoCuestionario(
            nombre="nombre_clase",
            prompt="Tipo de elemento a crear",
            tipo=parse_nombre_clase,
        )
    ],
    handler=_handler,
)
