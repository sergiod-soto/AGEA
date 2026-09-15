# Tests/Otros/test_salida_representacion_unity.py
"""
Muestra en consola, para varios casos, exactamente lo que
LogicaMundo.consultar_representacion() devolvería a Unity tras un tick.

No es un test de asserts (para eso está test_elemento.py y el futuro
test de logica_mundo): es una herramienta de inspección visual, pensada
para poder ver de un vistazo si la representación que viaja hacia Unity
tiene la forma esperada -- útil mientras se sigue tocando la cadena
Elemento.serializar / Comportamiento.get_comportamiento.

Cómo ejecutarlo:
    - Como script:  python Tests/Otros/test_salida_representacion_unity.py
    - Con pytest (para ver los prints hay que pasar -s):
          pytest -s Tests/Otros/test_salida_representacion_unity.py

Cómo ampliarlo:
    Añade una entrada a CASOS. Cada caso es autocontenido: crea su propia
    LogicaMundo (así los ids no se pisan entre casos) y describe qué
    elementos colocar, qué región consultar y qué comportamientos pedir.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

from Core.Entities.Elementos.elemento_test import Elemento_Test
from Core.Entities.entity import Modos
from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo import LogicaMundo

# ─────────────────────────────────────────────────────────────
#  Definición de un caso
# ─────────────────────────────────────────────────────────────


@dataclass
class ElementoAColocar:
    id_elemento: int  # único dentro del caso -- crear_elemento lo exige ya asignado
    pos: tuple[int, int]
    tipo_slot: str  # "suelo" | "bot" | "resto"
    peso: float = 1.0
    atributo_test: object = None  # visible en la salida si se pide Comportamiento_Test


@dataclass
class Caso:
    nombre: str
    descripcion: str
    elementos: list[ElementoAColocar]
    min_pos: tuple[int, int]
    max_pos: tuple[int, int]
    incluir: list[str] = field(default_factory=lambda: ["Peso"])
    tick_id: int = 1


CASOS: list[Caso] = [
    Caso(
        nombre="region_vacia",
        descripcion="Ningún elemento colocado en el mundo. La región consultada "
        "debe devolver 'elementos': [].",
        elementos=[],
        min_pos=(0, 0),
        max_pos=(10, 10),
    ),
    Caso(
        nombre="un_elemento_con_el_comportamiento_pedido",
        descripcion="Un elemento en 'suelo' con Peso, pidiendo justo 'Peso'. "
        "Debe aparecer con su comportamiento serializado.",
        elementos=[
            ElementoAColocar(id_elemento=1, pos=(2, 2), tipo_slot="suelo", peso=7.5),
        ],
        min_pos=(0, 0),
        max_pos=(10, 10),
        incluir=["Peso"],
    ),
    Caso(
        nombre="comportamiento_pedido_que_no_tiene",
        descripcion="Se pide 'Volumen' a un Elemento_Test que solo tiene Peso/"
        "Comportamiento_Test. Debe excluirse en silencio (ValueError "
        "capturado dentro de consultar_representacion), no aparecer vacío "
        "ni romper la consulta.",
        elementos=[
            ElementoAColocar(id_elemento=1, pos=(2, 2), tipo_slot="suelo", peso=3.0),
        ],
        min_pos=(0, 0),
        max_pos=(10, 10),
        incluir=["Volumen"],
    ),
    Caso(
        nombre="varios_elementos_misma_celda",
        descripcion="suelo + bot + resto en la misma celda. Los tres deben "
        "aparecer, cada uno con su x,y correcto (los de la celda).",
        elementos=[
            ElementoAColocar(id_elemento=1, pos=(5, 5), tipo_slot="suelo", peso=1.0),
            ElementoAColocar(id_elemento=2, pos=(5, 5), tipo_slot="bot", peso=2.0),
            ElementoAColocar(id_elemento=3, pos=(5, 5), tipo_slot="resto", peso=3.0),
        ],
        min_pos=(0, 0),
        max_pos=(10, 10),
        incluir=["Peso"],
    ),
    Caso(
        nombre="region_no_cubre_el_elemento",
        descripcion="Hay un elemento en el mundo, pero fuera de la región "
        "consultada. Debe devolver 'elementos': [] pese a que el elemento "
        "existe en otra parte del mundo.",
        elementos=[
            ElementoAColocar(id_elemento=1, pos=(50, 50), tipo_slot="suelo"),
        ],
        min_pos=(0, 0),
        max_pos=(10, 10),
    ),
    Caso(
        nombre="dos_comportamientos_a_la_vez",
        descripcion="Se piden 'Peso' y 'Comportamiento_Test' del mismo elemento "
        "-- deben aparecer ambos en 'comportamientos'.",
        elementos=[
            ElementoAColocar(
                id_elemento=1,
                pos=(1, 1),
                tipo_slot="suelo",
                peso=4.2,
                atributo_test="valor_de_ejemplo",
            ),
        ],
        min_pos=(0, 0),
        max_pos=(10, 10),
        incluir=["Peso", "Comportamiento_Test"],
    ),
]


# ─────────────────────────────────────────────────────────────
#  Motor: construye el mundo, avanza un tick, consulta, imprime
# ─────────────────────────────────────────────────────────────


async def _colocar_elemento(logica: LogicaMundo, e: ElementoAColocar) -> None:
    elemento = Elemento_Test(
        id_elemento=e.id_elemento,
        casilla=e.pos,
        peso=e.peso,
    )
    elemento.atributo_test = e.atributo_test

    # Ruta real de transporte: el mismo formato de bytes que usaría
    # _id_a_slot_bytes al mandar un elemento entre sectores.
    payload = json.dumps(elemento.serializar(modo=Modos.transporte)).encode()

    ok, error = await logica.crear_elemento(e.pos, e.tipo_slot, payload)
    if not ok:
        raise RuntimeError(f"No se pudo colocar elemento {e.id_elemento}: {error}")


async def _ejecutar_caso(caso: Caso) -> dict:
    logica = LogicaMundo()

    for e in caso.elementos:
        await _colocar_elemento(logica, e)

    # "Un tick": avanzar elementos globales (aunque hoy no haya ninguno
    # registrado, es el mismo paso que ocurre en producción antes de
    # que Unity pida representación) y luego consultar.
    await logica.avanzar_elementos_globales(caso.tick_id)

    salida_bytes = await logica.consultar_representacion(
        caso.min_pos, caso.max_pos, incluir=caso.incluir, modo=Modos.transporte
    )
    return json.loads(salida_bytes.decode())


def _imprimir_caso(caso: Caso, salida: dict | None, error: Exception | None) -> None:
    print("=" * 70)
    print(f"CASO: {caso.nombre}")
    print(f"  {caso.descripcion}")
    print(f"  region={caso.min_pos}..{caso.max_pos}  incluir={caso.incluir}")
    print("-" * 70)
    if error is not None:
        print(f"[FALLÓ] {type(error).__name__}: {error}")
        if isinstance(error, TypeError):
            print(
                "  -> Pinta a que el fix de Elemento.serializar(cls=None, ...) "
                "todavía no está aplicado (ver discusión sobre get_comportamiento)."
            )
    else:
        print(json.dumps(salida, indent=2, ensure_ascii=False))
    print()


async def _main() -> None:
    for caso in CASOS:
        try:
            salida = await _ejecutar_caso(caso)
            _imprimir_caso(caso, salida, None)
        except (
            Exception
        ) as exc:  # se quiere VER el fallo, no interrumpir los demás casos
            _imprimir_caso(caso, None, exc)


# ─────────────────────────────────────────────────────────────
#  Entradas: pytest y ejecución directa
# ─────────────────────────────────────────────────────────────


def test_mostrar_salida_representacion_hacia_unity():
    """Ejecutar con: pytest -s Tests/Otros/test_salida_representacion_unity.py"""
    asyncio.run(_main())


if __name__ == "__main__":
    asyncio.run(_main())
