# Tests/Infraestructura/Comunicacion/Remoto/Unitarios/test_vista_foco.py
"""
test_vista_foco.py — Pruebas unitarias de FocoBroadcaster
(Infraestructura/Gestores/Comunicacion/Remoto/vista_foco.py).

Qué se dobla y por qué:
  - logica_mundo se dobla con _FakeLogicaMundoClient en vez de FakeStub
    (Tests/conftest.py): FakeStub devuelve un valor FIJO por método, y
    aquí necesitamos que get_elementos_globales() devuelva cosas
    distintas en llamadas sucesivas (tick que cambia, un fallo puntual
    seguido de recuperación...). Se configura con una lista de
    respuestas a consumir en orden; al agotarse, repite la última
    (simula "Logica_Mundo sigue en el mismo tick").
  - pb.ActualizacionFoco se sustituye por _FakeActualizacionFoco: no
    tenemos aquí el .proto real de Comunicacion, y representacion /
    elementos_globales son mensajes anidados cuyo esquema no podemos
    fabricar de forma fiable en un test unitario. Un objeto plano que
    solo guarda los kwargs basta para comprobar QUÉ le llega a cada
    suscriptor, sin acoplar el test al esquema del mensaje real.
  - _POLL_INTERVAL_SEGUNDOS se reduce (autouse) para que los tests que
    dependen del bucle de polling sean rápidos y no dependan de los
    50ms reales de producción.

Sobre la sincronización: nunca se hace "sleep arbitrario + assert a
ciegas" para comprobar que SÍ llegó algo — se usa
asyncio.wait_for(agen.__anext__(), timeout=...) y se espera el evento
real. La única situación donde eso no es posible es comprobar que NO
llegó nada (no hay evento que esperar): ahí el propio TimeoutError de
wait_for es la aserción, y de paso su cancelación interna ya limpia el
generador (dispara su `finally`), así que no hace falta un aclose()
manual después.
"""

from __future__ import annotations

import asyncio
import contextlib
from types import SimpleNamespace
from typing import Any

import pytest

from Infraestructura.Gestores.Comunicacion.Remoto import vista_foco
from Infraestructura.Gestores.Comunicacion.Remoto.vista_foco import FocoBroadcaster

# ── Dobles específicos de este test ─────────────────────────────


class _FakeLogicaMundoClient:
    """
    Doble de logica_mundo. Se configura con una lista de respuestas
    para get_elementos_globales (consumidas en orden; si se agotan, se
    repite la última) y, opcionalmente, una lista de respuestas para
    consultar_representacion (si no se da, genera una por llamada).
    Registra cuántas veces y con qué argumentos se le llama.
    """

    def __init__(self, respuestas_globales, representaciones=None):
        self._respuestas_globales = list(respuestas_globales)
        self._ultima_respuesta_global: Any = None
        self._representaciones = list(representaciones) if representaciones else None
        self.llamadas_globales = 0
        self.llamadas_representacion = 0
        self.args_representacion: list[tuple] = []

    async def get_elementos_globales(self):
        self.llamadas_globales += 1
        if self._respuestas_globales:
            self._ultima_respuesta_global = self._respuestas_globales.pop(0)
        respuesta = self._ultima_respuesta_global
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    async def consultar_representacion(self, min_pos, max_pos, incluir, modo):
        self.llamadas_representacion += 1
        self.args_representacion.append((min_pos, max_pos, incluir, modo))
        if self._representaciones:
            return self._representaciones.pop(0)
        return f"representacion-fake-{self.llamadas_representacion}"


