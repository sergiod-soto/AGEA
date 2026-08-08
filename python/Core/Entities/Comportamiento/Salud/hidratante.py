from Core.Entities.Comportamiento.Salud.salud import Salud


class Hidratante(Salud):
    """
    Recupera hidratacion si se ingiere

    Parametros:

    - valor_hidratacion: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"valor_hidratacion: float"}
    ABSTRACTOS = {}

    def __init__(self, valor_hidratacion: float, **kwargs):
        super().__init__(**kwargs)
        self.valor_hidratacion = valor_hidratacion
