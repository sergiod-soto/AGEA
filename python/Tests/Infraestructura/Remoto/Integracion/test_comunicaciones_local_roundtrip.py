# Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_local_roundtrip.py
"""
test_comunicaciones_local_roundtrip.py — Integración de extremo a
extremo del puente completo: ComunicacionesLocal (cliente, en la
máquina local) → ComunicacionRemotaService real (gRPC) →
ComunicacionesRemotoServicer → ComunicacionesRemoto.ejecutar() →
dispatch real de Funciones/*.py.

Es el único test que ejercita las TRES capas juntas; los tests de
test_comunicaciones_remoto_ejecutar.py y test_comunicaciones_remoto.py
ya cubren cada capa por separado con más detalle de casos — aquí basta
con unos pocos casos representativos para confirmar que el cableado
end-to-end funciona.

Sección Vista_Foco (NUEVA): mismo criterio, pero para
ActualizarFoco/SuscribirseFoco — confirma que el master (vía
ComunicacionesLocal.actualizar_foco) y un espectador (vía
ComunicacionesLocal.suscribirse_foco, en OTRA instancia de
ComunicacionesLocal, como sería un segundo proceso Unity) reciben de
verdad la misma emisión a través de la red real, no solo en memoria
(eso ya lo cubre test_comunicaciones_remoto.py con dobles).
"""

import asyncio
from types import SimpleNamespace

import pytest

from Core.Entities.entity import Modos
from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)
from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto import (
    ComunicacionesRemoto,
)
from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto_servicer import (
    ComunicacionesRemotoServicer,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    comunicacion_remota_service_pb2 as bridge_pb,
    comunicacion_remota_service_pb2_grpc as bridge_pb_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as mundo_pb,
)


@pytest.fixture
async def cliente_comunicaciones_local(levantar_servidor):
    async def pause():
        return True, ""

    async def get_active_events():
        return []

    clientes = SimpleNamespace(
        logica_mundo=SimpleNamespace(get_active_events=get_active_events),
        gestor_mundo=SimpleNamespace(pause=pause),
        gestor_bots=SimpleNamespace(),
    )
    logica_remoto = ComunicacionesRemoto(clientes)
    servicer = ComunicacionesRemotoServicer(logica_remoto)
    servidor = await levantar_servidor(
        lambda s: bridge_pb_grpc.add_ComunicacionRemotaServiceServicer_to_server(
            servicer, s
        )
    )

    local = ComunicacionesLocal(servidor.address)
    yield local
    await local.close()


@pytest.mark.integration
async def test_pause_roundtrip_completo(cliente_comunicaciones_local):
    ok, error = await cliente_comunicaciones_local.pause()

    assert ok is True
    assert error == ""


@pytest.mark.integration
async def test_get_active_events_roundtrip_completo(cliente_comunicaciones_local):
    resp = await cliente_comunicaciones_local.get_active_events()

    assert resp.ok is True
    assert list(resp.events) == []


@pytest.mark.integration
async def test_operacion_no_registrada_en_remoto_lanza_runtimeerror(
    cliente_comunicaciones_local,
):
    """
    ComunicacionesLocal._ejecutar() traduce un ok=False del PUENTE
    (operación desconocida, ver comunicaciones_remoto.py) en
    RuntimeError — los métodos públicos solo construyen operaciones
    válidas, así que se llama a _ejecutar directamente para forzar
    este caso.
    """
    with pytest.raises(RuntimeError):
        await cliente_comunicaciones_local._ejecutar(
            bridge_pb.GESTOR_MUNDO, "OperacionInventada", mundo_pb.PauseRequest()
        )


# ══════════════════════════════════════════════════════════════════
#  Vista_Foco — roundtrip real end-to-end (master + espectador)
# ══════════════════════════════════════════════════════════════════


class FakeGlobalesResponse:
    def __init__(self, ok=True, tick_actual=0, elementos_globales=(), error=""):
        self.ok = ok
        self.tick_actual = tick_actual
        self.elementos_globales = list(elementos_globales)
        self.error = error


class FakeLogicaMundoFoco:
    """Mismo doble que en test_comunicaciones_remoto.py — aquí lo que
    cambia es que se golpea vía red real, no en memoria."""

    def __init__(self):
        self.tick_actual = 0

    async def get_elementos_globales(self):
        return FakeGlobalesResponse(tick_actual=self.tick_actual)

    async def consultar_representacion(self, min_pos, max_pos, incluir, modo):
        return b"representacion_real"


