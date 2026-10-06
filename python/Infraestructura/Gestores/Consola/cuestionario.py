# Infraestructura/Gestores/Consola/cuestionario.py
"""
cuestionario.py — Motor genérico para pedir por consola los campos que
necesita una AccionConsola (ver accion_consola.py).

Una AccionConsola declara QUÉ necesita (lista de CampoCuestionario);
este módulo decide CÓMO se pide (prompt, casteo, reintento si el
valor no es válido, valor por defecto si el campo es opcional). Así
ninguna acción repite lógica de "leer input, validar, parsear".
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CampoCuestionario:
    """
    numero            : alternativa a nombre.
    nombre            : clave con la que este valor llega al handler (**kwargs).
    prompt            : texto mostrado al usuario.
    tipo              : función de casteo sobre el texto introducido (ej. int,
                        float, o un parser propio como parse_posicion). Si
                        lanza ValueError, se vuelve a pedir el campo.
    opcional          : si es True, una entrada vacía usa valor_por_defecto
                        en vez de forzar a escribir algo.
    valor_por_defecto : usado solo cuando opcional=True y el usuario no escribe nada.
    """
    nombre: str
    prompt: str
    tipo: Callable[[str], Any] = str
    opcional: bool = False
    valor_por_defecto: Any = None


def parse_bool(texto: str) -> bool:
    """Acepta s/n, si/no, true/false (sin distinguir mayúsculas) — pensado
    para responder cuestionarios desde teclado, no para parsear JSON."""
    t = texto.strip().lower()
    if t in ("s", "si", "sí", "true", "1"):
        return True
    if t in ("n", "no", "false", "0"):
        return False
    raise ValueError(f"'{texto}' no es un booleano reconocible (s/n).")


def parse_posicion(texto: str) -> tuple[int, int]:
    """Formato esperado: 'x,y', ej. '12,7'."""
    partes = texto.split(",")
    if len(partes) != 2:
        raise ValueError(f"'{texto}' no tiene formato 'x,y'.")
    return int(partes[0].strip()), int(partes[1].strip())


async def ejecutar_cuestionario(campos: list[CampoCuestionario]) -> dict[str, Any]:
    """
    Pide cada campo por teclado, en orden, y devuelve un dict listo
    para pasar como **kwargs al handler de la AccionConsola.

    Usa asyncio.to_thread() para el input() bloqueante. La consola
    corre en su propio hilo con su propio event loop (ver consola.py
    y su integración en bootstrap.py), así que hoy no hay nada más
    compitiendo por ese loop — pero se hace así de todos modos por
    higiene, para no depender de esa suposición si en el futuro la
    consola llegara a compartir loop con otra cosa.
    """
    valores: dict[str, Any] = {}
    for campo in campos:
        sufijo = " (opcional, Enter para omitir): " if campo.opcional else ": "
        while True:
            texto = await asyncio.to_thread(input, f"{campo.prompt}{sufijo}")
            if not texto.strip() and campo.opcional:
                valores[campo.nombre] = campo.valor_por_defecto
                break
            try:
                valores[campo.nombre] = campo.tipo(texto)
                break
            except ValueError as exc:
                print(f"  ✗ Valor inválido: {exc}. Vuelve a intentarlo.")
    return valores


def parse_nombre_clase(texto: str) -> str:
    """
    Valida contra el registry real de Core -- si el nombre no existe
    ahí, falla aquí mismo (se vuelve a pedir) en vez de dejar que el
    error aparezca más tarde, ya con red de por medio, en
    construir_elemento().
    """
    from Core.Entities.Elementos.registry import ELEMENTOS

    nombre = texto.strip()
    if nombre not in ELEMENTOS:
        raise ValueError(f"'{nombre}' no es un tipo de elemento conocido.")
    return nombre
