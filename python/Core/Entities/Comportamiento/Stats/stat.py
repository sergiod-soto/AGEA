import json

from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Stat(Comportamiento):
    def __init__(self, nombre: str, valor,**kwargs):
        super().__init__(**kwargs)
        self.valor = valor
        self.nombre = nombre

    def to_dict(self):
        return {self.nombre: self.valor}

    @classmethod
    def serializar(cls, bot):
        stats = {
            nombre: attr.to_dict()
            for nombre, attr in bot.__dict__.items()
            if isinstance(attr, cls)
        }
        return json.dumps(stats)
