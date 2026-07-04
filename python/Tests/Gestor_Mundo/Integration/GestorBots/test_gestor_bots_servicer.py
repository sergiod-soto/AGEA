"""
Integration/GestorBots/test_gestor_bots_servicer.py
Tests de integración del Gestor_Bots_Servicer con un Gestor_Bots real.
Verifica que el dispatch del servicer conecta correctamente con la lógica del gestor.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def servicer(gestor_bots):
    from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots_servicer import (
        Gestor_Bots_Servicer,
    )

    hv_client_factory = MagicMock(
        return_value=MagicMock(
            spawn_bot=AsyncMock(return_value=MagicMock(ok=True, error="")),
            kill_bot=AsyncMock(return_value=True),
            reset_budgets=AsyncMock(return_value=True),
        )
    )
    return Gestor_Bots_Servicer(
        gestor_bots, hypervisor_client_factory=hv_client_factory
    )


@pytest.fixture
def context():
    return MagicMock()


# ---------------------------------------------------------------------------
# RegisterHypervisor
# ---------------------------------------------------------------------------


class TestRegisterHypervisor:
    async def test_registro_exitoso(self, servicer, context):
        request = MagicMock()
        request.hypervisor_id = "hv_001"
        request.address = "localhost"
        request.port = 50052
        request.proxy_port = 50053
        request.capacity = 10
        with patch.object(
            servicer._gestor, "get_delegated_action_names", return_value=[]
        ):
            resp = await servicer.RegisterHypervisor(request, context)
        assert resp.ok is True

    async def test_registro_crea_cliente(self, servicer, context):
        request = MagicMock()
        request.hypervisor_id = "hv_nuevo"
        request.address = "localhost"
        request.port = 50052
        request.proxy_port = 50053
        request.capacity = 10
        with patch.object(
            servicer._gestor, "get_delegated_action_names", return_value=[]
        ):
            await servicer.RegisterHypervisor(request, context)
        assert "hv_nuevo" in servicer._gestor._hypervisor_clients

    async def test_registro_incluye_acciones_delegadas(self, servicer, context):
        request = MagicMock()
        request.hypervisor_id = "hv_001"
        request.address = "localhost"
        request.port = 50052
        request.proxy_port = 50053
        request.capacity = 10
        with patch.object(
            servicer._gestor, "get_delegated_action_names", return_value=["mirar"]
        ):
            resp = await servicer.RegisterHypervisor(request, context)
        assert "mirar" in resp.delegated_actions


# ---------------------------------------------------------------------------
# SpawnBot
# ---------------------------------------------------------------------------


class TestSpawnBot:
    async def _register_hv(self, servicer, context):
        req = MagicMock()
        req.hypervisor_id = "hv_001"
        req.address = "localhost"
        req.port = 50052
        req.proxy_port = 50053
        req.capacity = 10
        with patch.object(
            servicer._gestor, "get_delegated_action_names", return_value=[]
        ):
            await servicer.RegisterHypervisor(req, context)

    async def test_spawn_exitoso(self, servicer, context):
        await self._register_hv(servicer, context)
        request = MagicMock()
        request.config.bot_id = "bot_001"
        request.config.codigo_gz = b""
        request.config.budget = 100
        request.config.metadata = {}
        resp = await servicer.SpawnBot(request, context)
        assert resp.ok is True

    async def test_spawn_sin_hvs_falla(self, servicer, context):
        request = MagicMock()
        request.config.bot_id = "bot_001"
        request.config.codigo_gz = b""
        request.config.stats = {}
        request.config.metadata = {}
        resp = await servicer.SpawnBot(request, context)
        assert resp.ok is False


# ---------------------------------------------------------------------------
# KillBot
# ---------------------------------------------------------------------------


class TestKillBot:
    async def test_kill_bot(self, servicer, context):
        # Registrar HV y spawn
        reg_req = MagicMock()
        reg_req.hypervisor_id = "hv_001"
        reg_req.address = "localhost"
        reg_req.port = 50052
        reg_req.proxy_port = 50053
        reg_req.capacity = 10
        with patch.object(
            servicer._gestor, "get_delegated_action_names", return_value=[]
        ):
            await servicer.RegisterHypervisor(reg_req, context)

        spawn_req = MagicMock()
        spawn_req.config.bot_id = "bot_001"
        spawn_req.config.codigo_gz = b""
        spawn_req.config.budget = 100
        spawn_req.config.metadata = {}
        await servicer.SpawnBot(spawn_req, context)

        kill_req = MagicMock()
        kill_req.bot_id = "bot_001"
        resp = await servicer.KillBot(kill_req, context)
        assert resp.ok is True
        assert "bot_001" not in servicer._gestor._bots


# ---------------------------------------------------------------------------
# BroadcastBudgets
# ---------------------------------------------------------------------------


class TestBroadcastBudgets:
    async def test_broadcast(self, servicer, context):
        request = MagicMock()
        request.default_budget = 100
        request.overrides = []
        resp = await servicer.BroadcastBudgets(request, context)
        assert resp.ok is True


# ---------------------------------------------------------------------------
# UpdateHypervisorLoad
# ---------------------------------------------------------------------------


class TestUpdateHypervisorLoad:
    async def test_update_load(self, servicer, context):
        reg_req = MagicMock()
        reg_req.hypervisor_id = "hv_001"
        reg_req.address = "localhost"
        reg_req.port = 50052
        reg_req.proxy_port = 50053
        reg_req.capacity = 10
        with patch.object(
            servicer._gestor, "get_delegated_action_names", return_value=[]
        ):
            await servicer.RegisterHypervisor(reg_req, context)

        request = MagicMock()
        request.hypervisor_id = "hv_001"
        request.current_load = 7
        resp = await servicer.UpdateHypervisorLoad(request, context)
        assert resp.ok is True
        assert servicer._gestor._hypervisors["hv_001"].current_load == 7


# ---------------------------------------------------------------------------
# ListHypervisors
# ---------------------------------------------------------------------------


class TestListHypervisors:
    async def test_list_hvs(self, servicer, context):
        reg_req = MagicMock()
        reg_req.hypervisor_id = "hv_001"
        reg_req.address = "localhost"
        reg_req.port = 50052
        reg_req.proxy_port = 50053
        reg_req.capacity = 10
        with patch.object(
            servicer._gestor, "get_delegated_action_names", return_value=[]
        ):
            await servicer.RegisterHypervisor(reg_req, context)

        request = MagicMock()
        resp = await servicer.ListHypervisors(request, context)
        assert any(hv.hypervisor_id == "hv_001" for hv in resp.hypervisors)


# ---------------------------------------------------------------------------
# ForwardAction
# ---------------------------------------------------------------------------


class TestForwardAction:
    async def test_forward_action(self, servicer, context, mundo_client):
        from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import ActionResult

        mundo_client.forward_action = AsyncMock(
            return_value=ActionResult(ok=True, payload=b"resultado", error="")
        )
        request = MagicMock()
        request.bot_id = "bot_001"
        request.hypervisor_id = "hv_001"
        request.action_type = "mirar"
        request.payload = b"payload"
        resp = await servicer.ForwardAction(request, context)
        assert resp.ok is True
