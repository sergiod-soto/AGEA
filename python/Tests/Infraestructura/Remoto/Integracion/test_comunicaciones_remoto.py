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
"""

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
