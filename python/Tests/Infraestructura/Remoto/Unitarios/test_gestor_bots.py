# Tests/Infraestructura/Remoto/Unitarios/test_gestor_bots.py
"""
test_gestor_bots.py — Pruebas unitarias de Gestor_Bots: selección de
HV, spawn/kill de bots, y detección de HVs caídos por staleness
(hypervisores_caidos), que es la pieza nueva de la cascada de heartbeat.

Los "clientes de HV" aquí son objetos falsos simples (no FakeStub de
conftest, porque Gestor_Bots habla con un cliente Python de alto nivel
—HypervisorClient—, no con un stub gRPC crudo).
"""

import time

import pytest

from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import (
    Gestor_Bots,
    UMBRAL_HV_CAIDO_SEGUNDOS,
)
from Infraestructura.Gestores.tipos_comunes import ActionResult


class FakeHypervisorClient:
    def __init__(self, ok: bool = True, error: str = ""):
        self._ok = ok
        self._error = error
        self.spawn_bot_llamado_con = None

    async def spawn_bot(self, bot_config: dict) -> ActionResult:
        self.spawn_bot_llamado_con = bot_config
        return ActionResult(ok=self._ok, error=self._error)

    async def kill_bot(self, bot_id: int) -> None:
        pass


@pytest.fixture
def gestor() -> Gestor_Bots:
    return Gestor_Bots(logica_client=None, bots_por_hypervisor=2)


@pytest.mark.unit
def test_hvs_necesarios_redondea_hacia_arriba(gestor: Gestor_Bots):
    assert gestor.hvs_necesarios(total_bots=5) == 3  # ceil(5/2)
    assert gestor.hvs_necesarios(total_bots=4) == 2
    assert gestor.hvs_necesarios(total_bots=0) == 0


@pytest.mark.unit
def test_bots_por_hypervisor_invalido_lanza():
    with pytest.raises(ValueError):
        Gestor_Bots(logica_client=None, bots_por_hypervisor=0)


@pytest.mark.unit
async def test_spawn_bot_sin_hypervisores_falla(gestor: Gestor_Bots):
    info = await gestor.spawn_bot({"bot_id": "bot_1", "budget": 10})
    assert info.ok is False
    assert "sin hypervisores" in info.error.lower()


@pytest.mark.unit
async def test_spawn_bot_bot_id_vacio_falla(gestor: Gestor_Bots):
    info = await gestor.spawn_bot({"bot_id": "", "budget": 10})
    assert info.ok is False
    assert "bot_id" in info.error.lower()


@pytest.mark.unit
async def test_spawn_bot_selecciona_hv_con_menos_carga(gestor: Gestor_Bots):
    await gestor.register_hypervisor("hv_a", "localhost", 1, 2, capacity=2)
    await gestor.register_hypervisor("hv_b", "localhost", 3, 4, capacity=2)

    client_a = FakeHypervisorClient(ok=True)
    client_b = FakeHypervisorClient(ok=True)
    await gestor.set_hypervisor_client("hv_a", client_a)
    await gestor.set_hypervisor_client("hv_b", client_b)

    # Ambos HV empiezan con carga 0 — min() debe elegir el primero
    # (empate resuelto por orden de inserción, comportamiento de min()).
    info = await gestor.spawn_bot({"bot_id": "bot_1", "budget": 5})
    assert info.ok is True
    assert info.hypervisor_id == "hv_a"
    assert client_a.spawn_bot_llamado_con["bot_id"] == "bot_1"


@pytest.mark.unit
async def test_spawn_bot_hv_a_plena_capacidad_no_se_elige(gestor: Gestor_Bots):
    await gestor.register_hypervisor("hv_lleno", "localhost", 1, 2, capacity=2)
    await gestor.set_hypervisor_client("hv_lleno", FakeHypervisorClient(ok=True))

    # Llenar manualmente hasta capacidad (2, según bots_por_hypervisor de la fixture)
    await gestor.spawn_bot({"bot_id": "b1", "budget": 1})
    await gestor.spawn_bot({"bot_id": "b2", "budget": 1})

    info = await gestor.spawn_bot({"bot_id": "b3", "budget": 1})
    assert info.ok is False
    assert "sin hypervisores" in info.error.lower()


@pytest.mark.unit
async def test_spawn_bot_fallo_de_hv_revierte_registro(gestor: Gestor_Bots):
    """
    Si el cliente del HV falla, el bot no debe quedar registrado ni la
    carga incrementada — Gestor_Bots debe deshacer su propio estado.
    """
    await gestor.register_hypervisor("hv_a", "localhost", 1, 2, capacity=5)
    await gestor.set_hypervisor_client(
        "hv_a", FakeHypervisorClient(ok=False, error="boom")
    )

    info = await gestor.spawn_bot({"bot_id": "bot_x", "budget": 5})
    assert info.ok is False

    lista = await gestor.list_hypervisors()
    assert (
        lista.hypervisors[0].current_load == 0
    ), "la carga debe revertirse tras el fallo"


@pytest.mark.unit
async def test_kill_bot_decrementa_carga(gestor: Gestor_Bots):
    await gestor.register_hypervisor("hv_a", "localhost", 1, 2, capacity=5)
    await gestor.set_hypervisor_client("hv_a", FakeHypervisorClient(ok=True))
    await gestor.spawn_bot({"bot_id": "bot_1", "budget": 5})

    await gestor.kill_bot("bot_1")

    lista = await gestor.list_hypervisors()
    assert lista.hypervisors[0].current_load == 0


@pytest.mark.unit
async def test_kill_bot_desconocido_no_lanza(gestor: Gestor_Bots):
    await gestor.kill_bot("no_existe")  # no debe lanzar, solo loguear warning


# ── hypervisores_caidos() — detección por staleness ────────────────


@pytest.mark.unit
async def test_hypervisores_caidos_vacio_si_todos_recientes(gestor: Gestor_Bots):
    await gestor.register_hypervisor("hv_a", "localhost", 1, 2, capacity=5)
    assert await gestor.hypervisores_caidos() == []


@pytest.mark.unit
async def test_hypervisores_caidos_detecta_por_last_seen_antiguo(gestor: Gestor_Bots):
    await gestor.register_hypervisor("hv_a", "localhost", 1, 2, capacity=5)

    # Forzar last_seen al pasado, más allá del umbral — sin esperar de
    # verdad UMBRAL_HV_CAIDO_SEGUNDOS reales en el test.
    async with gestor._lock:
        gestor._hypervisors["hv_a"].last_seen = time.monotonic() - (
            UMBRAL_HV_CAIDO_SEGUNDOS + 1
        )

    caidos = await gestor.hypervisores_caidos()
    assert caidos == ["hv_a"]


@pytest.mark.unit
async def test_update_hypervisor_load_resetea_last_seen(gestor: Gestor_Bots):
    await gestor.register_hypervisor("hv_a", "localhost", 1, 2, capacity=5)

    async with gestor._lock:
        gestor._hypervisors["hv_a"].last_seen = time.monotonic() - (
            UMBRAL_HV_CAIDO_SEGUNDOS + 1
        )

    await gestor.update_hypervisor_load("hv_a", current_load=1)

    assert (
        await gestor.hypervisores_caidos() == []
    ), "un push reciente de carga debe limpiar el estado de caído"


@pytest.mark.unit
async def test_update_hypervisor_load_hv_desconocido_no_lanza(gestor: Gestor_Bots):
    await gestor.update_hypervisor_load("no_existe", current_load=1)  # solo warning
