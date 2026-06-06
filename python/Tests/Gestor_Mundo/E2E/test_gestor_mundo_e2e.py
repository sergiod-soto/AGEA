"""
test_gestor_mundo_e2e.py
------------------------
Tests E2E de GestorMundo.

Carpeta destino: Tests/Gestor_Mundo/E2E/
Ejecutar desde D:/AGEA/python/:
    pytest Tests/Gestor_Mundo/E2E/test_gestor_mundo_e2e.py -v
"""

from __future__ import annotations

import json
import os

import pytest

from Gestores.Mundo.Gestor_Mundo.gestor_mundo import (
    GestorMundo,
    SectorInfo,
    SystemState,
)
from Gestores.Mundo.Sector.sector import SectorMode
from Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as sector_pb


SECTOR_SIZE = 10


def _make_bot(bot_id, x, y, budget=100):
    return sector_pb.BotSnapshot(
        bot_id=bot_id,
        pos=sector_pb.Position(x=x, y=y),
        state=b"",
        budget=budget,
    )


def _bot_en_sector(col, row, bot_id="bot_x"):
    cx = col * SECTOR_SIZE + SECTOR_SIZE // 2
    cy = row * SECTOR_SIZE + SECTOR_SIZE // 2
    return _make_bot(bot_id, cx, cy)


def _bot_en_borde_derecho(col, row, bot_id="bot_migra"):
    x = (col + 1) * SECTOR_SIZE
    y = row * SECTOR_SIZE + SECTOR_SIZE // 2
    return _make_bot(bot_id, x, y)


# ═══════════════════════════════════════════════════════════════════════════
#  Tick completo
# ═══════════════════════════════════════════════════════════════════════════


class TestTickCompleto:

    async def test_run_tick_no_explota(self, mundo_2x2):
        gestor, sectores, _ = mundo_2x2
        await gestor._run_tick()

    async def test_run_tick_incrementa_tick_id_en_todos(self, mundo_2x2):
        gestor, sectores, _ = mundo_2x2
        await gestor._run_tick()
        for sector in sectores.values():
            assert sector._current_tick_id == gestor._tick_id

    async def test_tres_ticks_consecutivos(self, mundo_2x2):
        gestor, sectores, _ = mundo_2x2
        for _ in range(3):
            await gestor._run_tick()
            gestor._tick_id += 1
        assert gestor._tick_id == 3

    async def test_reset_budgets_llamado_cada_tick(self, mundo_2x2):
        gestor, _, bots_svc = mundo_2x2
        n_ticks = 3
        for _ in range(n_ticks):
            await gestor._run_tick()
            gestor._tick_id += 1
        assert bots_svc.reset_count == n_ticks

    async def test_tick_con_sectores_dormidos_no_falla(self, mundo_2x2):
        gestor, sectores, _ = mundo_2x2
        info = gestor._sectores[(1, 1)]
        await gestor._set_sector_mode(info, SectorMode.DORMIDO)
        await gestor._run_tick()


# ═══════════════════════════════════════════════════════════════════════════
#  Gold cells y LoadState
# ═══════════════════════════════════════════════════════════════════════════


class TestGoldCells:

    async def test_gold_cells_llegan_al_sector_correcto(
        self, mundo_con_sectores, fake_bots_server, tmp_path
    ):
        bots_addr, _ = fake_bots_server
        gestor, sectores, _ = await mundo_con_sectores(
            n_cols=2, n_rows=2,
            bots_address=bots_addr,
            snapshot_dir=tmp_path,
        )
        gestor._gold_cells[(3, 3)] = b"\x01"
        gestor._gold_cells[(15, 15)] = b"\x02"
        await gestor._distribute_gold_to_sectors()
        assert sectores[(0, 0)]._celdas.get(3, 3) is not None
        assert sectores[(0, 0)]._celdas.get(15, 15) is None
        assert sectores[(1, 1)]._celdas.get(15, 15) is not None
        assert sectores[(1, 1)]._celdas.get(3, 3) is None

    async def test_gold_vacio_carga_sin_error(
        self, mundo_con_sectores, fake_bots_server, tmp_path
    ):
        bots_addr, _ = fake_bots_server
        gestor, _, _ = await mundo_con_sectores(
            n_cols=2, n_rows=2,
            bots_address=bots_addr,
            snapshot_dir=tmp_path,
        )
        await gestor._distribute_gold_to_sectors()


# ═══════════════════════════════════════════════════════════════════════════
#  Ghost zone
# ═══════════════════════════════════════════════════════════════════════════


