# Core/Entities/Comportamiento/Stats/stat_con_tope.py

# Stat cuyo valor no puede superar el de otro stat (su "maximo"), p.ej.
# vida no puede superar vida_maxima. El maximo se referencia directamente,
# igual que los derivados referencian sus complejos.
from Core.Entities.Comportamiento.Stats.stat import Stat


class Stat_Con_Tope(Stat):
    def __init__(self, nombre: str, maximo: Stat, valor: float = None):
        valor_inicial = maximo.valor if valor is None else min(valor, maximo.valor)
        super().__init__(nombre=nombre, valor=valor_inicial)
        self.maximo = maximo

    def modificar(self, delta: float) -> None:
        """Suma delta a self.valor sin superar self.maximo.valor ni bajar
        de 0. Uso: dano (-delta) o curacion (+delta) en combate."""
        self.valor = max(0.0, min(self.valor + delta, self.maximo.valor))
