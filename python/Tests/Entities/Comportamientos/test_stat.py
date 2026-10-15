# tests/test_stat.py

import pytest

from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Stats.Complejos.stat_derivado import Stat_Derivado
from Core.Entities.Comportamiento.Stats.stat_con_tope import Stat_Con_Tope


class TestStat:
    def test_guarda_nombre_y_valor(self):
        s = Stat(nombre="vida", valor=100)
        assert s.nombre == "vida"
        assert s.valor == 100

    def test_a_dict(self):
        s = Stat(nombre="energia", valor=50)
        assert s.a_dict() == {"energia": 50}

    def test_dos_stats_no_comparten_estado(self):
        # el bug historico: instancias distintas no deben pisarse entre si
        vida = Stat(nombre="vida", valor=100)
        energia = Stat(nombre="energia", valor=50)
        vida.valor = 30
        assert energia.valor == 50
        assert vida.nombre == "vida"
        assert energia.nombre == "energia"

    def test_repr(self):
        s = Stat(nombre="vida", valor=10)
        assert repr(s) == "Stat(vida=10)"


# NOTA: se elimina la clase TestStatComplejo que probaba "Stat_Complejo",
# residuo del diseno viejo (cuando los distintos tipos de stat se
# heredaban en vez de componerse). En el diseno actual no existe una
# clase Stat_Complejo -- los Complejos (Armadura, Grasa...) son
# instancias de Stat directamente, sin marcador de subtipo -- por eso
# no hay nada que sustituya a ese test.

# --- Stat_Derivado ---------------------------------------------------


class Velocidad_Doble_Tamanho(Stat_Derivado):
    """Derivado de prueba: velocidad = base - tamanho * 2."""

    def __init__(self, tamanho: Stat, valor_base: float = 10):
        self._tamanho = tamanho
        self.valor_base = valor_base
        super().__init__(nombre="velocidad", valor=self.calcular())

    def calcular(self) -> float:
        return self.valor_base - self._tamanho.valor * 2


class TestStatDerivado:
    def test_calcular_no_implementado_por_defecto(self):
        base = Stat_Derivado(nombre="x", valor=0)
        with pytest.raises(NotImplementedError):
            base.calcular()

    def test_valor_inicial_ya_viene_calculado(self):
        tamanho = Stat(nombre="tamanho", valor=3)
        velocidad = Velocidad_Doble_Tamanho(tamanho=tamanho)
        assert velocidad.valor == 10 - 3 * 2  # = 4

    def test_recalcular_refleja_cambio_en_el_complejo(self):
        tamanho = Stat(nombre="tamanho", valor=3)
        velocidad = Velocidad_Doble_Tamanho(tamanho=tamanho)
        assert velocidad.valor == 4

        tamanho.valor = 1  # el bot crece... o encoge
        # el valor NO cambia solo por mutar el complejo (no es automatico)
        assert velocidad.valor == 4

        velocidad.recalcular()
        assert velocidad.valor == 10 - 1 * 2  # = 8


# --- Stat_Con_Tope -----------------------------------------------------


class TestStatConTope:
    def test_arranca_al_maximo_si_no_se_especifica_valor(self):
        vida_maxima = Stat(nombre="vida_maxima", valor=100)
        vida = Stat_Con_Tope(nombre="vida", maximo=vida_maxima)
        assert vida.valor == 100

    def test_valor_inicial_explicito_por_debajo_del_maximo(self):
        vida_maxima = Stat(nombre="vida_maxima", valor=100)
        vida = Stat_Con_Tope(nombre="vida", maximo=vida_maxima, valor=40)
        assert vida.valor == 40

    def test_valor_inicial_explicito_no_puede_superar_el_maximo(self):
        vida_maxima = Stat(nombre="vida_maxima", valor=100)
        vida = Stat_Con_Tope(nombre="vida", maximo=vida_maxima, valor=999)
        assert vida.valor == 100

    def test_modificar_resta_dano_sin_bajar_de_cero(self):
        vida_maxima = Stat(nombre="vida_maxima", valor=100)
        vida = Stat_Con_Tope(nombre="vida", maximo=vida_maxima, valor=10)
        vida.modificar(-50)
        assert vida.valor == 0

    def test_modificar_suma_curacion_sin_superar_el_maximo(self):
        vida_maxima = Stat(nombre="vida_maxima", valor=100)
        vida = Stat_Con_Tope(nombre="vida", maximo=vida_maxima, valor=90)
        vida.modificar(50)
        assert vida.valor == 100

    def test_el_maximo_puede_bajar_y_recortar_el_valor_actual(self):
        # ilustra por que el maximo se referencia y no se copia: si
        # vida_maxima baja (p.ej. Stat_Derivado.recalcular()), la
        # siguiente modificacion de vida respeta el nuevo techo
        vida_maxima = Stat(nombre="vida_maxima", valor=100)
        vida = Stat_Con_Tope(nombre="vida", maximo=vida_maxima, valor=100)
        vida_maxima.valor = 20
        vida.modificar(0)  # fuerza el recorte al nuevo maximo
        assert vida.valor == 20
