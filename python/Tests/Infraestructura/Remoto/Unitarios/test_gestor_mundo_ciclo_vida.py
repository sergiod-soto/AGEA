# Tests/Infraestructura/Remoto/Unitarios/test_gestor_mundo_ciclo_vida.py
"""
test_gestor_mundo_ciclo_vida.py — Complementa test_gestor_mundo.py con
lo que aún no estaba cubierto: freeze/resume, set_tick_rate y
_actualizar_modos_sector (anti-thrashing). Se mantiene en fichero
aparte para no tocar el test_gestor_mundo.py ya existente.

No se ejercita start()/run_loop() (abrirían canales gRPC reales) — se
construye GestorMundo() e inyecta manualmente _bots_stub/_sectores,
igual que ya hace test_gestor_mundo.py con FakeStub.

HALLAZGO durante la escritura de estos tests (ver también el fichero
de integración test_gestor_mundo_servicer.py): Gestor_Mundo/Funciones/
set_tick_rate.py llama a `gestor.set_tick_rate(...)` SIN await, pese a
que GestorMundo.set_tick_rate es `async def`. Eso significa que se crea
la corrutina pero nunca se ejecuta su cuerpo — el RPC responde ok=True
pero el tick rate NO cambia realmente. El test de este fichero
(test_set_tick_rate_calcula_intervalo) prueba GestorMundo.set_tick_rate
directamente (con await, correcto) y por tanto pasa; es el test de
integración del servicer el que expone el bug end-to-end.
"""

from types import SimpleNamespace

import pytest

from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import (
    GestorMundo,
    SectorInfo,
    SystemState,
)
from Infraestructura.Gestores.Mundo.Sector.sector import SectorMode


class FakeLogicaClient:
    """Solo lo que necesita _distribute_gold_to_sectors() en resume()."""

    async def obtener_celdas_en_region(self, *args, **kwargs):
        return []


@pytest.fixture
def gestor() -> GestorMundo:
    return GestorMundo(logica_client=FakeLogicaClient())


def _ack(ok=True, error=""):
    return SimpleNamespace(ok=ok, error=error)


# ── freeze() ─────────────────────────────────────────────────────


@pytest.mark.unit
async def test_freeze_no_actua_si_no_esta_running(gestor, fake_stub_factory):
    gestor._state = SystemState.PAUSED
    # Sin respuestas configuradas: si freeze() intentara llamar a algo
    # de este stub, el test fallaría con AttributeError.
    gestor._bots_stub = fake_stub_factory()

    await gestor.freeze()

    assert gestor._state == SystemState.PAUSED  # no cambia


@pytest.mark.unit
async def test_freeze_pausa_bots_y_sectores_activos(gestor, fake_stub_factory):
    gestor._bots_stub = fake_stub_factory(FreezeAll=_ack())
    info_activo = SectorInfo(col=0, row=0, address="x", mode=SectorMode.ACTIVO)
    info_activo.stub = fake_stub_factory(SetSectorMode=_ack())
    info_inactivo = SectorInfo(col=1, row=0, address="x", mode=SectorMode.INACTIVO)
    gestor._sectores = {(0, 0): info_activo, (1, 0): info_inactivo}

    await gestor.freeze()

    assert gestor._state == SystemState.PAUSED
    assert gestor._pause_event.is_set() is False


# ── resume() ─────────────────────────────────────────────────────


@pytest.mark.unit
async def test_resume_no_actua_si_no_esta_paused(gestor):
    gestor._state = SystemState.RUNNING
    await gestor.resume()
    assert gestor._state == SystemState.RUNNING


@pytest.mark.unit
async def test_resume_recarga_gold_y_reanuda_bots(gestor, fake_stub_factory):
    gestor._state = SystemState.PAUSED
    gestor._pause_event.clear()
    gestor._bots_stub = fake_stub_factory(ResumeAll=_ack())
    info = SectorInfo(col=0, row=0, address="x")
    info.stub = fake_stub_factory(LoadState=_ack())
    gestor._sectores = {(0, 0): info}

    await gestor.resume()

    assert gestor._state == SystemState.RUNNING
    assert gestor._pause_event.is_set() is True


# ── set_tick_rate() ──────────────────────────────────────────────


@pytest.mark.unit
async def test_set_tick_rate_sin_limite_con_cero(gestor):
    await gestor.set_tick_rate(0)
    assert gestor._tick_rate == 0
    assert gestor._tick_interval == 0.0


@pytest.mark.unit
async def test_set_tick_rate_calcula_intervalo(gestor):
    await gestor.set_tick_rate(10)
    assert gestor._tick_rate == 10
    assert gestor._tick_interval == pytest.approx(0.1)


# ── _actualizar_modos_sector() — anti-thrashing ──────────────────


@pytest.mark.unit
async def test_actualizar_modos_sector_duerme_tras_alcanzar_umbral(
    gestor, fake_stub_factory
):
    gestor.TICKS_ANTES_DE_DORMIR = 1
    info = SectorInfo(col=0, row=0, address="x", mode=SectorMode.ACTIVO)
    info.ticks_sin_actividad = 0
    info.stub = fake_stub_factory(SetSectorMode=_ack())
    gestor._sectores = {(0, 0): info}

    await gestor._actualizar_modos_sector()

    assert info.mode == SectorMode.DORMIDO


@pytest.mark.unit
async def test_actualizar_modos_sector_despierta_vecinos_inactivos(
    gestor, fake_stub_factory
):
    """
    Un sector ACTIVO que aún no llega al umbral de dormir despierta (a
    DORMIDO) a sus vecinos INACTIVOS — para que estén listos si el bot
    se mueve hacia ellos en el siguiente tick.
    """
    gestor.TICKS_ANTES_DE_DORMIR = 100  # lejos de dormir en este tick
    activo = SectorInfo(col=1, row=1, address="x", mode=SectorMode.ACTIVO)
    vecino = SectorInfo(col=1, row=0, address="x", mode=SectorMode.INACTIVO)
    vecino.stub = fake_stub_factory(SetSectorMode=_ack())
    gestor._sectores = {(1, 1): activo, (1, 0): vecino}

    await gestor._actualizar_modos_sector()

    assert vecino.mode == SectorMode.DORMIDO
    assert activo.ticks_sin_actividad == 1
