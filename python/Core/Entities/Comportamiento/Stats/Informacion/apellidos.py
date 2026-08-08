

from Core.Entities.Elementos.Abstractos.Informacion.informacion import Informacion


class Apellidos(Informacion):
    def __init__(self, apellidos: list,**kwargs):
        super().__init__("apellidos", apellidos,**kwargs)

    def generar_apellidos(ape1, ape2):
        """
        Genera los apellidos del bot a partir de los del padre y la madre
        """

        apellidos = []
        for i in range(int(len(ape1) / 2)):
            apellidos.append(ape1[i])
            apellidos.append(ape2[i])
        return apellidos    