class _FakeActualizacionFoco:
    """Sustituye a pb.ActualizacionFoco (ver docstring del módulo)."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self) -> str:
        return f"_FakeActualizacionFoco({self.__dict__!r})"


def _resp_ok(tick: int, elementos_globales: str = "globales-fake"):
    return SimpleNamespace(
        ok=True, error="", tick_actual=tick, elementos_globales=elementos_globales
    )


def _resp_error(mensaje: str = "fallo simulado"):
    return SimpleNamespace(
        ok=False, error=mensaje, tick_actual=None, elementos_globales=None
    )


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _poll_rapido(monkeypatch):
    """
    Sin esto, cada ciclo del vigilante tarda los 0.05s reales de
    producción y la suite se vuelve lenta e innecesariamente sensible
    a temporizaciones. 5ms deja margen de sobra para los timeouts de
    los tests (0.05-1s cubren varios ciclos).
    """
    monkeypatch.setattr(vista_foco, "_POLL_INTERVAL_SEGUNDOS", 0.005)


@pytest.fixture(autouse=True)
def _actualizacion_foco_fake(monkeypatch):
    monkeypatch.setattr(vista_foco.pb, "ActualizacionFoco", _FakeActualizacionFoco)


@pytest.fixture
async def crear_broadcaster():
    """
    Factory fixture: crea un FocoBroadcaster con un
    _FakeLogicaMundoClient detrás, y para su tarea vigilante al acabar
    el test. Sin esto, la tarea de fondo (bucle infinito) seguiría
    viva en el event loop una vez terminado el test, consultando un
    fake_cliente que ya no tiene sentido y acumulándose test tras test.
    """
    broadcasters: list[FocoBroadcaster] = []

    def _crear(respuestas_globales, representaciones=None):
        fake_cliente = _FakeLogicaMundoClient(respuestas_globales, representaciones)
        clientes = SimpleNamespace(logica_mundo=fake_cliente)
        broadcaster = FocoBroadcaster(clientes)
        broadcasters.append(broadcaster)
        return broadcaster, fake_cliente

    yield _crear

    for broadcaster in broadcasters:
        tarea = broadcaster._tarea_vigilante
        if tarea is not None and not tarea.done():
            tarea.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await tarea


async def _recibir(agen, timeout: float = 1.0):
    """
    Espera la siguiente actualización del generador de suscripción,
    con timeout. Si el timeout salta, wait_for cancela la llamada
    __anext__ pendiente, lo que dispara el `finally` de suscribirse()
    (se quita la cola de _suscriptores) antes de propagar el
    TimeoutError.
    """
    return await asyncio.wait_for(agen.__anext__(), timeout=timeout)


async def _cancelar(tarea: asyncio.Task) -> None:
    """Cancela una tarea de consumo (__anext__ pendiente) y espera a que termine."""
    tarea.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await tarea


# ── Sin foco fijado ──────────────────────────────────────────────


@pytest.mark.unit
async def test_sin_foco_fijado_el_vigilante_no_consulta_logica_mundo(crear_broadcaster):
    broadcaster, fake_cliente = crear_broadcaster(respuestas_globales=[_resp_ok(1)])
    agen = broadcaster.suscribirse()

    with pytest.raises(asyncio.TimeoutError):
        await _recibir(agen, timeout=0.05)

    assert fake_cliente.llamadas_globales == 0


# ── Broadcast a varios suscriptores ──────────────────────────────


@pytest.mark.unit
async def test_actualizar_foco_dispara_broadcast_a_todos_los_suscriptores(
    crear_broadcaster,
):
    broadcaster, fake_cliente = crear_broadcaster(
        respuestas_globales=[_resp_ok(tick=1)],
        representaciones=["repr-1"],
    )

    agen_1 = broadcaster.suscribirse()
    agen_2 = broadcaster.suscribirse()
    tarea_1 = asyncio.ensure_future(agen_1.__anext__())
    tarea_2 = asyncio.ensure_future(agen_2.__anext__())

    # Dejamos que ambas suscripciones terminen de registrarse (quedan
    # bloqueadas en `await cola.get()`) ANTES de fijar el foco, para no
    # depender de en qué orden calendariza el event loop las tareas
    # recién creadas frente a la propia tarea vigilante.
    await asyncio.sleep(0.02)
    assert fake_cliente.llamadas_globales == 0  # confirma que aún no hay foco

    broadcaster.actualizar_foco(
        min_pos=(0, 0), max_pos=(10, 10), incluir=["bots"], modo="completo"
    )

    actualizacion_1, actualizacion_2 = await asyncio.wait_for(
        asyncio.gather(tarea_1, tarea_2), timeout=1.0
    )

    # Es un broadcast real: mismo objeto para todos los suscriptores,
    # no una consulta independiente por cliente.
    assert actualizacion_1 is actualizacion_2
    assert actualizacion_1.ok is True
    assert actualizacion_1.tick_actual == 1
    assert actualizacion_1.elementos_globales == "globales-fake"
    assert actualizacion_1.representacion == "repr-1"

    # La representación se pide UNA sola vez para ambos suscriptores.
    assert fake_cliente.llamadas_representacion == 1
    assert fake_cliente.args_representacion[0] == (
        (0, 0),
        (10, 10),
        ["bots"],
        "completo",
    )

    await agen_1.aclose()
    await agen_2.aclose()


# ── No reenvío si el tick no cambia ──────────────────────────────


@pytest.mark.unit
async def test_no_reenvia_si_el_tick_no_ha_cambiado(crear_broadcaster):
    # Una sola respuesta configurada: al agotarse la lista, el fake
    # repite la misma (mismo tick), simulando que Logica_Mundo no ha
    # avanzado entre polls.
    broadcaster, fake_cliente = crear_broadcaster(
        respuestas_globales=[_resp_ok(tick=1)], representaciones=["repr-1"]
    )
    broadcaster.actualizar_foco((0, 0), (10, 10), ["bots"], "completo")

    agen = broadcaster.suscribirse()
    primera = await _recibir(agen)
    assert primera.tick_actual == 1

    with pytest.raises(asyncio.TimeoutError):
        await _recibir(agen, timeout=0.05)  # varios ciclos de poll de sobra


# ── Resiliencia: ok=False ────────────────────────────────────────


@pytest.mark.unit
async def test_respuesta_ok_false_no_bloquea_y_se_recupera(crear_broadcaster):
    broadcaster, fake_cliente = crear_broadcaster(
        respuestas_globales=[_resp_error("timeout simulado"), _resp_ok(tick=5)],
        representaciones=["repr-5"],
    )
    broadcaster.actualizar_foco((0, 0), (10, 10), ["bots"], "completo")

    agen = broadcaster.suscribirse()
    actualizacion = await _recibir(agen)

    assert actualizacion.tick_actual == 5
    assert actualizacion.representacion == "repr-5"
    # Con ok=False el código corta antes de pedir representación
    # (`if not globales_resp.ok: ... continue`), así que solo debe
    # haber una llamada, la del ciclo que sí tuvo éxito.
    assert fake_cliente.llamadas_representacion == 1

    await agen.aclose()


# ── Resiliencia: excepción inesperada (el "FIX" del docstring) ──


@pytest.mark.unit
async def test_excepcion_inesperada_en_el_poll_no_mata_al_vigilante(crear_broadcaster):
    broadcaster, fake_cliente = crear_broadcaster(
        respuestas_globales=[RuntimeError("fallo de red simulado"), _resp_ok(tick=9)],
        representaciones=["repr-9"],
    )
    broadcaster.actualizar_foco((0, 0), (10, 10), ["bots"], "completo")

    agen = broadcaster.suscribirse()
    # Si la excepción matara la tarea vigilante (en vez de loguearse y
    # seguir, como documenta el FIX), este await agotaría el timeout.
    actualizacion = await _recibir(agen)

    assert actualizacion.tick_actual == 9
    assert fake_cliente.llamadas_globales >= 2  # el fallo + el éxito posterior

    await agen.aclose()


# ── Una sola tarea vigilante para varios suscriptores ───────────


@pytest.mark.unit
async def test_una_sola_tarea_vigilante_para_varios_suscriptores(crear_broadcaster):
    broadcaster, fake_cliente = crear_broadcaster(respuestas_globales=[_resp_ok(1)])

    agen_1 = broadcaster.suscribirse()
    tarea_1 = asyncio.ensure_future(agen_1.__anext__())
    await asyncio.sleep(0.01)  # deja que se registre y arranque el vigilante

    vigilante_inicial = broadcaster._tarea_vigilante
    assert vigilante_inicial is not None
    assert not vigilante_inicial.done()

    agen_2 = broadcaster.suscribirse()
    tarea_2 = asyncio.ensure_future(agen_2.__anext__())
    await asyncio.sleep(0.01)

    # Un segundo suscriptor NO debe levantar una segunda tarea de
    # fondo: sigue siendo la misma instancia de Task.
    assert broadcaster._tarea_vigilante is vigilante_inicial

    await _cancelar(tarea_1)
    await _cancelar(tarea_2)


# ── Baja de un suscriptor al desconectarse ──────────────────────


@pytest.mark.unit
async def test_al_desconectarse_el_suscriptor_se_quita_de_la_lista(crear_broadcaster):
    broadcaster, fake_cliente = crear_broadcaster(
        respuestas_globales=[_resp_ok(tick=1)], representaciones=["repr-1"]
    )
    broadcaster.actualizar_foco((0, 0), (10, 10), ["bots"], "completo")

    agen = broadcaster.suscribirse()
    await _recibir(agen)  # se registra y recibe la primera actualización
    assert len(broadcaster._suscriptores) == 1

    # Simula la desconexión del cliente gRPC: el `async for` de fuera
    # deja de iterar -> el generador se cierra -> se dispara el `finally`.
    await agen.aclose()

    assert len(broadcaster._suscriptores) == 0
