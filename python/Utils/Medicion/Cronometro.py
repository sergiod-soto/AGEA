import time


class Cronometro:
    inicio = None

    def start_cronometro(self):
        self.inicio = time.perf_counter()

    def stop_cronometro(self):
        fin = time.perf_counter()
        return fin - self.inicio
