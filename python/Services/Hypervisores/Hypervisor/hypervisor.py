import queue
import threading
import time
from typing import Optional


class Hypervisor(MundoAPI):

    def __init__(
        self,
        bot_id: str,
        grpc_client,
        bot_factory,
    ):
        self.bot_id = bot_id
        self.grpc_client = grpc_client

        self._tick_actual = 0
        self._ultima_observacion: Optional[Observation] = None

        self._cola_acciones = queue.Queue()

        self.bot = bot_factory(self)

        self._activo = False

    # ======================================================
    # API visible para el bot
    # ======================================================

    def mover(self, dx: int, dy: int):
        accion = Action(
            bot_id=self.bot_id,
            action_type="MOVE",
            payload={
                "dx": dx,
                "dy": dy,
            },
        )

        self._cola_acciones.put(accion)

    def observar(self) -> Observation:
        return self._ultima_observacion

    # ======================================================
    # Comunicación con gestor
    # ======================================================

    def conectar(self):
        self.grpc_client.register_hypervisor(self.bot_id)
        self._activo = True

    def recibir_tick(self, tick: int, observation: Observation):
        self._tick_actual = tick
        self._ultima_observacion = observation

        self.bot.tick()

        self._flush_acciones()

    def _flush_acciones(self):
        acciones = []

        while not self._cola_acciones.empty():
            acciones.append(self._cola_acciones.get())

        if acciones:
            self.grpc_client.send_actions(self.bot_id, acciones)

    # ======================================================
    # Infraestructura
    # ======================================================

    def start_heartbeat(self):
        def loop():
            while self._activo:
                self.grpc_client.ping(self.bot_id)
                time.sleep(2)

        threading.Thread(target=loop, daemon=True).start()