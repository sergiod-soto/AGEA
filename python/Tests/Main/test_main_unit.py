"""
Tests/Main/test_main_unit.py
-----------------------------
Tests unitarios de main.py — sin subprocesos reales ni gRPC real.
Todo mockeado. Para tests de integración con procesos reales, ver
test_main_integration.py.

No se testea aquí:
  - _arrancar_local() end-to-end: ya cubierto en
    test_main_integration.py::TestArranqueCompleto con el mismo enfoque
    de mocks; duplicarlo aquí no añade cobertura, solo mantenimiento extra.
  - main() a nivel de CLI completo: es solo parseo de argparse + despacho
    a las funciones que sí se testean aquí una a una.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

import main


@pytest.fixture(autouse=True)
def _entorno_limpio():
    """
    Aísla os.environ entre tests.

    Necesario porque _cargar_env y _arrancar_componente_produccion escriben
    directamente en os.environ (no via monkeypatch.setenv), así que sin este
    fixture un test podría dejar variables filtradas al siguiente.
    """
    antes = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(antes)


# ─────────────────────────────────────────────────────────────
#  _cargar_env
# ─────────────────────────────────────────────────────────────


class TestCargarEnv:

    def test_carga_variables_de_fichero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main, "ROOT", tmp_path)
        (tmp_path / ".env.test").write_text("MI_VAR=hola\n")

        main._cargar_env("test")

        assert os.environ["MI_VAR"] == "hola"

    def test_no_sobreescribe_variables_existentes(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main, "ROOT", tmp_path)
        os.environ["MI_VAR"] = "original"
        (tmp_path / ".env.test").write_text("MI_VAR=nuevo\n")

        main._cargar_env("test")

        assert os.environ["MI_VAR"] == "original"

    def test_ignora_comentarios_y_lineas_vacias(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main, "ROOT", tmp_path)
        (tmp_path / ".env.test").write_text(
            "# comentario\n\nMI_VAR=hola\n\n# otro comentario\n"
        )

        main._cargar_env("test")

        assert os.environ["MI_VAR"] == "hola"

    def test_fichero_inexistente_no_lanza_excepcion(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main, "ROOT", tmp_path)
        # No se crea ningún .env.test — debe limitarse a avisar, no fallar.
        main._cargar_env("test")


# ─────────────────────────────────────────────────────────────
#  _build_sector_components
# ─────────────────────────────────────────────────────────────


class TestBuildSectorComponents:

    def _set_env(self, monkeypatch, grid_w, grid_h, sector_sz=100):
        monkeypatch.setenv("GRID_WIDTH", str(grid_w))
        monkeypatch.setenv("GRID_HEIGHT", str(grid_h))
        monkeypatch.setenv("SECTOR_SIZE", str(sector_sz))
        monkeypatch.setenv("SECTOR_BASE_PORT", "50100")
        monkeypatch.setenv("SECTOR_HOST", "localhost")

    def test_grid_100x100_sector_100_genera_un_sector(self, monkeypatch):
        self._set_env(monkeypatch, 100, 100)
        comps = main._build_sector_components()
        assert len(comps) == 1
        assert comps[0]["nombre"] == "sector_0_0"

    def test_grid_200x100_sector_100_genera_dos_sectores(self, monkeypatch):
        self._set_env(monkeypatch, 200, 100)
        comps = main._build_sector_components()
        nombres = {c["nombre"] for c in comps}
        assert nombres == {"sector_0_0", "sector_1_0"}

    def test_puertos_no_colisionan(self, monkeypatch):
        self._set_env(monkeypatch, 300, 200)
        comps = main._build_sector_components()
        puertos = [c["healthcheck_address"] for c in comps]
        assert len(puertos) == len(set(puertos))

    def test_env_extra_contiene_col_y_row(self, monkeypatch):
        self._set_env(monkeypatch, 100, 100)
        comps = main._build_sector_components()
        env_extra = comps[0]["env_extra"]
        assert env_extra["SECTOR_COL"] == "0"
        assert env_extra["SECTOR_ROW"] == "0"


# ─────────────────────────────────────────────────────────────
#  _build_components
# ─────────────────────────────────────────────────────────────


class TestBuildComponents:

    def _set_env_minimo(self, monkeypatch):
        monkeypatch.setenv("GRID_WIDTH", "100")
        monkeypatch.setenv("GRID_HEIGHT", "100")
        monkeypatch.setenv("SECTOR_SIZE", "100")
        monkeypatch.setenv("GESTOR_MUNDO_HOST", "localhost")
        monkeypatch.setenv("GESTOR_MUNDO_PORT", "50200")
        monkeypatch.setenv("GESTOR_BOTS_HOST", "localhost")
        monkeypatch.setenv("GESTOR_BOTS_PORT", "50051")
        monkeypatch.setenv("HYPERVISOR_HOST", "localhost")
        monkeypatch.setenv("HYPERVISOR_BASE_PORT", "50300")
        monkeypatch.setenv("HYPERVISOR_PROXY_BASE_PORT", "50400")
        monkeypatch.setenv("HYPERVISOR_COUNT", "1")

    def test_orden_arranque(self, monkeypatch):
        """
        _build_components devuelve list[list[dict]] — grupos ejecutados en
        orden, componentes de un mismo grupo en paralelo (sin orden entre
        ellos). Se testea contra esa estructura real, no aplanada, para no
        perder justo la invariante que la función garantiza.
        """
        self._set_env_minimo(monkeypatch)
        grupos = main._build_components()

        assert len(grupos) == 4
        assert all(c["nombre"].startswith("sector_") for c in grupos[0])
        assert [c["nombre"] for c in grupos[1]] == ["gestor_mundo"]
        assert [c["nombre"] for c in grupos[2]] == ["gestor_bots"]
        assert all(c["nombre"].startswith("hypervisor_") for c in grupos[3])

    def test_hypervisor_count_respetado(self, monkeypatch):
        self._set_env_minimo(monkeypatch)
        monkeypatch.setenv("HYPERVISOR_COUNT", "3")

        grupos = main._build_components()
        hvs = grupos[3]

        assert len(hvs) == 3
        assert {c["nombre"] for c in hvs} == {
            "hypervisor_00",
            "hypervisor_01",
            "hypervisor_02",
        }

    def test_gestor_bots_conoce_direccion_gestor_mundo(self, monkeypatch):
        self._set_env_minimo(monkeypatch)
        grupos = main._build_components()
        gestor_bots = grupos[2][0]

        assert gestor_bots["env_extra"]["GESTOR_MUNDO_ADDRESS"] == "localhost:50200"


# ─────────────────────────────────────────────────────────────
#  _healthcheck
# ─────────────────────────────────────────────────────────────


class TestHealthcheck:

    def _comp(self, **overrides):
        base = dict(
            healthcheck_address="localhost:50100",
            healthcheck_stub_module="modulo.stub_grpc",
            healthcheck_stub_class="StubFalso",
            healthcheck_request_module="modulo.request",
            healthcheck_request_class="RequestFalso",
            healthcheck_method="Metodo",
        )
        base.update(overrides)
        return base

    def test_retorna_true_si_responde(self, monkeypatch):
        stub_instance = MagicMock()
        stub_class = MagicMock(return_value=stub_instance)
        modulo_stub = MagicMock(StubFalso=stub_class)
        modulo_request = MagicMock(RequestFalso=MagicMock(return_value=MagicMock()))

        def fake_import_module(name):
            return {
                "modulo.stub_grpc": modulo_stub,
                "modulo.request": modulo_request,
            }[name]

        canal_mock = MagicMock()
        canal_mock.__enter__ = MagicMock(return_value=MagicMock())
        canal_mock.__exit__ = MagicMock(return_value=False)

        monkeypatch.setattr(main.importlib, "import_module", fake_import_module)
        monkeypatch.setattr(
            main.grpc, "insecure_channel", MagicMock(return_value=canal_mock)
        )

        assert main._healthcheck(self._comp()) is True

    def test_retorna_false_si_agota_timeout(self, monkeypatch):
        # Secuencia de time.monotonic(): deadline, primera comprobación
        # (aún dentro de plazo), segunda comprobación (ya fuera de plazo).
        tiempos = iter([0, 0, 999])
        monkeypatch.setattr(main.time, "monotonic", lambda: next(tiempos))
        monkeypatch.setattr(main.time, "sleep", lambda s: None)
        monkeypatch.setattr(main.importlib, "import_module", lambda name: MagicMock())
        monkeypatch.setattr(
            main.grpc,
            "insecure_channel",
            MagicMock(side_effect=ConnectionError("no disponible")),
        )

        assert main._healthcheck(self._comp(), timeout_s=1) is False


# ─────────────────────────────────────────────────────────────
#  _lanzar_proceso
# ─────────────────────────────────────────────────────────────


class TestLanzarProceso:

    def test_lanza_con_env_extra(self, tmp_path, monkeypatch):
        script = tmp_path / "dummy_server.py"
        script.write_text("# dummy")

        componente = {
            "nombre": "dummy",
            "script": script,
            "env_extra": {"FOO": "bar"},
        }

        proc_mock = MagicMock(pid=1234)
        popen_mock = MagicMock(return_value=proc_mock)
        monkeypatch.setattr(main.subprocess, "Popen", popen_mock)

        resultado = main._lanzar_proceso(componente)

        assert resultado is proc_mock
        args, kwargs = popen_mock.call_args
        assert args[0] == [sys.executable, str(script)]
        assert kwargs["env"]["FOO"] == "bar"

    def test_script_inexistente_lanza_error(self, tmp_path):
        componente = {
            "nombre": "dummy",
            "script": tmp_path / "no_existe.py",
            "env_extra": {},
        }
        with pytest.raises(FileNotFoundError):
            main._lanzar_proceso(componente)


# ─────────────────────────────────────────────────────────────
#  _lanzar_grupo
# ─────────────────────────────────────────────────────────────


class TestLanzarGrupo:

    def test_todos_los_componentes_ok(self, monkeypatch):
        grupo = [{"nombre": "a"}, {"nombre": "b"}]
        monkeypatch.setattr(
            main, "_lanzar_proceso", MagicMock(side_effect=lambda c: MagicMock())
        )
        monkeypatch.setattr(main, "_healthcheck", MagicMock(return_value=True))

        procs, fallidos = main._lanzar_grupo(grupo)

        assert len(procs) == 2
        assert fallidos == []

    def test_componente_fallido_se_reporta_por_nombre(self, monkeypatch):
        grupo = [{"nombre": "a"}, {"nombre": "b"}]
        monkeypatch.setattr(
            main, "_lanzar_proceso", MagicMock(side_effect=lambda c: MagicMock())
        )
        # executor.map preserva el orden de entrada, así que esto asigna
        # de forma determinista True→"a", False→"b".
        monkeypatch.setattr(main, "_healthcheck", MagicMock(side_effect=[True, False]))

        _, fallidos = main._lanzar_grupo(grupo)

        assert fallidos == ["b"]


# ─────────────────────────────────────────────────────────────
#  _apagar_procesos
# ─────────────────────────────────────────────────────────────


class TestApagarProcesos:

    def test_termina_procesos_vivos(self):
        proc = MagicMock()
        proc.poll.return_value = None  # vivo

        main._apagar_procesos([proc])

        proc.terminate.assert_called_once()

    def test_no_termina_procesos_ya_muertos(self):
        proc = MagicMock()
        proc.poll.return_value = 0  # ya terminó

        main._apagar_procesos([proc])

        proc.terminate.assert_not_called()

    def test_kill_si_no_termina_a_tiempo(self):
        proc = MagicMock()
        proc.poll.return_value = None
        proc.wait.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=5)

        main._apagar_procesos([proc])

        proc.kill.assert_called_once()


# ─────────────────────────────────────────────────────────────
#  _arrancar_componente_produccion
# ─────────────────────────────────────────────────────────────


class TestArrancarComponenteProduccion:

    def test_componente_desconocido_sale_con_error(self):
        args = argparse.Namespace(
            componente="componente_inventado", id=None, sesion=None, bucket=None
        )
        with pytest.raises(SystemExit) as exc:
            main._arrancar_componente_produccion(args)
        assert exc.value.code == 1

    def test_script_inexistente_lanza_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main, "SCRIPT_GESTOR_MUNDO", tmp_path / "no_existe.py")
        args = argparse.Namespace(
            componente="gestor_mundo", id=None, sesion=None, bucket=None
        )
        with pytest.raises(FileNotFoundError):
            main._arrancar_componente_produccion(args)

    def test_arranca_componente_valido(self, tmp_path, monkeypatch):
        script = tmp_path / "sector_server.py"
        script.write_text("# dummy")
        monkeypatch.setattr(main, "SCRIPT_SECTOR", script)

        # componente = tipo ("sector"); id = instancia concreta
        # ("sector_0_1"). Son campos distintos de main() --componente/--id;
        # no hay ninguna normalización de nombres en el código real.
        args = argparse.Namespace(
            componente="sector", id="sector_0_1", sesion="s1", bucket="b1"
        )

        with patch("main.os.execv") as mock_execv:
            main._arrancar_componente_produccion(args)

        assert os.environ["COMPONENT_ID"] == "sector_0_1"
        assert os.environ["SESSION_ID"] == "s1"
        assert os.environ["S3_BUCKET"] == "b1"
        mock_execv.assert_called_once_with(
            sys.executable, [sys.executable, str(script)]
        )
