# Tests/Infraestructura/Remoto/Unitarios/test_sector_movimiento.py

"""
Movimiento de un elemento entre Sectores: recibir_elemento (destino) y
confirmar_salida (origen). Se usa un Suelo_Piedra como elemento de prueba
porque es simple de construir; el flujo de slots es el mismo para cualquier
elemento (el slot sale de tipo_slot_de).
"""

import json

import pytest

from Config.settings import SECTOR_SIZE
from Core.Entities.Mundo.Suelo.suelo_piedra import Suelo_Piedra
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
from Infraestructura.Gestores.Transporte.Proto_Generated import (
    common_pb2 as common_pb,
)


def _movimiento(id_elemento: int, origen, destino) -> common_pb.MovimientoSaliente:
    """Construye el MovimientoSaliente tal como lo declararía el Sector origen:
    el elemento va serializado (JSON en bytes), sin slot (sale de la clase)."""
    suelo = Suelo_Piedra(casilla=destino, id_elemento=id_elemento)
    return common_pb.MovimientoSaliente(
        id_elemento=id_elemento,
        pos_origen=common_pb.Position(x=origen[0], y=origen[1]),
        pos_destino=common_pb.Position(x=destino[0], y=destino[1]),
        elemento=json.dumps(suelo.serializar()).encode(),
    )


def test_recibir_elemento_lo_aloja_y_devuelve_la_celda():
    sector = Sector()  # región (0,0): [0, SECTOR_SIZE) en x e y
    aceptado, motivo, celda = sector.recibir_elemento(_movimiento(101, (-1, 5), (0, 5)))

    assert aceptado, motivo
    assert celda is not None
    assert (celda.pos.x, celda.pos.y) == (0, 5)
    assert celda.suelo != b""  # el slot de suelo quedó ocupado


def test_recibir_elemento_fuera_de_region_se_rechaza():
    sector = Sector()
    fuera = (SECTOR_SIZE + 5, 0)
    aceptado, motivo, celda = sector.recibir_elemento(_movimiento(102, (0, 0), fuera))

    assert not aceptado
    assert "región" in motivo
    assert celda is None


def test_recibir_elemento_slot_ocupado_se_rechaza():
    sector = Sector()
    assert sector.recibir_elemento(_movimiento(103, (-1, 5), (0, 5)))[0]

    aceptado, motivo, celda = sector.recibir_elemento(_movimiento(104, (-1, 5), (0, 5)))

    assert not aceptado
    assert "ocupado" in motivo
    assert celda is None


def test_confirmar_salida_elimina_el_elemento():
    sector = Sector()
    sector.recibir_elemento(_movimiento(105, (-1, 5), (0, 5)))

    celda = sector.confirmar_salida(105, (0, 5))

    assert celda.suelo == b""  # el slot quedó libre


def test_confirmar_salida_de_elemento_inexistente_es_error():
    sector = Sector()
    with pytest.raises(ValueError, match="no está"):
        sector.confirmar_salida(999, (0, 5))
