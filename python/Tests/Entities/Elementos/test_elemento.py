# Tests/Core/Entities/Elementos/test_elemento.py
"""
Tests unitarios de serializar()/deserializar() en la cadena
Elemento -> Elemento_Simple -> Elemento_Test, y de la reconciliación de
comportamientos dinámicos en registry.reconstruir_elemento().

No usan ninguna fixture de conftest.py (grpc/env real): son puramente en
memoria, así que no hace falta red, disco ni asyncio.
"""

from __future__ import annotations

import pytest

from Core.Entities.Comportamiento.comportamiento import Comportamiento, NO_SERIALIZAR
from Core.Entities.Comportamiento.comportamiento_test import Comportamiento_Test
from Core.Entities.Comportamiento.Fisico.fisico import Fisico
from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.registry import COMPORTAMIENTOS
from Core.Entities.Elementos.elemento_test import Elemento_Test
from Core.Entities.Elementos.registry import ELEMENTOS, reconstruir_elemento

# Valor por defecto para el parámetro obligatorio de Comportamiento_Test en
# todos los tests que no lo estén probando explícitamente — su contenido no
# importa para estos tests, solo que exista y viaje intacto en el roundtrip.
ATRIBUTO_TEST_DEFAULT = None


# ─────────────────────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def elemento_basico() -> Elemento_Test:
    """
    Un Elemento_Test 'normal', creado por __init__ real (no por
    reconstrucción). Trae Peso/Fisico/Comportamiento_Test de fábrica,
    como cualquier instancia declarada estáticamente.
    """
    return Elemento_Test(casilla=(3, 4), id_elemento=1, peso=10.0)


class _MundoFalso:
    """
    Doble mínimo de Mundo: basta con que sea un objeto distinto de None
    para comprobar que deserializar() lo asigna tal cual a self.mundo,
    sin necesitar un Mundo real (que arrastraría toda la simulación).
    """

    pass


# ─────────────────────────────────────────────────────────────
#  __clase__ y campos excluidos (tipo / mundo)
# ─────────────────────────────────────────────────────────────


def test_serializar_incluye_clase(elemento_basico):
    """__clase__ debe existir y coincidir con el nombre real de la clase,
    porque reconstruir_elemento() lo usa para resolver en ELEMENTOS."""
    data = elemento_basico.serializar(modo="guardado")
    assert data["__clase__"] == "Elemento_Test"


def test_serializar_excluye_tipo_y_mundo(elemento_basico):
    """
    'tipo' (la propia clase Python) y 'mundo' (referencia al Mundo) no
    deben aparecer en el dict serializado: no son JSON-serializables
    (tipo) o arrastrarían el grafo completo del mundo (mundo).
    """
    data = elemento_basico.serializar(modo="guardado")
    assert "tipo" not in data
    assert "mundo" not in data


def test_serialize_tipo_y_mundo_devuelven_sentinel(elemento_basico):
    """Comprobación directa del hook: debe ser NO_SERIALIZAR, no None
    ni cualquier otro valor (None podría ser un valor legítimo de mundo)."""
    assert elemento_basico.serialize_tipo() is NO_SERIALIZAR
    assert elemento_basico.serialize_mundo() is NO_SERIALIZAR


def test_deserializar_restaura_tipo_como_clase_real():
    """Tras reconstruir, self.tipo debe ser exactamente type(self), no un
    valor heredado de 'data' (porque nunca estuvo en 'data')."""
    original = Elemento_Test(casilla=(0, 0), id_elemento=1, peso=5.0)
    data = original.serializar(modo="guardado")

    reconstruido = reconstruir_elemento(data)

    assert reconstruido.tipo is Elemento_Test
    assert reconstruido.tipo is type(reconstruido)


def test_deserializar_asigna_mundo_recibido_como_parametro():
    """mundo no viaja en el JSON: quien reconstruye decide qué mundo
    asignar, pasándolo explícitamente a reconstruir_elemento/deserializar."""
    original = Elemento_Test(casilla=(0, 0), id_elemento=1, peso=5.0)
    data = original.serializar(modo="guardado")
    mundo_falso = _MundoFalso()

    reconstruido = reconstruir_elemento(data, mundo=mundo_falso)

    assert reconstruido.mundo is mundo_falso


