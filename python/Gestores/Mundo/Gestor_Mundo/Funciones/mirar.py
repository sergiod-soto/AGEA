import struct
from typing import Optional

from Gestores.Mundo.Gestor_Mundo.gestor_mundo import ActionResult

TRANSPARENCIA_UMBRAL = 0.99  # por encima de esto se considera transparente


async def _handle_mirar(self, bot_id: str, payload: bytes) -> ActionResult:
        """
        Lanza un rayo desde la posición del bot en la dirección de su rotación.
        Devuelve la lista de colores RGB de la primera celda bloqueante,
        o [(0,0,0)] si no hay nada en el camino.
        """
        import json

        # Deserializar payload
        try:
            (distancia,) = struct.unpack("<i", payload)
        except struct.error:
            return ActionResult(ok=False, error="Payload inválido para 'mirar'.")

        # Obtener posición del bot
        pos = self._bot_positions.get(bot_id)
        if pos is None:
            return ActionResult(ok=False, error=f"Bot {bot_id!r} no encontrado.")
        x0, y0 = pos

        # Obtener elemento Bot para leer rotación
        celda = self._gold_cells.get((x0, y0))
        if celda is None or celda.bot is None:
            return ActionResult(ok=False, error=f"Bot {bot_id!r} no tiene celda.")

        elemento_bot = self._elements.get(celda.bot)
        if elemento_bot is None:
            return ActionResult(
                ok=False, error=f"Elemento bot {bot_id!r} no encontrado."
            )

        rotacion = elemento_bot.rotacion  # campo del Elemento Bot

        # Limitar distancia al máximo permitido
        distancia = min(distancia, MAX_VISION_DISTANCE)

        # Raycast
        resultado = self._raycast(x0, y0, rotacion, distancia)

        # Serializar resultado como JSON
        payload_out = json.dumps(resultado).encode()
        return ActionResult(ok=True, payload=payload_out)

def _raycast(
    self, x0: int, y0: int, angulo: float, distancia: int
) -> list[list[int]]:
    """
    Lanza un rayo y devuelve los colores RGB de la primera celda bloqueante.
    Un elemento bloquea si tiene comportamiento Color y transparencia < umbral.
    Devuelve [[0,0,0]] si no hay nada.
    """
    for cx, cy in _bresenham_celdas(x0, y0, angulo, distancia):
        celda = self._gold_cells.get((cx, cy))
        if celda is None:
            continue

        colores = self._extraer_colores_bloqueantes(celda)
        if colores:
            return colores

    return [[0, 0, 0]]

def _extraer_colores_bloqueantes(self, celda: CeldaData) -> list[list[int]]:
    """
    Extrae los colores RGB de los elementos bloqueantes de una celda.
    Un elemento bloquea si tiene comportamiento Color y transparencia < umbral.
    Devuelve lista vacía si ningún elemento bloquea.
    """
    colores = []

    ids = []
    if celda.suelo is not None:
        ids.append(celda.suelo)
    if celda.bot is not None:
        ids.append(celda.bot)
    ids.extend(celda.resto)

    for eid in ids:
        elemento = self._elements.get(eid)
        if elemento is None:
            continue
        color = self._get_color_si_bloquea(elemento)
        if color is not None:
            colores.append(color)

    return colores

def _get_color_si_bloquea(self, elemento) -> Optional[list[int]]:
    """
    Devuelve [r, g, b] si el elemento tiene Color y no es transparente.
    Devuelve None si no bloquea la visión.
    """
    color_comportamiento = elemento.get_comportamiento("Color")
    if color_comportamiento is None:
        return None
    if color_comportamiento.transparencia >= TRANSPARENCIA_UMBRAL:
        return None
    c = color_comportamiento
    return [c.r, c.g, c.b]

def _handle_observe(self, payload: bytes) -> ActionResult:
    """
    Acción 'observe': el bot pide el contenido de una celda (x, y).
    Payload esperado: JSON {"x": int, "y": int}
    """
    import json

    try:
        data = json.loads(payload)
        x, y = int(data["x"]), int(data["y"])
    except Exception:
        return ActionResult(
            ok=False,
            error='Payload inválido para \'observe\'. Esperado: {"x": int, "y": int}',
        )

    contenido = self.get_celda(x, y)
    return ActionResult(
        ok=True,
        payload=contenido if contenido is not None else b"",
    )