class TestGhostZone:

    async def test_ghost_zone_sector_central_recibe_celdas_vecinas(
        self, mundo_con_sectores, fake_bots_server, tmp_path
    ):
        bots_addr, _ = fake_bots_server
        gestor, sectores, _ = await mundo_con_sectores(
            n_cols=2, n_rows=2,
            bots_address=bots_addr,
            snapshot_dir=tmp_path,
        )
        gestor._gold_cells[(9, 9)] = b"\xAA"
        ghost = gestor._calcular_ghost_zone(gestor._sectores[(1, 1)])
        posiciones = [(c.pos.x, c.pos.y) for c in ghost]
        assert (9, 9) in posiciones

    async def test_ghost_zone_no_incluye_celdas_propias(
        self, mundo_con_sectores, fake_bots_server, tmp_path
    ):
        bots_addr, _ = fake_bots_server
        gestor, _, _ = await mundo_con_sectores(
            n_cols=2, n_rows=2,
            bots_address=bots_addr,
            snapshot_dir=tmp_path,
        )
        gestor._gold_cells[(15, 15)] = b"\x01"
        ghost = gestor._calcular_ghost_zone(gestor._sectores[(1, 1)])
        posiciones = [(c.pos.x, c.pos.y) for c in ghost]
        assert (15, 15) not in posiciones

    async def test_fase0_envia_ghost_zone_a_sectores(self, mundo_2x2):
        gestor, sectores, _ = mundo_2x2
        gestor._gold_cells[(9, 9)] = b"\xBB"
        await gestor._fase_0()
        assert (9, 9) in sectores[(1, 1)]._ghost


# ═══════════════════════════════════════════════════════════════════════════
#  Migración de bots entre sectores
# ═══════════════════════════════════════════════════════════════════════════


class TestMigracion:

    async def test_bot_migra_de_sector_00_a_10(self, mundo_2x2):
        gestor, sectores, _ = mundo_2x2
        bot = _bot_en_borde_derecho(col=0, row=0, bot_id="bot_migra")
        sectores[(0, 0)].load_state(cells=[], bots=[bot])
        await gestor._run_tick()
        assert "bot_migra" not in sectores[(0, 0)]._bots
        assert "bot_migra" in sectores[(1, 0)]._bots

    async def test_bot_dentro_no_migra(self, mundo_2x2):
        gestor, sectores, _ = mundo_2x2
        bot = _bot_en_sector(col=0, row=0, bot_id="bot_fijo")
        sectores[(0, 0)].load_state(cells=[], bots=[bot])
        await gestor._run_tick()
        assert "bot_fijo" in sectores[(0, 0)]._bots
        for key, s in sectores.items():
            if key != (0, 0):
                assert "bot_fijo" not in s._bots

    async def test_bot_migra_y_sigue_existiendo_en_destino_tras_segundo_tick(
        self, mundo_2x2
    ):
        gestor, sectores, _ = mundo_2x2
        bot = _bot_en_borde_derecho(col=0, row=0, bot_id="bot_viajero")
        sectores[(0, 0)].load_state(cells=[], bots=[bot])
        await gestor._run_tick()
        gestor._tick_id += 1
        assert "bot_viajero" in sectores[(1, 0)]._bots
        await gestor._run_tick()
        assert "bot_viajero" in sectores[(1, 0)]._bots

    async def test_migracion_activa_sector_inactivo(
        self, mundo_con_sectores, fake_bots_server, tmp_path
    ):
        bots_addr, _ = fake_bots_server
        gestor, sectores, _ = await mundo_con_sectores(
            n_cols=2, n_rows=2,
            bots_address=bots_addr,
            snapshot_dir=tmp_path,
            modo_inicial=SectorMode.ACTIVO,
        )
        await gestor._set_sector_mode(gestor._sectores[(1, 0)], SectorMode.INACTIVO)
        assert gestor._sectores[(1, 0)].mode == SectorMode.INACTIVO
        bot = _bot_en_borde_derecho(col=0, row=0, bot_id="bot_activa")
        sectores[(0, 0)].load_state(cells=[], bots=[bot])
        await gestor._run_tick()
        assert gestor._sectores[(1, 0)].mode == SectorMode.ACTIVO


# ═══════════════════════════════════════════════════════════════════════════
#  Anti-thrashing
# ═══════════════════════════════════════════════════════════════════════════


