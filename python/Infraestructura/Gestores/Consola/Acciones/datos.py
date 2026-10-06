# Infraestructura/Gestores/Consola/Acciones/datos.py
"""
datos.py — Acción de consola "datos": punto único para consultar
información del mundo en modo lectura.

Diseño: un diccionario SUBCOMANDOS mapea el tipo de dato elegido (ej.
"zona", "bots") a una función que define SU PROPIO cuestionario
(lista de CampoCuestionario) y hace la consulta. Añadir una consulta
nueva es:

    1. Escribir una función  async def _datos_xxx(comunicaciones) -> str
       que declara sus propios campos y llama a ejecutar_cuestionario.
    2. Añadirla a SUBCOMANDOS.

Sin tocar el dispatcher, sin tocar accion_consola.py, sin tocar el
.proto -- igual que ComandosConsola/registry_consola.py hace para los
comandos de escritura hacia Gestor_Mundo.

Flujo en consola:
    > datos
    ¿Qué datos? Disponibles:
    - Zona
    - Bots
    : zona
    Coordenada esquina izquierda (ej: 0,0):
    Coordenada esquina derecha (ej: 5,5):
    Comportamientos a incluir (opcional, Enter para omitir):
"""

from __future__ import annotations

from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Consola.cuestionario import (
    CampoCuestionario,
    ejecutar_cuestionario,
    parse_posicion,
)
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)

# Las consultas de datos son siempre para MOSTRAR algo por consola,
# nunca para guardar estado -- por eso van fijas en modo "representacion"
# (frente a "profundidad", que usan los guardados/snapshots y que
# incluye más detalle, ej. un elemento sonoro expone solo el id del
# sonido en "representacion" pero el array de intensidades/frecuencias
# en "profundidad"). No es un parámetro que la consola deba preguntar.
MODO_CONSOLA = "representacion"


def parse_lista_comportamientos(texto: str) -> list[str]:
    """'Peso,Rastreable' -> ['Peso', 'Rastreable']. Cadena vacía -> []."""
    return [c.strip() for c in texto.split(",") if c.strip()]


async def _datos_zona(comunicaciones: ComunicacionesLocal) -> str:
    """
    'zona' -> pide las dos esquinas y los comportamientos a incluir,
    cada uno como campo propio de cuestionario, y consulta esa región
    vía LogicaMundoService.ConsultarRepresentacion (modo="representacion").
    """
    campos = [
        CampoCuestionario(
            nombre="min_pos",
            prompt="Coordenada esquina izquierda (ej: 0,0)",
            tipo=parse_posicion,
        ),
        CampoCuestionario(
            nombre="max_pos",
            prompt="Coordenada esquina derecha (ej: 5,5)",
            tipo=parse_posicion,
        ),
        CampoCuestionario(
            nombre="incluir",
            prompt="Comportamientos a incluir (ej: Peso,Rastreable)",
            tipo=parse_lista_comportamientos,
            opcional=True,
            valor_por_defecto=[],
        ),
    ]
    valores = await ejecutar_cuestionario(campos)

    resp = await comunicaciones.consultar_representacion(
        min_pos=valores["min_pos"],
        max_pos=valores["max_pos"],
        incluir=valores["incluir"],
        modo=MODO_CONSOLA,
    )
    if not resp.ok:
        return f"Error consultando zona: {resp.error}"
    return (
        f"Zona {valores['min_pos']} - {valores['max_pos']} "
        f"(incluir={valores['incluir'] or '[]'}):\n{resp.datos!r}"
    )


async def _datos_bots(comunicaciones: ComunicacionesLocal) -> str:
    """
    'bots' -> número de bots vivos, sumando el 'current_load' de cada
    hipervisor (GestorBotsService.ListHypervisors -> HypervisorList).
    Sin campos propios: no necesita preguntar nada más.

    Asunción: 'current_load' en HypervisorInfo (common.proto) es el
    número de bots asignados actualmente a ese hipervisor, frente a
    'capacity' que es el máximo. Solo se cuentan hipervisores 'online'
    -- uno caído no debería sumar bots "activos" aunque su último
    current_load conocido sea > 0.
    """
    resp = await comunicaciones.list_hypervisors()

    online = [h for h in resp.hypervisors if h.online]
    total_bots = sum(h.current_load for h in online)
    total_capacidad = sum(h.capacity for h in online)

    return (
        f"Bots activos: {total_bots}/{total_capacidad} "
        f"(en {len(online)}/{len(resp.hypervisors)} hipervisores online)"
    )


# Registro: nombre del tipo de dato (en minúsculas) -> función que lo resuelve.
# Añadir una consulta nueva = escribir la función + una línea aquí + una
# línea en el prompt de _parse_tipo_dato.
SUBCOMANDOS = {
    "zona": _datos_zona,
    "bots": _datos_bots,
}


def _parse_tipo_dato(texto: str) -> str:
    tipo = texto.strip().lower()
    if tipo not in SUBCOMANDOS:
        raise ValueError(
            f"'{texto}' no es una consulta conocida. "
            f"Disponibles: {', '.join(SUBCOMANDOS)}."
        )
    return tipo


async def _handler(comunicaciones: ComunicacionesLocal, tipo_dato: str) -> str:
    # tipo_dato ya viene validado por _parse_tipo_dato (ejecutar_cuestionario
    # reintenta hasta que sea una clave válida de SUBCOMANDOS).
    return await SUBCOMANDOS[tipo_dato](comunicaciones)


ACCION = AccionConsola(
    num = 3,
    nombre="datos",
    descripcion="Consulta información del mundo (zona, bots, ...).",
    campos=[
        CampoCuestionario(
            nombre="tipo_dato",
            prompt=("¿Qué datos? Disponibles:\n" "- Zona\n" "- Bots\n"),
            tipo=_parse_tipo_dato,
        )
    ],
    handler=_handler,
)
