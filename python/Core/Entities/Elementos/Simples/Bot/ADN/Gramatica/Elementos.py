from collections import defaultdict
from typing import List

from Core.Entities.Elementos.Simples.Bot.ADN.empaquetador import (
    PackedDNA,
    ADNAgotadoError,
    ADNSobranteError,
)
'''
    # ejemplo de uso:

    # compilacion normal
    with Genoma.desde_fichero("adn.bin", chunk_size=4096) as genoma:
        codigo = nodo_programa.compilar(genoma)
    # → ADNSobranteError si queda ADN
    # → ADNAgotadoError si se agota antes de terminar
    # → fichero cerrado en cualquier caso

    # consulta de rango sin afectar la compilacion
    adn_trozo = genoma.leer_rango(0, 99)
'''



class Genoma:
    """
    Clase usada para individualizar la gramatica de un bot,
    con su propio contexto.
    Soporta lectura desde fichero por chunks o desde lista en memoria.
    """

    def __init__(self, packed_dna: PackedDNA):
        self._dna = packed_dna
        self.librerias_usadas = defaultdict(set)
        self.contexto = Genoma.Contexto(self)

    # --------------------------------------------------
    # constructores alternativos
    # --------------------------------------------------
    @classmethod
    def desde_lista(cls, adn: list[int]) -> "Genoma":
        """Crea un Genoma desde una lista de enteros en memoria."""
        dna = PackedDNA()
        dna.from_list(adn)
        # simular streaming sobre memoria usando next() via buffer
        # reutilizamos el mismo mecanismo: cargamos todo como buffer
        dna._buf = adn
        dna._buf_pos = 0
        dna._global_pos = 0
        dna.length = len(adn)
        dna._file = object()  # centinela para que next() no falle por _file is None
        # parchear next para que use el buffer directamente
        return cls(dna)

    @classmethod
    def desde_fichero(cls, filepath: str, chunk_size: int = 4096) -> "Genoma":
        """
        Abre el fichero y crea el Genoma para lectura por chunks.
        Usar con context manager:
            with Genoma.desde_fichero("adn.bin") as genoma:
                nodo.compilar(genoma)
        """
        dna = PackedDNA()
        dna.open(filepath, chunk_size)
        return cls(dna)

    # --------------------------------------------------
    # context manager — cierra fichero y verifica ADN sobrante
    # --------------------------------------------------
    def __enter__(self) -> "Genoma":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # solo verificar sobrante si no hay ya una excepcion activa
            if exc_type is None:
                restantes = self._dna.elementos_restantes()
                if restantes > 0:
                    raise ADNSobranteError(
                        f"Compilacion terminada pero quedan {restantes} "
                        f"elementos de ADN sin consumir "
                        f"(posicion {self._dna._global_pos} "
                        f"de {self._dna.length})"
                    )
        finally:
            self._dna.close()

        return False  # nunca suprime excepciones

    # --------------------------------------------------
    # acceso al ADN sobrante para consulta externa
    # --------------------------------------------------
    def leer_rango(self, inicio: int, fin: int) -> list[int]:
        """Delega en PackedDNA para leer un rango por offset absoluto."""
        return self._dna.leer_rango(inicio, fin)

    class Contexto:

        def __init__(self, genoma: "Genoma"):
            self._dna = genoma._dna
            self.librerias_usadas = genoma.librerias_usadas
            self.ite = 0  # indice global absoluto — espejo de _dna._global_pos

        def next_adn(self) -> int:
            """
            Consume el siguiente elemento del ADN.
            Lanza ADNAgotadoError si el ADN se agota durante la compilacion.
            """
            valor = self._dna.next()  # lanza ADNAgotadoError si procede
            self.ite += 1  # mantener ite sincronizado con _global_pos
            return valor

        def get_current_adn(self) -> int:
            """Devuelve el elemento actual sin consumirlo."""
            if self._dna._buf_pos < len(self._dna._buf):
                return self._dna._buf[self._dna._buf_pos]
            raise ADNAgotadoError(
                f"No hay elemento actual — ADN agotado en posicion {self.ite}"
            )

        def get_imports(self) -> str:
            partes = []
            for libreria, paquetes in self.librerias_usadas.items():
                if libreria is None:
                    for paquete in sorted(paquetes):
                        partes.append(f"import {paquete}")
                else:
                    paquetes_str = ", ".join(sorted(paquetes))
                    partes.append(f"from {libreria} import {paquetes_str}")
            return "\n".join(partes)


