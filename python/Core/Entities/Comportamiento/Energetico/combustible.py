from Core.Entities.Comportamiento.Energetico.energetico import Energetico


class Combustible(Energetico):
    """
    No se mira la parte de arder, si no la parte energetica.

    Util para poder crear cosas que almacenen energia, desligado del
    proceso de combustion

    Parametros:

    - energia_maxima: float,
    - ratio_emision: float,
    - energia_actual: float = None,
    - ratio_recarga: float = 0.0
    
    Metodos abstractos:
    
    -
    """

    def __init__(
        self,
        energia_maxima: float,
        ratio_emision: float,
        energia_actual: float = None,
        ratio_recarga: float = 0.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.energia_maxima = energia_maxima
        self.ratio_emision = ratio_emision
        self.energia_actual = energia_actual or energia_maxima
        self.ratio_recarga = ratio_recarga

    def gastar(self, cantidad: float):
        if cantidad > self.ratio_emision:
            cantidad = self.ratio_emision

        if self.energia_actual >= cantidad:
            self.energia_actual -= cantidad
            return cantidad
        else:
            cantidad = self.energia_actual
            self.energia_actual = 0.0
            return cantidad

    def cargar(self, cantidad: float):
        if cantidad > self.ratio_recarga:
            cantidad = self.ratio_recarga

        self.energia_actual += cantidad

        if self.energia_actual > self.energia_maxima:
            self.energia_actual = self.energia_maxima

   