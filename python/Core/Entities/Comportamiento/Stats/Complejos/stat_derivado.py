# Core/Entities/Comportamiento/Stats/Complejos/stat_derivado.py

# Stat cuyo valor no se asigna a mano: se calcula a partir de otros stats
# (normalmente Stats Complejos) que se le inyectan explicitamente al
# construirlo, como referencias directas a los objetos concretos -- no
# busqueda por nombre. La formula de combinacion vive en cada subclase
# concreta (metodo calcular()), porque no hay una regla unica de como se
# combinan varios complejos sobre el mismo derivado.
from Core.Entities.Comportamiento.Stats.stat import Stat


class Stat_Derivado(Stat):

    def calcular(self) -> float:
        """Sobreescribir en cada subclase: usa las referencias guardadas
        en __init__ (p.ej. self._tamanho) para devolver el valor nuevo."""
        raise NotImplementedError

    def recalcular(self) -> None:
        """Actualiza self.valor ejecutando calcular(). Se llama a mano
        (o via Tiene_Stats.recalcular_derivados()) cuando cambie algun
        complejo del que depende este derivado -- no es automatico."""
        self.valor = self.calcular()
