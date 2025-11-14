from Core.Entities.Elemento import Elemento

# los arboles no se pueden mover. generan comida y semillas periodicamente
# las semillas se convierten en arbol despues de un tiempo si no hay mas de una cierta
# cantidad de arboles alrededor y hay agua
#
# las semillas se dispersan en un area alrededor del arbol en funcion del viento




class Arbol(Elemento):

    def __init__(self):
        self.edad = 0
