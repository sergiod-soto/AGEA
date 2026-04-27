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

        def compilar(self, genoma: Genoma, padre: "Nodo" = None):
            item = self.opciones[genoma.contexto.next_adn()]

            if isinstance(item, str):
                return item

            if isinstance(item, list):
                # array de elementos dentro de una eleccion: Nodo.Eleccion([[_a, _b], _c])
                nodo_lista = Nodo("_eleccion_lista", item)
                resultado = nodo_lista.compilar(genoma)
                if padre is not None:
                    padre.hijos.append(nodo_lista)
                return resultado

            if callable(item):
                # funcion de gramatica: _dato, _variable, etc.
                nodo = item()
                resultado = nodo.compilar(genoma)
                if padre is not None:
                    padre.hijos.append(nodo)
                return resultado

            if hasattr(item, "compilar"):
                # Eleccion, Tab, Import anidados
                return item.compilar(genoma, padre)

            raise TypeError(f"Elemento no reconocido en Eleccion: {type(item)}")

        def get_nodos(self, genoma: Genoma):
            # mantenido por compatibilidad, pero ya no es necesario en el flujo principal
            return None

    class Tab:

        def __init__(self, items):
            # items puede ser un callable (funcion de gramatica) o una lista
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

        def get_nodos(self, genoma: Genoma):
            return None

    class Import:

        def __init__(self, libreria: str, paquetes: list):
            self.libreria = libreria
            self.paquetes = paquetes

        def _agregar(self, libreria: str, paquetes: list, librerias_usadas: dict):
            for paquete in paquetes:
                librerias_usadas[libreria].add(paquete)

        def compilar(self, genoma: Genoma, padre: "Nodo" = None):
            if self.libreria is None and self.paquetes is None:
                # import vacio — senial de fin de imports, vuelca lo acumulado
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
        self.hijos: List["Nodo"] = []
        self.adn_offset_min = -1
        self.adn_offset_max = -1

    def compilar(self, genoma: Genoma) -> str:
        partes = []

        for elemento in self.items:

            if isinstance(elemento, str):
                partes.append(elemento)
                continue

            if callable(elemento):
                # funcion de gramatica: _dato, _variable, etc.
                nodo = elemento()
                resultado = nodo.compilar(genoma)   # puebla nodo.hijos recursivamente
                self.hijos.append(nodo)             # guardamos ya con sus hijos
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
                # nodo instanciado directamente
                resultado = elemento.compilar(genoma)
                self.hijos.append(elemento)
                partes.append(resultado)
                continue

            if isinstance(elemento, list):
                # array plano de elementos: [_a, _b, "texto"]
                nodo_lista = Nodo("_lista", elemento)
                resultado = nodo_lista.compilar(genoma)
                self.hijos.extend(nodo_lista.hijos)
                partes.append(resultado)
                continue

            raise TypeError(
                f"Elemento no reconocido en compilar [{self.nombre}]: {type(elemento)}"
            )

        return "".join(partes)

    def get_hijos(self) -> List["Nodo"]:
        return self.hijos

    def get_nombre(self) -> str:
        return self.nombre

    def __repr__(self):
        return f"Nodo({self.nombre!r}, hijos={len(self.hijos)})"
