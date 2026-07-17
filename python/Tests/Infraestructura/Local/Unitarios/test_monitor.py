# Tests/Infraestructura/Local/Unitarios/test_monitor.py
"""
test_monitor.py — Pruebas unitarias de MonitorComponentes.

Se prueban dos niveles:
  1. _poll_uno() directamente — lógica de conteo de fallos, sin hilos
     ni tiempos reales de por medio.
  2. iniciar()/detener() con un intervalo real muy pequeño — para
     comprobar la integración del hilo de fondo (fail-fast, disparo
     único de on_fallo). Estos usan time.sleep real y timeouts de
     sondeo generosos para no ser frágiles en CI lento.
"""

import time

import pytest

from Infraestructura.AWS.monitor import MonitorComponentes


def _config(intervalo=0.02, max_perdidos=2):
    return {
        "timeouts": {
            "heartbeat_intervalo": intervalo,
            "heartbeat_perdidos_max": max_perdidos,
        }
    }


# ── _poll_uno — lógica pura de conteo ───────────────────────────────


@pytest.mark.unit
def test_poll_uno_devuelve_none_si_ping_ok():
    monitor = MonitorComponentes(_config(), on_fallo=lambda c: None)
    monitor.registrar("comp_a", lambda: None)

    resultado = monitor._poll_uno("comp_a", monitor._pings["comp_a"])

    assert resultado is None
    assert monitor._fallos["comp_a"] == 0


@pytest.mark.unit
def test_poll_uno_incrementa_fallos_sin_disparar_bajo_el_umbral():
    monitor = MonitorComponentes(_config(max_perdidos=3), on_fallo=lambda c: None)

    def ping_falla():
        raise RuntimeError("no responde")

    monitor.registrar("comp_a", ping_falla)

    resultado = monitor._poll_uno("comp_a", ping_falla)

    assert resultado is None  # aún no llega al máximo (1 < 3)
    assert monitor._fallos["comp_a"] == 1


@pytest.mark.unit
def test_poll_uno_dispara_al_alcanzar_el_maximo():
    monitor = MonitorComponentes(_config(max_perdidos=2), on_fallo=lambda c: None)

    def ping_falla():
        raise RuntimeError("no responde")

    monitor.registrar("comp_a", ping_falla)
    monitor._poll_uno("comp_a", ping_falla)  # fallo 1/2
    resultado = monitor._poll_uno("comp_a", ping_falla)  # fallo 2/2 → dispara

    assert resultado == "comp_a"


@pytest.mark.unit
def test_poll_uno_exito_tras_fallos_resetea_contador():
    monitor = MonitorComponentes(_config(max_perdidos=3), on_fallo=lambda c: None)

    def ping_falla():
        raise RuntimeError("no responde")

    def ping_ok():
        return None

    monitor.registrar("comp_a", ping_falla)
    monitor._poll_uno("comp_a", ping_falla)
    monitor._poll_uno("comp_a", ping_falla)
    assert monitor._fallos["comp_a"] == 2

    monitor._poll_uno("comp_a", ping_ok)
    assert monitor._fallos["comp_a"] == 0


# ── iniciar()/detener() — integración del hilo de fondo ─────────────


def _esperar(condicion, timeout=2.0, paso=0.01):
    """Sondea condicion() hasta que sea True o expire timeout."""
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        if condicion():
            return True
        time.sleep(paso)
    return False


@pytest.mark.unit
def test_bucle_no_dispara_on_fallo_si_todo_va_bien():
    llamadas = []
    monitor = MonitorComponentes(
        _config(intervalo=0.02, max_perdidos=2), on_fallo=lambda c: llamadas.append(c)
    )
    monitor.registrar("comp_a", lambda: None)
    monitor.iniciar()

    # Damos tiempo a varios ciclos de polling — no debe dispararse nada.
    time.sleep(0.15)
    monitor.detener()

    assert llamadas == []


@pytest.mark.unit
def test_bucle_dispara_on_fallo_una_sola_vez():
    """
    Con dos componentes fallando a la vez, on_fallo debe dispararse
    UNA sola vez (fail-fast se detiene tras el primer disparo) — es la
    garantía central de _fallo_disparado en monitor.py.
    """
    llamadas = []

    def ping_falla():
        raise RuntimeError("caído")

    monitor = MonitorComponentes(
        _config(intervalo=0.02, max_perdidos=1), on_fallo=lambda c: llamadas.append(c)
    )
    monitor.registrar("comp_a", ping_falla)
    monitor.registrar("comp_b", ping_falla)
    monitor.iniciar()

    disparado = _esperar(lambda: len(llamadas) >= 1, timeout=2.0)

    # Margen extra para comprobar que no llega una segunda llamada.
    time.sleep(0.5)

    assert disparado, "on_fallo no se disparó dentro del timeout"
    assert len(llamadas) == 1