def test_deserializar_sin_mundo_lo_deja_en_none():
    """Si no se pasa mundo explícitamente, el default es None (elemento
    'huérfano', pendiente de que alguien lo reinserte en un Mundo)."""
    original = Elemento_Test(casilla=(0, 0), id_elemento=1, peso=5.0)
    data = original.serializar(modo="guardado")

    reconstruido = reconstruir_elemento(data)

    assert reconstruido.mundo is None


# ─────────────────────────────────────────────────────────────
#  casilla / rotacion (hooks serialize_X / deserialize_X con transformación)
# ─────────────────────────────────────────────────────────────


def test_serialize_casilla_produce_dict_json_valido():
    """
    Regresión del bug: antes devolvía str({"x":.., "y":..}) (repr de
    Python, no JSON). Ahora debe ser un dict real con claves x/y.
    """
    elem = Elemento_Test(casilla=(7, 9), id_elemento=1, peso=1.0)
    assert elem.serialize_casilla() == {"x": 7, "y": 9}


def test_casilla_roundtrip_reconstruye_tupla():
    """El valor debe volver a ser una tupla (x, y) tras deserializar,
    no el dict intermedio usado para el transporte."""
    original = Elemento_Test(casilla=(7, 9), id_elemento=1, peso=1.0)
    data = original.serializar(modo="guardado")

    reconstruido = reconstruir_elemento(data)

    assert reconstruido.casilla == (7, 9)
    assert isinstance(reconstruido.casilla, tuple)


def test_rotacion_se_normaliza_a_0_360():
    """serialize_rotacion debe devolver el ángulo módulo 360, incluso si
    el valor interno es negativo o mayor de una vuelta completa."""
    elem = Elemento_Test(
        casilla=(0, 0),
        id_elemento=1,
        peso=1.0,
        rotacion=370,
    )
    assert elem.serialize_rotacion() == 10

    elem_negativo = Elemento_Test(
        casilla=(0, 0),
        id_elemento=1,
        peso=1.0,
        rotacion=-10,
    )
    assert elem_negativo.serialize_rotacion() == 350


# ─────────────────────────────────────────────────────────────
#  Comportamientos: valores propios (Peso) y roundtrip completo
# ─────────────────────────────────────────────────────────────


def test_comportamiento_peso_se_serializa_bajo_su_propio_nombre(elemento_basico):
    """Cada comportamiento aporta sus atributos propios bajo su nombre de
    clase en 'comportamientos', vía Comportamiento.serializar (no vars(self))."""
    data = elemento_basico.serializar(modo="guardado")
    assert data["comportamientos"]["Peso"] == {"peso": 10.0}


def test_comportamiento_categoria_sin_atributos_sale_vacio(elemento_basico):
    """Fisico no declara parámetros propios en su __init__ (solo agrupa
    por herencia), así que su entrada debe existir pero vacía — no debe
    fallar ni desaparecer solo por no tener datos propios."""
    data = elemento_basico.serializar(modo="guardado")
    assert data["comportamientos"]["Fisico"] == {}


def test_comportamiento_test_se_serializa_bajo_su_propio_nombre(elemento_basico):
    """Mismo mecanismo que Peso, para el segundo comportamiento propio
    de Elemento_Test: Comportamiento_Test."""
    data = elemento_basico.serializar(modo="guardado")
    assert data["comportamientos"]["Comportamiento_Test"] == {
        "atributo_test": ATRIBUTO_TEST_DEFAULT
    }


def test_roundtrip_completo_conserva_todos_los_valores():
    """
    Test de extremo a extremo: crear -> serializar -> reconstruir debe
    devolver un objeto equivalente en todos los atributos propios y de
    comportamientos, sin pasar nunca por __init__.
    """
    original = Elemento_Test(
        casilla=(2, 3),
        id_elemento=42,
        peso=7.5,
        rotacion=90,
    )
    data = original.serializar(modo="guardado")

    reconstruido = reconstruir_elemento(data)

    assert reconstruido.id_elemento == original.id_elemento
    assert reconstruido.casilla == original.casilla
    assert reconstruido.tamanho == original.tamanho
    assert reconstruido.capa == original.capa
    assert reconstruido.rotacion == original.rotacion
    assert reconstruido.peso == original.peso
    assert reconstruido.atributo_test == original.atributo_test
    assert isinstance(reconstruido, Peso)
    assert isinstance(reconstruido, Fisico)
    assert isinstance(reconstruido, Comportamiento_Test)


