# Core/Entities/Comportamiento/comportamiento_test.py

from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Comportamiento_Test(Comportamiento):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.atributo_test = None

    @classmethod
    def _campos_internos(cls):
        return {"atributo_test"}
