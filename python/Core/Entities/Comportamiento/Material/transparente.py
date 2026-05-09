from Core.Entities.Comportamiento.Material.material import Material


class Transparente(Material):
    """
    Solo afecta a solidos.
    Indica cuanta luz atenua a la hora de iluminar objetos y cuanta luz atenua a la hora de ver
    
    Ejemplo:
    
    Fuego (luz 100%) -> cristal: -10% (luz 90%) -> cristal: -10% (luz 89%) -> bot
    
    Cuanto menos luz le de algo, 
    Parametros:

    -

    Metodos abstractos:

    -
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
