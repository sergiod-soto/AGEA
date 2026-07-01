# tests/test_hypervisor.py
from unittest.mock import MagicMock
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor


def make_hv():
    gestor_mock = MagicMock()
    gestor_mock.forward_action.return_value = MagicMock(
        ok=True, payload=b"", error="", world_tick=1
    )
    return Hypervisor(
        hypervisor_id="hv_test",
        gestor_client=gestor_mock,
        capacity=10,
    )


# Test spawn y kill
def test_spawn_kill():
    hv = make_hv()
    info = hv.spawn_bot({"bot_id": "bot_001", "budget": 100})
    assert info.ok
    assert "bot_001" in hv._bots

    hv.kill_bot("bot_001")
    assert "bot_001" not in hv._bots


# Test crítico: try_spend_points
def test_puntos_suficientes():
    hv = make_hv()
    hv.spawn_bot({"bot_id": "bot_001", "budget": 5})

    ok, remaining = hv.try_spend_points("bot_001", cost=2)
    assert ok
    assert remaining == 3


def test_puntos_insuficientes():
    hv = make_hv()
    hv.spawn_bot({"bot_id": "bot_001", "budget": 1})

    ok, remaining = hv.try_spend_points("bot_001", cost=2)
    assert not ok
    assert remaining == 1  # no se descontó nada


def test_puntos_atomicos():
    # Dos hilos intentan gastar el mismo punto a la vez
    import threading

    hv = make_hv()
    hv.spawn_bot({"bot_id": "bot_001", "budget": 1})

    resultados = []

    def gastar():
        ok, _ = hv.try_spend_points("bot_001", cost=1)
        resultados.append(ok)

    hilos = [threading.Thread(target=gastar) for _ in range(10)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    # Solo uno debe haber tenido éxito
    assert resultados.count(True) == 1


# Test reset de presupuesto
def test_reset_budgets():
    hv = make_hv()
    hv.spawn_bot({"bot_id": "bot_001", "budget": 100})
    hv.try_spend_points("bot_001", cost=50)
    assert hv._bots["bot_001"].budget == 50

    hv.reset_budgets(["bot_001"], {"bot_001": 100})
    assert hv._bots["bot_001"].budget == 100


# Test capacidad máxima
def test_capacidad():
    hv = make_hv()  # capacity=10
    for i in range(10):
        info = hv.spawn_bot({"bot_id": f"bot_{i:03d}", "budget": 100})
        assert info.ok

    info = hv.spawn_bot({"bot_id": "bot_overflow", "budget": 100})
    assert not info.ok
    assert "capacidad" in info.error.lower()
