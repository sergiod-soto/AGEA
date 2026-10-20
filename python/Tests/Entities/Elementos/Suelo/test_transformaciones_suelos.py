# Tests/Entities/Elementos/Suelo/test_transformaciones_suelos.py
"""
Transformaciones de Barro (franja de secado) y Tierra (a césped) a lo largo de
varios ticks, con un TickContext real. Comprueba la regla de ids: una
transformación en su sitio ELIMINA y luego CREA con el MISMO id.
"""
import json

from Core.Entities.Elementos.registry import reconstruir_elemento
from Core.Entities.Mundo.Suelo.suelo_barro import Suelo_Barro, TICKS_SECADO_BARRO
from Core.Entities.Mundo.Suelo.suelo_cesped import Suelo_Cesped
from Core.Entities.Mundo.Suelo.suelo_tierra import Suelo_Tierra
from Infraestructura.Gestores.Mundo.Sector.mutaciones import (
    CrearElemento,
    EliminarElemento,
)

VIGILANCIA = ["suelo_barro_entra_en_franja_secado"]
EN_FRANJA = ["suelo_barro_secar", "suelo_barro_sale_de_franja_secado"]


def _barro():
    return Suelo_Barro(casilla=(5, 5), id_elemento=42)


# ---------------- Barro ----------------


def test_barro_humedo_no_hace_nada(crear_ctx):
    barro = _barro()
    ctx = crear_ctx(tick_id=10, humedad_relativa=50.0)
    barro.tick(ctx)
    assert list(barro.dict_transformable) == VIGILANCIA
    assert ctx.obtener_mutaciones() == []


def test_barro_entra_en_franja_con_humedad_baja(crear_ctx):
    barro = _barro()
    ctx = crear_ctx(tick_id=100, humedad_relativa=5.0)
    barro.tick(ctx)
    assert list(barro.dict_transformable) == EN_FRANJA
    assert (
        barro.dict_transformable["suelo_barro_secar"].tick_objetivo
        == 100 + TICKS_SECADO_BARRO
    )
    assert ctx.obtener_mutaciones() == []  # entrar en la franja no muta el terreno


def test_barro_sale_de_franja_si_sube_la_humedad(crear_ctx):
    barro = _barro()
    barro.tick(crear_ctx(tick_id=100, humedad_relativa=5.0))
    barro.tick(crear_ctx(tick_id=200, humedad_relativa=50.0))
    assert list(barro.dict_transformable) == VIGILANCIA


def test_barro_se_seca_a_tierra_con_el_mismo_id(crear_ctx):
    barro = _barro()
    barro.tick(crear_ctx(tick_id=100, humedad_relativa=5.0))

    # Justo antes del objetivo: sigue en franja.
    ctx = crear_ctx(tick_id=100 + TICKS_SECADO_BARRO - 1, humedad_relativa=5.0)
    barro.tick(ctx)
    assert ctx.obtener_mutaciones() == []

    ctx = crear_ctx(tick_id=100 + TICKS_SECADO_BARRO, humedad_relativa=5.0)
    barro.tick(ctx)
    baja, alta = ctx.obtener_mutaciones()  # el ORDEN importa: baja antes que alta
    assert isinstance(baja, EliminarElemento)
    assert (baja.id_elemento, baja.pos) == (42, (5, 5))
    assert isinstance(alta, CrearElemento)
    assert alta.tipo_slot == "suelo" and alta.pos == (5, 5)
    assert isinstance(alta.elemento, Suelo_Tierra)
    assert alta.elemento.id_elemento == 42  # transformación en su sitio: mismo id


def test_barro_en_franja_sobrevive_al_roundtrip():
    barro = _barro()
    barro.dict_transformable = {
        "suelo_barro_secar": __import__(
            "Core.Entities.Elementos.Abstractos.Condiciones.Condiciones_Temporales."
            "condicion_tick_objetivo",
            fromlist=["CondicionTickObjetivo"],
        ).CondicionTickObjetivo(tick_objetivo=777),
    }
    copia = reconstruir_elemento(json.loads(json.dumps(barro.serializar())))
    assert list(copia.dict_transformable) == ["suelo_barro_secar"]
    assert copia.dict_transformable["suelo_barro_secar"].tick_objetivo == 777


# ---------------- Tierra -> Césped ----------------


def _tierra():
    return Suelo_Tierra(casilla=(0, 0), id_elemento=9)


def test_tierra_se_convierte_con_humedad_en_rango_y_cesped_cerca(crear_ctx):
    cesped = Suelo_Cesped(casilla=(1, 0), id_elemento=10)
    ctx = crear_ctx(humedad_relativa=7.0, suelos_vecinos={(1, 0): cesped})
    tierra = _tierra()
    tierra.tick(ctx)
    baja, alta = ctx.obtener_mutaciones()
    assert isinstance(baja, EliminarElemento) and baja.id_elemento == 9
    assert isinstance(alta.elemento, Suelo_Cesped)
    assert alta.elemento.id_elemento == 9


def test_tierra_sin_cesped_cerca_no_se_convierte(crear_ctx):
    ctx = crear_ctx(humedad_relativa=7.0)
    _tierra().tick(ctx)
    assert ctx.obtener_mutaciones() == []


def test_tierra_con_humedad_fuera_de_rango_no_se_convierte(crear_ctx):
    cesped = Suelo_Cesped(casilla=(1, 0), id_elemento=10)
    for humedad in (2.0, 20.0):  # por debajo del mínimo y por encima del máximo
        ctx = crear_ctx(humedad_relativa=humedad, suelos_vecinos={(1, 0): cesped})
        _tierra().tick(ctx)
        assert ctx.obtener_mutaciones() == [], f"humedad {humedad}"