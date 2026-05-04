from Core.Entities.Comportamiento.Salud.salud import Salud


class Nutritivo(Salud):
    """Recupera energia si se ingiere"""

    def __init__(self, valor_nutritivo: float):
        super().__init__()
        self.valor_nutritivo = valor_nutritivo
