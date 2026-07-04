"""
Tests para Infraestructura/AWS/remote.py.

Solo se testean las funciones auxiliares puras o con dependencias
mockeables. arrancar_remoto() es un flujo de integración completo
que se cubrirá con tests de integración cuando exista entorno AWS de test.
"""

from unittest.mock import MagicMock, patch, call

import pytest

from Infraestructura.AWS.remote import (
    _make_shutdown_fn,
    _tipo,
)


# ─────────────────────────────────────────────────────────────
#  _tipo
# ─────────────────────────────────────────────────────────────

class TestTipo:

    def test_gestores_directos(self):
        assert _tipo("gestor_bots")  == "gestor_bots"
        assert _tipo("gestor_mundo") == "gestor_mundo"

    def test_hypervisor(self):
        assert _tipo("hv_0")   == "hypervisor"
        assert _tipo("hv_00")  == "hypervisor"
        assert _tipo("hv_12")  == "hypervisor"

    def test_sector(self):
        assert _tipo("sector_0")   == "sector"
        assert _tipo("sector_0_1") == "sector"

    def test_id_desconocido_lanza_value_error(self):
        with pytest.raises(ValueError, match="No se puede inferir"):
            _tipo("componente_desconocido")

    def test_string_vacio_lanza_value_error(self):
        with pytest.raises(ValueError):
            _tipo("")


# ─────────────────────────────────────────────────────────────
#  _make_shutdown_fn
# ─────────────────────────────────────────────────────────────

class TestMakeShutdownFn:

    def test_llama_shutdown_del_stub_con_el_request(self):
        stub = MagicMock()
        stub.Shutdown.return_value = MagicMock(ok=True)
        req = MagicMock()

        fn = _make_shutdown_fn(stub, timeout=30)
        fn(req)

        stub.Shutdown.assert_called_once_with(req, timeout=30)

    def test_respeta_el_timeout_configurado(self):
        stub = MagicMock()
        req = MagicMock()

        _make_shutdown_fn(stub, timeout=10)(req)
        _make_shutdown_fn(stub, timeout=60)(req)

        timeouts = [c[1]["timeout"] for c in stub.Shutdown.call_args_list]
        assert timeouts == [10, 60]

    def test_distintos_stubs_no_se_mezclan(self):
        """
        Verifica que el closure captura el stub correcto en cada llamada.
        Protege contra el bug clásico de captura de variable en bucle.
        """
        stub_a = MagicMock()
        stub_b = MagicMock()
        req = MagicMock()

        fn_a = _make_shutdown_fn(stub_a, timeout=5)
        fn_b = _make_shutdown_fn(stub_b, timeout=5)

        fn_a(req)
        stub_a.Shutdown.assert_called_once()
        stub_b.Shutdown.assert_not_called()

        fn_b(req)
        stub_b.Shutdown.assert_called_once()


# ─────────────────────────────────────────────────────────────
#  _healthcheck_remoto
# ─────────────────────────────────────────────────────────────

CFG = {
    "red":      {"puerto_grpc_componentes": 50051},
    "timeouts": {"arranque_segundos": 5},
}


class TestHealthcheckRemoto:
    """
    El healthcheck mockea grpc e importlib para no requerir
    los protos compilados ni conexión de red.
    """

    def _import_mock(self, stub_raises=None):
        """Devuelve un mock de importlib.import_module que produce stubs controlables."""
        mock_stub = MagicMock()
        if stub_raises:
            mock_stub.ListHypervisors.side_effect = stub_raises
            mock_stub.GetGlobalState.side_effect  = stub_raises
            mock_stub.ListBots.side_effect         = stub_raises
            mock_stub.GetState.side_effect         = stub_raises
        mock_module = MagicMock()
        # Cualquier atributo del módulo devuelve el stub o su clase
        mock_module.GestorBotsServiceStub  = MagicMock(return_value=mock_stub)
        mock_module.GestorMundoServiceStub = MagicMock(return_value=mock_stub)
        mock_module.HypervisorServiceStub  = MagicMock(return_value=mock_stub)
        mock_module.SectorServiceStub      = MagicMock(return_value=mock_stub)
        # Clases de request (se instancian sin args)
        for cls in ["ListHypervisorsRequest", "GetGlobalStateRequest",
                    "ListBotsRequest", "GetStateRequest"]:
            setattr(mock_module, cls, MagicMock)
        return mock_module

    def test_devuelve_true_si_el_componente_responde(self):
        from Infraestructura.AWS.remote import _healthcheck_remoto

        with patch("Infraestructura.AWS.remote.importlib.import_module",
                   return_value=self._import_mock()):
            with patch("Infraestructura.AWS.remote.grpc.insecure_channel"):
                with patch("Infraestructura.AWS.remote.time.monotonic",
                           return_value=0):
                    resultado = _healthcheck_remoto("gestor_bots", "1.2.3.4", CFG)

        assert resultado is True

    def test_devuelve_false_si_se_agota_el_timeout(self):
        from Infraestructura.AWS.remote import _healthcheck_remoto

        with patch("Infraestructura.AWS.remote.importlib.import_module",
                   return_value=self._import_mock(stub_raises=Exception("sin respuesta"))):
            with patch("Infraestructura.AWS.remote.grpc.insecure_channel"):
                with patch("Infraestructura.AWS.remote.time.sleep"):
                    # monotonic: deadline=0+5=5; primera comprobación=0 (ok, sigue);
                    # segunda=999 (> deadline, sale del bucle)
                    with patch("Infraestructura.AWS.remote.time.monotonic",
                               side_effect=[0, 0, 999]):
                        resultado = _healthcheck_remoto("gestor_bots", "1.2.3.4", CFG)

        assert resultado is False

    @pytest.mark.parametrize("comp_id,ip", [
        ("gestor_bots",  "10.0.0.1"),
        ("gestor_mundo", "10.0.0.2"),
        ("hv_0",         "10.0.0.3"),
        ("sector_0",     "10.0.0.4"),
    ])
    def test_todos_los_tipos_de_componente(self, comp_id, ip):
        """El healthcheck funciona para los cuatro tipos de componente."""
        from Infraestructura.AWS.remote import _healthcheck_remoto

        with patch("Infraestructura.AWS.remote.importlib.import_module",
                   return_value=self._import_mock()):
            with patch("Infraestructura.AWS.remote.grpc.insecure_channel"):
                with patch("Infraestructura.AWS.remote.time.monotonic", return_value=0):
                    resultado = _healthcheck_remoto(comp_id, ip, CFG)

        assert resultado is True