@pytest.fixture
async def stack_foco(levantar_servidor):
    """
    Levanta el servicer real con un logica_mundo falso controlable, y
    devuelve DOS ComunicacionesLocal distintas contra el mismo
    servidor — una para hacer de "master" (llama a actualizar_foco) y
    otra para hacer de "espectador" (solo se suscribe), tal como
    serían dos procesos Unity distintos hablando con el mismo
    Comunicaciones_Remoto.

    También se expone el propio FocoBroadcaster (logica_remoto._foco):
    algunos tests necesitan sincronizarse con su estado interno (ver
    comentarios en test_master_y_espectador_...) porque es un
    componente de solo-servidor, invisible desde ComunicacionesLocal.
    """
    logica_mundo_fake = FakeLogicaMundoFoco()
    clientes = SimpleNamespace(
        logica_mundo=logica_mundo_fake,
        gestor_mundo=SimpleNamespace(),
        gestor_bots=SimpleNamespace(),
    )
    logica_remoto = ComunicacionesRemoto(clientes)
    servicer = ComunicacionesRemotoServicer(logica_remoto)
    servidor = await levantar_servidor(
        lambda s: bridge_pb_grpc.add_ComunicacionRemotaServiceServicer_to_server(
            servicer, s
        )
    )

    master = ComunicacionesLocal(servidor.address)
    espectador = ComunicacionesLocal(servidor.address)

    yield master, espectador, logica_mundo_fake, logica_remoto._foco

    await master.close()
    await espectador.close()
    tarea = logica_remoto._foco._tarea_vigilante
    if tarea is not None:
        tarea.cancel()


@pytest.mark.integration
async def test_actualizar_foco_via_grpc_responde_ok(stack_foco):
    master, _, _, _ = stack_foco

    ok, error = await master.actualizar_foco(
        min_pos=(0, 0), max_pos=(10, 10), incluir=["Color"], modo=Modos.transporte
    )

    assert ok is True
    assert error == ""


@pytest.mark.integration
async def test_master_y_espectador_reciben_la_misma_actualizacion_via_grpc_real(
    stack_foco,
):
    """
    El caso central del diseño, ahora sobre red real: el master fija
    el foco desde SU ComunicacionesLocal; un espectador con OTRA
    ComunicacionesLocal (mismo servidor) se suscribe sin haber fijado
    nada — y recibe la misma actualización que vería el master.
    """
    master, espectador, logica_mundo_fake, foco_broadcaster = stack_foco

    await master.actualizar_foco(
        min_pos=(0, 0), max_pos=(10, 10), incluir=[], modo=Modos.transporte
    )

    # FocoBroadcaster arranca con _ultimo_tick=None, así que en cuanto
    # llega el PRIMER suscriptor (master o espectador, lo que gane la
    # carrera de conexión de red) el vigilante emite de inmediato con
    # el tick_actual que haya EN ESE MOMENTO (0, el inicial), aunque no
    # sea un cambio real. Esa emisión "fantasma" solo le llega a quien
    # ya esté suscrito — si es el master, su __anext__() se resuelve
    # ahí mismo con tick=0 y nunca llega a ver la transición real a
    # tick=1 de más abajo; el espectador, que se suscribe una fracción
    # de segundo más tarde, sí la ve. Eso es justo lo que causó el
    # `assert 0 == 1` del run anterior.
    #
    # Se neutraliza fijando _ultimo_tick al valor actual ANTES de que
    # nadie se suscriba: así el único disparo posible en este test es
    # el cambio real a tick=1, y llega a ambos por igual porque para
    # entonces los dos ya están suscritos.
    foco_broadcaster._ultimo_tick = logica_mundo_fake.tick_actual

    gen_espectador = espectador.suscribirse_foco()
    gen_master = master.suscribirse_foco()

    # suscribirse_foco() es una función generadora asíncrona: llamarla
    # no ejecuta nada de su cuerpo (ni abre el canal) hasta el primer
    # __anext__(). Por eso se envuelven en tareas ANTES del sleep: así
    # el sleep(0.1) sí espera a que ambas suscripciones lleguen al
    # servidor, en vez de no hacer nada.
    tarea_espectador = asyncio.create_task(gen_espectador.__anext__())
    tarea_master = asyncio.create_task(gen_master.__anext__())
    await asyncio.sleep(0.1)  # deja que ambas suscripciones lleguen al servidor

    logica_mundo_fake.tick_actual = 1

    actualizacion_espectador = await asyncio.wait_for(tarea_espectador, timeout=2.0)
    actualizacion_master = await asyncio.wait_for(tarea_master, timeout=2.0)

    assert actualizacion_espectador.ok is True
    assert actualizacion_espectador.tick_actual == 1
    assert actualizacion_espectador.representacion == b"representacion_real"
    assert actualizacion_master.tick_actual == actualizacion_espectador.tick_actual

    await gen_espectador.aclose()
    await gen_master.aclose()
