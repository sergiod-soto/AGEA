from Core.Entities.Elementos.elemento import Elemento


class Elemento_Compuesto(Elemento):

    def __init__(
        self,
        tipo: type,
        capa: int,
        **kwargs,
    ):
        super().__init__(
            tipo=tipo,
            capa=capa,
            **kwargs,
        )