def test_reconstruir_elemento_clase_desconocida_lanza_value_error():
    """Si '__clase__' no está en ELEMENTOS (dato corrupto o clase no
    registrada), debe fallar con un mensaje claro, no un KeyError críptico."""
    with pytest.raises(ValueError):
        reconstruir_elemento({"__clase__": "Esto_No_Existe", "comportamientos": {}})


def test_get_comportamiento_sobre_elemento_real(elemento_basico):
    resultado = elemento_basico.get_comportamiento("Peso", modo="representacion")
    assert resultado == {"peso": 10.0}


def test_get_comportamiento_sobre_elemento_real(elemento_basico):
    """
    Camino que usa consultar_representacion() en producción. Antes del
    fix de 'cls=None' en Elemento.serializar, esto lanzaba TypeError en
    vez de devolver el dict del comportamiento pedido.
    """
    resultado = elemento_basico.get_comportamiento("Peso", modo="representacion")
    assert resultado == {"peso": 10.0}


def test_get_comportamiento_nombre_inexistente_lanza_value_error(elemento_basico):
    """Comportamiento que el elemento no tiene -> ValueError, que es
    justo lo que consultar_representacion sabe capturar y saltarse."""
    with pytest.raises(ValueError):
        elemento_basico.get_comportamiento("Volumen", modo="representacion")


def test_get_comportamiento_devuelve_mismo_resultado_en_los_tres_modos(elemento_basico):
    """
    De momento 'representacion' es intencionalmente idéntico a
    'guardado'/'transporte' (no hay hooks serialize_X_representacion
    todavía). Este test fija ese contrato actual: si algún día se añade
    un hook específico de representación en algún comportamiento, este
    test empezará a fallar y avisará de que el contrato cambió on
    purpose -- momento de revisar si el test debe actualizarse o si el
    cambio fue accidental.
    """
    en_guardado = elemento_basico.get_comportamiento("Peso", modo="guardado")
    en_transporte = elemento_basico.get_comportamiento("Peso", modo="transporte")
    en_representacion = elemento_basico.get_comportamiento(
        "Peso", modo="representacion"
    )

    assert en_guardado == en_transporte == en_representacion == {"peso": 10.0}


# ─────────────────────────────────────────────────────────────
#  Comportamientos dinámicos (anhadir/quitar) — reconciliación
# ─────────────────────────────────────────────────────────────


def test_quitar_comportamiento_dinamicamente_se_conserva_tras_roundtrip():
    """
    Si a una instancia se le quita Peso en caliente (Comportamiento.quitar)
    ANTES de serializar, la clase estática de Elemento_Test seguiría
    trayendo Peso de fábrica al reconstruir. reconstruir_elemento debe
    detectar esa diferencia (vía las claves de 'comportamientos') y volver
    a quitarlo, para no resucitar un comportamiento que el objeto original
    no tenía.
    """
    original = Elemento_Test(casilla=(0, 0), id_elemento=1, peso=3.0)
    assert isinstance(original, Peso)

    Comportamiento.quitar(original, Peso)
    assert not isinstance(original, Peso)
    assert not hasattr(original, "peso")

    data = original.serializar(modo="guardado")
    assert "Peso" not in data["comportamientos"]

    reconstruido = reconstruir_elemento(data)

    assert not isinstance(reconstruido, Peso)
    assert not hasattr(reconstruido, "peso")
    # Sigue siendo un Elemento_Test válido en todo lo demás
    assert reconstruido.casilla == (0, 0)


