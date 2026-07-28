# Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_local_roundtrip.py


import asyncio
from types import SimpleNamespace

import pytest

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

    async def obtener_celdas_en_region(self, min_pos, max_pos):
        return []

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

    yield master, espectador, logica_mundo_fake

    await master.close()
    await espectador.close()
    tarea = logica_remoto._foco._tarea_vigilante
    if tarea is not None:
        tarea.cancel()


@pytest.mark.integration
async def test_actualizar_foco_via_grpc_responde_ok(stack_foco):
    master, _, _ = stack_foco

    ok, error = await master.actualizar_foco(
        min_pos=(0, 0), max_pos=(10, 10), incluir=["Color"], modo="test"
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
    master, espectador, logica_mundo_fake = stack_foco

    await master.actualizar_foco(
        min_pos=(0, 0), max_pos=(10, 10), incluir=[], modo="modo_real"
    )

    gen_espectador = espectador.suscribirse_foco()
    gen_master = master.suscribirse_foco()
    await asyncio.sleep(0.1)  # deja que ambas suscripciones lleguen al servidor

    logica_mundo_fake.tick_actual = 1

    actualizacion_espectador = await asyncio.wait_for(
        gen_espectador.__anext__(), timeout=2.0
    )
    actualizacion_master = await asyncio.wait_for(gen_master.__anext__(), timeout=2.0)

    assert actualizacion_espectador.ok is True
    assert actualizacion_espectador.tick_actual == 1
    assert actualizacion_espectador.representacion == b"representacion_real"
    assert actualizacion_master.tick_actual == actualizacion_espectador.tick_actual

    await gen_espectador.aclose()
    await gen_master.aclose()
