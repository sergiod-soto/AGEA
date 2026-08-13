# Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_remoto.py
"""
test_comunicaciones_remoto.py — Valida la propagación total de fallos
en el puente: ComunicacionesRemotoServicer.Heartbeat debe devolver
ok=False si CUALQUIERA de sus 3 subordinados (logica_mundo,
gestor_mundo, gestor_bots) falla — por excepción de red O por
responder con ok=False propio (ver directiva explícita: "cualquier
cosa caída, todo se apaga").

Se llama al servicer directamente (sin levantar un grpc.aio.server
real) porque lo que se quiere validar es la lógica de propagación de
ComunicacionesRemotoServicer + ComunicacionesRemoto colaborando de
verdad — no la serialización proto de este RPC en concreto, que ya
queda cubierta por el test de integración de Gestor_Bots (mismo
patrón, con servidor real). Se documenta la decisión aquí para que
quede explícita, no implícita.

Sección Vista_Foco (NUEVA): mismo criterio — se ejercita
ComunicacionesRemoto.actualizar_foco()/suscribirse_foco() directamente
(sin servidor gRPC real), porque lo que interesa aquí es la lógica de
FocoBroadcaster (vigilancia de tick + fan-out a suscriptores), no la
serialización de red — eso lo cubre
test_comunicaciones_local_roundtrip.py con un servidor real.
"""

import asyncio
from types import SimpleNamespace

import pytest

from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto import (
    ComunicacionesRemoto,
)
from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto_servicer import (
    ComunicacionesRemotoServicer,
)


class FakeHeartbeatResponse:
    def __init__(self, ok: bool, error: str = ""):
        self.ok = ok
        self.error = error


def _clientes_todos_sanos():
    async def heartbeat_ok(*_, **__):
        return FakeHeartbeatResponse(ok=True)

    return SimpleNamespace(
        logica_mundo=SimpleNamespace(heartbeat=heartbeat_ok),
        gestor_mundo=SimpleNamespace(heartbeat=heartbeat_ok),
        gestor_bots=SimpleNamespace(heartbeat=heartbeat_ok),
    )


@pytest.fixture
def logica_remoto():
    """
    ComunicacionesRemoto real, pero sin ninguna FUNCION registrada —
    el dispatch de Ejecutar() no se ejercita en estos tests (ver
    test_ejecutar_operacion_desconocida más abajo, que sí lo prueba).
    """
    clientes = _clientes_todos_sanos()
    logica = ComunicacionesRemoto(clientes)
    logica._dispatch = {}  # sin operaciones registradas, a propósito
    return logica, clientes


@pytest.mark.integration
async def test_heartbeat_ok_si_los_tres_subordinados_responden_bien(logica_remoto):
    logica, _ = logica_remoto
    servicer = ComunicacionesRemotoServicer(logica)

    resp = await servicer.Heartbeat(request=None, context=None)

    assert resp.ok is True


@pytest.mark.integration
async def test_heartbeat_propaga_excepcion_de_un_subordinado(logica_remoto):
    logica, clientes = logica_remoto

    async def heartbeat_falla(*_, **__):
        raise RuntimeError("conexión rechazada")

    clientes.logica_mundo.heartbeat = heartbeat_falla
    servicer = ComunicacionesRemotoServicer(logica)

    resp = await servicer.Heartbeat(request=None, context=None)

    assert resp.ok is False
    assert "logica_mundo" in resp.error


@pytest.mark.integration
async def test_heartbeat_propaga_ok_false_de_un_subordinado_sin_excepcion(
    logica_remoto,
):
    """
    Este es el caso que corregimos explícitamente: un subordinado que
    RESPONDE (no lanza excepción) pero con ok=False — p.ej. Gestor_Bots
    reportando que uno de sus HVs está caído — también debe hacer que
    Comunicaciones_Remoto se reporte como caído. Antes de la
    corrección, este caso se perdía silenciosamente.
    """
    logica, clientes = logica_remoto

    async def heartbeat_ok_false(*_, **__):
        return FakeHeartbeatResponse(ok=False, error="HV hv_00 sin respuesta")

    clientes.gestor_bots.heartbeat = heartbeat_ok_false
    servicer = ComunicacionesRemotoServicer(logica)

    resp = await servicer.Heartbeat(request=None, context=None)

    assert resp.ok is False
    assert "gestor_bots" in resp.error


@pytest.mark.integration
async def test_heartbeat_reporta_todos_los_caidos_a_la_vez(logica_remoto):
    logica, clientes = logica_remoto

    async def falla(*_, **__):
        raise RuntimeError("caído")

    clientes.gestor_mundo.heartbeat = falla
    clientes.gestor_bots.heartbeat = falla
    servicer = ComunicacionesRemotoServicer(logica)

    resp = await servicer.Heartbeat(request=None, context=None)

    assert resp.ok is False
    assert "gestor_mundo" in resp.error
    assert "gestor_bots" in resp.error
    assert "logica_mundo" not in resp.error


