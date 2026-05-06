from Core.Entities.Comportamiento.Material.material import Material


class Transparente(Material):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.transparente = True
