class Genoma:

    librerias_usadas = {}

    def __init__(self, adn: list):
        self.contexto = Genoma.Contexto()
        self.adn = adn

    def get_adn(self):
        pass

    def add_gen(self):
        pass
    
    def get_imports(self):
        partes = []
        
        for x, y in self.librerias_usadas:
            string1 = x + y
            string2 = y + x
        

    class Contexto:

        def __init__(self):
            self.adn = Genoma.get_adn()
            self.librerias_usadas = Genoma.librerias_usadas
            self.ite = 0

        def next_adn(self):
            elemento = self.adn[self.ite]
            self.ite += 1
            return elemento


class Nodo:

    class Eleccion:

        def __init__(self, opciones: list):
            self.opciones = opciones

        def compilar(self, genoma: Genoma):
            contexto = genoma.contexto
            item = self.opciones[contexto.next_adn()]

            if isinstance(item, str):
                return item

            if hasattr(
                item, "compilar"
            ):  # es Eleccion, Nodo o Tab. Ej: Nodo.Eleccion([ _dato, ... ,_variable])
                return item.compilar(contexto)

            if callable(item):  # es una funcion. Ej: _dato
                return item().compilar(contexto)

            if isinstance(
                item, list
            ):  # Array. Se puede encontrar como conjunto de elementos que conforman una posibilidad en una eleccion. Ej: [_a(), _b()]
                return Nodo.compilar_lista(item, genoma)

            raise TypeError(f"Elemento no reconocido: {type(item)}")

    class Tab:
        def __init__(self, items: list):
            self.items = items

        def compilar(self, genoma: Genoma):
            contexto = genoma.contexto
            resultado = ""
            partes = []

            for item in self.items:
                partes.append("\t")

                if isinstance(item, str):
                    partes.append(item)

                if hasattr(item, "compilar"):
                    partes.append(item.compilar(genoma))

                if callable(item):
                    partes.append(item().compilar(genoma))

                if isinstance(item, list):
                    partes.append("\t")
                    partes.append(Nodo.compilar_lista(item, genoma))

            return resultado.join(partes)

    class Import:

        def __init__(self, libreria: str, paquete: str, gestor: set, nodo: "Nodo"):
            self.nodo = nodo
           
            if gestor is None:
                raise Exception("Se ha intentado registrar un import con el set de imports a None")
            
            
            
        def compilar(self):
            return self.nodo.compilar()

    def __init__(self, nombre: str, items: list):

        self.nombre = nombre
        self.items = items

    def compilar_lista(self, lista: list, genoma: Genoma):
        resultado = ""
        partes = []

        for elemento in lista:

            if isinstance(elemento, str):
                partes.append(elemento)
                continue

            if hasattr(elemento, "compilar"):
                partes.append(elemento.compilar(genoma))
                continue

            if callable(elemento):
                partes.append(elemento().compilar(genoma))
                continue

            if isinstance(elemento, list):
                partes.append(self.compilar_lista(elemento, genoma))
                continue

        return resultado.join(partes)

    def get_nombre(self):
        return self.nombre

    def compilar(self, genoma: Genoma):
        return self.compilar_lista(self.items, genoma)
