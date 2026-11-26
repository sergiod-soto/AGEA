# Tests/Infraestructura/Gestores/test_gestor_hidrografico.py
"""
test_gestor_hidrografico.py — Pruebas unitarias y de integración del subsistema
hidrográfico desacoplado:
  1. DAG fluvial, orden topológico y separación de cauce vs. ensanchamiento/batimetría.
  2. Ciclo Río -> Lago -> Río: retención bajo la cota crítica X y desborde por emisario al superar X.
  3. Lluvia y evaporación agregadas con modelo Dalton.
  4. Proyección discreta al terreno con histéresis anti-parpadeo.
  5. Inhibición de evaporación individual en elementos gestionados por hidrografía.
  6. Serialización / deserialización de snapshots.
  7. Integración con las 3 fases síncronas de GestorMundo.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from Core.Entities.Elementos.Complejos.Lago.Lago import Lago
from Core.Entities.Elementos.Complejos.Rio.Rio import Rio
from Core.Entities.Elementos.Complejos.Oceano.Oceano import Oceano
from Core.Entities.Elementos.Simples.Agua.agua import Agua
from Core.Entities.Mundo.Suelo.suelo_agua import Suelo_Agua
from Core.Entities.Elementos.elemento import Elemento
from Core.Entities.Comportamiento.Terreno.gestionado_hidrografia import (
    GestionadoHidrografia,
)
from Infraestructura.Gestores.Mundo.Hidrologia import (
    GestorHidrografico,
    RedFluvial,
    DatosAtmosferaHidro,
    ResultadoTickHidro,
)
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import (
    GestorMundo,
    SectorInfo,
)
from Infraestructura.Gestores.Mundo.Sector.sector_mode import SectorMode
from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo import LogicaMundo


@pytest.fixture
def red_prueba():
    """
    Grafo de prueba:
      Río 1 (manantial) \
                         -> Río 3 (confluencia) -> Lago 1 -> Río 4 (desagüe) -> Mar
      Río 2 (manantial) /
    """
    red = {
        "rios": {
            1: {
                "nace_de": ("manantial", (2, 2)),
                "muere_en": ("confluencia", 3),
                "camino": [(2, 2), (2, 3), (2, 4)],
            },
            2: {
                "nace_de": ("manantial", (4, 2)),
                "muere_en": ("confluencia", 3),
                "camino": [(4, 2), (4, 3), (3, 4)],
            },
            3: {
                "nace_de": ("confluencia", (2, 4)),
                "muere_en": ("lago", 1),
                "camino": [(2, 5), (2, 6)],
            },
            4: {
                "nace_de": ("lago", 1),
                "muere_en": ("mar", None),
                "camino": [(2, 8), (2, 9)],
            },
        },
        "lagos": {
            1: {
                "nace_de_rio": 3,
                "desagua_en_rio": 4,
                "capacidad_maxima": 10.0,
                "fondo": 2.0,
                "area": 4,
            }
        },
    }

    hidrologia = {
        # Río 1: camino + 1 celda de ensanchamiento
        (2, 2): {"tipo": "rio", "id": 1, "dir": (0, 1)},
        (2, 3): {"tipo": "rio", "id": 1, "dir": (0, 1)},
        (2, 4): {"tipo": "rio", "id": 1, "dir": (0, 1)},
        (1, 3): {"tipo": "rio", "id": 1, "dir": (0, 1)},  # ensanchamiento
        # Río 2: camino
        (4, 2): {"tipo": "rio", "id": 2, "dir": (0, 1)},
        (4, 3): {"tipo": "rio", "id": 2, "dir": (-1, 1)},
        (3, 4): {"tipo": "rio", "id": 2, "dir": (-1, 1)},
        # Río 3: camino
        (2, 5): {"tipo": "rio", "id": 3, "dir": (0, 1)},
        (2, 6): {"tipo": "rio", "id": 3, "dir": (0, 1)},
        # Lago 1: 4 celdas con batimetría escalonada (cota 2.0 a 8.0)
        (2, 7): {"tipo": "lago", "id": 1, "elev": 2.0, "capacidad_maxima": 10.0, "fondo": 2.0},
        (3, 7): {"tipo": "lago", "id": 1, "elev": 4.0, "capacidad_maxima": 10.0, "fondo": 2.0},
        (1, 7): {"tipo": "lago", "id": 1, "elev": 6.0, "capacidad_maxima": 10.0, "fondo": 2.0},
        (2, 8): {"tipo": "lago", "id": 1, "elev": 8.0, "capacidad_maxima": 10.0, "fondo": 2.0},
        # Río 4: camino
        (2, 9): {"tipo": "rio", "id": 4, "dir": (0, 1)},
        (2, 10): {"tipo": "rio", "id": 4, "dir": (0, 1)},
    }

    alturas = {pos: int(info.get("elev", 5)) for pos, info in hidrologia.items()}
    suelos_orig = {pos: "Suelo_Tierra" for pos in hidrologia}

    return red, hidrologia, alturas, suelos_orig


# ── 1. DAG fluvial y orden topológico ──────────────────────────────────────


@pytest.mark.unit
def test_inicializacion_dag_y_orden_topologico(red_prueba):
    red, hidrologia, alturas, suelos_orig = red_prueba
    fluvial = RedFluvial()
    fluvial.inicializar_desde_red(red, hidrologia, alturas, suelos_orig)

    # Verificar separación de cauce vs ensanchamiento
    rio_1 = fluvial.rios[1]
    assert rio_1.camino == [(2, 2), (2, 3), (2, 4)]
    assert (1, 3) in rio_1.ancho_celdas
    assert (1, 3) not in rio_1.camino

    # Verificar batimetría de lago ordenada por elevación
    lago_1 = fluvial.lagos[1]
    assert len(lago_1.celdas_cuenca) == 4
    cotas = [elev for _, _, elev in lago_1.celdas_cuenca]
    assert cotas == sorted(cotas)
    assert cotas[0] == 2.0
    assert cotas[-1] == 8.0

    # Verificar orden topológico:
    # R1 y R2 antes de R3; R3 antes de Lago 1; Lago 1 antes de R4; R4 antes de Océano
    orden = fluvial.orden_topologico
    idx_r1 = orden.index("rio_1")
    idx_r2 = orden.index("rio_2")
    idx_r3 = orden.index("rio_3")
    idx_lago = orden.index("lago_1")
    idx_r4 = orden.index("rio_4")
    idx_mar = orden.index("oceano")

    assert idx_r1 < idx_r3
    assert idx_r2 < idx_r3
    assert idx_r3 < idx_lago
    assert idx_lago < idx_r4
    assert idx_r4 < idx_mar


# ── 2. Ciclo Río -> Lago -> Río: retención y desborde ────────────────────────


@pytest.mark.unit
def test_lago_retencion_bajo_cota_critica(red_prueba):
    red, hidrologia, alturas, suelos_orig = red_prueba
    gestor = GestorHidrografico()
    gestor.inicializar(red, hidrologia, alturas, suelos_orig)

    # Fijar volumen de Lago 1 muy bajo (debajo de su capacidad de desborde)
    lago = gestor.red_fluvial.lagos[1]
    lago.volumen = 100.0  # muy inferior a capacidad máxima (cota 10.0)

    # Río 4 inicialmente sin volumen
    rio_4 = gestor.red_fluvial.rios[4]
    rio_4.volumen = 0.0

    # Avanzar un tick sin lluvia ni extracciones
    gestor.preparar_tick(tick_id=1, datos_atmosfera={})
    import asyncio
    res = asyncio.run(gestor.avanzar_tick(tick_id=1))

    # Bajo la cota crítica X: caudal_salida = 0 (el lago retiene agua)
    assert lago.caudal_salida == 0.0
    assert 1 not in res.lagos_desbordando


@pytest.mark.unit
def test_lago_desborda_al_superar_cota_critica(red_prueba):
    red, hidrologia, alturas, suelos_orig = red_prueba
    gestor = GestorHidrografico()
    gestor.inicializar(red, hidrologia, alturas, suelos_orig)

    lago = gestor.red_fluvial.lagos[1]
    rio_4 = gestor.red_fluvial.rios[4]
    rio_4.volumen = 0.0

    # Llenar el lago hasta el umbral crítico de desborde y suministrar un aporte masivo
    vol_max = gestor.red_fluvial._calcular_volumen_cuenca(
        lago.celdas_cuenca, lago.capacidad_maxima
    )
    lago.volumen = vol_max + 50000.0  # supera la cota crítica

    gestor.preparar_tick(tick_id=1, datos_atmosfera={})
    import asyncio
    res = asyncio.run(gestor.avanzar_tick(tick_id=1))

    # El lago debe desbordar por su emisario Río 4
    assert 1 in res.lagos_desbordando
    assert lago.caudal_salida > 0.0
    assert rio_4.caudal_salida > 0.0 or rio_4.volumen > 0.0
    assert res.caudal_vertido_mar > 0.0


# ── 3. Proyección discreta al terreno con histéresis ─────────────────────────


@pytest.mark.unit
def test_proyeccion_discreta_histeresis_anti_parpadeo(red_prueba):
    red, hidrologia, alturas, suelos_orig = red_prueba
    fluvial = RedFluvial()
    fluvial.inicializar_desde_red(red, hidrologia, alturas, suelos_orig)

    lago = fluvial.lagos[1]
    # Forzar celda (2, 8) a no estar inundada inicialmente
    pos_borde = (2, 8)
    lago.celdas_inundadas.remove(pos_borde)

    # Celda (2, 8) tiene cota 8.0. Margen de histéresis = 0.5
    # 1. Nivel alcanza 8.2 (menor que 8.0 + 0.5 = 8.5): la celda NO se inunda (retiene estado seco)
    fluvial._calcular_volumen_cuenca = MagicMock(return_value=1e9)
    fluvial._calcular_nivel_desde_volumen = MagicMock(return_value=8.2)

    res1 = fluvial.simular_paso(tick_id=1, datos_atmosfera={}, histeresis=0.5)
    assert pos_borde not in lago.celdas_inundadas
    assert not any(c["pos"] == pos_borde for c in res1.changed_cells)

    # 2. Nivel supera 8.5 (por ejemplo 8.6): la celda SE INUNDA
    fluvial._calcular_nivel_desde_volumen = MagicMock(return_value=8.6)
    res2 = fluvial.simular_paso(tick_id=2, datos_atmosfera={}, histeresis=0.5)
    assert pos_borde in lago.celdas_inundadas
    assert any(c["pos"] == pos_borde and c["suelo"] == "Suelo_Agua" for c in res2.changed_cells)

    # 3. Nivel cae a 8.2 (mayor que 8.0 - 0.5 = 7.5): NO se seca gracias a la histéresis
    fluvial._calcular_nivel_desde_volumen = MagicMock(return_value=8.2)
    res3 = fluvial.simular_paso(tick_id=3, datos_atmosfera={}, histeresis=0.5)
    assert pos_borde in lago.celdas_inundadas
    assert not any(c["pos"] == pos_borde for c in res3.changed_cells)

    # 4. Nivel cae por debajo de 7.5 (por ejemplo 7.0): la celda SE SECA y vuelve a Suelo_Tierra
    fluvial._calcular_nivel_desde_volumen = MagicMock(return_value=7.0)
    res4 = fluvial.simular_paso(tick_id=4, datos_atmosfera={}, histeresis=0.5)
    assert pos_borde not in lago.celdas_inundadas
    assert any(c["pos"] == pos_borde and c["suelo"] == "Suelo_Tierra" for c in res4.changed_cells)


# ── 4. Inhibición de evaporación individual en Agua gestionada ──────────────


@pytest.mark.unit
def test_inhibicion_evaporacion_en_acuoso():
    # Suelo_Agua con gestionado_por_hidrografia=True
    suelo = Suelo_Agua(id_elemento=1, casilla=(5, 5), gestionado_por_hidrografia=True)

    ctx = MagicMock()
    # Debe abortar sin llamar a ctx.get_atmosfera ni ctx.evaporar
    suelo.tick_comportamiento(ctx)
    ctx.get_atmosfera.assert_not_called()
    ctx.evaporar.assert_not_called()


@pytest.mark.unit
def test_elemento_agua_flag_y_atributo_gestionado():
    agua = Agua(
        id_elemento=10,
        casilla=(1, 1),
        peso=500.0,
        gestionado_por_hidrografia=True,
    )
    assert agua.gestionado_por_hidrografia is True
    # Serializar y deserializar preserva el flag
    datos = agua.serializar()
    assert datos.get("gestionado_por_hidrografia") is True

    agua2 = Agua(id_elemento=11, casilla=(1, 1), peso=500.0)
    agua2.deserializar(datos)
    assert agua2.gestionado_por_hidrografia is True


# ── 5. Serialización / Deserialización de Snapshots ──────────────────────────


@pytest.mark.unit
def test_red_fluvial_snapshot_roundtrip(red_prueba):
    red, hidrologia, alturas, suelos_orig = red_prueba
    gestor1 = GestorHidrografico()
    gestor1.inicializar(red, hidrologia, alturas, suelos_orig)

    datos_snap = gestor1.serializar()
    assert "red_fluvial" in datos_snap

    gestor2 = GestorHidrografico()
    gestor2.deserializar(datos_snap)
    assert gestor2.inicializado is True
    assert len(gestor2.red_fluvial.rios) == len(gestor1.red_fluvial.rios)
    assert len(gestor2.red_fluvial.lagos) == len(gestor1.red_fluvial.lagos)
    assert gestor2.red_fluvial.orden_topologico == gestor1.red_fluvial.orden_topologico


@pytest.mark.unit
def test_logica_mundo_red_a_dict_roundtrip(red_prueba):
    red, _, _, _ = red_prueba
    dict_json = LogicaMundo._red_a_dict(red)
    red_restaurada = LogicaMundo._red_desde_dict(dict_json)

    assert 1 in red_restaurada["rios"]
    assert red_restaurada["rios"][1]["nace_de"] == ("manantial", (2, 2))
    assert red_restaurada["rios"][1]["muere_en"] == ("confluencia", 3)
    assert red_restaurada["rios"][1]["camino"] == [(2, 2), (2, 3), (2, 4)]
    assert red_restaurada["lagos"][1]["capacidad_maxima"] == 10.0


# ── 6. Integración con GestorMundo en Fase 0, 1 y 2 ──────────────────────────


@pytest.mark.unit
async def test_gestor_mundo_fase_0_1_2_con_hidrografia(red_prueba, fake_stub_factory):
    red, hidrologia, alturas, suelos_orig = red_prueba
    gestor_hidro = GestorHidrografico()
    gestor_hidro.inicializar(red, hidrologia, alturas, suelos_orig)

    fake_logica = MagicMock()
    fake_logica.obtener_progreso_ciclos = AsyncMock(return_value=(0.1, 0.2, 0.3))
    fake_logica.tomar_parches_atmosfera = AsyncMock(return_value=[])
    fake_logica.actualizar_celdas = AsyncMock()
    fake_logica.emitir_eventos = AsyncMock()
    fake_logica.avanzar_tick = AsyncMock()

    gestor_mundo = GestorMundo(
        logica_client=fake_logica,
        gestor_hidrografico=gestor_hidro,
    )
    gestor_mundo._bots_stub = MagicMock()
    gestor_mundo._bots_stub.ResetBudgets = AsyncMock()

    # Fase 0 prepara inputs para hidro
    await gestor_mundo._fase_0()

    # Sector falso
    class RespuestaOk:
        ok = True
        timed_out = False

    class DeltaOk:
        ok = True
        changed_cells = []
        changed_atmosphere_cells = []
        dead_bot_ids = []
        eventos = []
        movimientos_salientes = []
        emitted_sounds = []

    info = SectorInfo(col=0, row=0, address="localhost:1", mode=SectorMode.ACTIVO)
    info.stub = fake_stub_factory(StartTick=RespuestaOk(), GetDelta=DeltaOk())
    gestor_mundo._sectores[(0, 0)] = info

    # Fase 1 avanza en paralelo con sectores
    await gestor_mundo._fase_1()
    assert gestor_mundo._ultimo_delta_hidro is not None

    # Fase 2 consolida deltas
    await gestor_mundo._fase_2()


@pytest.mark.unit
async def test_obtener_datos_hidrograficos_rpc(red_prueba):
    import grpc
    from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo import LogicaMundo
    from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo_servicer import (
        LogicaMundoServicer,
    )
    from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
        logica_mundo_service_pb2_grpc as pb_grpc,
    )
    from Infraestructura.Gestores.Transporte.logica_mundo_client import (
        LogicaMundoClient,
    )

    red, hidrologia, alturas, _ = red_prueba
    logica = LogicaMundo()
    logica.mundo.red = red
    logica.mundo.hidrologia = hidrologia
    logica.mundo.alturas = alturas

    servicer = LogicaMundoServicer(logica)
    server = grpc.aio.server()
    pb_grpc.add_LogicaMundoServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port("localhost:0")
    await server.start()

    try:
        client = LogicaMundoClient(f"localhost:{port}")
        r, a, h = await client.obtener_datos_hidrograficos()
        assert 1 in r["rios"]
        assert a == alturas
        assert h == hidrologia
        await client.close()
    finally:
        await server.stop(grace=None)


@pytest.mark.unit
async def test_gestor_mundo_auto_inicializa_hidrografia(red_prueba):
    from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import (
        GestorMundo,
    )

    red, hidrologia, alturas, _ = red_prueba

    class FakeLogicaClient:
        async def obtener_datos_hidrograficos(self):
            return red, alturas, hidrologia

    gestor = GestorMundo(logica_client=FakeLogicaClient())
    assert gestor.gestor_hidrografico is None

    await gestor._inicializar_gestor_hidrografico()
    assert gestor.gestor_hidrografico is not None
    assert gestor.gestor_hidrografico.inicializado is True
    assert len(gestor.gestor_hidrografico.red_fluvial.rios) == 4


@pytest.mark.unit
async def test_gestor_mundo_funciona_sin_bots(monkeypatch, tmp_path, red_prueba):
    import Config.settings as config
    from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import (
        GestorMundo,
    )

    monkeypatch.setattr(config, "HABILITAR_BOTS", False)
    monkeypatch.setattr(
        "Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo.SNAPSHOT_DIR",
        tmp_path,
    )
    red, hidrologia, alturas, _ = red_prueba

    class FakeLogicaClient:
        async def obtener_datos_hidrograficos(self):
            return red, alturas, hidrologia

        async def load_state(self, snapshot_id):
            pass

        async def _distribute_gold_to_sectors(self):
            pass

    gestor = GestorMundo(logica_client=FakeLogicaClient())

    async def fake_async(*args, **kwargs):
        pass

    monkeypatch.setattr(gestor, "_asegurar_mundo_generado", fake_async)
    monkeypatch.setattr(gestor, "_connect_sector", fake_async)
    monkeypatch.setattr(gestor, "_distribute_gold_to_sectors", fake_async)
    monkeypatch.setattr(gestor, "_activar_todos", fake_async)
    await gestor.start(fresh=True)

    assert gestor._bots_stub is None
    assert gestor._bots_channel is None

    # Reset budgets no falla
    await gestor._reset_budgets()

    # Freeze y resume no fallan
    await gestor.freeze()
    await gestor.resume()

    await gestor.close()

