# Tests/Infraestructura/Remoto/Integracion/test_logica_mundo_servicer.py
"""
test_logica_mundo_servicer.py — Integración: LogicaMundoServicer real
sobre un grpc.aio.server real, golpeado con LogicaMundoClient real (no
un stub artesanal) — así se ejercita también la (de)serialización que
hace el propio cliente, no solo la del servicer.
"""

import json

import pytest

from Core.Entities.Elementos.elemento_test import Elemento_Test
from Core.Entities.Elementos.Simples.Bot.Bot import Bot
from Core.Entities.entity import Modos
from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo import LogicaMundo
from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo_servicer import (
    LogicaMundoServicer,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Transporte.logica_mundo_client import LogicaMundoClient


def _elemento_bytes(eid: int) -> bytes:
    """
    Blob que crear_elemento() espera para un elemento cualquiera.
    """
    elemento = Elemento_Test(casilla=(0, 0), id_elemento=eid, peso=1.0)
    return json.dumps(elemento.serializar(modo=Modos.guardado)).encode()


def _bot_bytes(id_elemento: int, id_bot: int) -> bytes:
    """
    Blob de un Bot real y completo para tests que necesiten un avatar de
    bot de verdad (no basta un Elemento_Test genérico: eliminar_avatar_bot
    depende del stat "id" que solo Bot declara).

    id_elemento (id del avatar en el mundo, asignado por Logica_Mundo) y
    id_bot (id del bot/script en GestorBots) son intencionalmente
    distintos aquí para no repetir la confusión que motivó separarlos.
    """
    bot = Bot(
        id_elemento=id_elemento,
        stats_script={
            "armadura": 1,
            "grasa": 1,
            "longevidad": 1,
            "movilidad": 1,
            "percepcion": 1,
        },
        id_bot=id_bot,
        tamanho=1,
        casilla=(0, 0),
        rotacion=0.0,
    )
    return json.dumps(bot.serializar(modo=Modos.guardado)).encode()


@pytest.fixture
async def cliente_logica_mundo(levantar_servidor):
    logica = LogicaMundo(gestor_bots_client=None)
    servicer = LogicaMundoServicer(logica)
    servidor = await levantar_servidor(
        lambda s: pb_grpc.add_LogicaMundoServiceServicer_to_server(servicer, s)
    )

    client = LogicaMundoClient(servidor.address)
    yield client, logica
    await client.close()


@pytest.mark.integration
async def test_heartbeat_via_grpc(cliente_logica_mundo):
    client, _ = cliente_logica_mundo
    resp = await client.heartbeat()
    assert resp.ok is True


@pytest.mark.integration
async def test_asignar_id_incrementa_via_grpc(cliente_logica_mundo):
    client, _ = cliente_logica_mundo
    primero = await client.asignar_id()
    segundo = await client.asignar_id()
    assert segundo == primero + 1


@pytest.mark.integration
async def test_crear_y_eliminar_elemento_roundtrip_via_grpc(cliente_logica_mundo):
    client, logica = cliente_logica_mundo

    ok, error = await client.crear_elemento(
        pos=(1, 1), type_id="suelo", element=_elemento_bytes(1)
    )
    assert ok is True
    assert (1, 1) in logica._gold_cells

    ok, error = await client.eliminar_elemento(pos=(1, 1), element_id=1)
    assert ok is True
    assert (1, 1) not in logica._gold_cells


@pytest.mark.integration
async def test_resolver_accion_desconocida_via_grpc(cliente_logica_mundo):
    client, _ = cliente_logica_mundo

    # FIX: bot_id es uint64 en el proto (ResolverAccionRequest.bot_id) —
    # antes se pasaba un string de ejemplo ("bot_1").
    resultado = await client.resolver_accion(
        bot_id=1, action_type="no_existe", payload=b""
    )

    assert resultado.ok is False
    assert "desconocida" in resultado.error.lower()


@pytest.mark.integration
async def test_obtener_celdas_en_region_via_grpc(cliente_logica_mundo):
    client, _ = cliente_logica_mundo
    await client.crear_elemento(pos=(2, 2), type_id="suelo", element=_elemento_bytes(5))

    celdas = await client.obtener_celdas_en_region(min_pos=(0, 0), max_pos=(10, 10))

    assert len(celdas) == 1
    assert (celdas[0].pos.x, celdas[0].pos.y) == (2, 2)


# ── ModificarElemento ──────────────────────────────────────────────


@pytest.mark.integration
async def test_modificar_elemento_via_grpc(cliente_logica_mundo):
    client, logica = cliente_logica_mundo
    await client.crear_elemento(
        pos=(3, 3), type_id="suelo", element=_elemento_bytes(10)
    )

    ok, error = await client.modificar_elemento(
        pos=(3, 3), type_id="suelo", patch=json.dumps({"nueva_propiedad": 42}).encode()
    )

    assert ok is True
    assert logica._elements[10].nueva_propiedad == 42


@pytest.mark.integration
async def test_modificar_elemento_celda_inexistente_falla(cliente_logica_mundo):
    client, _ = cliente_logica_mundo

    ok, error = await client.modificar_elemento(
        pos=(99, 99), type_id="suelo", patch=b"{}"
    )

    assert ok is False


# ── Eventos globales ───────────────────────────────────────────────


@pytest.mark.integration
async def test_spawn_get_y_despawn_global_event_via_grpc(cliente_logica_mundo):
    client, _ = cliente_logica_mundo

    ok, error, event_id = await client.spawn_global_event(
        event_id="ignorado_por_logica_mundo",
        type_="tormenta",
        pos=(1, 1),
        payload=b"payload",
    )
    assert ok is True
    assert event_id  # Logica_Mundo asigna siempre su propio event_id

    eventos = await client.get_active_events()
    assert len(eventos) == 1
    assert eventos[0].type == "tormenta"

    ok, error = await client.despawn_global_event(event_id, reason="fin")
    assert ok is True

    eventos = await client.get_active_events()
    assert eventos == []


# ── GetElementosGlobales ───────────────────────────────────────────


@pytest.mark.integration
async def test_get_elementos_globales_via_grpc_vacio_por_defecto(cliente_logica_mundo):
    """
    Los ficheros de elementos globales (clima.py, ciclo_lunar.py...)
    están vacíos hoy (biomas/mecánicas aún sin implementar) — por eso
    _elementos_globales empieza (y se queda) vacío.
    """
    client, _ = cliente_logica_mundo

    resp = await client.get_elementos_globales()

    assert resp.ok is True
    assert list(resp.elementos_globales) == []


@pytest.mark.integration
async def test_get_elementos_globales_tick_actual_es_cero_antes_de_avanzar(
    cliente_logica_mundo,
):
    """
    tick_actual (campo de GetElementosGlobalesResponse para que
    Vista_Foco/FocoBroadcaster pueda detectar "hubo tick nuevo"): antes
    de cualquier AvanzarElementosGlobales, debe llegar como 0 — no como
    el valor por defecto "ausente" de proto3, que también es 0, pero
    aquí lo comprobamos explícitamente para dejar documentado el
    contrato.
    """
    client, _ = cliente_logica_mundo

    resp = await client.get_elementos_globales()

    assert resp.tick_actual == 0


@pytest.mark.integration
async def test_get_elementos_globales_tick_actual_refleja_el_ultimo_avance_via_grpc(
    cliente_logica_mundo,
):
    """
    El caso real que motivó el campo: tras llamar a
    AvanzarElementosGlobales(tick_id=N) por la red, una llamada
    POSTERIOR (y separada) a GetElementosGlobales debe devolver ese
    mismo N en tick_actual. Esto es justo lo que FocoBroadcaster hace
    en su bucle de vigilancia — dos llamadas RPC distintas, no una
    combinada.
    """
    client, _ = cliente_logica_mundo

    await client.avanzar_elementos_globales(tick_id=3)
    resp = await client.get_elementos_globales()

    assert resp.tick_actual == 3


@pytest.mark.integration
async def test_get_elementos_globales_tick_actual_refleja_solo_el_ultimo_avance(
    cliente_logica_mundo,
):
    client, _ = cliente_logica_mundo

    await client.avanzar_elementos_globales(tick_id=3)
    await client.avanzar_elementos_globales(tick_id=4)
    resp = await client.get_elementos_globales()

    assert resp.tick_actual == 4


# ── ActualizarCeldas / ConsultarRepresentacion ──────────────────────


@pytest.mark.integration
async def test_actualizar_celdas_via_grpc(cliente_logica_mundo):
    client, logica = cliente_logica_mundo
    from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

    cell = common_pb2.Cell(pos=common_pb2.Position(x=5, y=5), suelo=_elemento_bytes(20))

    ok = await client.actualizar_celdas([cell])

    assert ok is True
    assert (5, 5) in logica._gold_cells


@pytest.mark.integration
async def test_consultar_representacion_via_grpc_devuelve_json_valido(
    cliente_logica_mundo,
):
    client, _ = cliente_logica_mundo
    await client.crear_elemento(
        pos=(4, 4), type_id="suelo", element=_elemento_bytes(30)
    )

    datos = await client.consultar_representacion(
        min_pos=(0, 0), max_pos=(10, 10), incluir=["Color"], modo=Modos.transporte
    )

    parsed = json.loads(datos.decode())
    assert parsed["modo"] == "test"
    assert "elementos" in parsed


# ── SaveSnapshot / LoadState ─────────────────────────────────────────


@pytest.mark.integration
async def test_save_snapshot_y_load_state_roundtrip_via_grpc(
    cliente_logica_mundo, snapshot_dir_aislado
):
    client, logica = cliente_logica_mundo
    logica.SNAPSHOT_DIR = snapshot_dir_aislado
    await client.crear_elemento(
        pos=(6, 6), type_id="suelo", element=_elemento_bytes(40)
    )

    ok, error = await client.save_snapshot("snap_test")
    assert ok is True

    # Se vacía el estado en memoria para comprobar que load_state lo
    # recupera de verdad desde disco, no que simplemente no lanza.
    logica._gold_cells = {}
    logica._elements = {}

    ok_load = await client.load_state("snap_test")

    assert ok_load is True
    assert (6, 6) in logica._gold_cells


# ── EliminarAvatarBot ────────────────────────────────────────────────


@pytest.mark.integration
async def test_eliminar_avatar_bot_via_grpc(cliente_logica_mundo):
    client, logica = cliente_logica_mundo

    # FIX: id_elemento (avatar en el mundo) e id_bot (script en
    # GestorBots) son ids distintos a propósito — antes el test usaba
    # el mismo valor ("50") para ambos, ocultando que _bot_positions
    # debe indexarse por bot_id, no por id_elemento.
    await client.crear_elemento(
        pos=(7, 7), type_id="bot", element=_bot_bytes(id_elemento=50, id_bot=99)
    )

    ok, error = await client.eliminar_avatar_bot(bot_id=99)

    assert ok is True
    assert 99 not in logica._bot_positions


# ── AvanzarElementosGlobales ─────────────────────────────────────────


@pytest.mark.integration
async def test_avanzar_elementos_globales_via_grpc_sin_elementos_devuelve_vacio(
    cliente_logica_mundo,
):
    client, _ = cliente_logica_mundo

    cambios = await client.avanzar_elementos_globales(tick_id=1)

    assert cambios == {}
