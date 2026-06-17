# Gestores/Bots/Gestor_Bots/gestor_bots_servicer.py
import logging
from Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2_grpc as pb_grpc,
)
from Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
from Gestores.Bots.Gestor_Bots.registry import FUNCIONES

logger = logging.getLogger(__name__)


class Gestor_Bots_Servicer(pb_grpc.GestorBotsServiceServicer):

    def __init__(self, gestor: Gestor_Bots, hypervisor_client_factory=None):
        self._gestor = gestor
        self._hv_client_factory = hypervisor_client_factory
        self._dispatch = {fn.NAME: fn for fn in FUNCIONES}

    def SpawnBot(self, request, context):
        return self._dispatch["SpawnBot"].handle(self._gestor, request, context)

    def KillBot(self, request, context):
        return self._dispatch["KillBot"].handle(self._gestor, request, context)

    def BroadcastBudgets(self, request, context):
        return self._dispatch["BroadcastBudgets"].handle(self._gestor, request, context)

    def RegisterHypervisor(self, request, context):
        ack = self._dispatch["RegisterHypervisor"].handle(
            self._gestor, request, context
        )
        # El cliente de vuelta se inyecta aquí porque requiere acceso al factory,
        # que no pertenece a la lógica pura del gestor.
        if ack.ok and self._hv_client_factory is not None:
            client = self._hv_client_factory(request.address, request.port)
            self._gestor.set_hypervisor_client(request.hypervisor_id, client)
        return ack

    def UpdateHypervisorLoad(self, request, context):
        return self._dispatch["UpdateHypervisorLoad"].handle(
            self._gestor, request, context
        )

    def ListHypervisors(self, request, context):
        return self._dispatch["ListHypervisors"].handle(self._gestor, request, context)

    def ForwardAction(self, request, context):
        return self._dispatch["ForwardAction"].handle(self._gestor, request, context)
