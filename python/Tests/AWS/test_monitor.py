"""
Tests para Infraestructura/AWS/monitor.py.

Los tests de timing usan threading.Event para sincronizar en lugar de
sleep fijos, lo que los hace más robustos en entornos lentos.
"""

import time
import threading
from unittest.mock import MagicMock, call

import pytest

from Infraestructura.AWS.monitor import MonitorComponentes

# Intervalo corto para que los tests no tarden
FAST_CFG = {
    "timeouts": {
        "heartbeat_intervalo":  0.05,   # 50 ms
        "heartbeat_perdidos_max": 2,
    }
}


def _esperar_evento(evento: threading.Event, timeout: float = 2.0) -> bool:
    """Espera a que un evento se active, con timeout de seguridad."""
    return evento.wait(timeout=timeout)


class TestMonitorComponentes:

    def test_on_fallo_se_llama_cuando_ping_falla_n_veces(self):
        """on_fallo se dispara cuando un componente supera el límite de fallos consecutivos."""
        llamado = threading.Event()
        on_fallo = MagicMock(side_effect=lambda _: llamado.set())

        monitor = MonitorComponentes(FAST_CFG, on_fallo)
        monitor.registrar("comp_a", MagicMock(side_effect=Exception("sin respuesta")))
        monitor.iniciar()

        assert _esperar_evento(llamado), "on_fallo no se llamó en el tiempo esperado"
        monitor.detener()

        on_fallo.assert_called_once_with("comp_a")

    def test_fallo_resetea_si_ping_recupera(self):
        """Si el ping falla menos de N veces seguidas y luego recupera, on_fallo no se llama."""
        on_fallo = MagicMock()
        monitor = MonitorComponentes(FAST_CFG, on_fallo)

        # Falla 1 vez (< max_perdidos=2), luego recupera indefinidamente
        ping = MagicMock(side_effect=[Exception("fallo puntual")] + [None] * 20)
        monitor.registrar("comp_a", ping)
        monitor.iniciar()

        # Esperar suficiente para que el monitor haga varios ciclos
        time.sleep(0.4)
        monitor.detener()

        on_fallo.assert_not_called()

    def test_on_fallo_se_llama_solo_una_vez_con_multiples_componentes_caidos(self):
        """on_fallo se llama una única vez aunque varios componentes fallen a la vez."""
        llamado = threading.Event()
        on_fallo = MagicMock(side_effect=lambda _: llamado.set())

        monitor = MonitorComponentes(FAST_CFG, on_fallo)
        monitor.registrar("comp_a", MagicMock(side_effect=Exception("muerto")))
        monitor.registrar("comp_b", MagicMock(side_effect=Exception("muerto")))
        monitor.iniciar()

        _esperar_evento(llamado)
        # Esperar un ciclo extra para confirmar que no hay llamadas adicionales
        time.sleep(0.2)
        monitor.detener()

        assert on_fallo.call_count == 1

    def test_detener_para_el_monitor_sin_llamar_on_fallo(self):
        """detener() cierra el monitor limpiamente; on_fallo no se invoca."""
        on_fallo = MagicMock()
        monitor = MonitorComponentes(FAST_CFG, on_fallo)
        monitor.registrar("comp_a", MagicMock())  # ping siempre ok
        monitor.iniciar()

        time.sleep(0.1)
        monitor.detener()
        time.sleep(0.2)  # esperar para detectar llamadas tardías

        on_fallo.assert_not_called()

    def test_contador_de_fallos_se_resetea_entre_episodios(self):
        """
        Un fallo puntual no acumula con fallos de un ciclo posterior.
        Secuencia: falla 1 → ok → falla 1 → ok → on_fallo nunca se llama.
        """
        on_fallo = MagicMock()
        monitor = MonitorComponentes(FAST_CFG, on_fallo)

        ping = MagicMock(side_effect=[
            Exception("fallo"),  # ciclo 1: falla (count=1)
            None,                # ciclo 2: ok    (count=0)
            Exception("fallo"),  # ciclo 3: falla (count=1)
            None,                # ciclo 4: ok    (count=0)
            *([None] * 10),
        ])
        monitor.registrar("comp_a", ping)
        monitor.iniciar()

        time.sleep(0.5)
        monitor.detener()

        on_fallo.assert_not_called()