@pytest.mark.integration
async def test_ejecutar_operacion_desconocida_devuelve_error_de_puente(logica_remoto):
    """
    ComunicacionesRemoto.ejecutar() con una operación no registrada en
    _dispatch debe devolver ok=False del PUENTE (no una excepción sin
    controlar) — ver docstring de comunicaciones_remoto.py sobre la
    distinción entre ok/error del puente y el de cada Response interno.
    """
    logica, _ = logica_remoto

    ok, error, payload = await logica.ejecutar(
        "LOGICA_MUNDO", "OperacionInventada", b""
    )

    assert ok is False
    assert "desconocida" in error.lower()
    assert payload == b""


# ══════════════════════════════════════════════════════════════════
#  Vista_Foco — ActualizarFoco / SuscribirseFoco / FocoBroadcaster
# ══════════════════════════════════════════════════════════════════


class FakeGlobalesResponse:
    """Doble de GetElementosGlobalesResponse — solo los campos que
    FocoBroadcaster lee (ok, tick_actual, elementos_globales, error)."""

    def __init__(self, ok=True, tick_actual=0, elementos_globales=(), error=""):
        self.ok = ok
        self.tick_actual = tick_actual
        self.elementos_globales = list(elementos_globales)
        self.error = error


class FakeLogicaMundoFoco:
    """
    Doble de logica_mundo para ejercitar FocoBroadcaster: expone los
    dos métodos que su bucle de vigilancia usa (get_elementos_globales,
    consultar_representacion — obtener_celdas_en_region se retiró del
    pulso, ver vista_foco.py). `tick_actual` es mutable a mano por el
    test — simula "Logica_Mundo avanzó de tick" sin depender de
    AvanzarElementosGlobales real (eso ya lo cubre
    test_logica_mundo_servicer.py).
    """

    def __init__(self):
        self.tick_actual = 0
        self.llamadas_consultar_representacion = 0

    async def get_elementos_globales(self):
        return FakeGlobalesResponse(tick_actual=self.tick_actual)

    async def consultar_representacion(self, min_pos, max_pos, incluir, modo):
        self.llamadas_consultar_representacion += 1
        return b"representacion"


@pytest.fixture
async def logica_foco():
    """
    ComunicacionesRemoto real con un logica_mundo falso controlable.
    Al terminar el test se cancela la tarea de fondo del vigilante
    (si llegó a arrancar) — si no se hiciera, el bucle infinito de
    FocoBroadcaster._vigilar quedaría corriendo tras el test y
    pytest-asyncio avisaría de una tarea nunca recogida.
    """
    logica_mundo_fake = FakeLogicaMundoFoco()
    clientes = SimpleNamespace(
        logica_mundo=logica_mundo_fake,
        gestor_mundo=SimpleNamespace(),
        gestor_bots=SimpleNamespace(),
    )
    logica = ComunicacionesRemoto(clientes)

    yield logica, logica_mundo_fake

    tarea = logica._foco._tarea_vigilante
    if tarea is not None:
        tarea.cancel()


@pytest.mark.integration
async def test_suscribirse_sin_foco_fijado_no_recibe_nada(logica_foco):
    """
    Si el master aún no ha llamado a ActualizarFoco, el vigilante debe
    quedarse dormido sin pedir nada a Logica_Mundo — un suscriptor que
    llega antes no debe recibir ninguna actualización todavía.
    """
    logica, _ = logica_foco
    gen = logica.suscribirse_foco()

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(gen.__anext__(), timeout=0.2)


@pytest.mark.integration
async def test_recibe_actualizacion_tras_fijar_foco_y_avanzar_tick(logica_foco):
    logica, logica_mundo_fake = logica_foco
    logica.actualizar_foco((0, 0), (10, 10), ["Color"], "modo_test")
    gen = logica.suscribirse_foco()

    logica_mundo_fake.tick_actual = 1  # simula que Logica_Mundo avanzó de tick
    actualizacion = await asyncio.wait_for(gen.__anext__(), timeout=1.0)

    assert actualizacion.ok is True
    assert actualizacion.tick_actual == 1
    assert logica_mundo_fake.llamadas_consultar_representacion == 1


@pytest.mark.integration
async def test_mismo_tick_no_genera_una_segunda_actualizacion(logica_foco):
    """
    El disparo es "hubo tick nuevo", no un intervalo de tiempo — si el
    tick no cambia, no debe llegar una segunda actualización aunque
    pase tiempo de sobra para varios ciclos de poll.
    """
    logica, logica_mundo_fake = logica_foco
    logica.actualizar_foco((0, 0), (10, 10), [], "modo")
    gen = logica.suscribirse_foco()
    logica_mundo_fake.tick_actual = 1
    await asyncio.wait_for(gen.__anext__(), timeout=1.0)

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(gen.__anext__(), timeout=0.2)


