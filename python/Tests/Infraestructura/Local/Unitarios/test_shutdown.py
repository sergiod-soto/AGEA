# Tests/Infraestructura/Local/Unitarios/test_shutdown.py
"""
test_shutdown.py — Pruebas unitarias de ShutdownCoordinator.

terminar_instancias (AWS real) se monkeypatchea siempre a través de la
fixture sin_terminar_ec2: este módulo no debe tocar boto3 real en
ningún test de aquí — eso ya lo cubre
Tests/Infraestructura/Local/Integracion/test_aws.py.
"""

from types import SimpleNamespace

import pytest

import Infraestructura.AWS.shutdown as shutdown_mod
from Infraestructura.AWS.shutdown import ShutdownCoordinator


def _config(shutdown_segundos=1):
    return {"timeouts": {"shutdown_segundos": shutdown_segundos}}


def _ack(ok=True, error=""):
    return SimpleNamespace(ok=ok, error=error)


@pytest.fixture
def sin_terminar_ec2(monkeypatch):
    """Evita cualquier llamada real a AWS; devuelve la lista de ids
    con los que se llamó a terminar_instancias en cada invocación."""
    llamadas = []
    monkeypatch.setattr(
        shutdown_mod, "terminar_instancias", lambda config, ids: llamadas.append(ids)
    )
    return llamadas


def _coordinador(
    gestor_bots=lambda req: _ack(),
    gestor_mundo=lambda req: _ack(),
    logica_mundo=lambda req: _ack(),
    comunicaciones_remoto=lambda req: _ack(),
    hv=None,
    sector=None,
    instance_ids=None,
):
    return ShutdownCoordinator(
        config=_config(),
        session_id="sesion-test",
        instance_ids=instance_ids or {"gestor_bots": "i-1", "gestor_mundo": "i-2"},
        shutdown_gestor_bots=gestor_bots,
        shutdown_gestor_mundo=gestor_mundo,
        shutdown_hv=hv or {},
        shutdown_sector=sector or {},
        shutdown_logica_mundo=logica_mundo,
        shutdown_comunicaciones_remoto=comunicaciones_remoto,
    )


@pytest.mark.unit
def test_ejecutar_es_idempotente(sin_terminar_ec2):
    """
    Llamadas repetidas a ejecutar() tras la primera deben ignorarse
    silenciosamente — protege contra doble disparo (monitor + señal
    SIGTERM a la vez, por ejemplo).
    """
    llamadas = []
    coord = _coordinador(gestor_bots=lambda req: (llamadas.append(1), _ack())[1])

    coord.ejecutar(reason="user")
    coord.ejecutar(reason="user")
    coord.ejecutar(reason="user")

    assert len(llamadas) == 1


@pytest.mark.unit
def test_ejecutar_llama_a_los_cuatro_componentes_principales(sin_terminar_ec2):
    llamados = set()

    def _marcar(nombre):
        def _fn(req):
            llamados.add(nombre)
            return _ack()

        return _fn

    coord = _coordinador(
        gestor_bots=_marcar("gestor_bots"),
        gestor_mundo=_marcar("gestor_mundo"),
        logica_mundo=_marcar("logica_mundo"),
        comunicaciones_remoto=_marcar("comunicaciones_remoto"),
    )

    coord.ejecutar(reason="user")

    assert llamados == {
        "gestor_bots",
        "gestor_mundo",
        "logica_mundo",
        "comunicaciones_remoto",
    }


@pytest.mark.unit
def test_ejecutar_sin_logica_mundo_ni_comunicaciones_remoto_no_falla(sin_terminar_ec2):
    """
    Ambos son opcionales (None por defecto) — remote.py siempre los
    provee, pero el coordinador no debe asumirlo.
    """
    coord = ShutdownCoordinator(
        config=_config(),
        session_id="s",
        instance_ids={},
        shutdown_gestor_bots=lambda req: _ack(),
        shutdown_gestor_mundo=lambda req: _ack(),
        shutdown_hv={},
        shutdown_sector={},
    )
    coord.ejecutar(reason="user")  # no debe lanzar


@pytest.mark.unit
def test_fallback_a_hvs_si_gestor_bots_no_confirma(sin_terminar_ec2):
    hv_llamados = []
    coord = _coordinador(
        gestor_bots=lambda req: _ack(ok=False, error="caído"),
        hv={"hv_00": lambda req: (hv_llamados.append("hv_00"), _ack())[1]},
    )

    coord.ejecutar(reason="user")

    assert hv_llamados == ["hv_00"]


@pytest.mark.unit
def test_fallback_a_sectores_si_gestor_mundo_no_confirma(sin_terminar_ec2):
    sector_llamados = []
    coord = _coordinador(
        gestor_mundo=lambda req: _ack(ok=False, error="caído"),
        sector={
            "sector_0_0": lambda req: (sector_llamados.append("sector_0_0"), _ack())[1]
        },
    )

    coord.ejecutar(reason="user")

    assert sector_llamados == ["sector_0_0"]


@pytest.mark.unit
def test_sin_fallback_si_gestores_confirman(sin_terminar_ec2):
    """Si gestor_bots/gestor_mundo confirman ok=True, NO debe llamarse
    directamente a HVs/sectores — sería trabajo redundante."""
    hv_llamados = []
    sector_llamados = []
    coord = _coordinador(
        hv={"hv_00": lambda req: (hv_llamados.append("hv_00"), _ack())[1]},
        sector={
            "sector_0_0": lambda req: (sector_llamados.append("sector_0_0"), _ack())[1]
        },
    )

    coord.ejecutar(reason="user")

    assert hv_llamados == []
    assert sector_llamados == []


@pytest.mark.unit
def test_llamar_con_timeout_devuelve_false_si_fn_lanza_excepcion(sin_terminar_ec2):
    coord = _coordinador()

    def _falla(req):
        raise RuntimeError("conexión rechazada")

    resultado = coord._llamar_con_timeout("comp", _falla, req=None)

    assert resultado is False


@pytest.mark.unit
def test_llamar_con_timeout_devuelve_false_si_ok_false(sin_terminar_ec2):
    coord = _coordinador()

    resultado = coord._llamar_con_timeout(
        "comp", lambda req: _ack(ok=False, error="x"), req=None
    )

    assert resultado is False


@pytest.mark.unit
def test_termina_instancias_ec2_siempre_al_final(sin_terminar_ec2):
    coord = _coordinador(instance_ids={"gestor_bots": "i-1"})

    coord.ejecutar(reason="user")

    assert sin_terminar_ec2 == [["i-1"]]


@pytest.mark.unit
def test_termina_instancias_no_propaga_si_terminar_instancias_lanza(monkeypatch):
    """
    Un fallo al terminar instancias EC2 no debe impedir que ejecutar()
    complete — solo se registra el error (ver comentario en _shutdown).
    """

    def _lanza(config, ids):
        raise RuntimeError("AWS caído")

    monkeypatch.setattr(shutdown_mod, "terminar_instancias", _lanza)

    coord = _coordinador()
    coord.ejecutar(reason="user")  # no debe propagar la excepción
