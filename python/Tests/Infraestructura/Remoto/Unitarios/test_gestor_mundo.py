# Tests/Infraestructura/Remoto/Unitarios/test_gestor_mundo.py
"""
test_gestor_mundo.py — Pruebas unitarias de GestorMundo centradas en
la detección de sectores caídos (sectores_caidos), que es la pieza
nueva de la cascada de heartbeat. Se construye GestorMundo directamente
(sin llamar a start(), que abriría un canal gRPC real hacia
Gestor_Bots) y se le inyectan SectorInfo con FakeStub como stub.
"""

import pytest

from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import (
    GestorMundo,
    SectorInfo,
    FALLOS_CONSECUTIVOS_SECTOR_CAIDO,
)
from Infraestructura.Gestores.Mundo.Sector.sector import SectorMode


class FakeLogicaClient:
    """No se ejercita en estos tests — solo para satisfacer el constructor."""

    pass


@pytest.fixture
def gestor() -> GestorMundo:
    return GestorMundo(logica_client=FakeLogicaClient())


@pytest.mark.unit
def test_sectores_caidos_vacio_por_defecto(gestor: GestorMundo):
    gestor._sectores[(0, 0)] = SectorInfo(col=0, row=0, address="localhost:1")
    assert gestor.sectores_caidos() == []


@pytest.mark.unit
def test_sectores_caidos_detecta_por_fallos_consecutivos(gestor: GestorMundo):
    info = SectorInfo(col=0, row=0, address="localhost:1")
    info.fallos_consecutivos = FALLOS_CONSECUTIVOS_SECTOR_CAIDO
    gestor._sectores[(0, 0)] = info

    assert gestor.sectores_caidos() == ["0_0"]


@pytest.mark.unit
def test_sectores_caidos_por_debajo_del_umbral_no_cuenta(gestor: GestorMundo):
    info = SectorInfo(col=1, row=2, address="localhost:1")
    info.fallos_consecutivos = FALLOS_CONSECUTIVOS_SECTOR_CAIDO - 1
    gestor._sectores[(1, 2)] = info

    assert gestor.sectores_caidos() == []


@pytest.mark.unit
async def test_fase_1_incrementa_fallos_en_excepcion(
    gestor: GestorMundo, fake_stub_factory
):
    info = SectorInfo(col=0, row=0, address="localhost:1", mode=SectorMode.ACTIVO)
    info.stub = fake_stub_factory(StartTick=RuntimeError("sector caído"))
    gestor._sectores[(0, 0)] = info

    await gestor._fase_1()

    assert info.fallos_consecutivos == 1


@pytest.mark.unit
async def test_fase_1_resetea_fallos_tras_exito(gestor: GestorMundo, fake_stub_factory):
    class RespuestaOk:
        ok = True
        timed_out = False

    info = SectorInfo(col=0, row=0, address="localhost:1", mode=SectorMode.ACTIVO)
    info.fallos_consecutivos = 2
    info.stub = fake_stub_factory(StartTick=RespuestaOk())
    gestor._sectores[(0, 0)] = info

    await gestor._fase_1()

    assert info.fallos_consecutivos == 0


@pytest.mark.unit
async def test_fase_1_timeout_cuenta_como_fallo(gestor: GestorMundo, fake_stub_factory):
    class RespuestaTimeout:
        ok = True
        timed_out = True

    info = SectorInfo(col=0, row=0, address="localhost:1", mode=SectorMode.ACTIVO)
    info.stub = fake_stub_factory(StartTick=RespuestaTimeout())
    gestor._sectores[(0, 0)] = info

    await gestor._fase_1()

    assert info.fallos_consecutivos == 1


@pytest.mark.unit
def test_vecinos_devuelve_los_8_adyacentes(gestor: GestorMundo):
    for col in range(3):
        for row in range(3):
            gestor._sectores[(col, row)] = SectorInfo(col=col, row=row, address="x")

    vecinos = gestor._vecinos(gestor._sectores[(1, 1)])
    assert len(vecinos) == 8
    assert gestor._sectores[(1, 1)] not in vecinos


@pytest.mark.unit
def test_sector_para_posicion_calcula_col_row(gestor: GestorMundo):
    gestor.SECTOR_SIZE = 100
    gestor._sectores[(2, 3)] = SectorInfo(col=2, row=3, address="x")

    encontrado = gestor._sector_para_posicion(x=250, y=350)

    assert encontrado is gestor._sectores[(2, 3)]
