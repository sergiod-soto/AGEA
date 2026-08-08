# tests/test_comportamiento.py

import pytest

from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Stats.tiene_stats import Tiene_Stats


# Comportamientos minimos de prueba, con la misma forma que Peso/Color en
# el proyecto real: cada uno define su propio atributo con nombre fijo.
class Peso(Comportamiento):
    def __init__(self, peso: float, **kwargs):
        super().__init__(**kwargs)
        self.peso = peso


class Color(Comportamiento):
    def __init__(self, color: str = "gris", **kwargs):
        super().__init__(**kwargs)
        self.color = color


comportamientos_fisicos = Comportamiento.declarar_comportamientos(Peso, Color)


class Cosa(comportamientos_fisicos, Tiene_Stats):
    def __init__(self, peso, color, stats=None):
        super().__init__(peso=peso, color=color, stats=stats)


class TestComportamientos:
    def test_devuelve_las_clases_mezcladas(self):
        # incluye tambien clases intermedias (la generada por
        # declarar_comportamientos, y la propia Cosa), no solo las hojas
        c = Cosa(peso=10, color="rojo")
        nombres = {cls.__name__ for cls in c.comportamientos()}
        assert {"Peso", "Color", "Tiene_Stats"} <= nombres

    def test_devuelve_clases_no_instancias(self):
        c = Cosa(peso=10, color="rojo")
        for cls in c.comportamientos():
            assert isinstance(cls, type)  # son clases, no instancias


class TestCategorias:
    def test_incluye_las_categorias_presentes(self):
        c = Cosa(peso=10, color="rojo")
        nombres = {cls.__name__ for cls in c.categorias()}
        assert {"Peso", "Color", "Tiene_Stats"} <= nombres


class TestTieneComportamiento:
    def test_true_si_lo_tiene(self):
        c = Cosa(peso=10, color="rojo")
        assert c.tiene_comportamiento(Peso) is True

    def test_false_si_no_lo_tiene(self):
        class Volumen(Comportamiento):
            def __init__(self, volumen, **kwargs):
                super().__init__(**kwargs)
                self.volumen = volumen

        c = Cosa(peso=10, color="rojo")
        assert c.tiene_comportamiento(Volumen) is False


class TestGetComportamiento:
    def test_devuelve_el_estado_serializado_del_comportamiento_pedido(self):
        c = Cosa(peso=10, color="rojo")
        assert c.get_comportamiento("Peso", modo="transporte") == {"peso": 10}
        assert c.get_comportamiento("Color", modo="transporte") == {"color": "rojo"}

    def test_nombre_inexistente_lanza_error(self):
        c = Cosa(peso=10, color="rojo")
        with pytest.raises(ValueError):
            c.get_comportamiento("Volumen", modo="transporte")

    def test_no_sirve_para_pedir_un_stat_individual(self):
        # "Vida" no es un comportamiento propio en el MRO (vive en
        # composicion dentro de Tiene_Stats) -- por eso get_comportamiento
        # no puede encontrarlo, y hay que usar get_stat en su lugar.
        c = Cosa(peso=10, color="rojo", stats=[Stat("vida", 100)])
        with pytest.raises(ValueError):
            c.get_comportamiento("vida", modo="transporte")
        assert c.get_stat("vida") == 100
