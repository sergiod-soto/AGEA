"""
Tests para Infraestructura/AWS/shutdown.py.

common_pb2 no existe en el entorno de test (requiere protos compilados),
así que se mockea con patch.dict antes de cada llamada a ejecutar().
"""

from unittest.mock import MagicMock, patch

import pytest

from Infraestructura.AWS.shutdown import ShutdownCoordinator

CFG = {
    "aws":      {"region": "us-east-1"},
    "timeouts": {"shutdown_segundos": 2},
}

INSTANCE_IDS = {
    "gestor_bots":  "i-001",
    "gestor_mundo": "i-002",
    "hv_0":         "i-003",
    "sector_0":     "i-004",
}

# common_pb2 mock reutilizable
_MOCK_COMMON = MagicMock()


def _ok():
    return MagicMock(ok=True)


def _falla():
    return MagicMock(side_effect=Exception("timeout"))


def _nok():
    return MagicMock(return_value=MagicMock(ok=False, error="sin respuesta"))


def _coord(**kwargs) -> ShutdownCoordinator:
    """Construye un coordinador con defaults razonables, sobreescribibles por kwargs."""
    defaults = dict(
        config=CFG,
        session_id="sesion-test",
        instance_ids=INSTANCE_IDS,
        shutdown_gestor_bots=MagicMock(return_value=_ok()),
        shutdown_gestor_mundo=MagicMock(return_value=_ok()),
        shutdown_hv={},
        shutdown_sector={},
    )
    defaults.update(kwargs)
    return ShutdownCoordinator(**defaults)


class TestShutdownCoordinator:

    def test_happy_path_termina_instancias_ec2(self):
        """Cuando ambos gestores confirman, se terminan todas las instancias EC2."""
        coord = _coord()

        with patch.dict("sys.modules", {"common_pb2": _MOCK_COMMON}):
            with patch("Infraestructura.AWS.shutdown.terminar_instancias") as mock_term:
                coord.ejecutar(reason="user")

        mock_term.assert_called_once_with(CFG, list(INSTANCE_IDS.values()))

    def test_fallback_hvs_si_gestor_bots_no_responde(self):
        """Si gestor_bots lanza excepción, el shutdown se envía directamente a los HVs."""
        hv_0 = MagicMock(return_value=_ok())
        hv_1 = MagicMock(return_value=_ok())

        coord = _coord(
            shutdown_gestor_bots=_falla(),
            shutdown_hv={"hv_0": hv_0, "hv_1": hv_1},
        )

        with patch.dict("sys.modules", {"common_pb2": _MOCK_COMMON}):
            with patch("Infraestructura.AWS.shutdown.terminar_instancias"):
                coord.ejecutar(reason="component_failure")

        hv_0.assert_called_once()
        hv_1.assert_called_once()

    def test_fallback_sectores_si_gestor_mundo_responde_nok(self):
        """Si gestor_mundo devuelve ok=False, el shutdown se envía a los sectores."""
        sec_0 = MagicMock(return_value=_ok())

        coord = _coord(
            shutdown_gestor_mundo=_nok(),
            shutdown_sector={"sector_0": sec_0},
        )

        with patch.dict("sys.modules", {"common_pb2": _MOCK_COMMON}):
            with patch("Infraestructura.AWS.shutdown.terminar_instancias"):
                coord.ejecutar(reason="spot_interruption")

        sec_0.assert_called_once()

    def test_no_fallback_si_gestor_responde_ok(self):
        """Si un gestor confirma ok, no se contacta directamente a sus hijos."""
        hv_0 = MagicMock(return_value=_ok())

        coord = _coord(
            shutdown_gestor_bots=MagicMock(return_value=_ok()),
            shutdown_hv={"hv_0": hv_0},
        )

        with patch.dict("sys.modules", {"common_pb2": _MOCK_COMMON}):
            with patch("Infraestructura.AWS.shutdown.terminar_instancias"):
                coord.ejecutar(reason="user")

        hv_0.assert_not_called()

    def test_ejecutar_es_idempotente(self):
        """Llamar a ejecutar() dos veces solo ejecuta el shutdown una vez."""
        mock_gb = MagicMock(return_value=_ok())
        coord = _coord(shutdown_gestor_bots=mock_gb)

        with patch.dict("sys.modules", {"common_pb2": _MOCK_COMMON}):
            with patch("Infraestructura.AWS.shutdown.terminar_instancias"):
                coord.ejecutar(reason="user")
                coord.ejecutar(reason="user")

        assert mock_gb.call_count == 1

    def test_instancias_terminan_aunque_todo_falle(self):
        """Las instancias EC2 se terminan incluso si todos los componentes fallan."""
        coord = _coord(
            shutdown_gestor_bots=_falla(),
            shutdown_gestor_mundo=_falla(),
            shutdown_hv={"hv_0": _falla()},
            shutdown_sector={"sector_0": _falla()},
        )

        with patch.dict("sys.modules", {"common_pb2": _MOCK_COMMON}):
            with patch("Infraestructura.AWS.shutdown.terminar_instancias") as mock_term:
                coord.ejecutar(reason="component_failure")

        mock_term.assert_called_once()
