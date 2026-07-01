# tests/test_hypervisor_servicer.py
from unittest.mock import MagicMock
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor_servicer import HypervisorServicer
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    hypervisor_service_pb2
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import common_pb2

def make_servicer():
    gestor_mock = MagicMock()
    hv = Hypervisor("hv_test", gestor_mock, capacity=10)
    return HypervisorServicer(hv), MagicMock()  # (servicer, context_mock)

def test_spawn_bot_rpc():
    servicer, ctx = make_servicer()
    request = hypervisor_service_pb2.SpawnBotRequest(
        config=common_pb2.BotConfig(
            bot_id="bot_001",
            budget=100,
        )
    )
    response = servicer.SpawnBot(request, ctx)
    assert response.ok
    assert response.bot_id == "bot_001"

def test_reset_budgets_rpc():
    servicer, ctx = make_servicer()

    # Primero spawneamos
    servicer.SpawnBot(hypervisor_service_pb2.SpawnBotRequest(
        config=common_pb2.BotConfig(bot_id="bot_001", budget=100)
    ), ctx)

    # Reseteamos
    request = hypervisor_service_pb2.ResetBudgetsRequest(
        bot_ids=["bot_001"],
        default_budget=200,
    )
    response = servicer.ResetBudgets(request, ctx)
    assert response.ok

def test_get_bot_status_not_found():
    servicer, ctx = make_servicer()
    request = hypervisor_service_pb2.BotIdRequest(bot_id="no_existe")
    servicer.GetBotStatus(request, ctx)
    ctx.set_code.assert_called_once()   # debe haber puesto NOT_FOUND