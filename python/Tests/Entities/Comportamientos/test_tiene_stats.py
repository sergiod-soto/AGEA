# tests/test_tiene_stats.py

import pytest

from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Stats.stat_derivado import Stat_Derivado
from Core.Entities.Comportamiento.Stats.tiene_stats import Tiene_Stats


# NOTA: la anotacion de tipo usaba "Stat_Complejo", una clase que no
# existe en el rediseno actual (no esta en stat.py, stat_derivado.py ni
# en ningun Complejo). Se usa "Stat" a secas porque es lo unico que
# existe hoy; si en el futuro se crea una clase marcador Stat_Complejo,
# cambiar aqui y en test_stat.py, que tiene el mismo problema.
class Velocidad_Doble_Tamanho(Stat_Derivado):
    def __init__(self, tamanho: Stat, valor_base: float = 10):
        self._tamanho = tamanho
        self.valor_base = valor_base
        super().__init__(nombre="velocidad", valor=self.calcular())

    def calcular(self) -> float:
        return self.valor_base - self._tamanho.valor * 2


# Elemento minimo de prueba: solo mezcla Tiene_Stats, sin el resto de
# comportamientos de un Bot real (Peso, Color...), para aislar el
# comportamiento de Tiene_Stats en si mismo.
class Elemento_De_Prueba(Tiene_Stats):
    def __init__(self, stats=None):
        super().__init__(stats=stats)


class TestTieneStatsConstruccion:
    def test_sin_stats_no_falla(self):
        e = Elemento_De_Prueba()
        assert e.listar_stats() == {}

    def test_construye_con_lista_de_stats(self):
        e = Elemento_De_Prueba(stats=[Stat("vida", 100), Stat("energia", 50)])
        assert e.get_stat("vida") == 100
        assert e.get_stat("energia") == 50

    def test_nombres_duplicados_lanzan_error(self):
        with pytest.raises(ValueError):
            Elemento_De_Prueba(stats=[Stat("vida", 100), Stat("vida", 999)])


class TestTieneStatsAcceso:
    def test_get_stat_de_nombre_inexistente_lanza_keyerror(self):
        e = Elemento_De_Prueba(stats=[Stat("vida", 100)])
        with pytest.raises(KeyError):
            e.get_stat("energia")

    def test_set_stat_actualiza_el_valor(self):
        e = Elemento_De_Prueba(stats=[Stat("vida", 100)])
        e.set_stat("vida", 80)
        assert e.get_stat("vida") == 80

    def test_tiene_stat(self):
        e = Elemento_De_Prueba(stats=[Stat("vida", 100)])
        assert e.tiene_stat("vida") is True
        assert e.tiene_stat("energia") is False

    def test_listar_stats_devuelve_copia_no_el_original(self):
        e = Elemento_De_Prueba(stats=[Stat("vida", 100)])
        copia = e.listar_stats()
        copia["nueva_clave"] = Stat("intrusa", 1)
        assert "nueva_clave" not in e.listar_stats()


class TestTieneStatsRecalcularDerivados:
    def test_recalcula_solo_los_stat_derivado(self):
        tamanho = Stat(nombre="tamanho", valor=3)
        velocidad = Velocidad_Doble_Tamanho(tamanho=tamanho)
        vida = Stat(nombre="vida", valor=100)  # no derivado, no debe tocarse

        e = Elemento_De_Prueba(stats=[tamanho, velocidad, vida])
        assert e.get_stat("velocidad") == 10 - 3 * 2  # 4

        tamanho.valor = 1
        e.recalcular_derivados()
        assert e.get_stat("velocidad") == 10 - 1 * 2  # 8
        assert e.get_stat("vida") == 100  # intacto


class TestTieneStatsSerializacion:
    def test_serialize_stats_expone_estado_actual(self):
        e = Elemento_De_Prueba(stats=[Stat("vida", 100), Stat("energia", 50)])
        assert e.serialize_stats() == {"vida": 100, "energia": 50}

    def test_serializar_generico_incluye_stats_via_hook(self):
        # Comportamiento.serializar() debe usar el hook serialize_stats,
        # no el parametro crudo 'stats' que se paso a __init__
        e = Elemento_De_Prueba(stats=[Stat("vida", 100)])
        resultado = e.serializar(modo="transporte")
        assert resultado["stats"] == {"vida": 100}
