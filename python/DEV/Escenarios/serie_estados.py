# Dev/Escenarios/serie_estados.py
"""
Serie_Estados — máquina de estados para inicializar el mundo (o
manipularlo manualmente durante testeo). Cada "estado" agrupa
acciones que se ejecutan todas juntas en un tick; do() avanza al
siguiente estado en cada llamada.

Desde que Crear_Elemento pasó a hablar por gRPC con Logica_Mundo
(ver Crear_Elemento más abajo), el motor tiene que admitir acciones
async. Se admite tanto una función normal como una async: ejecutar()
sólo hace `await` si el resultado de llamarla es awaitable, así no
rompe nada que ya usara acciones síncronas (p.ej. Crear_Bot,
Mover_Elemento, que siguen operando sobre datos.bots local).
"""

import inspect
from functools import partial

from Core.Entities.Elementos.elemento import Elemento
from Core.Entities.Elementos.Simples.Bot.Bot import Bot
from Core.Entities.Mundo import datos
from Core.Entities.entity import Modos
from Infraestructura.Gestores.Transporte.logica_mundo_client import LogicaMundoClient


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

        async def ejecutar(self):
            """
            Ejecuta cada función del estado y devuelve lista con sus
            retornos. Si una función es async (o devuelve un
            awaitable, como una closure que llama a una async def),
            se espera su resultado; si es síncrona, se usa tal cual.
            """
            resultados = []
            for f in self.funciones:
                resultado = f()
                if inspect.isawaitable(resultado):
                    resultado = await resultado
                resultados.append(resultado)
            return resultados

    def __init__(self, logica_mundo_client: LogicaMundoClient):
        # Cliente propio hacia Logica_Mundo -- ver decisión: Serie_Estados
        # no reutiliza ClientesRemotos (eso es de Comunicaciones_Remoto,
        # pensado para el puente con Unity, sin relación con esto).
        self._logica = logica_mundo_client

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
    async def do(self):
        """Ejecuta el siguiente estado, si lo hay"""

        if len(self.estados) > 0:
            estado = self.estados.pop(0)
            print(f"🟦 Ejecutando estado [{self.indice_actual}]")
            resultados = await estado.ejecutar()
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
    async def Mover_Elemento_Logica(
        self, elemento, pos_destino: tuple[int, int], type_id: str = "resto"
    ):
        """
        "Mueve" un elemento ya creado en Logica_Mundo a pos_destino.

        AVISO: no existe un RPC de movimiento en LogicaMundoClient
        (ver conversación) -- esto se implementa como
        eliminar_elemento(pos_origen) + crear_elemento(pos_destino),
        reutilizando el mismo id_elemento. No es atómico: si falla el
        crear_elemento tras el eliminar_elemento, el elemento queda
        eliminado del mundo. Aceptable para testeo, no para producción
        sin revisar esa atomicidad.
        """
        import json

        pos_origen = elemento.casilla
        ok, error = await self._logica.eliminar_elemento(
            pos_origen, elemento.id_elemento
        )
        if not ok:
            raise RuntimeError(
                f"Mover_Elemento_Logica: eliminar_elemento falló en {pos_origen}: {error}"
            )

        elemento.casilla = pos_destino
        elemento_bytes = json.dumps(elemento.serializar(modo=Modos.transporte)).encode()
        ok, error = await self._logica.crear_elemento(
            pos_destino, type_id, elemento_bytes
        )
        if not ok:
            raise RuntimeError(
                f"Mover_Elemento_Logica: crear_elemento falló en {pos_destino}: {error}"
            )

        print(
            f"\t⚪ Serie_Estados.Mover_Elemento_Logica: elemento {elemento.id_elemento} -> {pos_destino}"
        )
        return elemento

    # endregion
    #####################################################################

    # region   ELEMENTO
    async def Crear_Elemento(
        self, clase, casilla: tuple[int, int], type_id: str = "resto", **kwargs
    ):
        """
        Crea un elemento real en Logica_Mundo (vía gRPC): pide un id
        nuevo con AsignarId, instancia `clase` con ese id, lo
        serializa igual que lo hace el propio LogicaMundoClient
        internamente (modo=Modos.transporte) y lo registra con
        CrearElemento.

        type_id es el SLOT de la celda en Logica_Mundo ("suelo",
        "bot", o cualquier otra cosa -> cae en "resto"), no la clase
        de Python -- por eso el valor por defecto es "resto", el que
        corresponde a un elemento que no es ni suelo ni bot.
        """
        import json

        id_elemento = await self._logica.asignar_id()
        elemento = clase(id_elemento=id_elemento, casilla=casilla, **kwargs)

        elemento_bytes = json.dumps(elemento.serializar(modo=Modos.transporte)).encode()
        ok, error = await self._logica.crear_elemento(casilla, type_id, elemento_bytes)
        if not ok:
            raise RuntimeError(
                f"Crear_Elemento: crear_elemento falló para {clase.__name__} "
                f"(id={id_elemento}) en {casilla}: {error}"
            )

        print(
            f"\t⚪ Serie_Estados.Crear_Elemento: {clase.__name__} id={id_elemento} en {casilla}"
        )
        return elemento

    async def Crear_Suelo(self, clase, casilla: tuple[int, int], **kwargs):
        """
        Crea un Suelo en `casilla`. Es un envoltorio fino sobre
        Crear_Elemento con type_id="suelo" fijo -- a nivel de
        Logica_Mundo un Suelo SIGUE viajando por el mismo RPC
        CrearElemento y viviendo en el mismo self._elements que
        cualquier otro elemento (ver LogicaMundo.crear_elemento: solo
        cambia a qué campo de Celda se cuelga según type_id). Lo único
        que hace esta función es evitar que quien escribe un escenario
        tenga que acordarse de pasar "suelo" a mano cada vez.

        `clase` es obligatoria y sin valor por defecto (decisión
        explícita: no hay un tipo de terreno "por defecto" razonable --
        Suelo, Suelo_Cesped, etc. deben elegirse siempre a propósito).
        """
        return await self.Crear_Elemento(clase, casilla, type_id="suelo", **kwargs)

    # endregion
    #####################################################################

    # region   BOT
    def Crear_Bot(self, id_elemento, id_bot, casilla):
        # AVISO: a diferencia de Crear_Elemento, esto sigue escribiendo
        # solo en datos.bots (local a este proceso) -- no llega a
        # Logica_Mundo ni por tanto a Unity. Es el mismo problema que
        # se identificó al principio de esta conversación; no se ha
        # tocado porque no era el objetivo de este cambio, pero un bot
        # creado así no será visible para el resto del sistema.
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
        return self.Crear_Bot(0, id_bot, (0, 0))
        # (se quitó la asignación duplicada a datos.bots[id_bot]: ya la
        # hace Crear_Bot, hacerla dos veces era ruido sin efecto)

    # endregion
    #####################################################################