class TestAntiThrashing:

    async def _gestor_thrashing(
        self, mundo_con_sectores, fake_bots_server, tmp_path, ticks_antes=2,
    ):
        bots_addr, bots_svc = fake_bots_server
        gestor, sectores, _ = await mundo_con_sectores(
            n_cols=2, n_rows=2,
            bots_address=bots_addr,
            snapshot_dir=tmp_path,
            modo_inicial=SectorMode.ACTIVO,
        )
        return gestor, sectores, bots_svc

    async def test_sector_sin_actividad_se_duerme(
        self, mundo_con_sectores, fake_bots_server, tmp_path
    ):
        """Sector ACTIVO sin actividad durante TICKS_ANTES_DE_DORMIR → DORMIDO."""
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module

        gestor, sectores, _ = await self._gestor_thrashing(
            mundo_con_sectores, fake_bots_server, tmp_path
        )
        # FIX: parchear ANTES de los ticks para que _actualizar_modos_sector lo lea
        gm_module.TICKS_ANTES_DE_DORMIR = 2

        for _ in range(2):
            await gestor._run_tick()
            gestor._tick_id += 1

        modos = [info.mode for info in gestor._sectores.values()]
        assert SectorMode.DORMIDO in modos

    async def test_vecino_de_activo_se_despierta(
        self, mundo_con_sectores, fake_bots_server, tmp_path
    ):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module
        bots_addr, _ = fake_bots_server
        gestor, sectores, _ = await mundo_con_sectores(
            n_cols=2, n_rows=2,
            bots_address=bots_addr,
            snapshot_dir=tmp_path,
            modo_inicial=SectorMode.INACTIVO,
        )
        gm_module.TICKS_ANTES_DE_DORMIR = 999

        info_00 = gestor._sectores[(0, 0)]
        await gestor._set_sector_mode(info_00, SectorMode.ACTIVO)
        info_00.ticks_sin_actividad = 0

        await gestor._actualizar_modos_sector()

        vecinos = gestor._vecinos(info_00)
        for v in vecinos:
            assert v.mode == SectorMode.DORMIDO, (
                f"Vecino ({v.col},{v.row}) debería ser DORMIDO, es {v.mode}"
            )

    async def test_sector_dormido_no_computa_tick(self, mundo_2x2):
        """Sector DORMIDO: GestorMundo no lo incluye en _fase_1, delta es None."""
        gestor, sectores, _ = mundo_2x2

        info = gestor._sectores[(0, 0)]
        await gestor._set_sector_mode(info, SectorMode.DORMIDO)

        bot = _bot_en_sector(col=0, row=0, bot_id="bot_dormido")
        sectores[(0, 0)].load_state(cells=[], bots=[bot])

        await gestor._run_tick()

        # FIX: sector DORMIDO no participa en _fase_1, así que
        # compute_tick nunca se llamó → get_delta devuelve None correctamente.
        delta = sectores[(0, 0)].get_delta(gestor._tick_id)
        assert delta is None  # correcto: no computó
        # El bot sigue en el sector (no hubo migración porque no computó)
        assert "bot_dormido" in sectores[(0, 0)]._bots


# ═══════════════════════════════════════════════════════════════════════════
#  Snapshot
# ═══════════════════════════════════════════════════════════════════════════


class TestSnapshot:

    async def test_save_snapshot_crea_fichero(self, mundo_2x2, tmp_path):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module
        gm_module.SNAPSHOT_DIR = tmp_path
        gestor, _, _ = mundo_2x2
        gestor._tick_id = 42
        await gestor._save_snapshot()
        assert len(list(tmp_path.glob("mundo_*.json"))) == 1

    async def test_save_snapshot_tick_id_correcto(self, mundo_2x2, tmp_path):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module
        gm_module.SNAPSHOT_DIR = tmp_path
        gestor, _, _ = mundo_2x2
        gestor._tick_id = 77
        await gestor._save_snapshot()
        fichero = list(tmp_path.glob("mundo_*.json"))[0]
        data = json.loads(fichero.read_text())
        assert data["tick_id"] == 77

    async def test_save_snapshot_incluye_sectores(self, mundo_2x2, tmp_path):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module
        gm_module.SNAPSHOT_DIR = tmp_path
        gestor, _, _ = mundo_2x2
        gestor._tick_id = 1
        await gestor._save_snapshot()
        data = json.loads(list(tmp_path.glob("mundo_*.json"))[0].read_text())
        assert len(data["sectores"]) == 4
        cols_rows = {(s["col"], s["row"]) for s in data["sectores"]}
        assert cols_rows == {(0, 0), (0, 1), (1, 0), (1, 1)}

    async def test_save_snapshot_incluye_gold_cells(self, mundo_2x2, tmp_path):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module
        gm_module.SNAPSHOT_DIR = tmp_path
        gestor, _, _ = mundo_2x2
        gestor._tick_id = 5
        gestor._gold_cells[(3, 3)] = b"\xDE\xAD"
        await gestor._save_snapshot()
        data = json.loads(list(tmp_path.glob("mundo_*.json"))[0].read_text())
        assert "3,3" in data["gold_cells"]
        assert data["gold_cells"]["3,3"] == b"\xDE\xAD".hex()

    async def test_latest_snapshot_path_sin_ficheros(self, mundo_2x2, tmp_path):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module
        gm_module.SNAPSHOT_DIR = tmp_path
        gestor, _, _ = mundo_2x2
        assert gestor._latest_snapshot_path() is None

    async def test_latest_snapshot_path_devuelve_el_mas_reciente(
        self, mundo_2x2, tmp_path
    ):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module
        gm_module.SNAPSHOT_DIR = tmp_path
        gestor, _, _ = mundo_2x2
        for tick in [1, 2, 3]:
            gestor._tick_id = tick
            await gestor._save_snapshot()
        data = json.loads(gestor._latest_snapshot_path().read_text())
        assert data["tick_id"] == 3

    async def test_save_snapshot_tras_tick_real(self, mundo_2x2, tmp_path):
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module
        gm_module.SNAPSHOT_DIR = tmp_path
        gestor, _, _ = mundo_2x2
        await gestor._run_tick()
        await gestor._save_snapshot()
        data = json.loads(list(tmp_path.glob("mundo_*.json"))[0].read_text())
        assert data["tick_id"] == gestor._tick_id


