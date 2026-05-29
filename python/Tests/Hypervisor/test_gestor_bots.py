"""
Test/Hypervisor/test_gestor.py

Tests de la lógica pura del Gestor. No necesitan gRPC.

Estructura:
    TestGestorConstructor     — bots_por_hypervisor como parámetro central
    TestCapacidad             — hvs_necesarios() y capacidad_total()
    TestNextBotId             — IDs incrementales y thread-safety
    TestRegistroHypervisor    — warning en mismatch de capacity
    TestSelectHypervisor      — límite efectivo = bots_por_hypervisor
    TestSpawnBotSinCliente    — spawn falla limpio si no hay cliente HV
    TestEnvPropagacion        — patrón que usa gestor_server para leer el env
"""

from __future__ import annotations

import os
import threading
import unittest
from unittest.mock import MagicMock, patch

from Hypervisores.Gestor_Bots.gestor_bots import BotInfo, BotStats, Gestor_Bots


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gestor(bots_por_hv: int = 10) -> Gestor_Bots:
    """Crea un Gestor_Bots sin mundo_client (modo test)."""
    return Gestor_Bots(bots_por_hypervisor=bots_por_hv)


def _registrar(g: Gestor_Bots, hv_id: str, capacity: int | None = None) -> None:
    """Registra un HV con capacity == bots_por_hypervisor por defecto."""
    g.register_hypervisor(
        hypervisor_id=hv_id,
        address="127.0.0.1",
        port=50100,
        proxy_port=50200,
        capacity=capacity if capacity is not None else g.bots_por_hypervisor,
    )


# ---------------------------------------------------------------------------
# 1. Constructor
# ---------------------------------------------------------------------------

class TestGestorConstructor(unittest.TestCase):

    def test_default_bots_por_hv(self):
        g = Gestor_Bots()
        self.assertEqual(g.bots_por_hypervisor, 100)

    def test_custom_bots_por_hv(self):
        g = _gestor(bots_por_hv=42)
        self.assertEqual(g.bots_por_hypervisor, 42)

    def test_atributo_publico(self):
        """gestor_server necesita leer el atributo directamente."""
        g = _gestor(50)
        self.assertIsInstance(g.bots_por_hypervisor, int)

    def test_mundo_client_sigue_siendo_inyectable(self):
        """Asegura retrocompatibilidad: mundo_client no se eliminó."""
        mc = MagicMock()
        g = Gestor_Bots(mundo_client=mc, bots_por_hypervisor=10)
        self.assertIs(g.mundo_client, mc)

    def test_cero_lanza_error(self):
        with self.assertRaises((ValueError, AssertionError)):
            Gestor_Bots(bots_por_hypervisor=0)

    def test_negativo_lanza_error(self):
        with self.assertRaises((ValueError, AssertionError)):
            Gestor_Bots(bots_por_hypervisor=-5)


# ---------------------------------------------------------------------------
# 2. hvs_necesarios y capacidad_total
# ---------------------------------------------------------------------------

class TestCapacidad(unittest.TestCase):

    def setUp(self):
        self.g = _gestor(bots_por_hv=100)

    def test_hvs_exacto(self):
        self.assertEqual(self.g.hvs_necesarios(200), 2)

    def test_hvs_redondeo_arriba(self):
        self.assertEqual(self.g.hvs_necesarios(101), 2)

    def test_hvs_uno(self):
        self.assertEqual(self.g.hvs_necesarios(1), 1)

    def test_hvs_limite_justo(self):
        self.assertEqual(self.g.hvs_necesarios(100), 1)

    def test_capacidad_sin_hvs(self):
        self.assertEqual(self.g.capacidad_total(), 0)

    def test_capacidad_con_dos_hvs(self):
        _registrar(self.g, "hv_01")
        _registrar(self.g, "hv_02")
        self.assertEqual(self.g.capacidad_total(), 200)

    def test_capacidad_usa_bots_por_hv_no_capacity_declarada(self):
        """
        Aunque el HV declare capacity=999, capacidad_total() usa bots_por_hypervisor.
        """
        g = _gestor(bots_por_hv=50)
        _registrar(g, "hv_01", capacity=999)
        self.assertEqual(g.capacidad_total(), 50)


# ---------------------------------------------------------------------------
# 3. next_bot_id — incrementales y thread-safe
# ---------------------------------------------------------------------------

