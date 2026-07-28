# Tests/Infraestructura/Remoto/Unitarios/test_hypervisor.py
"""
test_hypervisor.py — Pruebas unitarias de Hypervisor: spawn/kill,
control de presupuesto, y el Flujo B de muerte de bots
(_watch_bot_process detectando crash vs terminación deliberada).

Se inyecta un LanzadorProcesosBot falso para no escribir a disco ni
lanzar procesos reales del sistema operativo.

ADAPTADO a la migración de Hypervisor a asyncio (ver docstring de
hypervisor.py): todos los métodos de estado ahora son `async def`, y
_watch_bot_process ya no corre en un hilo daemon sino como una
asyncio.Task que hace `await proceso.wait()` — por eso FakeProceso usa
asyncio.Event en vez de threading.Event (bloquear con threading.Event
aquí congelaría el propio loop de eventos), y FakeLanzador.lanzar pasa
a ser `async def` (Hypervisor ahora hace `await self._lanzador.lanzar(...)`).
"""

import asyncio
from typing import AsyncGenerator

import pytest

from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor


class FakeProceso:
    """
    Doble de asyncio.subprocess.Process — controlable a mano desde el
    test. `wait()` es async (se espera con `await proceso.wait()`
    dentro de _watch_bot_process); `terminate()` sigue siendo síncrono,
    igual que en la API real de asyncio.subprocess.Process.
    """

    def __init__(self):
        self._terminado = asyncio.Event()
        self.returncode = None
        self.terminate_llamado = False

    async def wait(self):
        await self._terminado.wait()
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

    async def lanzar(self, hypervisor_id, bot_id, codigo_gz, env_extra):
        return self._proceso

    def limpiar(self, hypervisor_id, bot_id):
        self.limpiar_llamado_con.append((hypervisor_id, bot_id))


class FakeGestorClient:
    """
    Doble de GestorBotsClientAsync — notificar_avatar_sin_piloto ahora
    es async porque Hypervisor hace `await
    self.gestor_client.notificar_avatar_sin_piloto(bot_id)`.
    """

    def __init__(self):
        self.notificaciones = []

    async def notificar_avatar_sin_piloto(self, bot_id):
        self.notificaciones.append(bot_id)


@pytest.fixture
def proceso() -> FakeProceso:
    return FakeProceso()


@pytest.fixture
async def hv(proceso: FakeProceso) -> AsyncGenerator[Hypervisor, None]:
    """
    Fixture async: al terminar el test se cancelan los watchers que
    hayan quedado vivos (p.ej. en los tests que nunca crashean el
    proceso a propósito) — si no, la Task de _watch_bot_process
    quedaría esperando `proceso.wait()` para siempre tras cerrarse el
    loop del test, y pytest-asyncio avisaría de tareas no recogidas.
    """
    instancia = Hypervisor(
        hypervisor_id="hv_test",
        gestor_client=FakeGestorClient(),
        capacity=2,
        lanzador_procesos=FakeLanzador(proceso),
    )
    yield instancia
    for tarea in instancia._watchers.values():
        tarea.cancel()


@pytest.mark.unit
async def test_spawn_bot_ok(hv: Hypervisor):
    resultado = await hv.spawn_bot({"bot_id": "bot_1", "budget": 50})
    assert resultado.ok is True
    stats = await hv.get_bot_stats("bot_1")
    assert stats.points_left == 50


@pytest.mark.unit
async def test_spawn_bot_id_vacio_falla(hv: Hypervisor):
    resultado = await hv.spawn_bot({"bot_id": "", "budget": 50})
    assert resultado.ok is False


@pytest.mark.unit
async def test_spawn_bot_duplicado_falla(hv: Hypervisor):
    await hv.spawn_bot({"bot_id": "bot_1", "budget": 50})
    resultado = await hv.spawn_bot({"bot_id": "bot_1", "budget": 50})
    assert resultado.ok is False
    assert "ya existe" in resultado.error.lower()


@pytest.mark.unit
async def test_spawn_bot_a_plena_capacidad_falla(hv: Hypervisor):
    await hv.spawn_bot({"bot_id": "b1", "budget": 1})
    await hv.spawn_bot({"bot_id": "b2", "budget": 1})  # capacity=2, ya lleno
    resultado = await hv.spawn_bot({"bot_id": "b3", "budget": 1})
    assert resultado.ok is False
    assert "plena capacidad" in resultado.error.lower()


@pytest.mark.unit
async def test_try_spend_points_descuenta_y_rechaza_sin_saldo(hv: Hypervisor):
    await hv.spawn_bot({"bot_id": "bot_1", "budget": 10})

    ok, restante = await hv.try_spend_points("bot_1", cost=4)
    assert ok is True
    assert restante == 6

    ok, restante = await hv.try_spend_points("bot_1", cost=100)
    assert ok is False
    assert restante == 6, "un intento fallido no debe descontar puntos"


@pytest.mark.unit
async def test_try_spend_points_congelado_rechaza_siempre(hv: Hypervisor):
    await hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    await hv.freeze()

    ok, restante = await hv.try_spend_points("bot_1", cost=1)
    assert ok is False
    assert restante == 0


@pytest.mark.unit
async def test_kill_bot_termina_proceso_y_limpia(hv: Hypervisor, proceso: FakeProceso):
    await hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    await hv.kill_bot("bot_1")

    assert proceso.terminate_llamado is True
    assert await hv.get_bot_stats("bot_1") is None


@pytest.mark.unit
async def test_kill_bot_desconocido_no_lanza(hv: Hypervisor):
    await hv.kill_bot("no_existe")


@pytest.mark.unit
async def test_watch_bot_process_terminacion_deliberada_no_notifica(
    hv: Hypervisor, proceso: FakeProceso
):
    """
    Flujo A: kill_bot() ya quitó el bot de self._bots ANTES de que el
    proceso muera — _watch_bot_process no debe notificar nada.
    """
    await hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    await hv.kill_bot("bot_1")  # ya lo quita del registro y llama terminate()
    proceso.terminar_deliberadamente()

    await asyncio.sleep(0.1)  # dar tiempo a la Task watcher, que ya estaba corriendo

    assert hv.gestor_client.notificaciones == []


@pytest.mark.unit
async def test_watch_bot_process_crash_notifica_avatar_sin_piloto(
    hv: Hypervisor, proceso: FakeProceso
):
    """
    Flujo B: el proceso muere SIN que kill_bot lo haya quitado antes
    — debe considerarse un crash y notificar al Gestor.
    """
    await hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    proceso.crashear(codigo=1)

    await asyncio.sleep(0.1)

    assert hv.gestor_client.notificaciones == ["bot_1"]
    assert (
        await hv.get_bot_stats("bot_1") is None
    ), "el registro debe limpiarse tras el crash"


@pytest.mark.unit
async def test_reset_budgets_ignora_bots_desconocidos(hv: Hypervisor):
    await hv.spawn_bot({"bot_id": "bot_1", "budget": 10})
    await hv.reset_budgets(["bot_1", "no_existe"], {"bot_1": 99})

    stats = await hv.get_bot_stats("bot_1")
    assert stats.points_left == 99
