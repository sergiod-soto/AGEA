"""
Test/Main/test_main_unit.py
---------------------------
Tests unitarios de main.py.
No lanza procesos reales ni conexiones gRPC.
Todo subprocess y grpc se mockea.
"""

import os
import sys
import signal
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open, call
import pytest

# Aseguramos que la raíz del proyecto está en el path
ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

import main

# ─────────────────────────────────────────────────────────────
#  _cargar_env
# ─────────────────────────────────────────────────────────────


class TestCargarEnv:

    def test_carga_variables_de_fichero(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env.test"
        env_file.write_text("CLAVE_TEST=valor_test\nOTRA_CLAVE=123\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(main, "ROOT", tmp_path)
        monkeypatch.delenv("CLAVE_TEST", raising=False)
        monkeypatch.delenv("OTRA_CLAVE", raising=False)

        main._cargar_env("test")

        assert os.environ["CLAVE_TEST"] == "valor_test"
        assert os.environ["OTRA_CLAVE"] == "123"

    def test_no_sobreescribe_variables_existentes(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env.test"
        env_file.write_text("CLAVE_TEST=desde_fichero\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(main, "ROOT", tmp_path)
        monkeypatch.setenv("CLAVE_TEST", "ya_existia")

        main._cargar_env("test")

        assert os.environ["CLAVE_TEST"] == "ya_existia"

    def test_ignora_comentarios_y_lineas_vacias(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env.test"
        env_file.write_text("# comentario\n\nCLAVE_REAL=ok\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(main, "ROOT", tmp_path)
        monkeypatch.delenv("CLAVE_REAL", raising=False)

        main._cargar_env("test")

        assert os.environ["CLAVE_REAL"] == "ok"

    def test_fichero_inexistente_no_lanza_excepcion(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main, "ROOT", tmp_path)
        # No debe lanzar nada
        main._cargar_env("no_existe")


# ─────────────────────────────────────────────────────────────
#  _build_sector_components
# ─────────────────────────────────────────────────────────────


class TestBuildSectorComponents:

    def test_grid_100x100_sector_100_genera_un_sector(self, monkeypatch):
        monkeypatch.setenv("GRID_WIDTH", "100")
        monkeypatch.setenv("GRID_HEIGHT", "100")
        monkeypatch.setenv("SECTOR_SIZE", "100")
        monkeypatch.setenv("SECTOR_BASE_PORT", "50100")
        monkeypatch.setenv("SECTOR_HOST", "localhost")

        comps = main._build_sector_components()
        assert len(comps) == 1
        assert comps[0]["nombre"] == "sector_0_0"

    def test_grid_200x100_sector_100_genera_dos_sectores(self, monkeypatch):
        monkeypatch.setenv("GRID_WIDTH", "200")
        monkeypatch.setenv("GRID_HEIGHT", "100")
        monkeypatch.setenv("SECTOR_SIZE", "100")
        monkeypatch.setenv("SECTOR_BASE_PORT", "50100")
        monkeypatch.setenv("SECTOR_HOST", "localhost")

        comps = main._build_sector_components()
        assert len(comps) == 2
        nombres = {c["nombre"] for c in comps}
        assert nombres == {"sector_0_0", "sector_1_0"}

    def test_puertos_no_colisionan(self, monkeypatch):
        monkeypatch.setenv("GRID_WIDTH", "200")
        monkeypatch.setenv("GRID_HEIGHT", "200")
        monkeypatch.setenv("SECTOR_SIZE", "100")
        monkeypatch.setenv("SECTOR_BASE_PORT", "50100")
        monkeypatch.setenv("SECTOR_HOST", "localhost")

        comps = main._build_sector_components()
        direcciones = [c["healthcheck_address"] for c in comps]
        assert len(direcciones) == len(
            set(direcciones)
        ), "Colisión de puertos entre sectores"

    def test_env_extra_contiene_col_y_row(self, monkeypatch):
        monkeypatch.setenv("GRID_WIDTH", "100")
        monkeypatch.setenv("GRID_HEIGHT", "100")
        monkeypatch.setenv("SECTOR_SIZE", "100")
        monkeypatch.setenv("SECTOR_BASE_PORT", "50100")
        monkeypatch.setenv("SECTOR_HOST", "localhost")

        comp = main._build_sector_components()[0]
        assert comp["env_extra"]["SECTOR_COL"] == "0"
        assert comp["env_extra"]["SECTOR_ROW"] == "0"


# ─────────────────────────────────────────────────────────────
#  _build_components
# ─────────────────────────────────────────────────────────────


class TestBuildComponents:

    def _set_env_minimo(self, monkeypatch):
        monkeypatch.setenv("GRID_WIDTH", "100")
        monkeypatch.setenv("GRID_HEIGHT", "100")
        monkeypatch.setenv("SECTOR_SIZE", "100")
        monkeypatch.setenv("SECTOR_BASE_PORT", "50100")
        monkeypatch.setenv("SECTOR_HOST", "localhost")
        monkeypatch.setenv("GESTOR_MUNDO_HOST", "localhost")
        monkeypatch.setenv("GESTOR_MUNDO_PORT", "50200")
        monkeypatch.setenv("GESTOR_BOTS_HOST", "localhost")
        monkeypatch.setenv("GESTOR_BOTS_PORT", "50051")
        monkeypatch.setenv("HYPERVISOR_HOST", "localhost")
        monkeypatch.setenv("HYPERVISOR_BASE_PORT", "50300")
        monkeypatch.setenv("HYPERVISOR_PROXY_BASE_PORT", "50400")
        monkeypatch.setenv("HYPERVISOR_COUNT", "1")

    def test_orden_arranque(self, monkeypatch):
        self._set_env_minimo(monkeypatch)
        comps = main._build_components()
        nombres = [c["nombre"] for c in comps]

        # Los sectores van primero
        assert nombres[0].startswith("sector_")
        # gestor_mundo antes que gestor_bots
        idx_gm = nombres.index("gestor_mundo")
        idx_gb = nombres.index("gestor_bots")
        assert idx_gm < idx_gb

        # hypervisores al final
        idx_hv = nombres.index("hypervisor_00")
        assert idx_hv > idx_gb

    def test_hypervisor_count_respetado(self, monkeypatch):
        self._set_env_minimo(monkeypatch)
        monkeypatch.setenv("HYPERVISOR_COUNT", "3")

        comps = main._build_components()
        hvs = [c for c in comps if c["nombre"].startswith("hypervisor_")]
        assert len(hvs) == 3

    def test_gestor_bots_conoce_direccion_gestor_mundo(self, monkeypatch):
        self._set_env_minimo(monkeypatch)
        comps = main._build_components()
        gb = next(c for c in comps if c["nombre"] == "gestor_bots")
        assert "GESTOR_MUNDO_ADDRESS" in gb["env_extra"]


# ─────────────────────────────────────────────────────────────
#  _lanzar_proceso
# ─────────────────────────────────────────────────────────────


class TestLanzarProceso:

    def test_lanza_con_env_extra(self, tmp_path, monkeypatch):
        script = tmp_path / "dummy_server.py"
        script.write_text("import time; time.sleep(999)")
        monkeypatch.setattr(main, "PYTHON_ROOT", tmp_path)

        comp = {
            "nombre": "dummy",
            "script": script,
            "env_extra": {"MI_VAR": "mi_valor"},
        }

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(pid=1234)
            main._lanzar_proceso(comp)
            _, kwargs = mock_popen.call_args
            assert kwargs["env"]["MI_VAR"] == "mi_valor"

    def test_script_inexistente_lanza_error(self, tmp_path):
        # tmp_path vacío → el script no existe
        with pytest.raises(FileNotFoundError):
            main._arrancar_componente_produccion("gestor_mundo", python_root=tmp_path)


# ─────────────────────────────────────────────────────────────
#  _apagar_procesos
# ─────────────────────────────────────────────────────────────


class TestApagarProcesos:

    def test_termina_procesos_vivos(self):
        proc = MagicMock()
        proc.poll.return_value = None  # vivo
        proc.wait.return_value = None

        main._apagar_procesos([(None, proc)])

        proc.terminate.assert_called_once()

    def test_no_termina_procesos_ya_muertos(self):
        proc = MagicMock()
        proc.poll.return_value = 0  # ya terminó

        main._apagar_procesos([(None, proc)])

        proc.terminate.assert_not_called()

    def test_kill_si_no_termina_a_tiempo(self):
        proc = MagicMock()
        proc.poll.return_value = None
        proc.wait.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=5)

        main._apagar_procesos([(None, proc)])

        proc.kill.assert_called_once()


# ─────────────────────────────────────────────────────────────
#  _arrancar_componente_produccion
# ─────────────────────────────────────────────────────────────


class TestArrancarComponenteProduccion:

    def test_componente_desconocido_sale_con_error(self):
        with pytest.raises(SystemExit) as exc:
            main._arrancar_componente_produccion("componente_inventado")
        assert exc.value.code == 1

    def test_script_inexistente_lanza_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main, "PYTHON_ROOT", tmp_path)
        # PYTHON_ROOT vacío → el script no existe
        with pytest.raises(FileNotFoundError):
            main._arrancar_componente_produccion("gestor_mundo")

    def test_sector_con_sufijo_normaliza_a_sector(self, tmp_path):
        script = tmp_path / "Gestores" / "Mundo" / "Sector" / "sector_server.py"
        script.parent.mkdir(parents=True)
        script.write_text("")

        with patch("os.execv") as mock_execv:
            main._arrancar_componente_produccion("sector_0_1", python_root=tmp_path)
            mock_execv.assert_called_once()


# ─────────────────────────────────────────────────────────────
#  _healthcheck
# ─────────────────────────────────────────────────────────────


class TestHealthcheck:

    def test_retorna_true_si_canal_responde(self):
        with patch("main.grpc.insecure_channel") as mock_channel, patch(
            "main.grpc.channel_ready_future"
        ) as mock_future, patch("importlib.import_module") as mock_import:

            mock_stub = MagicMock()
            mock_import.return_value = MagicMock(**{"SectorServiceStub": mock_stub})
            mock_future.return_value.result.return_value = None
            mock_channel.return_value.__enter__ = lambda s: MagicMock()
            mock_channel.return_value.__exit__ = MagicMock(return_value=False)

            result = main._healthcheck(
                "localhost:50100",
                "Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2_grpc",
                "SectorServiceStub",
                timeout_s=5,
            )
            assert result is True

    def test_retorna_false_si_agota_timeout(self):
        with patch("main.grpc.insecure_channel") as mock_channel, patch(
            "main.grpc.channel_ready_future"
        ) as mock_future, patch("importlib.import_module") as mock_import, patch(
            "time.monotonic", side_effect=[0, 0, 999]
        ):  # timeout inmediato

            mock_import.return_value = MagicMock()
            mock_future.return_value.result.side_effect = Exception("timeout")

            result = main._healthcheck(
                "localhost:9999",
                "modulo.falso",
                "StubFalso",
                timeout_s=1,
            )
            assert result is False
