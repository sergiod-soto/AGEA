# Gestores/Bots/Hypervisor/hypervisor_servicer.py
import logging
from Gestores.Transporte.Proto_Generated.Bots import (
    hypervisor_service_pb2_grpc as pb_grpc,
)
from Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Gestores.Bots.Hypervisor.registry import FUNCIONES

logger = logging.getLogger(__name__)


class HypervisorServicer(pb_grpc.HypervisorServiceServicer):

    def __init__(self, hypervisor: Hypervisor):
        self._hv = hypervisor
        self._dispatch = {fn.NAME: fn for fn in FUNCIONES}

    def SpawnBot(self, request, context):
        return self._dispatch["SpawnBot"].handle(self._hv, request, context)

    def KillBot(self, request, context):
        return self._dispatch["KillBot"].handle(self._hv, request, context)

    def GetBotStats(self, request, context):
        return self._dispatch["GetBotStats"].handle(self._hv, request, context)

    def ListBots(self, request, context):
        return self._dispatch["ListBots"].handle(self._hv, request, context)

    def ResetBudgets(self, request, context):
        return self._dispatch["ResetBudgets"].handle(self._hv, request, context)

    def SetPointBudget(self, request, context):
        return self._dispatch["SetPointBudget"].handle(self._hv, request, context)

    def GetBotStatus(self, request, context):
        return self._dispatch["GetBotStatus"].handle(self._hv, request, context)

    def Freeze(self, request, context):
        return self._dispatch["Freeze"].handle(self._hv, request, context)

    def Resume(self, request, context):
        return self._dispatch["Resume"].handle(self._hv, request, context)

    def SaveSnapshot(self, request, context):
        return self._dispatch["SaveSnapshot"].handle(self._hv, request, context)