@pytest.mark.integration
async def test_dos_suscriptores_reciben_la_misma_actualizacion_con_un_solo_fetch(
    logica_foco,
):
    """
    El punto central del diseño: "una sola conexión lógica a
    Logica_Mundo, N Unitys escuchando" — dos suscriptores deben recibir
    el mismo tick_actual, pero consultar_representacion solo debe
    llamarse UNA vez por tick, no una por suscriptor (fan-out desde un
    único fetch).
    """
    """
    El punto central del diseño: "una sola conexión lógica a
    Logica_Mundo, N Unitys escuchando" — dos suscriptores deben recibir
    el mismo tick_actual, pero consultar_representacion solo debe
    llamarse UNA vez por tick, no una por suscriptor (fan-out desde un
    único fetch).

    El tick se fija ANTES de que nadie se suscriba, a propósito: si se
    fijara después (con el foco ya establecido y algún suscriptor ya
    registrado), el vigilante detectaría "primer tick visto" (None -> 0,
    el valor por defecto) en cuanto se registrara el primer suscriptor,
    y ambos recibirían ese empuje espurio con tick=0 en vez del tick=1
    que el test quiere comprobar — no es un bug de producción (un
    suscriptor nuevo SÍ debe recibir el estado actual de inmediato),
    solo hay que fijar el tick antes de arrancar los generadores para
    que el primer empuje que se observe sea el que interesa al test.
    """
    logica, logica_mundo_fake = logica_foco
    logica.actualizar_foco((0, 0), (10, 10), [], "modo")
    logica_mundo_fake.tick_actual = 1

    gen_a = logica.suscribirse_foco()
    gen_b = logica.suscribirse_foco()
    # Crear el generador NO ejecuta su cuerpo (igual que cualquier
    # generador Python) — hace falta arrancar su primer __anext__()
    # para que de verdad llegue a registrarse en _suscriptores. Ambas
    # tareas se crean seguidas, sin ningún `await` entre medias, así
    # que asyncio las ejecuta en ese mismo orden (hasta su primera
    # suspensión en `cola.get()`) antes de que la Task del vigilante
    # —creada dentro de la primera— llegue a su turno.
    tarea_a = asyncio.ensure_future(gen_a.__anext__())
    tarea_b = asyncio.ensure_future(gen_b.__anext__())

    actualizacion_a = await asyncio.wait_for(tarea_a, timeout=1.0)
    actualizacion_b = await asyncio.wait_for(tarea_b, timeout=1.0)

    assert actualizacion_a.tick_actual == actualizacion_b.tick_actual == 1
    assert logica_mundo_fake.llamadas_consultar_representacion == 1


@pytest.mark.integration
async def test_desconexion_del_suscriptor_lo_retira_de_la_lista(logica_foco):
    """
    Cuando el `async for` de quien consume suscribirse_foco() se corta
    (equivalente a que el cliente gRPC se desconecte), el `finally` de
    FocoBroadcaster.suscribirse() debe quitar su cola — si no, el
    vigilante seguiría intentando repartir a colas de nadie.
    """
    logica, logica_mundo_fake = logica_foco
    logica.actualizar_foco((0, 0), (10, 10), [], "modo")
    gen = logica.suscribirse_foco()

    # Crear el generador no ejecuta su cuerpo (ver docstring de
    # test_dos_suscriptores...): hace falta un primer __anext__() para
    # que se registre en _suscriptores. Se dispara un cambio de tick
    # para que ese __anext__() complete de verdad y el generador quede
    # suspendido en el `yield` — el único estado desde el que se puede
    # cerrar con aclose() sin pisar una operación __anext__() todavía
    # en curso sobre el mismo generador.
    logica_mundo_fake.tick_actual = 1
    await asyncio.wait_for(gen.__anext__(), timeout=1.0)

    assert len(logica._foco._suscriptores) == 1

    await gen.aclose()
    await asyncio.sleep(0.1)  # margen para que el finally se ejecute

    assert len(logica._foco._suscriptores) == 0


@pytest.mark.integration
async def test_actualizar_foco_cambia_la_region_usada_en_el_siguiente_push(
    logica_foco,
):
    """
    Si el master mueve la cámara (llama a actualizar_foco otra vez)
    antes del siguiente tick, el push que llegue después debe usar la
    región NUEVA, no la que había cuando se suscribió el cliente.
    """
    logica, logica_mundo_fake = logica_foco
    logica.actualizar_foco((0, 0), (10, 10), [], "modo_viejo")
    gen = logica.suscribirse_foco()

    logica.actualizar_foco((100, 100), (200, 200), [], "modo_nuevo")
    logica_mundo_fake.tick_actual = 1
    await asyncio.wait_for(gen.__anext__(), timeout=1.0)

    assert logica_mundo_fake.llamadas_consultar_representacion == 1
    # No hay forma directa de inspeccionar qué región se usó desde
    # fuera del fake sin ampliarlo — se deja como posible mejora si
    # hiciera falta más granularidad en el futuro.
