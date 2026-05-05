from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Es_De_Dia(Condicion):
    def __init__(self, umbral: float = 0.5):
        self.umbral = umbral

    def evaluar(self) -> bool:
        return self.mundo.get_luz() >= self.umbral


class Es_De_Noche(Condicion):
    def __init__(self, umbral: float = 0.5):
        self.umbral = umbral

    def evaluar(self) -> bool:
        return self.mundo.get_luz() < self.umbral


class Es_Hora(Condicion):
    def __init__(self, hora_inicio: float, hora_fin: float):
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin

    def evaluar(self) -> bool:
        hora = self.mundo.get_hora()
        return self.hora_inicio <= hora <= self.hora_fin


class Es_Estacion(Condicion):
    def __init__(self, estacion):
        self.estacion = estacion

    def evaluar(self) -> bool:
        return self.mundo.get_estacion() == self.estacion


class Es_Clima(Condicion):
    def __init__(self, clima):
        self.clima = clima

    def evaluar(self) -> bool:
        return self.mundo.get_clima() == self.clima


class Hay_Lluvia(Condicion):
    def evaluar(self) -> bool:
        return self.mundo.get_clima() == Clima.LLUVIA


class Hay_Nieve(Condicion):
    def evaluar(self) -> bool:
        return self.mundo.get_clima() == Clima.NIEVE


class Hay_Viento(Condicion):
    def evaluar(self) -> bool:
        return self.mundo.get_clima() == Clima.VIENTO


class Temperatura_Zona(Condicion):
    def __init__(self, op, valor: float):
        self.op = op
        self.valor = valor

    def evaluar(self) -> bool:
        return self.op(self.mundo.get_temperatura_zona(), self.valor)
