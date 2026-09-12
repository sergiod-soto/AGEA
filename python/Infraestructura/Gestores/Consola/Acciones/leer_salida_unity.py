# Infraestructura/Gestores/Consola/Acciones/leer_salida_unity.py
"""
leer_salida_unity.py — Acción de consola "leer_salida_unity": muestra
la ActualizacionFoco que se le mandaría a Unity para el próximo tick.

Solo tiene sentido en modo_paso (si el reloj corre solo, "el próximo
tick" ya habría pasado antes de poder leerlo). No se comprueba el modo
paso con un getter aparte -- avanza_tick() ya rechaza el intento si
modo_paso está desactivado (ver GestorMundo.avanza_tick), así que
reusamos ese resultado en vez de duplicar el estado.

Flujo:
  1. Se lee el tick actual (para saber qué contar como "nuevo").
  2. Se pide avanzar un tick (avanza_tick) -- si modo_paso está
     desactivado, esto ya falla aquí y no se sigue.
  3. Se espera, con timeout, una ActualizacionFoco cuyo tick_actual
     sea mayor que el de antes de avanzar.
  4. Si no llega a tiempo, se informa "Sin foco" -- ver nota sobre
     esta simplificación en _TIMEOUT_SEGUNDOS.
"""

from __future__ import annotations

import asyncio

from Infraestructura.Gestores.Consola.accion_consola import AccionConsola
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)

# Margen sobre el polling de 50ms del FocoBroadcaster (ver vista_foco.py)
# más el tiempo de una tanda completa de fases de sectores -- 3s da
# sobra sin dejar el comando colgado si algo va mal de verdad.
_TIMEOUT_SEGUNDOS = 3.0


async def _handler(comunicaciones: ComunicacionesLocal) -> str:
    # 1. Tick de referencia, para distinguir "ya había una actualización
    # vieja en la cola" de "esto es del tick que acabamos de pedir".
    antes = await comunicaciones.obtener_elementos_globales()
    tick_antes = antes.tick_actual

    # 2. Pedir avanzar el tick -- esto YA falla aquí si modo_paso está
    # desactivado, sin necesidad de comprobarlo aparte.
    ok, error = await comunicaciones.avanza_tick()
    if not ok:
        return f"No se pudo avanzar tick: {error}"

    # 3. Esperar la próxima actualización de foco con tick > tick_antes.
    #
    # TODO: no hay forma de preguntar "¿hay foco fijado?" de forma
    # directa (FocoBroadcaster no lo expone vía RPC). Por eso un
    # timeout aquí se interpreta como "Sin foco", aunque en teoría
    # también podría deberse a que Logica_Mundo o algún sector estén
    # respondiendo anormalmente despacio. Si hace falta distinguir
    # ambos casos, habría que añadir un getter de estado al
    # FocoBroadcaster (ver vista_foco.py).
    try:
        async with asyncio.timeout(_TIMEOUT_SEGUNDOS):
            async for actualizacion in comunicaciones.suscribirse_foco():
                if actualizacion.tick_actual > tick_antes:
                    if not actualizacion.ok:
                        return f"Error en la actualización: {actualizacion.error}"
                    return (
                        f"Tick {actualizacion.tick_actual} — "
                        f"lo que se enviaría a Unity:\n"
                        f"representacion={actualizacion.representacion!r}\n"
                        f"elementos_globales={list(actualizacion.elementos_globales)}"
                    )
    except TimeoutError:
        return "Sin foco/timeout."

    # Inalcanzable en la práctica (el generador de suscribirse_foco solo
    # termina si el canal gRPC se cae, lo cual ya se propaga como
    # RuntimeError antes de llegar aquí) -- se deja como red de
    # seguridad para no devolver None si algún día cambia ese contrato.
    return "Sin foco/timeout."


ACCION = AccionConsola(
    nombre="leer_salida_unity",
    descripcion=(
        "Avanza un tick (requiere modo_paso activo) y muestra lo que "
        "se le enviaría a Unity en ese tick."
    ),
    campos=[],
    handler=_handler,
)
