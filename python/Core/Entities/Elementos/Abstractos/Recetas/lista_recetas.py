from Core.Entities.Comportamiento.Energetico.termico import Termico
from Core.Entities.Comportamiento.Material.liquido import Liquido
from Core.Entities.Elementos.Abstractos.Acciones.mezclar import Mezclar
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta
from Core.Entities.Elementos.Simples.Agua.agua import Agua
from Core.Entities.Elementos.Simples.Comidas.Ingredientes.harina import Harina
from Core.Entities.Elementos.Simples.Comidas.Ingredientes.ingrediente import Ingrediente
from Core.Entities.Elementos.Simples.Comidas.Ingredientes.masa_pan import Masa_Pan
from Core.Entities.Elementos.elemento import Elemento
from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta


class Lista_Recetas:

    #
    #   clases con Accion como trigger
    #
    class Mezclar:

        class Comida:

            # ----------------------------------------------------------------------------

            def condicion1_funcion(agua: Agua):
                agua.tiene_comportamiento(Liquido) and agua.temperatura_propia < 40

            condicion1 = Condicion(
                evaluar=condicion1_funcion,
                evento=None,
                nombre="agua_liquida",
            )

            def resultado_MASA_PAN(
                destino: Elemento,
                ingredientes: list[
                    Ingrediente
                ],  # la lista de ingredientes CONCRETOS a usar
            ):
                masa_pan = Masa_Pan()
                for ingrediente in ingredientes:
                    ingrediente.eliminar()

            MASA_PAN = Receta(
                nombre="MASA_PAN",
                ingredientes=[Agua, Harina],
                condiciones=[condicion1],
                accion=Mezclar,  # solo indica cual es el trigger
                resultado=resultado_MASA_PAN,  # funcion que se ejecuta cuando la receta se lleva a cabo
            )

            # ----------------------------------------------------------------------------
            EMBUTIDO_CRUDO = Receta(
                nombre="EMBUTIDO_CRUDO",
                ingredientes=[],
                condiciones=[],
                accion=Mezclar,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            MANTEQUILLA = Receta(
                nombre="MANTEQUILLA",
                ingredientes=[],
                condiciones=[],
                accion=Mezclar,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            CALDO = Receta(
                nombre="CALDO",
                ingredientes=[],
                condiciones=[],
                accion=Mezclar,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            GACHAS = Receta(
                nombre="GACHAS",
                ingredientes=[],
                condiciones=[],
                accion=Mezclar,
                resultado=None,
            )

        class Salud:

            # ----------------------------------------------------------------------------
            CATAPLASMA = Receta(
                nombre="CATAPLASMA",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            UGUENTO = Receta(
                nombre="UGUENTO",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            JABON = Receta(
                nombre="JABON",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            VENDAJE_ESTERILIZADO = Receta(
                nombre="VENDAJE_ESTERILIZADO",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

        class Materiales: ...

        class Ingredientes:

            # ----------------------------------------------------------------------------
            POLVORA = Receta(
                nombre="POLVORA",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            HARINA = Receta(
                nombre="HARINA",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            LEVADURA = Receta(
                nombre="LEVADURA",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

        class Construccion:

            # ----------------------------------------------------------------------------
            CEMENTO = Receta(
                nombre="CEMENTO",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            HORMIGON = Receta(
                nombre="HORMIGON",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

        class Tintes:

            # ----------------------------------------------------------------------------
            # NEGRO
            TINTE_CARBON = Receta(
                nombre="HORMIGON",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
            # ROJO
            TINTE_SANGRE = Receta(
                nombre="HORMIGON",
                ingredientes=[],
                condiciones=[],
                accion=None,
                resultado=None,
            )

            # ----------------------------------------------------------------------------
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

    #
    #   clases con Condicion como trigger
    #
    # class Llover
