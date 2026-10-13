# Tests/Otros/ejemplo_tick_completo.py
"""
ejemplo_tick_completo.py — Genera un ejemplo real y completo de lo que
recibiría un cliente Unity suscrito a SuscribirseFoco: un mensaje
ActualizacionFoco construido exactamente como lo haría FocoBroadcaster
(vista_foco.py), sobre un LogicaMundo con elementos reales.

No es un test de asserts — es una herramienta de inspección visual,
mismo espíritu que test_salida_representacion_unity.py (mismo
directorio): construye el mundo, avanza un tick, y vuelca a consola la
forma exacta de los datos, para poder pasárselos tal cual a quien esté
trabajando en el lado Unity.

Cómo ejecutarlo:
    - Como script:  python Tests/Otros/ejemplo_tick_completo.py
    - Con pytest (para ver los prints hay que pasar -s):
          pytest -s Tests/Otros/ejemplo_tick_completo.py
"""

from __future__ import annotations

import asyncio
import json

from google.protobuf.json_format import MessageToDict

from Core.Entities.Elementos.elemento_test import Elemento_Test
from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo import LogicaMundo
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    comunicacion_remota_service_pb2 as bridge_pb,
    logica_mundo_service_pb2 as logica_pb,
)


async def _colocar_elemento(
    logica: LogicaMundo,
    id_elemento: int,
    pos: tuple[int, int],
    tipo_slot: str,
    peso: float,
) -> None:
    """
    Mismo patrón que test_salida_representacion_unity.py::
    _colocar_elemento: se construye el elemento real vía su __init__
    (no un JSON a mano) y se serializa con serializar(modo=Modos.transporte)
    — el mismo formato de bytes que usaría _id_a_slot_bytes al mandar
    un elemento entre sectores, que es la ruta real de transporte.
    """
    elemento = Elemento_Test(id_elemento=id_elemento, casilla=pos, peso=peso)
    payload = json.dumps(elemento.serializar()).encode()

    ok, error = await logica.crear_elemento(pos, tipo_slot, payload)
    if not ok:
        raise RuntimeError(f"No se pudo colocar elemento {id_elemento}: {error}")


async def _main() -> None:
    logica = LogicaMundo()

    # Un pequeño mundo con 3 elementos reales, en 2 celdas distintas —
    # para que el ejemplo tenga algo real que enseñar en cada slot
    # (suelo, bot, resto) y no salga todo vacío.
    await _colocar_elemento(
        logica, id_elemento=1, pos=(0, 0), tipo_slot="suelo", peso=10.0
    )
    await _colocar_elemento(
        logica, id_elemento=2, pos=(1, 0), tipo_slot="bot", peso=5.0
    )
    await _colocar_elemento(
        logica, id_elemento=3, pos=(1, 0), tipo_slot="resto", peso=2.5
    )

    # Avanza un tick real — hoy no hay elementos globales (clima/ciclo
    # lunar aún vacíos), así que "cambios" sale {}, pero tick_actual sí
    # queda registrado en LogicaMundo (ver get_tick_actual()).
    await logica.avanzar_elementos_globales(tick_id=1)

    # Las MISMAS tres llamadas que hace FocoBroadcaster._vigilar() en
    # cada pulso — ver vista_foco.py.
    celdas = await logica.obtener_celdas_en_region(min_pos=(0, 0), max_pos=(10, 10))
    representacion_bytes = await logica.consultar_representacion(
        min_pos=(0, 0), max_pos=(10, 10), incluir=["Peso"]
    )
    globales_dict = await logica.get_elementos_globales()
    tick_actual = await logica.get_tick_actual()

    # Construcción del ActualizacionFoco real — mismo ensamblaje que
    # vista_foco.py::generar_actualizaciones / FocoBroadcaster._vigilar.
    actualizacion = bridge_pb.ActualizacionFoco(
        ok=True,
        celdas=celdas,
        representacion=representacion_bytes,
        elementos_globales=[
            logica_pb.ElementoGlobalState(
                name=nombre, state=json.dumps(estado).encode()
            )
            for nombre, estado in globales_dict.items()
        ],
        tick_actual=tick_actual,
    )

    # ── Volcado legible ──────────────────────────────────────────

    print("=" * 70)
    print("ActualizacionFoco completo (protobuf -> dict, para ver la forma exacta)")
    print("=" * 70)
    print(
        json.dumps(
            MessageToDict(actualizacion, preserving_proto_field_name=True),
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print("=" * 70)
    print(
        "Contenido de 'representacion' (bytes -> JSON, formato usado por Unity para pintar)"
    )
    print("=" * 70)
    print(
        json.dumps(
            json.loads(representacion_bytes.decode()), indent=2, ensure_ascii=False
        )
    )

    print()
    print("=" * 70)
    print("Contenido de cada celda (bytes -> JSON, elemento serializado completo)")
    print("=" * 70)
    for cell in actualizacion.celdas:
        pos = (cell.pos.x, cell.pos.y)
        print(f"-- celda {pos} --")
        if cell.suelo:
            print("  suelo:", json.loads(cell.suelo))
        if cell.bot:
            print("  bot:", json.loads(cell.bot))
        for blob in cell.resto:
            print("  resto:", json.loads(blob))

    print()
    print(f"tick_actual final: {tick_actual}")


# ─────────────────────────────────────────────────────────────
#  Entradas: pytest y ejecución directa
# ─────────────────────────────────────────────────────────────


def test_mostrar_ejemplo_tick_completo():
    """Ejecutar con: pytest -s Tests/Otros/ejemplo_tick_completo.py"""
    asyncio.run(_main())


if __name__ == "__main__":
    asyncio.run(_main())
