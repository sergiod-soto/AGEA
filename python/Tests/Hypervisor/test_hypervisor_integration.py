# tests/test_hypervisor_integration.py
import time
import threading
from unittest.mock import MagicMock
from Hypervisores.Hypervisor.hypervisor import Hypervisor
from Hypervisores.Hypervisor.hypervisor_server import build_servers
from Hypervisores.Transporte.hypervisor_client import HypervisorClient


def test_servidor_completo():
    # Gestor mock: forward_action devuelve ok
    gestor_mock = MagicMock()
    gestor_mock.register_hypervisor.return_value = True
    gestor_mock.forward_action.return_value = MagicMock(
        ok=True, payload=b"", error="", world_tick=1
    )

    # Levantamos en puertos aleatorios para no colisionar
    mgmt_server, proxy_server, hv, _ = build_servers(
        hv_id="hv_test",
        my_port=59052,
        my_proxy_port=59053,
        gestor_address="localhost:59051",  # no existe, pero no se llama
    )
    mgmt_server.start()
    proxy_server.start()
    time.sleep(0.2)  # esperar a que levante

    try:
        client = HypervisorClient("localhost", 59052)

        # Spawn
        info = client.spawn_bot({"bot_id": "bot_001", "budget": 100})
        assert info.ok

        # Stats
        stats = client.get_bot_stats("bot_001")
        assert stats is not None
        assert stats.points_left == 100

        # Reset
        ok = client.reset_budgets(["bot_001"], {"bot_001": 50})
        assert ok

        stats = client.get_bot_stats("bot_001")
        assert stats.points_left == 50

        # Kill
        ok = client.kill_bot("bot_001")
        assert ok

        client.close()
    finally:
        mgmt_server.stop(0)
        proxy_server.stop(0)
