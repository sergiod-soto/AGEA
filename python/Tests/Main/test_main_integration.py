"""
Test/Main/test_main_integration.py
-----------------------------------
Tests de integración de main.py.
Lanza procesos reales y verifica que arrancan y responden por gRPC.

Requisitos:
  - Los _server.py deben ser funcionales.
  - Los protos deben estar compilados.
  - Las variables de entorno deben estar configuradas (o .env.local cargado).

Ejecución:
  pytest Test/Main/test_main_integration.py -v --timeout=60
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

import grpc
import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

import main

# ─────────────────────────────────────────────────────────────
#  Configuración compartida de integración
# ─────────────────────────────────────────────────────────────

# Puertos reservados para tests — distintos a los de desarrollo
# para poder correr ambos a la vez sin colisión.
TEST_SECTOR_PORT = 51150
TEST_GM_PORT = 51250
TEST_GB_PORT = 51151
TEST_HV_PORT = 51350
TEST_HV_PROXY_PORT = 51450

TEST_FULL_SECTOR_PORT = 52100
TEST_FULL_GM_PORT = 52200
TEST_FULL_GB_PORT = 52051
TEST_FULL_HV_PORT = 52300
TEST_FULL_HV_PROXY_PORT = 52400


@pytest.fixture(autouse=True)
def env_test(monkeypatch):
    """Inyecta variables de entorno de test en todos los tests de este módulo."""
    monkeypatch.setenv("GRID_WIDTH", "100")
    monkeypatch.setenv("GRID_HEIGHT", "100")
    monkeypatch.setenv("SECTOR_SIZE", "100")
    monkeypatch.setenv("SECTOR_HOST", "localhost")
    monkeypatch.setenv("SECTOR_BASE_PORT", str(TEST_SECTOR_PORT))
    monkeypatch.setenv("GESTOR_MUNDO_HOST", "localhost")
    monkeypatch.setenv("GESTOR_MUNDO_PORT", str(TEST_GM_PORT))
    monkeypatch.setenv("GESTOR_BOTS_HOST", "localhost")
    monkeypatch.setenv("GESTOR_BOTS_PORT", str(TEST_GB_PORT))
    monkeypatch.setenv("GESTOR_BOTS_ADDRESS", f"localhost:{TEST_GB_PORT}")
    monkeypatch.setenv("HYPERVISOR_HOST", "localhost")
    monkeypatch.setenv("HYPERVISOR_BASE_PORT", str(TEST_HV_PORT))
    monkeypatch.setenv("HYPERVISOR_PROXY_BASE_PORT", str(TEST_HV_PROXY_PORT))
    monkeypatch.setenv("HYPERVISOR_COUNT", "1")
    monkeypatch.setenv("FRESH_START", "1")
    monkeypatch.setenv("PYTHONPATH", str(ROOT))


def _wait_grpc(address: str, timeout_s: int = 20) -> bool:
    """Espera hasta que el canal gRPC en `address` esté disponible."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with grpc.insecure_channel(address) as ch:
                grpc.channel_ready_future(ch).result(timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def _lanzar(script_rel: str, env_extra: dict) -> subprocess.Popen:
    """Lanza un _server.py como subproceso con el entorno dado."""
    script = ROOT / script_rel
    assert script.exists(), f"Script no encontrado: {script}"
    env = os.environ.copy()
    env.update(env_extra)
    return subprocess.Popen(
        [sys.executable, str(script)],
        env=env,
        cwd=str(ROOT),
    )


# ─────────────────────────────────────────────────────────────
#  Tests individuales por componente
# ─────────────────────────────────────────────────────────────


class TestSectorArranca:

    def test_sector_responde_grpc(self):
        proc = _lanzar(
            "Gestores/Mundo/Sector/sector_server.py",
            {
                "SECTOR_COL": "0",
                "SECTOR_ROW": "0",
                "SECTOR_PORT": str(TEST_SECTOR_PORT),
                f"SECTOR_ADDR_C0_R0": f"localhost:{TEST_SECTOR_PORT}",
            },
        )
        try:
            ok = _wait_grpc(f"localhost:{TEST_SECTOR_PORT}")
            assert ok, "El sector no respondió por gRPC en el tiempo esperado"
        finally:
            proc.terminate()
            proc.wait(timeout=5)


class TestGestorMundoArranca:

    def test_gestor_mundo_responde_grpc(self):
        # El gestor_mundo necesita al menos el sector activo para arrancar
        sector = _lanzar(
            "Gestores/Mundo/Sector/sector_server.py",
            {
                "SECTOR_COL": "0",
                "SECTOR_ROW": "0",
                "SECTOR_PORT": str(TEST_SECTOR_PORT),
                f"SECTOR_ADDR_C0_R0": f"localhost:{TEST_SECTOR_PORT}",
            },
        )
        assert _wait_grpc(f"localhost:{TEST_SECTOR_PORT}"), "Sector no arrancó"

        gm = _lanzar(
            "Gestores/Mundo/Gestor_Mundo/gestor_mundo_server.py",
            {
                "GESTOR_MUNDO_PORT": str(TEST_GM_PORT),
                "GESTOR_BOTS_ADDRESS": f"localhost:{TEST_GB_PORT}",
            },
        )
        try:
            ok = _wait_grpc(f"localhost:{TEST_GM_PORT}")
            assert ok, "El gestor_mundo no respondió por gRPC en el tiempo esperado"
        finally:
            gm.terminate()
            sector.terminate()
            gm.wait(timeout=5)
            sector.wait(timeout=5)


class TestGestorBotsArranca:

    def test_gestor_bots_responde_grpc(self):
        gb = _lanzar(
            "Gestores/Bots/Gestor_Bots/gestor_bots_server.py",
            {"GESTOR_BOTS_PORT": str(TEST_GB_PORT)},
        )
        try:
            ok = _wait_grpc(f"localhost:{TEST_GB_PORT}")
            assert ok, "El gestor_bots no respondió por gRPC en el tiempo esperado"
        finally:
            gb.terminate()
            gb.wait(timeout=5)


class TestHypervisorArranca:

    def test_hypervisor_responde_grpc(self):
        # Hypervisor necesita gestor_bots para registrarse
        gb = _lanzar(
            "Gestores/Bots/Gestor_Bots/gestor_bots_server.py",
            {"GESTOR_BOTS_PORT": str(TEST_GB_PORT)},
        )
        assert _wait_grpc(f"localhost:{TEST_GB_PORT}"), "Gestor_bots no arrancó"

        hv = _lanzar(
            "Gestores/Bots/Hypervisor/hypervisor_server.py",
            {
                "HYPERVISOR_ID": "hv_test",
                "HYPERVISOR_PORT": str(TEST_HV_PORT),
                "HYPERVISOR_PROXY_PORT": str(TEST_HV_PROXY_PORT),
                "GESTOR_BOTS_ADDRESS": f"localhost:{TEST_GB_PORT}",
            },
        )
        try:
            ok = _wait_grpc(f"localhost:{TEST_HV_PORT}")
            assert ok, "El hypervisor no respondió por gRPC en el tiempo esperado"
        finally:
            hv.terminate()
            gb.terminate()
            hv.wait(timeout=5)
            gb.wait(timeout=5)


# ─────────────────────────────────────────────────────────────
#  Test de arranque completo del sistema
# ─────────────────────────────────────────────────────────────


class TestArranqueCompleto:
    """
    Lanza el sistema completo a través de main._arrancar_local()
    y verifica que todos los componentes responden.
    """

    def test_arranque_y_apagado_limpio(self):
        from unittest.mock import patch

        procesos = []

        # _arrancar_local bloquea con el supervisor — lo detenemos
        # justo después de que todos los healthchecks pasen.
        with patch("main._healthcheck", return_value=True), patch(
            "main._lanzar_proceso"
        ) as mock_lanzar:

            mock_proc = type(
                "P",
                (),
                {
                    "pid": 9999,
                    "poll": lambda self: None,
                    "terminate": lambda self: None,
                    "wait": lambda self, timeout=None: None,
                    "kill": lambda self: None,
                },
            )()
            mock_lanzar.return_value = mock_proc

            procesos = main._arrancar_local()

        # Todos los componentes fueron lanzados
        # Con grid 100x100, sector 100 → 1 sector + gm + gb + 1 hv = 4
        assert (
            mock_lanzar.call_count == 4
        ), f"Se esperaban 4 lanzamientos, se hicieron {mock_lanzar.call_count}"

    def test_apagado_si_proceso_falla_en_healthcheck(self):
        from unittest.mock import patch, MagicMock

        with patch("main._healthcheck", return_value=False), patch(
            "main._lanzar_proceso"
        ) as mock_lanzar, patch("main._apagar_procesos") as mock_apagar:

            mock_proc = MagicMock()
            mock_proc.pid = 1111
            mock_lanzar.return_value = mock_proc

            with pytest.raises(SystemExit) as exc:
                main._arrancar_local()

            assert exc.value.code == 1
            mock_apagar.assert_called_once()

    @pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Test de integración real — omitido en CI sin infraestructura",
    )
    def test_sistema_completo_real(self, monkeypatch):
        """
        Lanza el sistema completo con procesos reales y verifica
        que todos los componentes responden por gRPC.
        Solo corre si CI != true.
        """
        monkeypatch.setenv("SECTOR_BASE_PORT", str(TEST_FULL_SECTOR_PORT))
        monkeypatch.setenv("GESTOR_MUNDO_PORT", str(TEST_FULL_GM_PORT))
        monkeypatch.setenv("GESTOR_BOTS_PORT", str(TEST_FULL_GB_PORT))
        monkeypatch.setenv("HYPERVISOR_BASE_PORT", str(TEST_FULL_HV_PORT))
        monkeypatch.setenv("HYPERVISOR_PROXY_BASE_PORT", str(TEST_FULL_HV_PROXY_PORT))
        procesos = main._arrancar_local()
        try:
            componentes = main._build_components()
            for comp in componentes:
                ok = _wait_grpc(comp["healthcheck_address"], timeout_s=30)
                assert ok, f"{comp['nombre']} no respondió por gRPC"
        finally:
            main._apagar_procesos([(None, p) for p in procesos])
