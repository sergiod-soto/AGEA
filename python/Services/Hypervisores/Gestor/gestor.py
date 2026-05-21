import threading
import time


class Gestor:

    def __init__(self, mundo):
        self.mundo = mundo

        self.hypervisores = {}

        self.tick_actual = 0

        self.tick_rate = 20

        self._acciones_pendientes = []

        self._lock = threading.Lock()

    # ======================================================
    # Registro
    # ======================================================

    def registrar_hypervisor(self, hv):
        self.hypervisores[hv.bot_id] = hv

    # ======================================================
    # Recepción de acciones
    # ======================================================

    def recibir_acciones(self, acciones):
        with self._lock:
            self._acciones_pendientes.extend(acciones)

    # ======================================================
    # Loop principal
    # ======================================================

    def start(self):
        intervalo = 1 / self.tick_rate

        while True:
            inicio = time.time()

            self._procesar_tick()

            elapsed = time.time() - inicio
            restante = intervalo - elapsed

            if restante > 0:
                time.sleep(restante)

    def _procesar_tick(self):
        self.tick_actual += 1

        self._aplicar_acciones()

        self.mundo.actualizar()

        self._distribuir_observaciones()

    # ======================================================
    # Acciones
    # ======================================================

    def _aplicar_acciones(self):
        with self._lock:
            acciones = self._acciones_pendientes
            self._acciones_pendientes = []

        for accion in acciones:
            self.mundo.aplicar_accion(accion)

    # ======================================================
    # Distribución
    # ======================================================

    def _distribuir_observaciones(self):
        for bot_id, hv in self.hypervisores.items():

            obs = self.mundo.generar_observacion(bot_id)

            hv.recibir_tick(
                tick=self.tick_actual,
                observation=obs,
            )