class Nodo:
    """
    Clase general. Se usa para definir la gramatica.
    """

    class Eleccion:

        def __init__(self, opciones: list):
            self.opciones = opciones

        def compilar(self, genoma: Genoma, padre: "Nodo" = None):
            item = self.opciones[genoma.contexto.next_adn()]

            if isinstance(item, str):
                return item

            if isinstance(item, list):
                nodo_lista = Nodo("_eleccion_lista", item)
                resultado = nodo_lista.compilar(genoma)
                if padre is not None:
                    padre.hijos.append(nodo_lista)
                return resultado

            if callable(item):
                nodo = item()
                resultado = nodo.compilar(genoma)
                if padre is not None:
                    padre.hijos.append(nodo)
                return resultado

            if hasattr(item, "compilar"):
                return item.compilar(genoma, padre)

            raise TypeError(f"Elemento no reconocido en Eleccion: {type(item)}")

    class Tab:

        def __init__(self, items):
            if callable(items):
                self.items = [items]
            else:
                self.items = items

        def compilar(self, genoma: Genoma, padre: "Nodo" = None):
            partes = []

            for item in self.items:
                partes.append("\t")

                if isinstance(item, str):
                    partes.append(item)
                    continue

                if callable(item):
                    nodo = item()
                    resultado = nodo.compilar(genoma)
                    if padre is not None:
                        padre.hijos.append(nodo)
                    partes.append(resultado)
                    continue

                if hasattr(item, "compilar"):
                    partes.append(item.compilar(genoma, padre))
                    continue

                if isinstance(item, list):
                    raise TypeError("No se permiten listas directas en Tab")

                raise TypeError(f"Elemento no reconocido en Tab: {type(item)}")

            return "".join(partes)

    class Import:

        def __init__(self, libreria: str, paquetes: list):
            self.libreria = libreria
            self.paquetes = paquetes

        def _agregar(self, libreria: str, paquetes: list, librerias_usadas: dict):
            for paquete in paquetes:
                librerias_usadas[libreria].add(paquete)

        def compilar(self, genoma: Genoma, padre: "Nodo" = None):
            if self.libreria is None and self.paquetes is None:
                return genoma.contexto.get_imports()

            self._agregar(
                self.libreria, self.paquetes, genoma.contexto.librerias_usadas
            )
            return ""

    def __init__(self, nombre: str, items: list):
        self.nombre = nombre
        self.items = items
        self.hijos: List["Nodo"] = []
        self.adn_offset_min = -1
        self.adn_offset_max = -1

    def compilar(self, genoma: Genoma) -> str:
        # registrar inicio antes de compilar nada
        self.adn_offset_min = genoma.contexto.ite

        partes = []

        for elemento in self.items:

            if isinstance(elemento, str):
                partes.append(elemento)
                continue

            if callable(elemento):
                nodo = elemento()
                resultado = nodo.compilar(genoma)
                self.hijos.append(nodo)
                partes.append(resultado)
                continue

            if isinstance(elemento, Nodo.Eleccion):
                partes.append(elemento.compilar(genoma, padre=self))
                continue

            if isinstance(elemento, Nodo.Tab):
                partes.append(elemento.compilar(genoma, padre=self))
                continue

            if isinstance(elemento, Nodo.Import):
                partes.append(elemento.compilar(genoma, padre=self))
                continue

            if isinstance(elemento, Nodo):
                resultado = elemento.compilar(genoma)
                self.hijos.append(elemento)
                partes.append(resultado)
                continue

            if isinstance(elemento, list):
                nodo_lista = Nodo("_lista", elemento)
                resultado = nodo_lista.compilar(genoma)
                self.hijos.extend(nodo_lista.hijos)
                partes.append(resultado)
                continue

            raise TypeError(
                f"Elemento no reconocido en compilar [{self.nombre}]: {type(elemento)}"
            )

        # registrar fin tras compilar todo — ite apunta al siguiente sin consumir
        self.adn_offset_max = genoma.contexto.ite - 1

        return "".join(partes)

    def get_hijos(self) -> List["Nodo"]:
        return self.hijos

    def get_nombre(self) -> str:
        return self.nombre

    def get_offsets(self) -> tuple:
        return self.adn_offset_min, self.adn_offset_max

    def imprimir_arbol(self, nivel: int = 0):
        """
        Imprime el arbol de nodos con sus offsets para depuracion.
        Ejemplo:
            _programa: [0 - 42]
              _funciones: [0 - 20]
                _funcion: [0 - 10]
              _codigo: [21 - 42]
        """
        sangria = "  " * nivel
        print(
            f"{sangria}{self.nombre}: [{self.adn_offset_min} - {self.adn_offset_max}]"
        )
        for hijo in self.hijos:
            if isinstance(hijo, Nodo):
                hijo.imprimir_arbol(nivel + 1)

    def __repr__(self):
        return (
            f"Nodo({self.nombre!r}, "
            f"offsets=[{self.adn_offset_min}-{self.adn_offset_max}], "
            f"hijos={len(self.hijos)})"
        )
