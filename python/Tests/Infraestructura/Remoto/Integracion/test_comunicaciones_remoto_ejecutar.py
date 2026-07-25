# Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_remoto_ejecutar.py
"""
test_comunicaciones_remoto_ejecutar.py — Complementa
test_comunicaciones_remoto.py (que solo prueba Heartbeat y desactiva
el dispatch real con `logica._dispatch = {}`). Aquí se ejercita el
dispatch REAL de Ejecutar() contra las funciones registradas en
Comunicacion/Remoto/registry.py — validando que el payload se
serializa/deserializa de verdad y se responde con un proto válido,
para al menos un caso por cada componente destino (LOGICA_MUNDO,
GESTOR_MUNDO, GESTOR_BOTS).

Se usan dobles simples (SimpleNamespace) para ClientesRemotos en vez
de clientes reales: lo que se quiere validar aquí es el dispatch +
(de)serialización de ComunicacionesRemoto, no la red hacia cada
componente (eso ya lo cubren los tests de integración de cada
servicer, en este mismo directorio).
"""

from types import SimpleNamespace

import pytest

from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto import (
    ComunicacionesRemoto,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as logica_pb,
)


def _clientes(**overrides):
    """
    Construye un doble de ClientesRemotos con los 3 sub-clientes
    vacíos por defecto; `overrides` reemplaza uno de ellos por un
    SimpleNamespace con los métodos concretos que ese test necesita.
    Ej: _clientes(gestor_mundo={"pause": mi_fake_pause})
    """
    base = SimpleNamespace(
        logica_mundo=SimpleNamespace(),
        gestor_mundo=SimpleNamespace(),
        gestor_bots=SimpleNamespace(),
    )
    for destino, metodos in overrides.items():
        setattr(base, destino, SimpleNamespace(**metodos))
    return base


@pytest.mark.integration
async def test_ejecutar_get_active_events_dispatch_real():
    async def get_active_events():
        return []

    clientes = _clientes(logica_mundo={"get_active_events": get_active_events})
    logica = ComunicacionesRemoto(clientes)  # dispatch REAL, sin bypass

    ok, error, payload = await logica.ejecutar("LOGICA_MUNDO", "GetActiveEvents", b"")

    assert ok is True
    assert error == ""
    resp = logica_pb.GetActiveEventsResponse()
    resp.ParseFromString(payload)
    assert resp.ok is True
    assert list(resp.events) == []


@pytest.mark.integration
async def test_ejecutar_list_hypervisors_dispatch_real():
    async def list_hypervisors():
        return common_pb2.HypervisorList(hypervisors=[])

    clientes = _clientes(gestor_bots={"list_hypervisors": list_hypervisors})
    logica = ComunicacionesRemoto(clientes)

    ok, error, payload = await logica.ejecutar("GESTOR_BOTS", "ListHypervisors", b"")

    assert ok is True
    resp = common_pb2.HypervisorList()
    resp.ParseFromString(payload)
    assert list(resp.hypervisors) == []


@pytest.mark.integration
async def test_ejecutar_pause_dispatch_real():
    async def pause():
        return True, ""

    clientes = _clientes(gestor_mundo={"pause": pause})
    logica = ComunicacionesRemoto(clientes)

    ok, error, payload = await logica.ejecutar("GESTOR_MUNDO", "Pause", b"")

    assert ok is True
    ack = common_pb2.Ack()
    ack.ParseFromString(payload)
    assert ack.ok is True


@pytest.mark.integration
async def test_ejecutar_handler_que_lanza_excepcion_devuelve_error_de_puente():
    """
    Si el handler real (no el cliente de red) lanza una excepción
    inesperada, ComunicacionesRemoto.ejecutar() debe capturarla y
    devolver ok=False del PUENTE en vez de propagarla — ver el except
    genérico en comunicaciones_remoto.py::ejecutar().
    """

    async def pause_rota():
        raise RuntimeError("boom")

    clientes = _clientes(gestor_mundo={"pause": pause_rota})
    logica = ComunicacionesRemoto(clientes)

    ok, error, payload = await logica.ejecutar("GESTOR_MUNDO", "Pause", b"")

    assert ok is False
    assert "boom" in error
    assert payload == b""