class TestNextBotId(unittest.TestCase):

    def setUp(self):
        self.g = _gestor()

    def test_primero_bot_0001(self):
        self.assertEqual(self.g.next_bot_id(), "bot_0001")

    def test_incrementa_secuencialmente(self):
        ids = [self.g.next_bot_id() for _ in range(3)]
        self.assertEqual(ids, ["bot_0001", "bot_0002", "bot_0003"])

    def test_padding_cuatro_digitos(self):
        for _ in range(9):
            self.g.next_bot_id()
        self.assertEqual(self.g.next_bot_id(), "bot_0010")

    def test_thread_safe_sin_duplicados(self):
        ids = []
        lock = threading.Lock()

        def gen():
            bot_id = self.g.next_bot_id()
            with lock:
                ids.append(bot_id)

        threads = [threading.Thread(target=gen) for _ in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(ids), len(set(ids)), "IDs duplicados detectados")

    def test_contadores_independientes_por_instancia(self):
        g2 = _gestor()
        self.assertEqual(self.g.next_bot_id(), "bot_0001")
        self.assertEqual(g2.next_bot_id(), "bot_0001")


# ---------------------------------------------------------------------------
# 4. Registro de Hypervisores — warning en mismatch
# ---------------------------------------------------------------------------

class TestRegistroHypervisor(unittest.TestCase):

    def setUp(self):
        self.g = _gestor(bots_por_hv=100)

    def test_registro_exitoso(self):
        _registrar(self.g, "hv_01")
        hvs = self.g.list_hypervisors().hypervisors
        self.assertEqual(len(hvs), 1)
        self.assertEqual(hvs[0].hypervisor_id, "hv_01")

    def test_capacity_mismatch_emite_warning(self):
        with self.assertLogs("Hypervisores.Gestor_Bots.gestor_bots", level="WARNING") as cm:
            _registrar(self.g, "hv_01", capacity=999)
        self.assertTrue(
            any("capacity" in m.lower() or "bots_por_hypervisor" in m.lower()
                for m in cm.output),
            f"Warning esperado no encontrado en: {cm.output}",
        )

    def test_capacity_correcta_no_emite_warning_de_mismatch(self):
        with self.assertLogs("Hypervisores.Gestor_Bots.gestor_bots", level="DEBUG") as cm:
            _registrar(self.g, "hv_01", capacity=100)
        mismatch_warnings = [
            m for m in cm.output
            if "WARNING" in m and ("capacity" in m.lower() or "mismatch" in m.lower())
        ]
        self.assertEqual(mismatch_warnings, [])

    def test_registro_duplicado_emite_warning(self):
        _registrar(self.g, "hv_01")
        with self.assertLogs("Hypervisores.Gestor_Bots.gestor_bots", level="WARNING") as cm:
            _registrar(self.g, "hv_01")  # duplicado
        self.assertTrue(any("ya registrado" in m for m in cm.output))


# ---------------------------------------------------------------------------
# 5. _select_hypervisor — límite efectivo = bots_por_hypervisor
# ---------------------------------------------------------------------------

