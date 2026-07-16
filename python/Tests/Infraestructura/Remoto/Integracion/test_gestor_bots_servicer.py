# Tests/Infraestructura/Remoto/Integracion/test_gestor_bots_servicer.py
"""
test_gestor_bots_servicer.py — Prueba de integración: levanta un
Gestor_Bots_Servicer real sobre un grpc.aio.server real (puerto
efímero, mismo proceso de pytest — ver fixture levantar_servidor en
conftest.py), y lo golpea con un GestorBotsClientAsync real.

A diferencia de los unitarios, aquí SÍ viaja proto real por la red
(localhost) — valida serialización + dispatch del servicer, no solo la
lógica de Gestor_Bots en memoria.
"""

import pytest

from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots_servicer import (
    Gestor_Bots_Servicer,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
    GestorBotsClientAsync,
)


@pytest.mark.integration
async def test_register_hypervisor_via_grpc_real(levantar_servidor):
    gestor = Gestor_Bots(logica_client=None, bots_por_hypervisor=10)
    servicer = Gestor_Bots_Servicer(gestor=gestor, hypervisor_client_factory=None)

    servidor = await levantar_servidor(
        lambda s: pb_grpc.add_GestorBotsServiceServicer_to_server(servicer, s)
    )

    client = GestorBotsClientAsync(servidor.address)
    try:
        lista = await client.list_hypervisors()
        assert lista.hypervisors == []

        # RegisterHypervisor no tiene método de conveniencia en el
        # cliente async (solo en el síncrono, usado por el HV) — se
        # invoca vía la lógica de negocio directamente para este test,
        # que es lo que de verdad queremos comprobar aquí: que el
        # servicer real actualiza el estado real de Gestor_Bots.
        await gestor.register_hypervisor(
            hypervisor_id="hv_00",
            address="localhost",
            port=50300,
            proxy_port=50400,
            capacity=10,
        )

        lista = await client.list_hypervisors()
        assert len(lista.hypervisors) == 1
        assert lista.hypervisors[0].hypervisor_id == "hv_00"
    finally:
        await client.close()


@pytest.mark.integration
async def test_heartbeat_reporta_hv_caido_por_staleness(levantar_servidor, monkeypatch):
    """
    Verifica la cascada completa a nivel de RPC real: un HV que dejó de
    reportar carga hace más de UMBRAL_HV_CAIDO_SEGUNDOS debe hacer que
    el Heartbeat real (no solo la función interna) devuelva ok=False.
    """
    import Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots as gestor_bots_mod

    monkeypatch.setattr(gestor_bots_mod, "UMBRAL_HV_CAIDO_SEGUNDOS", 0.01)

    gestor = Gestor_Bots(logica_client=None, bots_por_hypervisor=10)
    servicer = Gestor_Bots_Servicer(gestor=gestor, hypervisor_client_factory=None)
    servidor = await levantar_servidor(
        lambda s: pb_grpc.add_GestorBotsServiceServicer_to_server(servicer, s)
    )

    await gestor.register_hypervisor(
        hypervisor_id="hv_00",
        address="localhost",
        port=50300,
        proxy_port=50400,
        capacity=10,
    )

    import asyncio

    await asyncio.sleep(0.05)  # supera el umbral de 0.01s

    client = GestorBotsClientAsync(servidor.address)
    try:
        resp = await client.heartbeat()
        assert resp.ok is False
        assert "hv_00" in resp.error
    finally:
        await client.close()
