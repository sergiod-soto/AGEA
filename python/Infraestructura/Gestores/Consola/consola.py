# Infraestructura/Gestores/Consola/consola.py
"""
consola.py — Bucle interactivo de administración.

Corre en su propio hilo con su propio event loop (ver
bootstrap.py::ejecutar_modo_local), hablando con la MISMA instancia de
ComunicacionesLocal que usa el resto del stack local — nunca abre su
propio canal gRPC, ver docstring de ComunicacionesLocal ("único módulo
local con permiso para hablar con AWS").
"""

from __future__ import annotations

import asyncio
import logging

from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)
from Infraestructura.Gestores.Consola.cuestionario import ejecutar_cuestionario
from Infraestructura.Gestores.Consola.registry import ACCIONES

logger = logging.getLogger("consola")


def _mostrar_ayuda() -> None:
    print("\nComandos disponibles:")
    for nombre, accion in sorted(ACCIONES.items()):
        print(f"  {nombre:<15} {accion.descripcion}")
    print("  ayuda           Muestra este listado.")
    print("  salir           Cierra la consola (el resto del stack sigue corriendo).\n")


async def iniciar(comunicaciones: ComunicacionesLocal) -> None:
    print("=== Consola de administración ===")
    _mostrar_ayuda()

    while True:
        try:
            linea = await asyncio.to_thread(input, "> ")
        except EOFError:
            # Puede pasar si el proceso pierde stdin (ej. lanzado sin
            # terminal adjunto) — se sale limpiamente en vez de entrar
            # en un bucle de excepciones repetidas.
            logger.info("Consola: stdin cerrado, terminando.")
            return

        nombre = linea.strip()
        if not nombre:
            continue
        if nombre in ("salir", "exit", "quit"):
            print("Cerrando consola (el stack local sigue corriendo).")
            return
        if nombre in ("ayuda", "help", "?"):
            _mostrar_ayuda()
            continue

        accion = ACCIONES.get(nombre)
        if accion is None:
            print(
                f"Comando desconocido: '{nombre}'. Escribe 'ayuda' para ver la lista."
            )
            continue

        try:
            valores = await ejecutar_cuestionario(accion.campos)
            resultado = await accion.handler(comunicaciones, **valores)
            print(resultado)
        except Exception as exc:
            # Un fallo de un comando concreto (ej. gRPC caído) no debe
            # matar el bucle entero de la consola.
            logger.error("Error ejecutando '%s': %s", nombre, exc)
            print(f"Error ejecutando '{nombre}': {exc}")
