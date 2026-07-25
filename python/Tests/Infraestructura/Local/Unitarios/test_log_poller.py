# Tests/Infraestructura/Local/Unitarios/test_log_poller.py
"""
test_log_poller.py — Pruebas unitarias de LogPoller: polling periódico
de PullLogs sobre varios componentes, escribiendo lo recibido vía la
función `escribir` inyectada. A diferencia de MonitorComponentes, NO
es fail-fast: un fallo puntual de un componente no debe afectar a los
demás ni detener el poller.
"""

import time

import pytest

from Infraestructura.Gestores.Log.log_poller import LogPoller


def _esperar(condicion, timeout=2.0, paso=0.01):
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        if condicion():
            return True
        time.sleep(paso)
    return False


@pytest.mark.unit
def test_poller_escribe_todos_los_registros_devueltos():
    escritos = []
    poller = LogPoller(intervalo_segundos=0.02, escribir=lambda r: escritos.append(r))
    poller.registrar("comp_a", lambda: [1, 2, 3])
    poller.iniciar()

    _esperar(lambda: len(escritos) >= 3)
    poller.detener()

    assert escritos[:3] == [1, 2, 3]


@pytest.mark.unit
def test_poller_fallo_en_un_componente_no_afecta_a_los_demas():
    escritos = []

    def pull_falla():
        raise RuntimeError("PullLogs falló")

    poller = LogPoller(intervalo_segundos=0.02, escribir=lambda r: escritos.append(r))
    poller.registrar("comp_roto", pull_falla)
    poller.registrar("comp_sano", lambda: ["ok"])
    poller.iniciar()

    disparado = _esperar(lambda: "ok" in escritos)
    poller.detener()

    assert (
        disparado
    ), "comp_sano debería seguir recibiendo pulls pese al fallo de comp_roto"


@pytest.mark.unit
def test_detener_para_nuevas_escrituras():
    escritos = []
    poller = LogPoller(intervalo_segundos=0.02, escribir=lambda r: escritos.append(r))
    poller.registrar("comp_a", lambda: [1])
    poller.iniciar()
    _esperar(lambda: len(escritos) >= 1)

    poller.detener()
    cantidad_al_detener = len(escritos)
    time.sleep(0.1)  # margen para comprobar que no siguen llegando

    assert len(escritos) == cantidad_al_detener