def test_anhadir_comportamiento_dinamicamente_se_conserva_tras_roundtrip(monkeypatch):
    class Comportamiento_Dinamico_De_Prueba(Comportamiento):
        def __init__(self, valor_prueba: float, **kwargs):
            super().__init__(**kwargs)
            self.valor_prueba = valor_prueba

    monkeypatch.setitem(
        COMPORTAMIENTOS,
        "Comportamiento_Dinamico_De_Prueba",
        Comportamiento_Dinamico_De_Prueba,
    )

    original = Elemento_Test(casilla=(0, 0), id_elemento=1, peso=3.0)
    assert not isinstance(original, Comportamiento_Dinamico_De_Prueba)

    Comportamiento.anhadir(
        original, Comportamiento_Dinamico_De_Prueba, valor_prueba=12.5
    )
    assert isinstance(original, Comportamiento_Dinamico_De_Prueba)

    data = original.serializar(modo="guardado")
    assert data["comportamientos"]["Comportamiento_Dinamico_De_Prueba"] == {
        "valor_prueba": 12.5
    }

    reconstruido = reconstruir_elemento(data)

    assert isinstance(reconstruido, Comportamiento_Dinamico_De_Prueba)
    assert reconstruido.valor_prueba == 12.5
    assert isinstance(reconstruido, Peso)
    assert reconstruido.peso == 3.0


# ─────────────────────────────────────────────────────────────
#  eliminar() — limpieza de estado + aviso al mundo
# ─────────────────────────────────────────────────────────────


class _MundoFalsoConRegistro:
    """Doble de Mundo que registra si se le avisó de la eliminación,
    y con qué elemento -- basta para comprobar el 'aviso al mundo' sin
    un Mundo real."""

    def __init__(self):
        self.elemento_eliminado = None

    def eliminar_elemento(self, elemento):
        self.elemento_eliminado = elemento


def test_eliminar_sin_mundo_lanza_type_error_y_no_toca_el_estado():
    """
    Guard clause: si mundo no está inicializado, eliminar() debe fallar
    ANTES de limpiar nada -- no tiene sentido destruir el estado de un
    elemento que ni siquiera se va a poder notificar/retirar
    correctamente. (Regresión del bug de orden: antes limpiaba primero
    y fallaba después, siempre, tuviera mundo o no.)
    """
    elem = Elemento_Test(casilla=(1, 2), id_elemento=1, peso=5.0)
    assert elem.mundo is None

    with pytest.raises(TypeError):
        elem.eliminar()

    # El estado NO debe haberse tocado: el fallo fue antes de limpiar.
    assert elem.peso == 5.0
    assert elem.casilla == (1, 2)
    assert elem.id_elemento == 1


def test_eliminar_con_mundo_limpia_atributos_propios_y_de_comportamientos():
    """
    Con mundo inicializado, eliminar() debe poner a None tanto los
    atributos propios de Elemento (casilla, tamanho...) como los de
    sus comportamientos (peso, atributo_test) -- opción B: limpieza
    uniforme, sin distinguir origen.
    """
    elem = Elemento_Test(casilla=(1, 2), id_elemento=1, peso=5.0)
    elem.mundo = _MundoFalsoConRegistro()

    elem.eliminar()

    assert elem.peso is None
    assert elem.atributo_test is None
    assert elem.casilla is None
    assert elem.tamanho is None
    assert elem.id_elemento is None


def test_eliminar_avisa_al_mundo_con_el_propio_elemento():
    """El mundo debe recibir la llamada a eliminar_elemento(self) --
    y recibir el MISMO objeto, no una copia ni None."""
    elem = Elemento_Test(casilla=(1, 2), id_elemento=1, peso=5.0)
    mundo_falso = _MundoFalsoConRegistro()
    elem.mundo = mundo_falso

    elem.eliminar()

    assert mundo_falso.elemento_eliminado is elem


def test_eliminar_no_toca_class_ni_isinstance(elemento_basico):
    """
    Diferencia deliberada frente a quitar(): eliminar() (opción B) NO
    reescribe __class__. isinstance() sigue dando True para los
    comportamientos que tenía, aunque sus atributos ya sean None --
    es aceptable porque el objeto no se va a volver a usar, pero se
    deja fijado aquí para que un cambio futuro a "reescribir __class__"
    sea una decisión consciente, no un efecto colateral no probado.
    """
    elemento_basico.mundo = _MundoFalsoConRegistro()
    elemento_basico.eliminar()

    assert isinstance(elemento_basico, Peso)
    assert elemento_basico.peso is None
