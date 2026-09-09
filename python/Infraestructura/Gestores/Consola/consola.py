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

from Core.Entities.Comportamiento.registry import COMPORTAMIENTOS
from Core.Entities.Elementos.registry import ELEMENTOS
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)
from Infraestructura.Gestores.Consola.cuestionario import ejecutar_cuestionario
from Infraestructura.Gestores.Consola.registry import ACCIONES

logger = logging.getLogger("consola")


def _buscar_clase_elemento(nombre: str):
    """
    Busca en ELEMENTOS sin distinguir mayúsculas -- las claves del
    registry son "Piedra", "Suelo_Arena"... pero teclear 'ayuda piedra'
    en minúsculas es lo natural desde consola.
    """
    nombre_lower = nombre.lower()
    for clave, clase in ELEMENTOS.items():
        if clave.lower() == nombre_lower:
            return clase
    return None


def _buscar_por_nombre(diccionario: dict, nombre: str):
    nombre_lower = nombre.lower()
    for clave, valor in diccionario.items():
        if clave.lower() == nombre_lower:
            return valor
    return None


def _mostrar_ayuda_elemento(clase) -> None:
    try:
        print(f"\n{clase.ayuda_creacion()}")
    except NotImplementedError as exc:
        print(f"\n{exc}")

    try:
        nombres = clase.campos_para_creacion()
    except NotImplementedError:
        print(
            "  (este tipo todavía no implementa campos_para_creacion(); "
            "no se puede crear desde consola)\n"
        )
        return

    if not nombres:
        print("  (sin campos preguntables)\n")
        return

    # print("Campos necesarios:")
    # for nombre_campo in nombres:
    #     comportamiento = clase._comportamiento_de_campo(nombre_campo)
    #     if comportamiento is None:
    #         print(
    #             f"  {nombre_campo}: (campo propio de {clase.__name__}, sin ayuda adicional)"
    #         )
    #         continue
    #     try:
    #         explicacion = comportamiento.ayuda_creacion()
    #     except NotImplementedError as exc:
    #         explicacion = str(exc)
    #     print(f"  {nombre_campo} ({comportamiento.__name__}): {explicacion}")
    print()


def _mostrar_ayuda_comportamiento(comportamiento) -> None:
    try:
        print(f"\n{comportamiento.ayuda_creacion()}")
    except NotImplementedError as exc:
        print(f"\n{exc}")
    # try:
    #     nombres = comportamiento.campos_para_creacion()
    # except NotImplementedError:
    #     nombres = None
    # if nombres:
    #     print(f"Campos: {', '.join(nombres)}")
    print()


def _mostrar_ayuda(argumento: str | None = None) -> None:
    if argumento is None:
        print("\nComandos disponibles:")
        for nombre, accion in sorted(ACCIONES.items()):
            print(f"  {nombre:<15} {accion.descripcion}")
        print(
            "  ayuda           Muestra este listado ('ayuda <comando|tipo|comportamiento>' para detalle)."
        )
        print(
            "  salir           Cierra la consola (el resto del stack sigue corriendo).\n"
        )
        return

    accion = ACCIONES.get(argumento)
    if accion is not None:
        print(f"\n{accion.nombre} — {accion.descripcion}")
        if accion.campos:
            print("Campos:")
            for campo in accion.campos:
                tipo_nombre = getattr(campo.tipo, "__name__", str(campo.tipo))
                sufijo = " (opcional)" if campo.opcional else ""
                print(f"  {campo.nombre} [{tipo_nombre}]{sufijo}: {campo.prompt}")
        print()
        return

    clase = _buscar_por_nombre(ELEMENTOS, argumento)
    if clase is not None:
        _mostrar_ayuda_elemento(clase)
        return

    comportamiento = _buscar_por_nombre(COMPORTAMIENTOS, argumento)
    if comportamiento is not None:
        _mostrar_ayuda_comportamiento(comportamiento)
        return

    print(
        f"\n'{argumento}' no es un comando, tipo de elemento ni comportamiento conocido.\n"
    )


async def iniciar(comunicaciones: ComunicacionesLocal) -> None:
    print("=== Consola de administración ===")
    _mostrar_ayuda()

    while True:
        try:
            linea = await asyncio.to_thread(input, "> ")
        except EOFError:
            logger.info("Consola: stdin cerrado, terminando.")
            return

        # Se parte en como mucho 2 trozos: 'ayuda crear_elemento' ->
        # comando='ayuda', argumento='crear_elemento'. Los comandos que
        # no usan argumento (todos salvo 'ayuda' por ahora) simplemente
        # lo ignoran.
        partes = linea.strip().split(maxsplit=1)
        if not partes:
            continue
        comando, argumento = partes[0], (partes[1].strip() if len(partes) > 1 else None)

        if comando in ("salir", "exit", "quit"):
            print("Cerrando consola (el stack local sigue corriendo).")
            return
        if comando in (
            "ayuda",
            "help",
            "h",
            "?",
        ):
            _mostrar_ayuda(argumento)
            continue

        accion = ACCIONES.get(comando)
        if accion is None:
            print(
                f"Comando desconocido: '{comando}'. Escribe 'ayuda' para ver la lista."
            )
            continue

        try:
            valores = await ejecutar_cuestionario(accion.campos)
            resultado = await accion.handler(comunicaciones, **valores)
            print(resultado)
        except Exception as exc:
            logger.error("Error ejecutando '%s': %s", comando, exc)
            print(f"Error ejecutando '{comando}': {exc}")
