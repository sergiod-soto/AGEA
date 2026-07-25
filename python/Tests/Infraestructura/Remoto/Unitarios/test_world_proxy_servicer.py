# Tests/Infraestructura/Remoto/Unitarios/test_world_proxy_servicer.py
"""
test_world_proxy_servicer.py — Pruebas unitarias de WorldProxyServicer


Se llama a Act() directamente con un FakeContext (sin levantar un
servidor real) — lo que se quiere validar aquí es la lógica de negocio
(coste, reenvío), no la serialización de red; eso lo cubre
test_world_proxy_servicer_grpc.py (Integración).

test_hypervisor_acciones_delegadas.py queda OBSOLETO por la corrección
2 (probaba métodos de Hypervisor que ya no existen) y debe borrarse.
"""

import struct

import grpc
import pytest

from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Infraestructura.Gestores.Bots.Hypervisor.world_proxy_servicer import (
    WorldProxyServicer,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    world_proxy_service_pb2 as pb,
)
from Infraestructura.Gestores.tipos_comunes import ActionResult


class FakeContext:
    """Doble mínimo de ServicerContext: solo lo que _spend_and_forward
    necesita (metadata de entrada + set_code/set_details de salida)."""

    def __init__(self, metadata=()):
        self._metadata = metadata
        self.code = None
        self.details = None

    def invocation_metadata(self):
        return self._metadata

    def set_code(self, code):
        self.code = code

    def set_details(self, details):
        self.details = details


class FakeProceso:
    """Proceso que nunca termina por sí solo — basta para spawn_bot()."""

    def wait(self):
        import threading

        threading.Event().wait()


class FakeLanzador:
    def lanzar(self, hypervisor_id, bot_id, codigo_gz, env_extra):
        return FakeProceso()

    def limpiar(self, hypervisor_id, bot_id):
        pass


class FakeGestorClient:
    def __init__(self):
        self.forward_action_llamado_con = None
        self.forward_action_resultado = ActionResult(ok=True, payload=b"", error="")
        self.forward_action_excepcion = None

    def forward_action(self, bot_id, hypervisor_id, action_type, payload):
        self.forward_action_llamado_con = (bot_id, hypervisor_id, action_type, payload)
        if self.forward_action_excepcion:
            raise self.forward_action_excepcion
        return self.forward_action_resultado

    def notificar_avatar_sin_piloto(self, bot_id):
        pass


@pytest.fixture
def gestor_client() -> FakeGestorClient:
    return FakeGestorClient()


@pytest.fixture
def hv(gestor_client) -> Hypervisor:
    return Hypervisor(
        hypervisor_id="hv_test",
        gestor_client=gestor_client,
        capacity=5,
        lanzador_procesos=FakeLanzador(),
    )


@pytest.fixture
def servicer(hv) -> WorldProxyServicer:
    return WorldProxyServicer(hv)


def _act_request(action_name: str, payload: bytes = b"") -> pb.ActRequest:
    return pb.ActRequest(action_name=action_name, payload=payload)


# ── Act() — identificación y presupuesto ─────────────────────────


@pytest.mark.unit
def test_act_sin_bot_id_header_rechaza(servicer):
    context = FakeContext(metadata=())

    resp = servicer.Act(_act_request("mover"), context)

    assert resp.ok is False
    assert context.code == grpc.StatusCode.UNAUTHENTICATED


@pytest.mark.unit
def test_act_sin_puntos_suficientes_rechaza(hv, servicer):
    hv.spawn_bot({"bot_id": "bot_1", "budget": 0})
    context = FakeContext(metadata=(("bot-id", "bot_1"),))

    resp = servicer.Act(_act_request("mirar", struct.pack("<i", 5)), context)

    assert resp.ok is False
    assert "puntos insuficientes" in resp.error.lower()


# ── Act() — acción NO delegada → reenvío al Gestor ───────────────


@pytest.mark.unit
def test_act_accion_no_delegada_reenvia_al_gestor(hv, servicer, gestor_client):
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    gestor_client.forward_action_resultado = ActionResult(
        ok=True, payload=b"resultado", error="", world_tick=7
    )
    context = FakeContext(metadata=(("bot-id", "bot_1"),))

    resp = servicer.Act(_act_request("mover", b"payload_mover"), context)

    assert resp.ok is True
    assert resp.payload == b"resultado"
    assert resp.world_tick == 7
    bot_id, hv_id, action_type, payload = gestor_client.forward_action_llamado_con
    assert (bot_id, hv_id, action_type, payload) == (
        "bot_1",
        "hv_test",
        "mover",
        b"payload_mover",
    )


@pytest.mark.unit
def test_act_error_de_red_al_reenviar_devuelve_unavailable(hv, servicer, gestor_client):
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    gestor_client.forward_action_excepcion = RuntimeError("gestor caído")
    context = FakeContext(metadata=(("bot-id", "bot_1"),))

    resp = servicer.Act(_act_request("mover"), context)

    assert resp.ok is False
    assert context.code == grpc.StatusCode.UNAVAILABLE


# ── Act() — ya no existe rama delegada: TODO se reenvía ──────────


@pytest.mark.unit
def test_act_mirar_ya_no_se_delega_se_reenvia_como_cualquier_accion(
    hv, servicer, gestor_client
):
    """
    Antes de eliminar la delegación, 'mirar' habría intentado
    ejecutarse localmente en el HV (y habría explotado — ver
    test_hypervisor_acciones_delegadas.py, ahora obsoleto). Tras la
    corrección, 'mirar' es una acción como cualquier otra: se reenvía
    al Gestor → Mundo, donde Logica_Mundo sí tiene el estado real y sí
    la resuelve correctamente.
    """
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    gestor_client.forward_action_resultado = ActionResult(
        ok=True, payload=b"[[0,0,0]]", error=""
    )
    context = FakeContext(metadata=(("bot-id", "bot_1"),))

    resp = servicer.Act(_act_request("mirar", struct.pack("<i", 5)), context)

    assert resp.ok is True
    bot_id, hv_id, action_type, payload = gestor_client.forward_action_llamado_con
    assert action_type == "mirar"
