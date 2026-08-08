# Core/Entities/Comportamiento/Stats/stat.py


# Representa un unico stat: nombre + valor. Es un objeto de composicion
# simple que vive dentro del dict interno de Tiene_Stats. Al ser una
# instancia propia por cada stat, su self.valor/self.nombre nunca puede
# colisionar con el de otro (el bug historico venia de que todos los
# stats compartian el __dict__ del Bot via herencia multiple, porque
# Stat era un mixin y el MRO deduplicaba su __init__ compartido).
class Stat:
    def __init__(self, nombre: str, valor):
        self.nombre = nombre
        self.valor = valor

    def a_dict(self) -> dict:
        return {self.nombre: self.valor}

    def __repr__(self):
        return f"Stat({self.nombre}={self.valor!r})"
