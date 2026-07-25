# Tests/Infraestructura/Remoto/Unitarios/test_transporte_clients_async_errores.py
"""
test_transporte_clients_async_errores.py — Rutas de error de los
clientes ASYNC de Transporte que aún no tenían ningún test: los
métodos "felices" de LogicaMundoClient ya quedaron cubiertos en
test_logica_mundo_servicer.py (Integración), pero ninguno de los tres
clientes de este fichero tenía probado qué pasa cuando el componente
remoto no responde.

Mismo truco que en test_transporte_clients_errores.py: apuntar a un
puerto sin nada escuchando y usar un timeout corto, en vez de mockear
grpc.

HALLAZGO DE INCONSISTENCIA (no bloqueante, mismo patrón en ambos
clientes): la mayoría de métodos capturan grpc.aio.AioRpcError y
devuelven un valor por defecto (False, lista vacía, ActionResult
ok=False...). Pero GestorMundoClient.heartbeat() y
LogicaMundoClient.asignar_id() NO lo hacen — el primero no envuelve la
llamada en try/except, y el segundo la envuelve pero vuelve a lanzar
(`raise`) tras loguear. Funcionalmente no es grave (quien las llama —
comunicaciones_remoto_servicer.py, resolver_accion callers — ya
envuelve sus propias llamadas en try/except), pero conviene saberlo:
no todos los métodos de estos clientes "async" siguen la misma
convención de manejo de errores.
"""

import grpc.aio
import pytest

from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
    GestorBotsClientAsync,
)
from Infraestructura.Gestores.Transporte.gestor_mundo_client import GestorMundoClient
from Infraestructura.Gestores.Transporte.logica_mundo_client import LogicaMundoClient

_DIRECCION_MUERTA = "127.0.0.1:59997"
_TIMEOUT_CORTO = 0.3


# ── GestorMundoClient ──────────────────────────────────────────────


@pytest.fixture
async def gestor_mundo_client_muerto():
    client = GestorMundoClient(_DIRECCION_MUERTA, timeout=_TIMEOUT_CORTO)
    yield client
    await client.close()


@pytest.mark.unit
async def test_gestor_mundo_client_heartbeat_propaga_la_excepcion(
    gestor_mundo_client_muerto,
):
    """Ver HALLAZGO DE INCONSISTENCIA en la cabecera del fichero."""
    with pytest.raises(grpc.aio.AioRpcError):
        await gestor_mundo_client_muerto.heartbeat()


@pytest.mark.unit
async def test_gestor_mundo_client_pause_devuelve_ok_false_si_no_hay_servidor(
    gestor_mundo_client_muerto,
):
    ok, error = await gestor_mundo_client_muerto.pause()
    assert ok is False
    assert error != ""


@pytest.mark.unit
async def test_gestor_mundo_client_get_snapshot_info_devuelve_ok_false_si_falla(
    gestor_mundo_client_muerto,
):
    resp = await gestor_mundo_client_muerto.get_snapshot_info()
    assert resp.ok is False


# ── GestorBotsClientAsync ──────────────────────────────────────────


@pytest.fixture
async def gestor_bots_client_async_muerto():
    client = GestorBotsClientAsync(_DIRECCION_MUERTA, timeout=_TIMEOUT_CORTO)
    yield client
    await client.close()


@pytest.mark.unit
async def test_gestor_bots_client_async_matar_script_bot_devuelve_false_si_falla(
    gestor_bots_client_async_muerto,
):
    assert await gestor_bots_client_async_muerto.matar_script_bot("bot_1") is False


@pytest.mark.unit
async def test_gestor_bots_client_async_list_hypervisors_devuelve_lista_vacia_si_falla(
    gestor_bots_client_async_muerto,
):
    lista = await gestor_bots_client_async_muerto.list_hypervisors()
    assert lista.hypervisors == []


@pytest.mark.unit
async def test_gestor_bots_client_async_save_snapshot_devuelve_ok_false_si_falla(
    gestor_bots_client_async_muerto,
):
    ok, error = await gestor_bots_client_async_muerto.save_snapshot("snap_1")
    assert ok is False
    assert error != ""


# ── LogicaMundoClient ────────────────────────────────────────────────


@pytest.fixture
async def logica_mundo_client_muerto():
    client = LogicaMundoClient(_DIRECCION_MUERTA, timeout=_TIMEOUT_CORTO)
    yield client
    await client.close()


@pytest.mark.unit
async def test_logica_mundo_client_asignar_id_propaga_la_excepcion(
    logica_mundo_client_muerto,
):
    """Ver HALLAZGO DE INCONSISTENCIA en la cabecera del fichero."""
    with pytest.raises(grpc.aio.AioRpcError):
        await logica_mundo_client_muerto.asignar_id()


@pytest.mark.unit
async def test_logica_mundo_client_crear_elemento_devuelve_ok_false_si_falla(
    logica_mundo_client_muerto,
):
    ok, error = await logica_mundo_client_muerto.crear_elemento(
        pos=(0, 0), type_id="suelo", element=b""
    )
    assert ok is False
    assert error != ""


@pytest.mark.unit
async def test_logica_mundo_client_get_active_events_devuelve_lista_vacia_si_falla(
    logica_mundo_client_muerto,
):
    assert await logica_mundo_client_muerto.get_active_events() == []


@pytest.mark.unit
async def test_logica_mundo_client_obtener_celdas_en_region_devuelve_vacio_si_falla(
    logica_mundo_client_muerto,
):
    celdas = await logica_mundo_client_muerto.obtener_celdas_en_region(
        min_pos=(0, 0), max_pos=(1, 1)
    )
    assert celdas == []


@pytest.mark.unit
async def test_logica_mundo_client_resolver_accion_devuelve_ok_false_si_falla(
    logica_mundo_client_muerto,
):
    resultado = await logica_mundo_client_muerto.resolver_accion(
        bot_id="bot_1", action_type="mirar", payload=b""
    )
    assert resultado.ok is False