class TestSelectHypervisor(unittest.TestCase):
    """
    _select_hypervisor es privado; lo probamos vía spawn_bot,
    inyectando clientes mock para que el spawn llegue hasta el HV.
    """

    def _gestor_con_cliente_mock(self, bots_por_hv: int, hv_id: str) -> Gestor_Bots:
        g = _gestor(bots_por_hv=bots_por_hv)
        _registrar(g, hv_id)
        mock_client = MagicMock()
        mock_client.spawn_bot.return_value = BotInfo(
            bot_id="", hypervisor_id=hv_id, proxy_address="", ok=True
        )
        g.set_hypervisor_client(hv_id, mock_client)
        return g

    def test_sin_hvs_spawn_falla(self):
        g = _gestor()
        info = g.spawn_bot({"bot_id": "bot_0001"})
        self.assertFalse(info.ok)
        self.assertIn("hypervisor", info.error.lower())

    def test_spawn_usa_hv_disponible(self):
        g = self._gestor_con_cliente_mock(bots_por_hv=2, hv_id="hv_01")
        info = g.spawn_bot({"bot_id": "bot_0001"})
        self.assertTrue(info.ok)
        self.assertEqual(info.hypervisor_id, "hv_01")

    def test_limite_efectivo_es_bots_por_hv(self):
        """
        Con bots_por_hv=2 y capacity declarada=999, solo deben caber 2 bots.
        """
        g = _gestor(bots_por_hv=2)
        _registrar(g, "hv_01", capacity=999)
        mock_client = MagicMock()
        mock_client.spawn_bot.side_effect = lambda cfg: BotInfo(
            bot_id=cfg["bot_id"], hypervisor_id="hv_01",
            proxy_address="127.0.0.1:50200", ok=True,
        )
        g.set_hypervisor_client("hv_01", mock_client)

        r1 = g.spawn_bot({"bot_id": "bot_0001"})
        r2 = g.spawn_bot({"bot_id": "bot_0002"})
        r3 = g.spawn_bot({"bot_id": "bot_0003"})  # debe fallar

        self.assertTrue(r1.ok)
        self.assertTrue(r2.ok)
        self.assertFalse(r3.ok, "El tercer bot no debería caber con bots_por_hv=2")

    def test_selecciona_hv_con_mas_espacio(self):
        """Con dos HVs, elige el que tiene menos carga relativa."""
        g = _gestor(bots_por_hv=5)
        for hv_id in ("hv_01", "hv_02"):
            _registrar(g, hv_id)
            mock_client = MagicMock()
            mock_client.spawn_bot.side_effect = lambda cfg, _hv=hv_id: BotInfo(
                bot_id=cfg["bot_id"], hypervisor_id=_hv,
                proxy_address="127.0.0.1:50200", ok=True,
            )
            g.set_hypervisor_client(hv_id, mock_client)

        # Manipulamos cargas directamente
        with g._lock:
            g._hypervisors["hv_01"].current_load = 4  # 1 libre
            g._hypervisors["hv_02"].current_load = 1  # 4 libres

        info = g.spawn_bot({"bot_id": "bot_nuevo"})
        self.assertTrue(info.ok)
        self.assertEqual(info.hypervisor_id, "hv_02")


# ---------------------------------------------------------------------------
# 6. spawn_bot sin cliente — rollback limpio
# ---------------------------------------------------------------------------

class TestSpawnBotSinCliente(unittest.TestCase):

    def test_sin_cliente_no_registra_bot(self):
        g = _gestor()
        _registrar(g, "hv_01")
        info = g.spawn_bot({"bot_id": "bot_0001"})
        self.assertFalse(info.ok)
        self.assertNotIn("bot_0001", g._bots)

    def test_sin_cliente_revierte_carga(self):
        g = _gestor()
        _registrar(g, "hv_01")
        carga_antes = g._hypervisors["hv_01"].current_load
        g.spawn_bot({"bot_id": "bot_0001"})
        carga_despues = g._hypervisors["hv_01"].current_load
        self.assertEqual(carga_antes, carga_despues)


# ---------------------------------------------------------------------------
# 7. Patrón de gestor_server: leer BOTS_POR_HYPERVISOR del entorno
# ---------------------------------------------------------------------------

class TestEnvPropagacion(unittest.TestCase):
    """
    Verifica el patrón exacto que usa serve() en gestor_server.py:
        bots_por_hv = int(os.environ.get("BOTS_POR_HYPERVISOR", "100"))
        gestor = Gestor(bots_por_hypervisor=bots_por_hv)
    """

    def _crear_gestor_desde_env(self) -> Gestor_Bots:
        bots_por_hv = int(os.environ.get("BOTS_POR_HYPERVISOR", "100"))
        return Gestor_Bots(bots_por_hypervisor=bots_por_hv)

    def test_default_sin_variable(self):
        env = {k: v for k, v in os.environ.items() if k != "BOTS_POR_HYPERVISOR"}
        with patch.dict(os.environ, env, clear=True):
            g = self._crear_gestor_desde_env()
        self.assertEqual(g.bots_por_hypervisor, 100)

    def test_lee_variable(self):
        with patch.dict(os.environ, {"BOTS_POR_HYPERVISOR": "77"}):
            g = self._crear_gestor_desde_env()
        self.assertEqual(g.bots_por_hypervisor, 77)

    def test_valor_uno(self):
        with patch.dict(os.environ, {"BOTS_POR_HYPERVISOR": "1"}):
            g = self._crear_gestor_desde_env()
        self.assertEqual(g.bots_por_hypervisor, 1)

    def test_valor_invalido_lanza_value_error(self):
        with patch.dict(os.environ, {"BOTS_POR_HYPERVISOR": "no_es_numero"}):
            with self.assertRaises(ValueError):
                self._crear_gestor_desde_env()

    def test_valor_cero_lanza_error_en_gestor(self):
        with patch.dict(os.environ, {"BOTS_POR_HYPERVISOR": "0"}):
            with self.assertRaises((ValueError, AssertionError)):
                self._crear_gestor_desde_env()


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
