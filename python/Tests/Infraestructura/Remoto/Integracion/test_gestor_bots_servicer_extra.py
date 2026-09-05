# Tests/Infraestructura/Remoto/Integracion/test_gestor_bots_servicer_extra.py
"""
test_gestor_bots_servicer_extra.py — Completa la cobertura de
Gestor_Bots_Servicer que dejaba fuera test_gestor_bots_servicer.py (el
fichero ya existente del proyecto, que solo prueba RegisterHypervisor/
ListHypervisors/Heartbeat). Aquí se ejercitan sobre gRPC real:
SpawnBot, KillBot, MatarScriptBot, NotificarAvatarSinPiloto,
BroadcastBudgets, ResetBudgets, FreezeAll, ResumeAll, SaveSnapshot,
UpdateHypervisorLoad, ForwardAction — y se documenta el hallazgo de
LoadState.
"""

import grpc.aio
import pytest

from Infraestructura.Gestores.Bots.GestorBots.gestor_bots import Gestor_Bots
from Infraestructura.Gestores.Bots.GestorBots.gestor_bots_servicer import (
    Gestor_Bots_Servicer,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as pb,
    gestor_bots_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.tipos_comunes import ActionResult


class FakeHVClient:
    """Doble async del cliente hacia un Hypervisor concreto — mismo
    contrato que HypervisorClient (spawn_bot/kill_bot/reset_budgets/
    freeze/resume/save_snapshot, todos async)."""

    def __init__(self):
        self.llamadas = []

    async def spawn_bot(self, bot_config):
        self.llamadas.append(("spawn_bot", bot_config))
        return type("FakeBotInfo", (), {"ok": True, "error": ""})()

    async def kill_bot(self, bot_id):
        self.llamadas.append(("kill_bot", bot_id))

    async def reset_budgets(self, bot_ids, budget_map):
        self.llamadas.append(("reset_budgets", bot_ids, budget_map))

    async def freeze(self):
        self.llamadas.append(("freeze",))

    async def resume(self):
        self.llamadas.append(("resume",))

    async def save_snapshot(self, snapshot_id):
        self.llamadas.append(("save_snapshot", snapshot_id))


class FakeLogicaClient:
    def __init__(self):
        self.eliminar_avatar_llamado_con = None
        self.resolver_accion_llamado_con = None

    async def eliminar_avatar_bot(self, bot_id):
        self.eliminar_avatar_llamado_con = bot_id
        return True, ""

    async def resolver_accion(self, bot_id, action_type, payload):
        self.resolver_accion_llamado_con = (bot_id, action_type, payload)
        return ActionResult(ok=True, payload=b"resultado", error="", world_tick=3)

    async def close(self):
        pass


@pytest.fixture
async def cliente_gestor_bots(levantar_servidor):
    logica_client = FakeLogicaClient()
    gestor = Gestor_Bots(logica_client=logica_client, bots_por_hypervisor=10)
    servicer = Gestor_Bots_Servicer(gestor=gestor, hypervisor_client_factory=None)
    servidor = await levantar_servidor(
        lambda s: pb_grpc.add_GestorBotsServiceServicer_to_server(servicer, s)
    )

    channel = grpc.aio.insecure_channel(servidor.address)
    stub = pb_grpc.GestorBotsServiceStub(channel)
    yield stub, gestor
    await channel.close()


async def _registrar_hv_con_cliente(gestor: Gestor_Bots, hv_id="hv_00") -> FakeHVClient:
    """
    Registra el HV en la lógica de negocio directamente (sin pasar por
    el RPC RegisterHypervisor) e inyecta un cliente falso — mismo
    patrón que ya usa test_gestor_bots_servicer.py (proyecto) para no
    depender de un HypervisorClient real.
    """
    await gestor.register_hypervisor(
        hypervisor_id=hv_id, address="localhost", port=1, proxy_port=2, capacity=10
    )
    cliente = FakeHVClient()
    await gestor.set_hypervisor_client(hv_id, cliente)
    return cliente


@pytest.mark.integration
async def test_spawn_bot_y_kill_bot_via_grpc(cliente_gestor_bots):
    stub, gestor = cliente_gestor_bots
    await _registrar_hv_con_cliente(gestor)

    resp = await stub.SpawnBot(
        pb.SpawnBotRequest(config=common_pb2.BotConfig(bot_id="bot_1", budget=10))
    )
    assert resp.ok is True

    resp_kill = await stub.KillBot(pb.BotIdRequest(bot_id="bot_1"))
    assert resp_kill.ok is True


@pytest.mark.integration
async def test_matar_script_bot_via_grpc(cliente_gestor_bots):
    stub, gestor = cliente_gestor_bots
    hv_cliente = await _registrar_hv_con_cliente(gestor)
    await stub.SpawnBot(
        pb.SpawnBotRequest(config=common_pb2.BotConfig(bot_id="bot_1", budget=10))
    )

    resp = await stub.MatarScriptBot(pb.BotIdRequest(bot_id="bot_1"))

    assert resp.ok is True
    assert ("kill_bot", "bot_1") in hv_cliente.llamadas


@pytest.mark.integration
async def test_notificar_avatar_sin_piloto_via_grpc(cliente_gestor_bots):
    stub, gestor = cliente_gestor_bots

    resp = await stub.NotificarAvatarSinPiloto(pb.BotIdRequest(bot_id="bot_1"))

    assert resp.ok is True
    assert gestor.logica_client.eliminar_avatar_llamado_con == "bot_1"


@pytest.mark.integration
async def test_broadcast_budgets_via_grpc(cliente_gestor_bots):
    stub, gestor = cliente_gestor_bots
    hv_cliente = await _registrar_hv_con_cliente(gestor)
    await stub.SpawnBot(
        pb.SpawnBotRequest(config=common_pb2.BotConfig(bot_id="bot_1", budget=10))
    )

    resp = await stub.BroadcastBudgets(
        pb.BroadcastBudgetsRequest(default_budget=50, overrides=[])
    )

    assert resp.ok is True
    llamadas_reset = [l for l in hv_cliente.llamadas if l[0] == "reset_budgets"]
    assert len(llamadas_reset) == 1


@pytest.mark.integration
async def test_reset_budgets_via_grpc(cliente_gestor_bots):
    """
    ResetBudgetsRequest está vacío por diseño (ver Funciones/
    reset_budgets.py — el budget por defecto viene de la config del
    propio gestor, no de la petición).
    """
    stub, gestor = cliente_gestor_bots
    await _registrar_hv_con_cliente(gestor)

    resp = await stub.ResetBudgets(pb.ResetBudgetsRequest())

    assert resp.ok is True


@pytest.mark.integration
async def test_freeze_all_y_resume_all_via_grpc(cliente_gestor_bots):
    stub, gestor = cliente_gestor_bots
    hv_cliente = await _registrar_hv_con_cliente(gestor)

    resp_freeze = await stub.FreezeAll(pb.FreezeAllRequest())
    assert resp_freeze.ok is True
    assert ("freeze",) in hv_cliente.llamadas

    resp_resume = await stub.ResumeAll(pb.ResumeAllRequest())
    assert resp_resume.ok is True
    assert ("resume",) in hv_cliente.llamadas


@pytest.mark.integration
async def test_save_snapshot_via_grpc(cliente_gestor_bots):
    stub, gestor = cliente_gestor_bots
    hv_cliente = await _registrar_hv_con_cliente(gestor)

    resp = await stub.SaveSnapshot(pb.SaveSnapshotRequest(snapshot_id="snap_1"))

    assert resp.ok is True
    assert resp.snapshot_id == "snap_1"
    assert ("save_snapshot", "snap_1") in hv_cliente.llamadas


@pytest.mark.integration
async def test_update_hypervisor_load_via_grpc(cliente_gestor_bots):
    stub, gestor = cliente_gestor_bots
    await _registrar_hv_con_cliente(gestor)

    resp = await stub.UpdateHypervisorLoad(
        pb.UpdateLoadRequest(hypervisor_id="hv_00", current_load=5)
    )

    assert resp.ok is True
    lista = await gestor.list_hypervisors()
    assert lista.hypervisors[0].current_load == 5


@pytest.mark.integration
async def test_forward_action_via_grpc(cliente_gestor_bots):
    stub, gestor = cliente_gestor_bots

    resp = await stub.ForwardAction(
        pb.ForwardActionRequest(
            bot_id="bot_1", hypervisor_id="hv_00", action_type="mover", payload=b"x"
        )
    )

    assert resp.ok is True
    assert resp.payload == b"resultado"
    assert gestor.logica_client.resolver_accion_llamado_con == ("bot_1", "mover", b"x")


@pytest.mark.integration
async def test_load_state_falla_por_funcion_no_registrada(cliente_gestor_bots):
    """
    HALLAZGO: registry.py de Gestor_Bots no registra ninguna función
    'LoadState' en FUNCIONES (no hay Funciones/load_state.py entre los
    módulos importados ni listados), pero Gestor_Bots_Servicer.
    LoadState() hace self._dispatch['LoadState'].handle(...) — KeyError
    sin capturar en el servidor. gRPC lo traduce en un error genérico
    hacia el cliente en vez de propagar el KeyError tal cual. Este test
    debe seguir en rojo hasta que se registre la función que falta, o
    se retire el RPC si ya no hace falta (Gestor_Bots no persiste
    snapshot propio más allá de reenviar SaveSnapshot a cada HV).
    """
    stub, _ = cliente_gestor_bots

    with pytest.raises(grpc.aio.AioRpcError):
        await stub.LoadState(pb.LoadStateRequest(snapshot_id="x"))
