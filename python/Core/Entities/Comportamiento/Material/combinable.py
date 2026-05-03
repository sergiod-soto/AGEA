from Core.Entities.Comportamiento.Material.material import Material

class Convinable(Material):
    '''
    Indica si 2 Elementos iguales se pueden fusionar en uno solo.
    Como crafteable, per reversible
    '''
    def __init__(self):
        super().__init__()