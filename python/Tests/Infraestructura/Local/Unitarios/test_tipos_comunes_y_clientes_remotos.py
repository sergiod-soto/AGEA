# Tests/Infraestructura/Local/Unitarios/test_tipos_comunes_y_clientes_remotos.py
"""
test_tipos_comunes_y_clientes_remotos.py — Sanidad mínima de las
estructuras de datos compartidas (tipos_comunes.py) y de
ClientesRemotos.close(), que hasta ahora no tenían ningún test propio
(solo se ejercitaban indirectamente a través de otros tests).
"""

import pytest

from Infraestructura.Gestores.Comunicacion.Remoto.clientes_remotos import (
    ClientesRemotos,
)
from Infraestructura.Gestores.tipos_comunes import (
    ActionResult,
    BotInfo,
    HypervisorInfo,
    HypervisorList,
)


@pytest.mark.unit
def test_action_result_valores_por_defecto():
    resultado = ActionResult(ok=True)
    assert resultado.payload == b""
    assert resultado.error == ""
    assert resultado.world_tick == 0


@pytest.mark.unit
def test_action_result_repr_incluye_ok_y_error():
    resultado = ActionResult(ok=False, error="boom")
    assert "ok=False" in repr(resultado)
    assert "boom" in repr(resultado)


@pytest.mark.unit
def test_bot_info_repr_no_lanza_con_error_vacio():
    info = BotInfo(
        bot_id="b1", hypervisor_id="hv_00", proxy_address="x", ok=True, error=""
    )
    assert "b1" in repr(info)


@pytest.mark.unit
def test_hypervisor_info_last_seen_por_defecto_es_numerico():
    hv = HypervisorInfo(
        hypervisor_id="hv_00", address="x", port=1, proxy_port=2, capacity=10
    )
    assert isinstance(hv.last_seen, float)


@pytest.mark.unit
def test_hypervisor_list_por_defecto_esta_vacia():
    assert HypervisorList().hypervisors == []


@pytest.mark.unit
async def test_clientes_remotos_close_cierra_los_tres_clientes():
    llamados = []

    class FakeClient:
        def __init__(self, nombre):
            self._nombre = nombre

        async def close(self):
            llamados.append(self._nombre)

    clientes = ClientesRemotos(
        logica_mundo=FakeClient("logica_mundo"),
        gestor_mundo=FakeClient("gestor_mundo"),
        gestor_bots=FakeClient("gestor_bots"),
    )

    await clientes.close()

    assert set(llamados) == {"logica_mundo", "gestor_mundo", "gestor_bots"}
