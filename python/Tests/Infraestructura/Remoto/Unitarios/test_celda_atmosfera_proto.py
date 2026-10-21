# Tests/Infraestructura/Transporte/test_celda_atmosfera_proto.py
"""
Pruebas del camino de datos que cruza la frontera entre Sectores:
    Celda_Atmosfera --a_proto--> AtmosphereCell (ghost zone)
                    --estado_desde_proto--> EstadoCelda
                    --EstadoVecino.desde_estado--> vecino de avanzar_celda

No instancian Sector: comprueban que, con la ghost zone como ÚNICA fuente del
vecino, la nube (y el vapor) se conservan. Es lo que haría cada Sector al ver
al otro lado de su frontera.
"""

import pytest
from vectors import Vector2

from Core.Entities.Mundo.Atmosfera import sistema_atmosferico as sa
from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera
from Infraestructura.Gestores.Transporte import celda_atmosfera_proto as cap


def _celda(pos, nube=0.0, humedad=0.005, viento=(0.0, 0.0)) -> Celda_Atmosfera:
    """Celda con suelo registrado (Temperatura exige inercia > 0)."""
    c = Celda_Atmosfera(pos, Vector2(0, 0))
    c.registrar_suelo(pos, 50.0, 4e5)
    c.nube.valor = nube
    c.humedad_absoluta.valor = humedad
    c.viento.intensidad = (viento[0] ** 2 + viento[1] ** 2) ** 0.5
    c.viento.direccion = (
        Vector2(viento[0] / c.viento.intensidad, viento[1] / c.viento.intensidad)
        if c.viento.intensidad > 0
        else Vector2(0, 0)
    )
    return c


# ---------------- Roundtrip de proto ----------------


def test_roundtrip_proto_conserva_nube_y_estado_simulado():
    origen = _celda((2, 3), nube=3.5e-4, humedad=0.007, viento=(1.5, -0.5))
    origen.temperatura.valor = 291.0
    origen.temperatura.valor_suelo = 295.0
    origen.presion.valor = 101000.0

    copia = cap.desde_proto(cap.a_proto(origen))

    assert copia.posicion == (2, 3)
    assert copia.nube.valor == origen.nube.valor
    assert copia.humedad_absoluta.valor == origen.humedad_absoluta.valor
    assert copia.temperatura.valor == 291.0
    assert copia.temperatura.valor_suelo == 295.0
    assert copia.presion.valor == 101000.0
    assert copia.viento.intensidad == pytest.approx(origen.viento.intensidad)
    assert copia.viento.direccion.x == pytest.approx(origen.viento.direccion.x)
    assert copia.viento.direccion.y == pytest.approx(origen.viento.direccion.y)


def test_aplicar_estado_simulado_sobreescribe_la_nube_de_una_celda_existente():
    # Es lo que hace Logica con actualizar_celdas_atmosfera.
    destino = _celda((0, 0), nube=0.0)
    cap.aplicar_estado_simulado(cap.a_proto(_celda((0, 0), nube=2e-4)), destino)
    assert destino.nube.valor == 2e-4


def test_estado_desde_proto_pasa_el_viento_a_componentes():
    celda = _celda((0, 0), nube=1e-4, viento=(3.0, 4.0))  # |v| = 5
    estado = cap.estado_desde_proto(cap.a_proto(celda))

    assert estado.nube == 1e-4
    assert estado.viento_x == pytest.approx(3.0)
    assert estado.viento_y == pytest.approx(4.0)
    assert estado.temperatura == celda.temperatura.valor


# ---------------- Frontera: ghost zone como único vecino ----------------


def _vecino_desde_ghost(celda_vecina, direccion) -> sa.EstadoVecino:
    """Lo que vería un Sector: el vecino llega como proto, no como objeto."""
    proto = cap.a_proto(celda_vecina)
    return sa.EstadoVecino.desde_estado(
        cap.estado_desde_proto(proto),
        Vector2(*direccion),
        proto.bloqueo_total_viento,
    )


def test_vapor_mas_nube_se_conservan_a_traves_de_la_frontera():
    # A (sector izquierdo) tiene nube; B (sector derecho) no. Viento de A a B.
    # Cada una ve a la otra SOLO como ghost (proto del inicio del tick).
    # La humedad de ambas es igual y está por debajo de la saturación, así que
    # la nube que llega a B se evapora: por eso se comprueba vapor + nube, que
    # sí se conserva (transporte + condensación/evaporación).
    a = _celda((0, 5), nube=1e-4, viento=(1.0, 0.0))
    b = _celda((1, 5), nube=0.0, viento=(1.0, 0.0))

    # Estados del inicio del tick, congelados ANTES de mutar nada.
    vecino_de_a = _vecino_desde_ghost(b, (1, 0))
    vecino_de_b = _vecino_desde_ghost(a, (-1, 0))
    total_antes = sum(c.humedad_absoluta.valor + c.nube.valor for c in (a, b))
    b_antes = b.humedad_absoluta.valor + b.nube.valor

    sa.avanzar_celda(a, 0.25, 0.25, [vecino_de_a])
    sa.avanzar_celda(b, 0.25, 0.25, [vecino_de_b])

    total_despues = sum(c.humedad_absoluta.valor + c.nube.valor for c in (a, b))
    assert total_despues == pytest.approx(total_antes, rel=1e-9)
    # Y de verdad hubo transporte: B ganó agua a costa de A.
    assert b.humedad_absoluta.valor + b.nube.valor > b_antes


def test_bloqueo_total_en_el_vecino_viaja_por_el_proto_y_corta_el_flujo():
    a = _celda((0, 5), nube=1e-4, viento=(1.0, 0.0))
    b = _celda((1, 5), nube=0.0, viento=(1.0, 0.0))
    b.registrar_resistencia_elemento(999, 1.0)  # bloqueo total en B
    assert b.bloqueo_total_viento

    vecino_de_a = _vecino_desde_ghost(b, (1, 0))
    assert vecino_de_a.bloqueo_total_viento  # el proto lo llevó hasta A

    nube_antes = a.nube.valor
    a.nube.actualizar([vecino_de_a], (1.0, 0.0), False)
    assert a.nube.valor == nube_antes  # sin flujo hacia/desde B
