# Dev/Escenarios/serie_estados.py

from functools import partial

from Core.Entities.Elementos.elemento import Elemento
from Core.Entities.Elementos.Simples.Bot.Bot import Bot
from Core.Entities.Mundo import datos


class Serie_Estados:

    class Estado:

        def __init__(self, funciones):
            # Cada elemento puede ser una función ya preparada (con partial o lambda)
            # o una tupla (func, args, kwargs)
            self.funciones = []
            for f in funciones:
                if callable(f):
                    self.funciones.append(f)
                elif isinstance(f, tuple):
                    func, args, kwargs = f
                    self.funciones.append(partial(func, *args, **kwargs))
                else:
                    raise ValueError(
                        "Cada función debe ser callable o una tupla (func, args, kwargs)"
                    )

        def ejecutar(self):
            """Ejecuta cada función del estado y devuelve lista con sus retornos."""
            resultados = []
            for f in self.funciones:
                resultados.append(f())
            return resultados

    def __init__(self):
        self.estados = []
        self.finalizado = False
        self.indice_actual = 0

    #   anhade nuevo estado
    def add(self, funciones):
        """Añade un nuevo estado (lista de funciones o tuplas)"""
        print("(➕) Añadiendo estado")

        estado = self.Estado(funciones)
        self.estados.append(estado)
        self.finalizado = False

    # ejecuta el estado actual y pasa al siguiente
    def do(self):
        """Ejecuta el siguiente estado, si lo hay"""

        if len(self.estados) > 0:
            estado = self.estados.pop(0)
            print(f"🟦 Ejecutando estado [{self.indice_actual}]")
            resultados = estado.ejecutar()
            self.indice_actual += 1
            return resultados
        else:
            if self.finalizado == False:
                print("✅ Todos los estados completados")
                self.finalizado = True
            return

    # #####################################################################
    # Instrucciones para la maquina de estados:

    # region GENERAL
    def Mover_Elemento(self, elemento: Elemento, casilla: tuple[int, int]):

        print(
            "\t⚪ Serie_Estados.Mover_Elemento: Moviendo elemento a ("
            + str(casilla[0])
            + ", "
            + str(casilla[1])
            + ")"
        )
        elemento.casilla = casilla
        return elemento

    # endregion
    #####################################################################

    # region   BOT
    def Crear_Bot(self, id_elemento, id_bot, casilla):

        print("\t⚪ Serie_Estados.Crear_Bot")
        bot = Bot(
            id_elemento=id_elemento,
            stats_script=None,
            id_bot=id_bot,
            tamanho=1,
            casilla=casilla,
            capa=1,
            rotacion=0,
        )
        datos.bots[id_bot] = bot
        return bot

    def Crear_Bot_Basico(self, id_bot):

        print("\t⚪ Serie_Estados.Creando bot basico. ID: [" + id_bot + "]")
        bot = self.Crear_Bot(0, id_bot, (0, 0))
        datos.bots[id_bot] = bot
        return bot

    # endregion
