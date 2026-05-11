#
#
#
# lista de recetas
#

from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta
from Core.Entities.Elementos.Simples.Agua.agua import Agua
from Core.Entities.Elementos.Simples.Comidas.Ingredientes.harina import Harina


class Lista_Recetas:

    class Mezclar:

        class Comida:

            #----------------------------------------------------------------------------
            def result_MASA_PAN(): ...
            MASA_PAN = Receta(
                nombre="MASA_PAN",
                ingredientes=[Agua, Harina],
                condiciones=[],
                accion="mezclar",   # solo indica cual es el trigger
                resultado=None,     # funcion que se ejecuta cuando la receta se lleva a cabo
            )

            #----------------------------------------------------------------------------
            EMBUTIDO_CRUDO = Receta(
                nombre="EMBUTIDO_CRUDO",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            MANTEQUILLA = Receta(
                nombre="MANTEQUILLA",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )
            
            #----------------------------------------------------------------------------
            CALDO = Receta(
                nombre="CALDO",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            GACHAS = Receta(
                nombre="GACHAS",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

        class Salud:

            #----------------------------------------------------------------------------
            CATAPLASMA = Receta(
                nombre="CATAPLASMA",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            UGUENTO = Receta(
                nombre="UGUENTO",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            JABON = Receta(
                nombre="JABON",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            VENDAJE_ESTERILIZADO = Receta(
                nombre="VENDAJE_ESTERILIZADO",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

        class Materiales: ...

        class Ingredientes:

            #----------------------------------------------------------------------------
            POLVORA = Receta(
                nombre="POLVORA",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            HARINA = Receta(
                nombre="HARINA",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            LEVADURA = Receta(
                nombre="LEVADURA",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

        class Construccion:

            #----------------------------------------------------------------------------
            CEMENTO = Receta(
                nombre="CEMENTO",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            HORMIGON = Receta(
                nombre="HORMIGON",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

        class Tintes:

            #----------------------------------------------------------------------------
            # NEGRO
            TINTE_CARBON = Receta(
                nombre="HORMIGON",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            # ROJO
            TINTE_SANGRE = Receta(
                nombre="HORMIGON",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            #----------------------------------------------------------------------------
            # AZUL
            TINTE_LAPISLAZULI = Receta(
                nombre="HORMIGON",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

        class Drogas: ...

        class Fertilizantes: ...

    class Filtrar: ...

    class Golpear: ...

    class Frotar: ...

    class Apretar: ...
