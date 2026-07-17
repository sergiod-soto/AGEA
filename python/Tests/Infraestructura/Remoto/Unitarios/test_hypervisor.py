# Tests/Infraestructura/Remoto/Unitarios/test_hypervisor.py
"""
test_hypervisor.py — Pruebas unitarias de Hypervisor: spawn/kill,
control de presupuesto, y el Flujo B de muerte de bots
(_watch_bot_process detectando crash vs terminación deliberada).

Se inyecta un LanzadorProcesosBot falso para no escribir a disco ni
lanzar procesos reales del sistema operativo.
"""

import threading
import time

import pytest

from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor


class FakeProceso:
    """Doble de subprocess.Popen — controlable a mano desde el test."""

    def __init__(self):
        self._terminado = threading.Event()
        self.returncode = None
        self.terminate_llamado = False

    def wait(self):
        self._terminado.wait()
        return self.returncode

    def terminar_deliberadamente(self):
        self.returncode = 0
        self._terminado.set()

    def crashear(self, codigo=1):
        self.returncode = codigo
        self._terminado.set()

    def terminate(self):
        self.terminate_llamado = True


class FakeLanzador:
    def __init__(self, proceso: FakeProceso):
        self._proceso = proceso
        self.limpiar_llamado_con = []

    def lanzar(self, hypervisor_id, bot_id, codigo_gz, env_extra):
        return self._proceso

    def limpiar(self, hypervisor_id, bot_id):
        self.limpiar_llamado_con.append((hypervisor_id, bot_id))


class FakeGestorClient:
    def __init__(self):
        self.notificaciones = []

    def notificar_avatar_sin_piloto(self, bot_id):
        self.notificaciones.append(bot_id)


@pytest.fixture
def proceso() -> FakeProceso:
    return FakeProceso()


@pytest.fixture
def hv(proceso: FakeProceso) -> Hypervisor:
    return Hypervisor(
        hypervisor_id="hv_test",
        gestor_client=FakeGestorClient(),
        capacity=2,
        lanzador_procesos=FakeLanzador(proceso),
    )


@pytest.mark.unit
def test_spawn_bot_ok(hv: Hypervisor):
    resultado = hv.spawn_bot({"bot_id": "bot_1", "budget": 50})
    assert resultado.ok is True
    assert hv.get_bot_stats("bot_1").points_left == 50


@pytest.mark.unit
def test_spawn_bot_id_vacio_falla(hv: Hypervisor):
    resultado = hv.spawn_bot({"bot_id": "", "budget": 50})
    assert resultado.ok is False


@pytest.mark.unit
def test_spawn_bot_duplicado_falla(hv: Hypervisor):
    hv.spawn_bot({"bot_id": "bot_1", "budget": 50})
    resultado = hv.spawn_bot({"bot_id": "bot_1", "budget": 50})
    assert resultado.ok is False
    assert "ya existe" in resultado.error.lower()


@pytest.mark.unit
def test_spawn_bot_a_plena_capacidad_falla(hv: Hypervisor):
    hv.spawn_bot({"bot_id": "b1", "budget": 1})
    hv.spawn_bot({"bot_id": "b2", "budget": 1})  # capacity=2, ya lleno
    resultado = hv.spawn_bot({"bot_id": "b3", "budget": 1})
    assert resultado.ok is False
    assert "plena capacidad" in resultado.error.lower()


@pytest.mark.unit
def test_try_spend_points_descuenta_y_rechaza_sin_saldo(hv: Hypervisor):
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})

    ok, restante = hv.try_spend_points("bot_1", cost=4)
    assert ok is True
    assert restante == 6

    ok, restante = hv.try_spend_points("bot_1", cost=100)
    assert ok is False
    assert restante == 6, "un intento fallido no debe descontar puntos"


@pytest.mark.unit
def test_try_spend_points_congelado_rechaza_siempre(hv: Hypervisor):
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    hv.freeze()

    ok, restante = hv.try_spend_points("bot_1", cost=1)
    assert ok is False
    assert restante == 0


@pytest.mark.unit
def test_kill_bot_termina_proceso_y_limpia(hv: Hypervisor, proceso: FakeProceso):
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    hv.kill_bot("bot_1")

    assert proceso.terminate_llamado is True
    assert hv.get_bot_stats("bot_1") is None


@pytest.mark.unit
def test_kill_bot_desconocido_no_lanza(hv: Hypervisor):
    hv.kill_bot("no_existe")


@pytest.mark.unit
def test_watch_bot_process_terminacion_deliberada_no_notifica(
    hv: Hypervisor, proceso: FakeProceso
):
    """
    Flujo A: kill_bot() ya quitó el bot de self._bots ANTES de que el
    proceso muera — _watch_bot_process no debe notificar nada.
    """
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    hv.kill_bot("bot_1")  # ya lo quita del registro y llama terminate()
    proceso.terminar_deliberadamente()

    time.sleep(0.2)  # dar tiempo al hilo watcher, que ya estaba corriendo

    assert hv.gestor_client.notificaciones == []


@pytest.mark.unit
def test_watch_bot_process_crash_notifica_avatar_sin_piloto(
    hv: Hypervisor, proceso: FakeProceso
):
    """
    Flujo B: el proceso muere SIN que kill_bot lo haya quitado antes
    — debe considerarse un crash y notificar al Gestor.
    """
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    proceso.crashear(codigo=1)

    time.sleep(0.2)

    assert hv.gestor_client.notificaciones == ["bot_1"]
    assert hv.get_bot_stats("bot_1") is None, "el registro debe limpiarse tras el crash"


@pytest.mark.unit
def test_reset_budgets_ignora_bots_desconocidos(hv: Hypervisor):
    hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    hv.reset_budgets(["bot_1", "no_existe"], {"bot_1": 99})

    assert hv.get_bot_stats("bot_1").points_left == 99
