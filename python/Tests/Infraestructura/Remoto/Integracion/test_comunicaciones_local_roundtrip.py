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
    nada — y recibe la misma actualización que vería el master, que
    se suscribe TARDE (después de que ya se repartió el primer frame)
    y aun así debe recibirlo, gracias a la caché de FocoBroadcaster.

    El tick se fija ANTES de que nadie se suscriba: el primer ciclo
    del vigilante dispara solo porque _ultimo_tick empieza en None
    (ver FocoBroadcaster._ciclo_de_vigilancia) — no hace falta forzar
    ninguna carrera con sleeps para que el espectador vea el tick=1
    como su primer frame.
    """
    master, espectador, logica_mundo_fake = stack_foco

    await master.actualizar_foco(
        min_pos=(0, 0), max_pos=(10, 10), incluir=[], modo="modo_real"
    )
    logica_mundo_fake.tick_actual = 1

    gen_espectador = espectador.suscribirse_foco()
    actualizacion_espectador = await asyncio.wait_for(
        gen_espectador.__anext__(), timeout=2.0
    )

    # El master se suscribe DESPUÉS de que el tick=1 ya se repartió:
    # debe recibir la actualización cacheada de inmediato, sin esperar
    # a un tick nuevo que en este test (fake con tick fijo) no llegaría
    # nunca — este es justo el caso que fallaba antes del fix.
    gen_master = master.suscribirse_foco()
    actualizacion_master = await asyncio.wait_for(gen_master.__anext__(), timeout=2.0)

    assert actualizacion_espectador.ok is True
    assert actualizacion_espectador.tick_actual == 1
    assert actualizacion_espectador.representacion == b"representacion_real"
    assert actualizacion_master.tick_actual == actualizacion_espectador.tick_actual

    await gen_espectador.aclose()
    await gen_master.aclose()


@pytest.mark.integration
async def test_actualizar_foco_dispara_reparto_aunque_no_cambie_el_tick(
    stack_foco,
):
    """
    Con el mundo pausado (Logica_Mundo actualiza 0 veces/s) la cámara
    se puede seguir moviendo: actualizar_foco() debe disparar un
    reparto nuevo a los suscriptores existentes aunque tick_actual no
    haya cambiado desde el último envío.
    """
    master, espectador, logica_mundo_fake = stack_foco

    await master.actualizar_foco(
        min_pos=(0, 0), max_pos=(10, 10), incluir=[], modo="modo_real"
    )
    logica_mundo_fake.tick_actual = 1

    gen_espectador = espectador.suscribirse_foco()
    primera_actualizacion = await asyncio.wait_for(
        gen_espectador.__anext__(), timeout=2.0
    )
    assert primera_actualizacion.tick_actual == 1

    # Simula "mundo en pausa": el tick NO vuelve a cambiar, pero el
    # master mueve la cámara (nueva región).
    ok, error = await master.actualizar_foco(
        min_pos=(5, 5), max_pos=(15, 15), incluir=[], modo="modo_real"
    )
    assert ok is True

    segunda_actualizacion = await asyncio.wait_for(
        gen_espectador.__anext__(), timeout=2.0
    )

    assert segunda_actualizacion.tick_actual == 1
    assert segunda_actualizacion.ok is True

    await gen_espectador.aclose()
