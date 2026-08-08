# Tests/Infraestructura/Remoto/Unitarios/test_vista_foco.py
"""
test_vista_foco.py — Tests unitarios de FocoBroadcaster.

Complementa (no repite) a
Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_local_roundtrip.py:
allí se prueba que el cableado gRPC real funciona (serialización,
dos ComunicacionesLocal reales, un servidor real); aquí se prueba la
LÓGICA de FocoBroadcaster en aislamiento — con qué argumentos exactos
se llama a Logica_Mundo en cada ciclo, y bajo qué condiciones se
dispara o no un reparto.

Se llama directamente a FocoBroadcaster._ciclo_de_vigilancia() en vez
de dejar correr _vigilar() con sus sleeps de polling: eso hace estos
tests deterministas e instantáneos, sin depender de ningún timing.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from Infraestructura.Gestores.Comunicacion.Remoto.vista_foco import FocoBroadcaster


class FakeGlobalesResponse:
    def __init__(self, ok: bool = True, tick_actual: int = 0, elementos_globales=()):
        self.ok = ok
        self.tick_actual = tick_actual
        self.elementos_globales = list(elementos_globales)


class LogicaMundoSpy:
    """
    Doble de Logica_Mundo que registra CON QUÉ ARGUMENTOS se le llama
    cada método — no solo si se llamó o no. Esto es lo que un test de
    integración con red real no puede comprobar fácilmente (el fake
    de allí ignora los argumentos), y es justo lo que hace falta para
    verificar que, tras mover la cámara, el fetch usa la región NUEVA.
    """

    def __init__(self):
        self.tick_actual = 0
        self.llamadas_representacion: list[tuple] = []
        self.llamadas_celdas: list[tuple] = []

    async def get_elementos_globales(self):
        return FakeGlobalesResponse(tick_actual=self.tick_actual)

    async def obtener_celdas_en_region(self, min_pos, max_pos):
        self.llamadas_celdas.append((min_pos, max_pos))
        return []

    async def consultar_representacion(self, min_pos, max_pos, incluir, modo):
        self.llamadas_representacion.append((min_pos, max_pos, incluir, modo))
        return b"representacion_fake"


@pytest.fixture
def broadcaster():
    """
    FocoBroadcaster real con un ClientesRemotos mínimo (SimpleNamespace)
    cuyo único miembro relevante aquí es logica_mundo, sustituido por
    el spy de arriba.
    """
    logica_mundo_spy = LogicaMundoSpy()
    clientes = SimpleNamespace(
        logica_mundo=logica_mundo_spy,
        gestor_mundo=SimpleNamespace(),
        gestor_bots=SimpleNamespace(),
    )
    return FocoBroadcaster(clientes), logica_mundo_spy


async def test_ciclo_no_hace_fetch_sin_suscriptores(broadcaster):
    """
    Sin nadie suscrito no se llama ni siquiera a get_elementos_globales
    de forma completa (la comprobación de guarda corta antes) — evita
    coste de red mientras nadie está mirando.
    """
    fb, logica_mundo_spy = broadcaster
    fb.actualizar_foco(min_pos=(0, 0), max_pos=(10, 10), incluir=[], modo="test")

    await fb._ciclo_de_vigilancia()

    assert logica_mundo_spy.llamadas_representacion == []


async def test_ciclo_no_hace_fetch_sin_foco_fijado(broadcaster):
    """
    Con un suscriptor pero sin que nadie haya llamado a
    actualizar_foco todavía, tampoco se hace fetch: no hay región que
    consultar.
    """
    fb, logica_mundo_spy = broadcaster
    fb._suscriptores.add(asyncio.Queue())

    await fb._ciclo_de_vigilancia()

    assert logica_mundo_spy.llamadas_representacion == []


async def test_mover_camara_sin_cambiar_tick_dispara_fetch_con_la_region_nueva(
    broadcaster,
):
    """
    Caso "mundo en pausa, cámara se mueve": aunque tick_actual no
    cambie entre dos ciclos, si actualizar_foco() se llamó entre medio
    con una región distinta, el siguiente ciclo debe:
      1) disparar un fetch (no cortar por "nada cambió", ver
         foco_cambio en _ciclo_de_vigilancia)
      2) usar la región NUEVA, no la vieja.
    """
    fb, logica_mundo_spy = broadcaster
    fb._suscriptores.add(asyncio.Queue())

    fb.actualizar_foco(min_pos=(0, 0), max_pos=(10, 10), incluir=[], modo="test")
    logica_mundo_spy.tick_actual = 1
    await fb._ciclo_de_vigilancia()  # primer reparto: dispara por tick None -> 1

    assert logica_mundo_spy.llamadas_representacion[-1][:2] == ((0, 0), (10, 10))

    # "Pausa": el tick se queda en 1, pero se mueve la cámara.
    fb.actualizar_foco(min_pos=(5, 5), max_pos=(15, 15), incluir=[], modo="test")
    await fb._ciclo_de_vigilancia()

    assert len(logica_mundo_spy.llamadas_representacion) == 2
    assert logica_mundo_spy.llamadas_representacion[-1][:2] == ((5, 5), (15, 15))


async def test_ciclo_no_repite_fetch_si_no_cambio_ni_tick_ni_foco(broadcaster):
    """
    Complemento del test anterior: si NI el tick NI la versión del
    foco cambiaron desde el último reparto, no debe volver a hacerse
    fetch — confirma que la condición añadida (foco_cambio) no
    convierte el ciclo en "siempre repartir".
    """
    fb, logica_mundo_spy = broadcaster
    fb._suscriptores.add(asyncio.Queue())
    fb.actualizar_foco(min_pos=(0, 0), max_pos=(10, 10), incluir=[], modo="test")
    logica_mundo_spy.tick_actual = 1

    await fb._ciclo_de_vigilancia()  # dispara
    await fb._ciclo_de_vigilancia()  # nada cambió: no debe repetir

    assert len(logica_mundo_spy.llamadas_representacion) == 1


async def test_suscriptor_tardio_recibe_la_cache_inmediatamente(broadcaster):
    """
    Réplica unitaria (sin red) del caso que prueba
    test_master_y_espectador_reciben_la_misma_actualizacion_via_grpc_real
    en el fichero de integración: un suscriptor que llega DESPUÉS de
    que ya se repartió un frame debe encontrarlo ya esperando en su
    cola, sin depender de que el vigilante vuelva a dispararse.
    """
    fb, logica_mundo_spy = broadcaster
    fb.actualizar_foco(min_pos=(0, 0), max_pos=(10, 10), incluir=[], modo="test")
    logica_mundo_spy.tick_actual = 1

    fb._suscriptores.add(asyncio.Queue())  # suscriptor "ya presente"
    await fb._ciclo_de_vigilancia()

    suscripcion_tardia = fb.suscribirse()
    actualizacion = await suscripcion_tardia.__anext__()

    assert actualizacion.tick_actual == 1
    await suscripcion_tardia.aclose()
