import time


class Cronometro:
    '''
        Mide el tiempo en segundos
    '''
    
    inicio = None

    def start_cronometro(self):
        self.inicio = time.perf_counter()

    def get_cronometro(self):
        fin = time.perf_counter()
        return fin - self.inicio
