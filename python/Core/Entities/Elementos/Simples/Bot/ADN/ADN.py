from array import array
import sys
import Core.Entities.Elementos.Simples.Bot.ADN.GuiaNodos as Guia


class ADN_Lineal:
    """
    El ADN que se compila al querer obtener el codigo asociado.
    Se obtiene a partir de "ADN_Genes"
    """

    def __init__(self, genes=None):
        if genes is None:
            genes = [0]
        self.genes = array("B", genes)
        self.iterator = 0

    def next_chromosome(self):
        if self.iterator >= len(self.genes):
            raise IndexError(
                f"Error.\nIndexOutOfBoundException.\n\tIterator: {self.iterator}, len(genes): {len(self.genes)}\n"
            )
        value = self.genes[self.iterator]
        self.iterator += 1
        return value

    def get_size(self):
        return sys.getsizeof(self.genes)


class Gen:
    """
    Representa el gen (seccion) del ADN de un bot, con sus hijos.
    """

    genoma:"Genoma" = None

    def __init__(self, id: list[int], nombre: str):
        if self.genoma is None:
            Exception('Falta instanciar "Genoma"')
        self.nombre = nombre
        try:
            self.guia = Guia.guia[nombre]
        except Exception as e:
            print(f"Nombre ({nombre}) de 'Gen' no encontrado en 'Guia'")
        self.id = id
        self.hijos = []
        self.items = []

    def get_adn(self):
        adn = []
        for item in self.items:
            if isinstance(item, Gen):
                adn.extend(item.get_adn())
            else:
                adn.append(item)
        return adn

    def get_id(self):
        return self.id

    def get_id_string(self):
        id_string = ""
        partes = []
        for item in self.id:
            partes.append(str(item))
            partes.append(".")
        partes.pop()

        return id_string.join(partes)

    def get_hijos(self):
        return self.hijos

    def add_elemento(self, elemento):
        self.items.append(elemento)
        if isinstance(elemento, Gen):
            self.hijos.append(elemento)
            self.genoma.genes[elemento.get_id_string()] = elemento
            return
        if isinstance(elemento, int):
            return
        raise Exception("Los genes solo pueden contener nodos o numeros enteros")

    def get_size(self):
        return (
            sys.getsizeof(self.hijos)
            + sys.getsizeof(self.id)
            + sys.getsizeof(self.items)
        )

    def print_gen(self):
        output = ""
        partes = []

        partes.append("[")

        for item in self.guia:
            if isinstance(item, Gen):
                partes.append("Gen[" + item.nombre + "]")
                partes.append(", ")
            else:
                partes.append(str(item))
                partes.append(", ")
        partes.pop()
        partes.append("]")

        output = output.join(partes)

        return output


class Genoma:

    def __init__(self):
        self.genes = {}
        Gen.genoma = self

    def get_adn(self, nodo: str = None):
        if nodo is None:
            return self.genes["0"].get_adn()
        return self.genes[nodo].get_adn()

    def get_size(self):
        total = 0
        for gen in self.genes.values:
            total += gen.get_size()
        return total

    def add_gen(self, gen: "Gen"):
        if gen.get_id_string() in self.genes:
            Exception(f"Nodo con id ({gen.get_id()}) duplicado.")
        self.genes[gen.get_id_string()] = gen
