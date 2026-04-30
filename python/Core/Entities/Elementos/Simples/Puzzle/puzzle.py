from abc import ABC, abstractmethod
from typing import Callable
from bitarray import bitarray
from Core.Entities.Elementos.Simples.Puzzle.premio import Premio

from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple

MAX_BOTS: int = 1_000_000


class Puzzle(ABC, Elemento_Simple):

    class Estado:
        def __init__(self, opciones: list[Callable]):
            self.opciones = opciones

        def get_opciones(self) -> list[Callable]:
            return self.opciones

    class MaquinaEstados:
        def __init__(
            self,
            estados: list["Puzzle.Estado"],
            estado_inicial: "Puzzle.Estado" = None,
            bot_id: int = None,  #   obtiene el id del bot que lo usa si el puzzle es personal
        ):
            self.estados = estados
            self.estado_inicial = estado_inicial or estados[0]
            self.estado_actual = self.estado_inicial
            self.historial: list[Callable] = []
            self.bot_id = bot_id

        def get_estado_actual(self) -> "Puzzle.Estado":
            return self.estado_actual

        def ejecutar_accion(self, accion: Callable) -> "Puzzle.Estado":
            resultado = accion()
            self.historial.append(accion)
            self.estado_actual = resultado
            return self.estado_actual

        def reset_maquina(self):
            self.estado_actual = self.estado_inicial
            self.historial.clear()

    class PuzzleParams:
        def __init__(
            self,
            nombre: str,
            premios: list[Premio],
            estados: list["Puzzle.Estado"],
            estado_inicial: "Puzzle.Estado" = None,
            cd: int = 0,
            abstracto: bool = False,
        ):
            self.nombre = nombre
            self.cd = cd
            self.premios = premios
            self.estados = estados
            self.estado_inicial = estado_inicial
            self.abstracto = abstracto

    # _____________________________________________________________________________________________

    def __init__(self, parametros: PuzzleParams):
        self.parametros = parametros
        self.maquinasEstados: dict[int, Puzzle.MaquinaEstados] = {}
        self._resuelto_por = bitarray(MAX_BOTS)
        self._resuelto_por.setall(0)

    def iniciar_bot(self, bot_id: int = None) -> None:
        """El mundo llama a esto cuando un bot empieza a interactuar con el puzzle."""
        self.maquinasEstados[bot_id] = Puzzle.MaquinaEstados(
            self.parametros.estados,
            self.parametros.estado_inicial,
            bot_id,
        )

    def es_abstracto(self):
        return self.parametros.abstracto

    def abandonar_bot(self, bot_id: int) -> None:
        """El mundo llama a esto cuando un bot abandona el puzzle. Resetea su progreso."""
        if bot_id in self.maquinasEstados:
            del self.maquinasEstados[bot_id]

    def get_list_acciones(self, bot_id: int) -> list[Callable]:
        """Retorna la lista de posibles acciones del estado actual para un bot."""
        return self.maquinasEstados[bot_id].get_estado_actual().get_opciones()

    def marcar_resuelto(self, bot_id: int) -> None:
        self._resuelto_por[bot_id] = 1

    def ha_resuelto(self, bot_id: int) -> bool:
        return self._resuelto_por[bot_id]

    def actualizar_ids(self, reasignaciones: list[tuple[int, int]]) -> None:
        valores = {
            id_viejo: self._resuelto_por[id_viejo] for id_viejo, _ in reasignaciones
        }
        for id_viejo, id_nuevo in reasignaciones:
            self._resuelto_por[id_nuevo] = valores[id_viejo]
            self._resuelto_por[id_viejo] = 0

        maquinas_nuevas = {}
        for id_viejo, id_nuevo in reasignaciones:
            if id_viejo in self.maquinasEstados:
                maquinas_nuevas[id_nuevo] = self.maquinasEstados.pop(id_viejo)
        self.maquinasEstados.update(maquinas_nuevas)

    @abstractmethod
    def dar_premio(self, premio: Premio):
        pass

    @abstractmethod
    def get_estado_actual(self, bot_id: int):
        pass

    @abstractmethod
    def check(self, bot_id: int) -> bool:
        pass
