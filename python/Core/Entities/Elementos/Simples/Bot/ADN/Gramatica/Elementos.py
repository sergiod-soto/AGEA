from collections import defaultdict
from typing import List, Union



class Genoma:
    """
    Clase usada para individualizar la gramatica de un bot,
    con su propio contexto
    """

    def __init__(self, adn: list):
        self.adn = adn
        self.librerias_usadas = defaultdict(set)
        self.contexto = Genoma.Contexto(self)

    def get_adn(self):
        pass

    def add_gen(self):
        pass

    class Contexto:

        def __init__(self, genoma: "Genoma"):
            self.adn = genoma.adn
            self.librerias_usadas = genoma.librerias_usadas
            self.ite = 0

        def next_adn(self):
            elemento = self.adn[self.ite]
            self.ite += 1
            return elemento

        def get_current_adn(self):
            return self.adn[self.ite]

        def get_imports(self):
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

        def compilar(self, genoma: Genoma):
            item = self.opciones[genoma.contexto.next_adn()]

            if isinstance(item, str):
                return item

            if hasattr(
                item, "compilar"
            ):  # es Eleccion, Nodo o Tab. Ej: Nodo.Eleccion([ _dato, ... ,_variable])
                return item.compilar(genoma)

            if callable(item):  # es una funcion. Ej: _dato
                return item().compilar(genoma)

            if isinstance(
                item, list
            ):  # Array. Se puede encontrar como conjunto de elementos que conforman una posibilidad en una eleccion. Ej: [_a(), _b()]
                return Nodo._compilar_lista(item, genoma)

            raise TypeError(f"Elemento no reconocido: {type(item)}")

        def get_nodos(self, genoma: Genoma):
            eleccion = self.opciones[genoma.contexto.get_current_adn()]

            if isinstance(eleccion, str):
                return None

            if hasattr(eleccion, "get_nodos"):
                return [eleccion.get_nodos(genoma)]

            if callable(eleccion):
                return [eleccion()]

            if isinstance(eleccion, list):
                return Nodo._get_hijos_lista(eleccion, genoma)

    class Tab:
        def __init__(self, items: list):
            self.items = items

        def compilar(self, genoma: Genoma):
            partes = []
            hijos = []

            for item in self.items:

                partes.append("\t")

                if isinstance(item, str):
                    partes.append(item)
                    continue

                if hasattr(item, "compilar"):
                    partes.append(item.compilar(genoma))
                    continue

                if callable(item):
                    partes.append(item().compilar(genoma))
                    hijos.append([item()])
                    continue

                if isinstance(item, list):
                    raise TypeError(f"No se permiten listas en la lista de Tab")

                raise TypeError(f"Elemento no reconocido en Tab: {type(item)}")

            return "".join(partes)

        def get_nodos(self, genoma: Genoma):
            hijos = []
            for hijo in self.items:

                if isinstance(hijo, str):
                    continue

                if hasattr(hijo, "get_nodos"):
                    hijos.append(hijo.get_nodos(genoma))
                    continue

                if callable(hijo):
                    hijos.append([hijo()])
                    continue

                if isinstance(hijo, list):
                    raise TypeError(f"No se permiten listas en la lista de Tab")

                raise TypeError(f"Elemento no reconocido en Tab: {type(hijo)}")

            return hijos

    class Import:

        def __init__(self, libreria: str, paquetes: list[str]):
            self.libreria = libreria
            self.paquetes = paquetes

        def _agregar(self, libreria: str, paquetes: list[str], librerias_usadas: set):
            for paquete in paquetes:
                self._agregar_paquete(libreria, paquete, librerias_usadas)

        def _agregar_paquete(self, libreria: str, paquete: str, librerias_usadas: set):
            librerias_usadas[libreria].add(paquete)

        def compilar(self, genoma: Genoma):
            if self.libreria is None and self.paquetes is None:
                # import vacio que indica fin de imports
                return genoma.contexto.get_imports()

            self._agregar(
                self.libreria, self.paquetes, genoma.contexto.librerias_usadas
            )
            return ""

        def get_nodos(self, genoma: Genoma):
            return None

    def __init__(self, nombre: str, items: list):

        self.nombre = nombre
        self.items = items
        self.hijos = []
        self.adn_offset_min = -1
        self.adn_offset_max = -1

    def _compilar_lista(self, lista: list, genoma: Genoma):
        partes = []

        for elemento in lista:

            if isinstance(elemento, str):
                partes.append(elemento)
                continue

            if hasattr(elemento, "compilar"):
                subhijos = elemento.get_nodos(genoma)
                if subhijos is not None and subhijos != []:
                    for hijo in subhijos:
                        if hijo is None:
                            continue
                        self.hijos.append(hijo)
                #
                partes.append(elemento.compilar(genoma))

                continue

            if callable(elemento):
                self.hijos.append(elemento())
                #
                partes.append(elemento().compilar(genoma))
                continue

            if isinstance(elemento, list):
                # subhijos = Nodo._get_hijos_lista(elemento, genoma)
                # for subhijo in subhijos:
                #     self.hijos.append(subhijo)
                #
                partes.append(Nodo._compilar_lista(elemento, genoma))
                continue

            raise TypeError(
                f"Elemento no reconocido en _compilar_lista: {type(elemento)}"
            )

        return "".join(partes)

    def _get_hijos_lista(self, lista: list, genoma: Genoma):
        hijos = []

        for item in lista:
            if isinstance(item, str):
                continue

            if hasattr(item, "get_nodos"):
                hijos.append(item.get_nodos(genoma))
                continue

            if callable(item):
                hijos.append([item()])
                continue

            if isinstance(item, list):
                hijos.append(self._get_hijos_lista(item, genoma))
                continue

        return hijos

    def get_hijos(self) -> List["Nodo"]:
        return self.hijos

    def get_nombre(self):
        return self.nombre

    def compilar(self, genoma: Genoma):
        return Nodo._compilar_lista(self, self.items, genoma)
