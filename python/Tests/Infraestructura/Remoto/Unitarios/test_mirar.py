# Tests/Infraestructura/Remoto/Unitarios/test_mirar.py
"""
test_mirar.py — Pruebas unitarias de la acción 'mirar'
(Gestores/Mundo/Logica_Mundo/Acciones/mirar.py): raycast Bresenham,
detección de elementos bloqueantes, transparencia, y validación de
payload. Sin ningún test hasta ahora, pese a ser la única acción de
juego implementada por completo.

Se construyen `Celda` (el dataclass interno de logica_mundo.py) y
elementos falsos con `.rotacion` y `.get_comportamiento(nombre)` —
igual que espera AccionContext, sin necesitar el resto de LogicaMundo.
"""

import json
import struct

import pytest

from Infraestructura.Gestores.Mundo.Logica_Mundo.Acciones.mirar import mirar
from Infraestructura.Gestores.Mundo.Logica_Mundo.api_acciones import AccionContext
from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo import Celda


class FakeColor:
    def __init__(self, r, g, b, transparencia):
        self.r, self.g, self.b = r, g, b
        self.transparencia = transparencia


class FakeElemento:
    """Doble mínimo de un elemento del gold: rotación (solo la usa el
    bot que mira) + get_comportamiento('Color') (solo lo usan los
    elementos potencialmente bloqueantes)."""

    def __init__(self, rotacion=0.0, color=None):
        self.rotacion = rotacion
        self._color = color

    def get_comportamiento(self, nombre):
        return self._color if nombre == "Color" else None


def _ctx(bot_id, gold_cells, elements, bot_positions, distancia=5) -> AccionContext:
    return AccionContext(
        bot_id=bot_id,
        payload=struct.pack("<i", distancia),
        gold_cells=gold_cells,
        elements=elements,
        bot_positions=bot_positions,
    )


def _escenario_bot_mirando_a_x_positivo(elemento_en_camino=None):
    """
    Bot en (0,0) mirando hacia +x (rotación 0). Si se pasa un
    `elemento_en_camino`, se coloca en (3,0) — dentro del alcance de
    una distancia de 5.
    """
    bot_id_elem = 1
    gold_cells = {(0, 0): Celda(bot=bot_id_elem)}
    elements = {bot_id_elem: FakeElemento(rotacion=0.0)}
    bot_positions = {"bot_1": (0, 0)}

    if elemento_en_camino is not None:
        obstaculo_id = 2
        gold_cells[(3, 0)] = Celda(resto=[obstaculo_id])
        elements[obstaculo_id] = elemento_en_camino

    return gold_cells, elements, bot_positions


@pytest.mark.unit
async def test_mirar_payload_invalido_devuelve_error():
    ctx = _ctx("bot_1", {}, {}, {})
    ctx.payload = b"\x01\x02"  # struct "<i" necesita exactamente 4 bytes

    resultado = await mirar(ctx)

    assert resultado.ok is False
    assert "payload" in resultado.error.lower()


@pytest.mark.unit
async def test_mirar_bot_sin_posicion_conocida_falla():
    ctx = _ctx("bot_fantasma", gold_cells={}, elements={}, bot_positions={})

    resultado = await mirar(ctx)

    assert resultado.ok is False
    assert "bot_positions" in resultado.error


@pytest.mark.unit
async def test_mirar_bot_sin_celda_en_gold_cells_falla():
    ctx = _ctx("bot_1", gold_cells={}, elements={}, bot_positions={"bot_1": (0, 0)})

    resultado = await mirar(ctx)

    assert resultado.ok is False
    assert "gold_cells" in resultado.error


@pytest.mark.unit
async def test_mirar_sin_obstaculos_devuelve_negro():
    gold_cells, elements, bot_positions = _escenario_bot_mirando_a_x_positivo()
    ctx = _ctx("bot_1", gold_cells, elements, bot_positions)

    resultado = await mirar(ctx)

    assert resultado.ok is True
    assert json.loads(resultado.payload) == [[0, 0, 0]]


@pytest.mark.unit
async def test_mirar_detecta_elemento_bloqueante_en_el_camino():
    obstaculo = FakeElemento(color=FakeColor(255, 0, 0, transparencia=0.0))
    gold_cells, elements, bot_positions = _escenario_bot_mirando_a_x_positivo(obstaculo)
    ctx = _ctx("bot_1", gold_cells, elements, bot_positions)

    resultado = await mirar(ctx)

    assert resultado.ok is True
    assert json.loads(resultado.payload) == [[255, 0, 0]]


@pytest.mark.unit
async def test_mirar_ignora_elemento_transparente():
    """Transparencia >= 0.99 (TRANSPARENCIA_UMBRAL) no bloquea el rayo."""
    transparente = FakeElemento(color=FakeColor(0, 255, 0, transparencia=1.0))
    gold_cells, elements, bot_positions = _escenario_bot_mirando_a_x_positivo(
        transparente
    )
    ctx = _ctx("bot_1", gold_cells, elements, bot_positions)

    resultado = await mirar(ctx)

    assert json.loads(resultado.payload) == [[0, 0, 0]]


@pytest.mark.unit
async def test_mirar_recorta_la_distancia_al_maximo_de_vision(monkeypatch):
    """
    Un obstáculo más allá de MAX_VISION_DISTANCE no debería detectarse
    aunque el bot pida una distancia mayor — mirar() recorta con
    `min(distancia, MAX_VISION_DISTANCE)`.
    """
    import Infraestructura.Gestores.Mundo.Logica_Mundo.Acciones.mirar as mirar_mod

    monkeypatch.setattr(mirar_mod, "MAX_VISION_DISTANCE", 2)

    obstaculo = FakeElemento(color=FakeColor(1, 1, 1, transparencia=0.0))
    gold_cells, elements, bot_positions = _escenario_bot_mirando_a_x_positivo(obstaculo)
    # obstáculo en (3,0), pero MAX_VISION_DISTANCE=2 recorta el alcance a 2
    ctx = _ctx("bot_1", gold_cells, elements, bot_positions, distancia=10)

    resultado = await mirar(ctx)

    assert json.loads(resultado.payload) == [[0, 0, 0]]
