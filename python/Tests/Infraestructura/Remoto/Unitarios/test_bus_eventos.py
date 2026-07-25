# Tests/Infraestructura/Remoto/Unitarios/test_bus_eventos.py
"""
test_bus_eventos.py — Pruebas unitarias de BusEventos
(Gestores/Mundo/Bus_Eventos/bus.py): pub/sub simple basado en
weakref.ref() para no retener artificialmente a los suscriptores.

HALLAZGO DE DISEÑO (no es un "bug" de lógica, pero es una trampa real
de Python que puede morder en producción): weakref.ref() sobre un
MÉTODO LIGADO (obj.metodo) no funciona como cabría esperar. Un método
ligado es un objeto temporal creado en el momento de acceder a él
(obj.metodo crea uno nuevo cada vez); si no se guarda una referencia
explícita a ESE objeto en concreto, nada más lo mantiene vivo — ni
siquiera que la instancia `obj` siga viva — y el weakref lo recolecta
casi de inmediato. El docstring de bus.py describe justo este patrón
de uso ("una Condicion que escucha dicho evento... ejecuta una
función" de un objeto), así que conviene saber que
`bus.suscribir('x', condicion.evaluar)` sin guardar la referencia al
método en sí NUNCA disparará el callback. test_suscribir_metodo_ligado
_sin_retenerlo_no_sobrevive lo demuestra.
"""

import gc

import pytest

from Infraestructura.Gestores.Mundo.Bus_Eventos.bus import BusEventos


@pytest.mark.unit
def test_suscribir_y_emitir_llama_al_callback_con_los_argumentos():
    bus = BusEventos()
    llamadas = []

    def callback(*args, **kwargs):
        llamadas.append((args, kwargs))

    bus.suscribir("temperatura_cambiada", callback)
    bus.emitir("temperatura_cambiada", 25, unidad="C")

    assert llamadas == [((25,), {"unidad": "C"})]


@pytest.mark.unit
def test_emitir_tipo_sin_suscriptores_no_lanza():
    bus = BusEventos()
    bus.emitir("evento_sin_nadie_escuchando")  # no debe lanzar


@pytest.mark.unit
def test_tipos_distintos_no_interfieren_entre_si():
    bus = BusEventos()
    llamados_a = []
    llamados_b = []

    def cb_a(*a):
        llamados_a.append(a)

    def cb_b(*a):
        llamados_b.append(a)

    bus.suscribir("a", cb_a)
    bus.suscribir("b", cb_b)

    bus.emitir("a")

    assert llamados_a == [()]
    assert llamados_b == []


@pytest.mark.unit
def test_callback_recolectado_no_se_llama_y_no_lanza():
    """
    Si nadie retiene una referencia fuerte al callback tras
    suscribirlo, el weakref lo pierde y emitir() simplemente lo
    ignora — no debe lanzar ni fallar por el suscriptor "muerto".
    """
    bus = BusEventos()
    llamado = []

    bus.suscribir("evento", lambda: llamado.append(1))  # sin referencia guardada
    gc.collect()

    bus.emitir("evento")

    assert llamado == []


@pytest.mark.unit
def test_suscribir_metodo_ligado_sin_retenerlo_no_sobrevive():
    """Ver HALLAZGO DE DISEÑO en la cabecera del fichero."""

    class Escuchador:
        def __init__(self):
            self.llamado = 0

        def metodo(self, *a):
            self.llamado += 1

    bus = BusEventos()
    escuchador = Escuchador()  # se mantiene vivo durante todo el test
    bus.suscribir("evento", escuchador.metodo)  # pero el bound method NO se retiene
    gc.collect()

    bus.emitir("evento")

    assert escuchador.llamado == 0  # sorprendente pero real: nunca se llegó a llamar


@pytest.mark.unit
def test_suscribir_metodo_ligado_retenido_explicitamente_si_sobrevive():
    """Contraprueba: guardando el bound method en una variable, sí
    sobrevive al garbage collector y el callback se dispara."""

    class Escuchador:
        def __init__(self):
            self.llamado = 0

        def metodo(self, *a):
            self.llamado += 1

    bus = BusEventos()
    escuchador = Escuchador()
    metodo_retenido = escuchador.metodo  # referencia explícita al bound method
    bus.suscribir("evento", metodo_retenido)
    gc.collect()

    bus.emitir("evento")

    assert escuchador.llamado == 1
