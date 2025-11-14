from Mundo import Datos
from Elementos.Bot.Bot import Bot
from Elementos.Elemento import Elemento
from functools import partial


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
        print("➕ Añadiendo estado")
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

    #
    #   GENERAL
    #
    # region
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

    #
    #   /GENERAL
    # endregion
    #####################################################################

    #
    #   BOT
    #
    # region
    def Crear_Bot(self, id_bot, adn, stats, padres, casilla):

        print("\t⚪ Serie_Estados.Crear_Bot")
        bot = Bot(id_bot, adn, stats, padres, casilla)
        Datos.bots[id_bot] = bot
        return bot

    def Crear_Bot_Basico(self, id_bot, adn):

        print("\t⚪ Serie_Estados.Creando bot basico. ID: [" + id_bot + "]")
        stats = {
            "vida": 1,
            "energia": 1,
            "curacion": 1,
            "regeneracion": 1,
            "velocidad": 1,
            "atk": 1,
            "def": 1,
            "deteccion": 1,
            "sigilo": 1,
            "edad": 1,
            "edad_adulta": 1,
            "temperatura": 1,
            "regulacion_temperatura": 1,
            "tamanho": 1,
            "grasa": 1,
            "movilidad": 1,
            "percepcion": 1,
            "armadura": 1,
            "metabolismo": 1,
            "agresividad": 1,
            "longevidad": 1,
            "temperatura_optima": 1,
            "heridas": 1,
            "focus": 1,
            "hambre": 1,
        }
        padres = {"padre": None, "madre": None}
        casilla = (0, 0)

        bot = Bot(id_bot, adn, stats, padres, casilla)
        Datos.bots[id_bot] = bot
        return bot

    def Set_Stats_Bot(self, bot: Bot, stats):

        print("\t⚪ Serie_Estados.Set_Stats_Bot")
        bot.stats = stats
        return bot

    def Set_Padres_Bot(self, bot: Bot, padre, madre):

        print("\t⚪ Serie_Estados.Set_Padres_Bot")
        bot.padres = (padre, madre)
        return bot
    
    #
    #   /BOT
    # endregion
    #####################################################################
