"""
Integration/Hypervisor/test_hypervisor_servicer.py
Tests de integración del HypervisorServicer con un Hypervisor real.
Sin red gRPC — el servicer se instancia directamente.
"""
import gzip
import pytest
from unittest.mock import MagicMock, patch


def _codigo_gz(contenido="print('bot')"):
    return gzip.compress(contenido.encode())


@pytest.fixture
def servicer(hypervisor):
    from Gestores.Bots.Hypervisor.hypervisor_servicer import HypervisorServicer
    return HypervisorServicer(hypervisor)


@pytest.fixture
def context():
    return MagicMock()


# ---------------------------------------------------------------------------
# SpawnBot
# ---------------------------------------------------------------------------

class TestSpawnBot:
    def test_spawn_exitoso(self, servicer, context, tmp_path):
        with patch.object(servicer._hv, "_codigo_path",
                          return_value=tmp_path / "bot.py"), \
             patch("subprocess.Popen", return_value=MagicMock()):
            request = MagicMock()
            request.config.bot_id = "bot_001"
            request.config.codigo_gz = _codigo_gz()
            request.config.budget = 100
            request.config.metadata = {}
            resp = servicer.SpawnBot(request, context)
        assert resp.ok is True
        assert resp.bot_id == "bot_001"

    def test_spawn_bot_id_vacio(self, servicer, context):
        request = MagicMock()
        request.config.bot_id = ""
        request.config.codigo_gz = _codigo_gz()
        request.config.budget = 100
        request.config.metadata = {}
        resp = servicer.SpawnBot(request, context)
        assert resp.ok is False


# ---------------------------------------------------------------------------
# KillBot
# ---------------------------------------------------------------------------

class TestKillBot:
    def test_kill_bot_existente(self, servicer, context, tmp_path):
        with patch.object(servicer._hv, "_codigo_path",
                          return_value=tmp_path / "bot.py"), \
             patch("subprocess.Popen", return_value=MagicMock()):
            spawn_req = MagicMock()
            spawn_req.config.bot_id = "bot_001"
            spawn_req.config.codigo_gz = _codigo_gz()
            spawn_req.config.budget = 100
            spawn_req.config.metadata = {}
            servicer.SpawnBot(spawn_req, context)

        kill_req = MagicMock()
        kill_req.bot_id = "bot_001"
        resp = servicer.KillBot(kill_req, context)
        assert resp.ok is True
        assert "bot_001" not in servicer._hv._bots

    def test_kill_bot_desconocido(self, servicer, context):
        request = MagicMock()
        request.bot_id = "bot_inexistente"
        resp = servicer.KillBot(request, context)
        assert resp.ok is True  # kill de desconocido no es error


# ---------------------------------------------------------------------------
# GetBotStats / GetBotStatus
# ---------------------------------------------------------------------------

class TestGetBotStats:
    def _spawn(self, servicer, context, tmp_path, bot_id="bot_001"):
        with patch.object(servicer._hv, "_codigo_path",
                          return_value=tmp_path / f"{bot_id}.py"), \
             patch("subprocess.Popen", return_value=MagicMock()):
            req = MagicMock()
            req.config.bot_id = bot_id
            req.config.codigo_gz = _codigo_gz()
            req.config.budget = 100
            req.config.metadata = {}
            servicer.SpawnBot(req, context)

    def test_get_bot_stats(self, servicer, context, tmp_path):
        self._spawn(servicer, context, tmp_path)
        request = MagicMock()
        request.bot_id = "bot_001"
        resp = servicer.GetBotStats(request, context)
        assert resp.bot_id == "bot_001"

    def test_get_bot_status(self, servicer, context, tmp_path):
        self._spawn(servicer, context, tmp_path)
        request = MagicMock()
        request.bot_id = "bot_001"
        resp = servicer.GetBotStatus(request, context)
        assert resp.bot_id == "bot_001"
        assert resp.alive is True


# ---------------------------------------------------------------------------
# ResetBudgets
# ---------------------------------------------------------------------------

class TestResetBudgets:
    def test_reset_budgets(self, servicer, context, tmp_path):
        with patch.object(servicer._hv, "_codigo_path",
                          return_value=tmp_path / "bot.py"), \
             patch("subprocess.Popen", return_value=MagicMock()):
            spawn_req = MagicMock()
            spawn_req.config.bot_id = "bot_001"
            spawn_req.config.codigo_gz = _codigo_gz()
            spawn_req.config.budget = 100
            spawn_req.config.metadata = {}
            servicer.SpawnBot(spawn_req, context)

        # Gastar algo de budget
        servicer._hv.try_spend_points("bot_001", 50)

        reset_req = MagicMock()
        reset_req.bot_ids = ["bot_001"]
        reset_req.default_budget = 100
        reset_req.overrides = []
        resp = servicer.ResetBudgets(reset_req, context)
        assert resp.ok is True
        assert servicer._hv._bots["bot_001"].budget == 100


# ---------------------------------------------------------------------------
# SetPointBudget
# ---------------------------------------------------------------------------

class TestSetPointBudget:
    def test_set_point_budget(self, servicer, context, tmp_path):
        with patch.object(servicer._hv, "_codigo_path",
                          return_value=tmp_path / "bot.py"), \
             patch("subprocess.Popen", return_value=MagicMock()):
            spawn_req = MagicMock()
            spawn_req.config.bot_id = "bot_001"
            spawn_req.config.codigo_gz = _codigo_gz()
            spawn_req.config.budget = 100
            spawn_req.config.metadata = {}
            servicer.SpawnBot(spawn_req, context)

        req = MagicMock()
        req.bot_id = "bot_001"
        req.points = 50
        resp = servicer.SetPointBudget(req, context)
        assert resp.ok is True
        assert servicer._hv._bots["bot_001"].budget == 50


# ---------------------------------------------------------------------------
# ListBots
# ---------------------------------------------------------------------------

class TestListBots:
    def test_list_bots(self, servicer, context, tmp_path):
        for i in range(3):
            with patch.object(servicer._hv, "_codigo_path",
                              return_value=tmp_path / f"bot_{i}.py"), \
                 patch("subprocess.Popen", return_value=MagicMock()):
                req = MagicMock()
                req.config.bot_id = f"bot_{i:03d}"
                req.config.codigo_gz = _codigo_gz()
                req.config.budget = 100
                req.config.metadata = {}
                servicer.SpawnBot(req, context)

        resp = servicer.ListBots(MagicMock(), context)
        assert len(resp.bots) == 3