# ═══════════════════════════════════════════════════════════════════════════
#  Freeze / Resume
# ═══════════════════════════════════════════════════════════════════════════


class TestFreezeResume:

    async def test_freeze_cambia_estado_a_paused(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        await gestor.freeze()
        assert gestor._state == SystemState.PAUSED

    async def test_freeze_bloquea_pause_event(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        await gestor.freeze()
        assert not gestor._pause_event.is_set()

    async def test_resume_reactiva_sistema(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        await gestor.freeze()
        await gestor.resume()
        assert gestor._state == SystemState.RUNNING
        assert gestor._pause_event.is_set()

    async def test_freeze_llama_freeze_all_en_bots(self, mundo_2x2):
        gestor, _, bots_svc = mundo_2x2
        await gestor.freeze()
        assert bots_svc.freeze_count == 1

    async def test_resume_llama_resume_all_en_bots(self, mundo_2x2):
        gestor, _, bots_svc = mundo_2x2
        await gestor.freeze()
        await gestor.resume()
        assert bots_svc.resume_count == 1

    async def test_freeze_doble_no_llama_freeze_dos_veces(self, mundo_2x2):
        gestor, _, bots_svc = mundo_2x2
        await gestor.freeze()
        await gestor.freeze()
        assert bots_svc.freeze_count == 1

    async def test_resume_sin_freeze_no_lanza(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        await gestor.resume()
        assert gestor._state == SystemState.RUNNING

    async def test_freeze_resume_ciclo_completo_con_tick(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        await gestor.freeze()
        await gestor.resume()
        await gestor._run_tick()


# ═══════════════════════════════════════════════════════════════════════════
#  Geometría del mundo
# ═══════════════════════════════════════════════════════════════════════════


class TestGeometria:

    async def test_sector_para_posicion_correcta(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        info = gestor._sector_para_posicion(5, 5)
        assert info is not None
        assert info.col == 0 and info.row == 0

    async def test_sector_para_posicion_segundo_sector(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        info = gestor._sector_para_posicion(15, 15)
        assert info is not None
        assert info.col == 1 and info.row == 1

    async def test_sector_para_posicion_fuera_del_mapa(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        assert gestor._sector_para_posicion(9999, 9999) is None

    async def test_vecinos_sector_esquina_tiene_3(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        vecinos = gestor._vecinos(gestor._sectores[(0, 0)])
        assert len(vecinos) == 3

    async def test_vecinos_no_incluye_el_propio_sector(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        info = gestor._sectores[(0, 0)]
        vecinos = gestor._vecinos(info)
        assert info not in vecinos

    async def test_celdas_de_sector_filtra_correctamente(self, mundo_2x2):
        gestor, _, _ = mundo_2x2
        gestor._gold_cells[(5, 5)] = b"\x01"
        gestor._gold_cells[(15, 15)] = b"\x02"
        cells_00 = gestor._celdas_de_sector(gestor._sectores[(0, 0)])
        cells_11 = gestor._celdas_de_sector(gestor._sectores[(1, 1)])
        posiciones_00 = [(c.pos.x, c.pos.y) for c in cells_00]
        posiciones_11 = [(c.pos.x, c.pos.y) for c in cells_11]
        assert (5, 5) in posiciones_00
        assert (15, 15) not in posiciones_00
        assert (15, 15) in posiciones_11
        assert (5, 5) not in posiciones_11
