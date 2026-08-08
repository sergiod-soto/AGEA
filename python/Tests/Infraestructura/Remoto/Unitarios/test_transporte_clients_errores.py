# Tests/Infraestructura/Remoto/Unitarios/test_transporte_clients_errores.py
"""
test_transporte_clients_errores.py — Prueba las rutas de manejo de
error de los clientes de Transporte: qué devuelven cuando el
componente remoto no responde. En vez de mockear grpc, se apunta a un
puerto local sin nada escuchando y se usa un timeout muy corto — el
error real (UNAVAILABLE/DEADLINE_EXCEEDED) se produce solo, sin
necesidad de fixtures ni servidores falsos.
"""

import pytest

from Infraestructura.Gestores.Transporte.bot_client import BotClient
from Infraestructura.Gestores.Transporte.gestor_bots_client import GestorBotsClient
from Infraestructura.Gestores.Transporte.hypervisor_client import HypervisorClient

_DIRECCION_MUERTA = "127.0.0.1"
_PUERTO_MUERTO = 59998
_TIMEOUT_CORTO = 0.3


# ── GestorBotsClient (síncrono) ───────────────────────────────────


@pytest.fixture
def gestor_bots_client_muerto():
    client = GestorBotsClient(
        f"{_DIRECCION_MUERTA}:{_PUERTO_MUERTO}", timeout=_TIMEOUT_CORTO
    )
    yield client
    client.close()


@pytest.mark.unit
def test_gestor_bots_client_spawn_bot_devuelve_ok_false_si_no_hay_servidor(
    gestor_bots_client_muerto,
):
    info = gestor_bots_client_muerto.spawn_bot(bot_id=1)
    assert info.ok is False
    assert info.error != ""


@pytest.mark.unit
def test_gestor_bots_client_kill_bot_devuelve_false_si_no_hay_servidor(
    gestor_bots_client_muerto,
):
    assert gestor_bots_client_muerto.kill_bot(1) is False


@pytest.mark.unit
def test_gestor_bots_client_list_hypervisors_devuelve_lista_vacia_si_falla(
    gestor_bots_client_muerto,
):
    lista = gestor_bots_client_muerto.list_hypervisors()
    assert lista.hypervisors == []


# ── HypervisorClient (async) ──────────────────────────────────────


@pytest.fixture
async def hypervisor_client_muerto():
    client = HypervisorClient(_DIRECCION_MUERTA, _PUERTO_MUERTO, timeout=_TIMEOUT_CORTO)
    yield client
    await client.close()


@pytest.mark.unit
async def test_hypervisor_client_spawn_bot_devuelve_ok_false_si_no_hay_servidor(
    hypervisor_client_muerto,
):
    info = await hypervisor_client_muerto.spawn_bot({"bot_id": 1})
    assert info.ok is False


@pytest.mark.unit
async def test_hypervisor_client_list_bots_devuelve_lista_vacia_si_falla(
    hypervisor_client_muerto,
):
    lista = await hypervisor_client_muerto.list_bots()
    assert lista.bots == []


@pytest.mark.unit
async def test_hypervisor_client_reset_budgets_devuelve_false_si_falla(
    hypervisor_client_muerto,
):
    ok = await hypervisor_client_muerto.reset_budgets([1], {1: 10})
    assert ok is False


@pytest.mark.unit
async def test_hypervisor_client_set_point_budget_devuelve_false_si_falla(
    hypervisor_client_muerto,
):
    ok = await hypervisor_client_muerto.set_point_budget(1, 50)
    assert ok is False


@pytest.mark.unit
async def test_hypervisor_client_freeze_y_resume_devuelven_false_si_falla(
    hypervisor_client_muerto,
):
    assert await hypervisor_client_muerto.freeze() is False
    assert await hypervisor_client_muerto.resume() is False


@pytest.mark.unit
async def test_hypervisor_client_save_snapshot_devuelve_false_si_falla(
    hypervisor_client_muerto,
):
    ok = await hypervisor_client_muerto.save_snapshot("snap_1")
    assert ok is False


@pytest.mark.unit
async def test_hypervisor_client_get_bot_stats_devuelve_none_si_falla(
    hypervisor_client_muerto,
):
    assert await hypervisor_client_muerto.get_bot_stats(1) is None


@pytest.mark.unit
async def test_hypervisor_client_get_bot_status_devuelve_none_si_falla(
    hypervisor_client_muerto,
):
    assert await hypervisor_client_muerto.get_bot_status(1) is None


# ── BotClient (síncrono) ──────────────────────────────────────────


@pytest.fixture
def bot_client_muerto():
    client = BotClient(
        bot_id="bot_1",
        proxy_address=f"{_DIRECCION_MUERTA}:{_PUERTO_MUERTO}",
        timeout=_TIMEOUT_CORTO,
    )
    yield client
    client.close()


@pytest.mark.unit
def test_bot_client_move_devuelve_ok_false_si_no_hay_servidor(bot_client_muerto):
    resultado = bot_client_muerto.move(dx=1, dy=0)
    assert resultado.ok is False
