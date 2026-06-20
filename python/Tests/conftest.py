"""
conftest.py — Fixtures compartidos entre todos los tests.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock


# ---------------------------------------------------------------------------
# Fixtures de GestorBots
# ---------------------------------------------------------------------------

@pytest.fixture
def mundo_client():
    client = MagicMock()
    client.forward_action = MagicMock(return_value=MagicMock(ok=True, payload=b"", error=""))
    return client


@pytest.fixture
def gestor_bots(mundo_client):
    from Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
    return Gestor_Bots(mundo_client=mundo_client, bots_por_hypervisor=10)


@pytest.fixture
def hv_client():
    client = MagicMock()
    client.spawn_bot = MagicMock(return_value=MagicMock(ok=True, error=""))
    client.kill_bot = MagicMock(return_value=True)
    client.reset_budgets = MagicMock(return_value=True)
    return client


@pytest.fixture
def gestor_bots_con_hv(gestor_bots, hv_client):
    """Gestor_Bots con un Hypervisor ya registrado y con cliente."""
    gestor_bots.register_hypervisor(
        hypervisor_id="hv_001",
        address="localhost",
        port=50052,
        proxy_port=50053,
        capacity=10,
    )
    gestor_bots.set_hypervisor_client("hv_001", hv_client)
    return gestor_bots, hv_client


# ---------------------------------------------------------------------------
# Fixtures de Hypervisor
# ---------------------------------------------------------------------------

@pytest.fixture
def gestor_client():
    client = MagicMock()
    client.register_hypervisor = MagicMock(
        return_value=MagicMock(ok=True, delegated_actions=[], error="")
    )
    client.update_hypervisor_load = MagicMock()
    client.forward_action = MagicMock(
        return_value=MagicMock(ok=True, payload=b"", error="")
    )
    return client


@pytest.fixture
def gestor_mundo_client():
    client = MagicMock()
    client.forward_action = MagicMock(
        return_value=MagicMock(ok=True, payload=b"", error="")
    )
    return client


@pytest.fixture
def hypervisor(gestor_client, gestor_mundo_client):
    from Gestores.Bots.Hypervisor.hypervisor import Hypervisor
    return Hypervisor(
        hypervisor_id="hv_test",
        gestor_client=gestor_client,
        gestor_mundo_client=gestor_mundo_client,
        capacity=5,
    )


# ---------------------------------------------------------------------------
# Fixtures de Sector
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=False)
def sector_env(monkeypatch):
    """Configura variables de entorno para un sector 0,0 de tamaño 10."""
    monkeypatch.setenv("SECTOR_COL", "0")
    monkeypatch.setenv("SECTOR_ROW", "0")
    monkeypatch.setenv("SECTOR_SIZE", "10")
    monkeypatch.setenv("MAX_VISION_DISTANCE", "5")


@pytest.fixture
def sector(sector_env):
    from Gestores.Mundo.Sector.sector import Sector
    return Sector()


@pytest.fixture
def sector_activo(sector):
    from Gestores.Mundo.Sector.sector import SectorMode
    sector.set_mode(SectorMode.ACTIVO)
    return sector


# ---------------------------------------------------------------------------
# Helpers de construcción de protos mock
# ---------------------------------------------------------------------------

def make_mock_cell(x, y, element=b"data"):
    cell = MagicMock()
    cell.pos.x = x
    cell.pos.y = y
    cell.element = element
    return cell


def make_mock_bot(bot_id, x, y, budget=100):
    bot = MagicMock()
    bot.bot_id = bot_id
    bot.pos.x = x
    bot.pos.y = y
    bot.budget = budget
    return bot
