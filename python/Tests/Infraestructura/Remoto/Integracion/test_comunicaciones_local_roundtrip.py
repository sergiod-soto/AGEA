# Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_local_roundtrip.py
"""
test_comunicaciones_local_roundtrip.py — Integración de extremo a
extremo del puente completo: ComunicacionesLocal (cliente, en la
máquina local) → ComunicacionRemotaService real (gRPC) →
ComunicacionesRemotoServicer → ComunicacionesRemoto.ejecutar() →
dispatch real de Funciones/*.py.

Es el único test que ejercita las TRES capas juntas; los tests de
test_comunicaciones_remoto_ejecutar.py y test_comunicaciones_remoto.py
ya cubren cada capa por separado con más detalle de casos — aquí basta
con unos pocos casos representativos para confirmar que el cableado
end-to-end funciona.
"""

from types import SimpleNamespace

import pytest

from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
    ComunicacionesLocal,
)
from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto import (
    ComunicacionesRemoto,
)
from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto_servicer import (
    ComunicacionesRemotoServicer,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    comunicacion_remota_service_pb2 as bridge_pb,
    comunicacion_remota_service_pb2_grpc as bridge_pb_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as mundo_pb,
)


@pytest.fixture
async def cliente_comunicaciones_local(levantar_servidor):
    async def pause():
        return True, ""

    async def get_active_events():
        return []

    clientes = SimpleNamespace(
        logica_mundo=SimpleNamespace(get_active_events=get_active_events),
        gestor_mundo=SimpleNamespace(pause=pause),
        gestor_bots=SimpleNamespace(),
    )
    logica_remoto = ComunicacionesRemoto(clientes)
    servicer = ComunicacionesRemotoServicer(logica_remoto)
    servidor = await levantar_servidor(
        lambda s: bridge_pb_grpc.add_ComunicacionRemotaServiceServicer_to_server(
            servicer, s
        )
    )

    local = ComunicacionesLocal(servidor.address)
    yield local
    await local.close()


@pytest.mark.integration
async def test_pause_roundtrip_completo(cliente_comunicaciones_local):
    ok, error = await cliente_comunicaciones_local.pause()

    assert ok is True
    assert error == ""


@pytest.mark.integration
async def test_get_active_events_roundtrip_completo(cliente_comunicaciones_local):
    resp = await cliente_comunicaciones_local.get_active_events()

    assert resp.ok is True
    assert list(resp.events) == []


@pytest.mark.integration
async def test_operacion_no_registrada_en_remoto_lanza_runtimeerror(
    cliente_comunicaciones_local,
):
    """
    ComunicacionesLocal._ejecutar() traduce un ok=False del PUENTE
    (operación desconocida, ver comunicaciones_remoto.py) en
    RuntimeError — los métodos públicos solo construyen operaciones
    válidas, así que se llama a _ejecutar directamente para forzar
    este caso.
    """
    with pytest.raises(RuntimeError):
        await cliente_comunicaciones_local._ejecutar(
            bridge_pb.GESTOR_MUNDO, "OperacionInventada", mundo_pb.PauseRequest()
        )
