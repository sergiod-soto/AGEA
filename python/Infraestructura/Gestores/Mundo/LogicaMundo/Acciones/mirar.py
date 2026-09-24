# Infraestructura/Gestores/Mundo/LogicaMundo/Acciones/mirar.py
from __future__ import annotations
import json
import math
import struct
import logging

from Config.settings import MAX_VISION_DISTANCE
from Infraestructura.Gestores.tipos_comunes import ActionResult

logger = logging.getLogger(__name__)
TRANSPARENCIA_UMBRAL = 0.99


async def mirar(ctx) -> "ActionResult":
    try:
        (distancia,) = struct.unpack("<i", ctx.payload)
    except struct.error:
        return ActionResult(ok=False, error="Payload inválido para 'mirar'.")

    if distancia <= 0:
        return ActionResult(ok=False, error="'mirar' exige distancia > 0.")
    distancia = min(distancia, MAX_VISION_DISTANCE)

    pos = ctx.bot_positions.get(ctx.bot_id)
    if pos is None:
        return ActionResult(
            ok=False, error=f"Bot {ctx.bot_id!r} no encontrado en bot_positions."
        )

    x0, y0 = pos
    celda = ctx.gold_cells.get((x0, y0))
    if celda is None or celda.bot is None:
        return ActionResult(
            ok=False, error=f"Bot {ctx.bot_id!r} no tiene celda en gold_cells."
        )

    elemento_bot = ctx.elements.get(celda.bot)
    if elemento_bot is None:
        return ActionResult(
            ok=False, error=f"Elemento bot {ctx.bot_id!r} no encontrado en elements."
        )

    colores = _raycast(
        x0=x0,
        y0=y0,
        angulo=elemento_bot.rotacion,
        distancia=distancia,
        gold_cells=ctx.gold_cells,
        elements=ctx.elements,
    )
    return ActionResult(ok=True, payload=json.dumps(colores).encode())


def _raycast(x0, y0, angulo, distancia, gold_cells, elements):
    for cx, cy in _bresenham_celdas(x0, y0, angulo, distancia):
        celda = gold_cells.get((cx, cy))
        if celda is None:
            continue
        colores = _extraer_colores_bloqueantes(celda, elements)
        if colores:
            return colores
    return [[0, 0, 0]]


def _bresenham_celdas(x0, y0, angulo, distancia):
    rad = math.radians(angulo)
    x1 = x0 + round(math.cos(rad) * distancia)
    y1 = y0 + round(math.sin(rad) * distancia)
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    celdas = []

    for _ in range(dx + dy + 1):
        if (x, y) != (x0, y0):
            celdas.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

    return celdas


def _extraer_colores_bloqueantes(celda, elements):
    colores = []
    ids = []
    if celda.suelo is not None:
        ids.append(celda.suelo)
    if celda.bot is not None:
        ids.append(celda.bot)
    ids.extend(celda.resto)
    for eid in ids:
        elemento = elements.get(eid)
        if elemento is None:
            continue
        color = _get_color_si_bloquea(elemento)
        if color is not None:
            colores.append(color)
    return colores


def _get_color_si_bloquea(elemento):
    color = elemento.get_comportamiento("Color")
    if color is None:
        return None
    if color.transparencia >= TRANSPARENCIA_UMBRAL:
        return None
    return [color.r, color.g, color.b]
