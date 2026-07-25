# Tests/Infraestructura/Local/Unitarios/test_remote_helpers.py
"""
test_remote_helpers.py — Pruebas unitarias de las funciones auxiliares
de remote.py que NO requieren AWS real: construcción de
especificaciones por fase (_lanzar_fase), registro de direcciones tras
esperar IPs (_esperar_y_registrar_direcciones), construcción de
callables de shutdown (_make_shutdown_fn), creación de stubs
(_crear_stubs) y fallo por timeout de _healthcheck_remoto.

lanzar_instancias/esperar_ips_publicas (AWS real) se monkeypatchean
siempre — arrancar_remoto() en su conjunto es demasiado costoso de
mockear con fidelidad (boto3 + gRPC + fases encadenadas) y queda fuera
de este fichero; sus piezas sí quedan cubiertas una a una aquí.
"""

import pytest

import Infraestructura.AWS.remote as remote_mod
from Infraestructura.Gestores.Bootstrap.topologia import ComponenteSpec


def _spec(nombre, tipo, default_port=100) -> ComponenteSpec:
    return ComponenteSpec(
        nombre=nombre,
        tipo=tipo,
        host_env_var="X_HOST",
        port_env_var="X_PORT",
        default_port=default_port,
    )


@pytest.mark.unit
def test_lanzar_fase_resuelve_env_extra_antes_de_lanzar(monkeypatch):
    capturado = {}

    def fake_lanzar_instancias(config, session_id, especificaciones):
        capturado["especificaciones"] = especificaciones
        return {spec["comp_id"]: f"i-{spec['comp_id']}" for spec in especificaciones}

    monkeypatch.setattr(remote_mod, "lanzar_instancias", fake_lanzar_instancias)

    spec = _spec("gestor_bots", tipo="gestor_bots", default_port=50051)
    direcciones = {"logica_mundo": "10.0.0.1:50250"}

    resultado = remote_mod._lanzar_fase(
        [spec], direcciones, config={}, session_id="sesion-1"
    )

    assert resultado == {"gestor_bots": "i-gestor_bots"}
    especificacion = capturado["especificaciones"][0]
    assert especificacion["componente"] == "gestor_bots"
    assert especificacion["comp_id"] == "gestor_bots"
    assert especificacion["env_extra"] == {"LOGICA_MUNDO_ADDRESS": "10.0.0.1:50250"}


@pytest.mark.unit
def test_esperar_y_registrar_direcciones_anade_host_puerto(monkeypatch):
    monkeypatch.setattr(
        remote_mod,
        "esperar_ips_publicas",
        lambda config, id_por_comp_fase, timeout: {"gestor_bots": "10.0.0.9"},
    )

    direcciones = {}
    config = {
        "red": {"puerto_grpc_componentes": 50051},
        "timeouts": {"arranque_segundos": 5},
    }

    remote_mod._esperar_y_registrar_direcciones(
        {"gestor_bots": "i-1"}, config, direcciones
    )

    assert direcciones == {"gestor_bots": "10.0.0.9:50051"}


@pytest.mark.unit
def test_make_shutdown_fn_invoca_stub_con_el_timeout_configurado():
    llamadas = []

    class FakeStub:
        def Shutdown(self, req, timeout):
            llamadas.append((req, timeout))
            return "respuesta"

    fn = remote_mod._make_shutdown_fn(FakeStub(), timeout=42)
    resultado = fn("mi-request")

    assert resultado == "respuesta"
    assert llamadas == [("mi-request", 42)]


@pytest.mark.unit
async def test_crear_stubs_construye_canal_y_dos_stubs_por_componente():
    ip_por_comp = {"gestor_bots": "127.0.0.1"}
    tipo_por_comp = {"gestor_bots": "gestor_bots"}
    config = {"red": {"puerto_grpc_componentes": 50051}}

    stubs, log_stubs, canales = remote_mod._crear_stubs(
        ip_por_comp, tipo_por_comp, config
    )

    assert set(stubs.keys()) == {"gestor_bots"}
    assert set(log_stubs.keys()) == {"gestor_bots"}
    assert len(canales) == 1

    for canal in canales:
        await canal.close()


@pytest.mark.unit
def test_healthcheck_remoto_falla_por_timeout_si_nadie_escucha():
    config = {
        "red": {"puerto_grpc_componentes": 59999},
        "timeouts": {"arranque_segundos": 0.3},
    }

    resultado = remote_mod._healthcheck_remoto("sector", "127.0.0.1", config)

    assert resultado is False
