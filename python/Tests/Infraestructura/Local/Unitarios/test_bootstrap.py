# Tests/Infraestructura/Local/Unitarios/test_bootstrap.py
"""
test_bootstrap.py — Pruebas unitarias de las piezas de bootstrap.py
que no requieren lanzar procesos ni gRPC real: construcción de
direcciones/env_extra en modo local, apagado de procesos, y carga de
variables de entorno desde el fichero .env.<modo>.

ejecutar_modo_local() en sí (que sí lanza subprocesos reales) ya está
cubierto por el test e2e test_stack_local.py — no se repite aquí.
"""

import os
import subprocess

import pytest

import Infraestructura.Gestores.Bootstrap.bootstrap as bootstrap_mod
from Infraestructura.Gestores.Bootstrap.topologia import ComponenteSpec


def _spec(
    nombre,
    tipo="x",
    default_port=100,
    extra_env=None,
    host_env_var="X_HOST",
    port_env_var="X_PORT",
) -> ComponenteSpec:
    return ComponenteSpec(
        nombre=nombre,
        tipo=tipo,
        host_env_var=host_env_var,
        port_env_var=port_env_var,
        default_port=default_port,
        extra_env=extra_env or {},
    )


# ── _direcciones_locales / _env_extra_local ─────────────────────


@pytest.mark.unit
def test_direcciones_locales_usa_localhost_y_puerto_de_cada_spec():
    grupos = [[_spec("a", default_port=100)], [_spec("b", default_port=200)]]

    direcciones = bootstrap_mod._direcciones_locales(grupos)

    assert direcciones == {"a": "localhost:100", "b": "localhost:200"}


@pytest.mark.unit
def test_env_extra_local_combina_propio_y_ajeno():
    spec = _spec(
        "gestor_bots",
        tipo="gestor_bots",
        default_port=50051,
        host_env_var="GESTOR_BOTS_HOST",
        port_env_var="GESTOR_BOTS_PORT",
    )
    direcciones = {"logica_mundo": "localhost:50250"}

    env = bootstrap_mod._env_extra_local(spec, direcciones)

    assert env["GESTOR_BOTS_HOST"] == "localhost"
    assert env["GESTOR_BOTS_PORT"] == "50051"
    assert env["LOGICA_MUNDO_ADDRESS"] == "localhost:50250"


# ── _apagar_procesos ─────────────────────────────────────────────


class FakeProceso:
    """Doble de subprocess.Popen controlable a mano — mismo patrón que
    FakeProceso en Tests/.../Unitarios/test_hypervisor.py."""

    def __init__(self, muere_al_terminate: bool):
        self._vivo = True
        self._muere_al_terminate = muere_al_terminate
        self.terminated = False
        self.killed = False

    def poll(self):
        return None if self._vivo else 0

    def terminate(self):
        self.terminated = True
        if self._muere_al_terminate:
            self._vivo = False

    def wait(self, timeout=None):
        if self._vivo:
            raise subprocess.TimeoutExpired(cmd="x", timeout=timeout)
        return 0

    def kill(self):
        self.killed = True
        self._vivo = False


@pytest.mark.unit
def test_apagar_procesos_termina_los_que_responden_a_terminate():
    proceso = FakeProceso(muere_al_terminate=True)

    bootstrap_mod._apagar_procesos([proceso])

    assert proceso.terminated is True
    assert proceso.killed is False


@pytest.mark.unit
def test_apagar_procesos_mata_los_que_no_responden_a_terminate():
    proceso = FakeProceso(muere_al_terminate=False)

    bootstrap_mod._apagar_procesos([proceso])

    assert proceso.terminated is True
    assert proceso.killed is True


# ── configurar_entorno — carga de .env.<modo> ────────────────────


@pytest.mark.unit
def test_configurar_entorno_carga_variables_nuevas_sin_pisar_las_existentes(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(bootstrap_mod, "ROOT", tmp_path)
    (tmp_path / ".env.test").write_text(
        "NUEVA_VAR=valor_del_fichero\nYA_EXISTE=deberia_ignorarse\n"
    )
    monkeypatch.setenv("YA_EXISTE", "valor_real_del_proceso")
    monkeypatch.delenv("NUEVA_VAR", raising=False)

    bootstrap_mod.configurar_entorno("test")

    assert os.environ["NUEVA_VAR"] == "valor_del_fichero"
    assert os.environ["YA_EXISTE"] == "valor_real_del_proceso"  # no sobreescrita


@pytest.mark.unit
def test_configurar_entorno_sin_fichero_env_no_lanza(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap_mod, "ROOT", tmp_path)

    bootstrap_mod.configurar_entorno("modo_sin_env_file")  # no debe lanzar


# ── _healthcheck ──────────────────────────────────────────────────


@pytest.mark.unit
def test_healthcheck_falla_por_timeout_si_nadie_escucha():
    """
    Puerto arbitrario sin servidor real detrás — el healthcheck debe
    agotar el timeout y devolver False, sin lanzar. timeout_s pequeño
    para no ralentizar la suite.
    """
    spec = _spec("sector_0_0", tipo="sector", default_port=59999)

    resultado = bootstrap_mod._healthcheck(spec, timeout_s=0.3)

    assert resultado is False
