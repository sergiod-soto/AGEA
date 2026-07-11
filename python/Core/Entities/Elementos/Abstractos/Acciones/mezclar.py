from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion


class Mezclar(Accion):
    def __init__(self, **kwargs):
        super().__init__(
            Mezclar,
            "mezclar",
            **kwargs,
        )

    def ejecutar(self):
        raise NotImplementedError("ejecutar() de mezclar.py")
