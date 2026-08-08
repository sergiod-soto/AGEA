# Core/Entities/Comportamiento/Stats/Informacion/id.py

# Stat informativo: incluso sin valor por defecto sensato (cada Bot
# necesita un id distinto), sigue el mismo patron que los demas stats
# para que Tiene_Stats no tenga que distinguir "informativo" de "simple".
from Core.Entities.Comportamiento.Stats.stat import Stat


class ID(Stat):
    def __init__(self, valor):
        super().__init__(nombre="id", valor=valor)
