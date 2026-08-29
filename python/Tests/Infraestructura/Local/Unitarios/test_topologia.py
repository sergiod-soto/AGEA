# Tests/Infraestructura/Local/Unitarios/test_topologia.py
"""
test_topologia.py — Pruebas unitarias de topologia.py: construcción de
la topología de componentes (orden de arranque, número de sectores/
hypervisores según variables de entorno) y resolución de env_extra
para cada tipo de componente.

ACTUALIZADO: el tamaño del mundo (ANCHO/ALTO) ya no se lee de
variables de entorno (GRID_WIDTH/GRID_HEIGHT) — ahora sale de
Config.settings, porque es un dato de MUNDO (debe ser igual en local y
en AWS), no de despliegue. Por eso estos tests fijan ANCHO/ALTO con
monkeypatch.setattr(config, ...) en vez de monkeypatch.setenv(...). El
resto (SECTOR_SIZE, puertos, HYPERVISOR_COUNT) sigue siendo config de
despliegue y se sigue fijando por entorno, sin cambios ahí.
"""

import pytest

import Config.settings as config
from Infraestructura.Gestores.Bootstrap.topologia import (
    HEALTHCHECK_INFO,
    ComponenteSpec,
    construir_topologia,
    resolver_env_extra,
)


def _entorno_grid_1_sector(monkeypatch):
    """Grid mínimo: exactamente 1 sector, 1 hypervisor — caso base."""
    monkeypatch.setattr(config, "ANCHO", 100)
    monkeypatch.setattr(config, "ALTO", 100)
    monkeypatch.setenv("SECTOR_SIZE", "100")
    monkeypatch.setenv("HYPERVISOR_COUNT", "1")


@pytest.mark.unit
def test_construir_topologia_orden_de_grupos(monkeypatch):
    """
    El orden de arranque es la garantía principal de este módulo: cada
    grupo debe poder recibir direcciones reales de todos los grupos
    anteriores (ver docstring de construir_topologia).
    """
    _entorno_grid_1_sector(monkeypatch)

    grupos = construir_topologia()

    assert len(grupos) == 5
    tipos_por_grupo = [{spec.tipo for spec in grupo} for grupo in grupos]
    assert tipos_por_grupo[0] == {"sector"}
    assert tipos_por_grupo[1] == {"logica_mundo"}
    assert tipos_por_grupo[2] == {"gestor_mundo", "gestor_bots"}
    assert tipos_por_grupo[3] == {"hypervisor"}
    assert tipos_por_grupo[4] == {"comunicaciones_remoto"}


@pytest.mark.unit
def test_construir_topologia_un_solo_sector(monkeypatch):
    _entorno_grid_1_sector(monkeypatch)

    grupos = construir_topologia()
    sectores = grupos[0]

    assert len(sectores) == 1
    assert sectores[0].nombre == "sector_0_0"
    assert sectores[0].extra_env == {"SECTOR_COL": "0", "SECTOR_ROW": "0"}


@pytest.mark.unit
def test_construir_topologia_multiples_sectores_en_grid_no_cuadrado(monkeypatch):
    """
    Grid de 200x100 con sectores de 100 → 2 columnas x 1 fila. Verifica
    que _sectores() usa math.ceil (no división entera) y que el puerto
    de cada sector es determinista (base_port + col*rows + row).
    """
    monkeypatch.setattr(config, "ANCHO", 200)
    monkeypatch.setattr(config, "ALTO", 100)
    monkeypatch.setenv("SECTOR_SIZE", "100")
    monkeypatch.setenv("SECTOR_BASE_PORT", "50100")
    monkeypatch.setenv("HYPERVISOR_COUNT", "1")

    grupos = construir_topologia()
    sectores = grupos[0]
    nombres = {s.nombre for s in sectores}

    assert nombres == {"sector_0_0", "sector_1_0"}
    puertos = {s.nombre: s.default_port for s in sectores}
    assert puertos["sector_0_0"] == 50100  # col=0,row=0 → base+0*1+0
    assert puertos["sector_1_0"] == 50101  # col=1,row=0 → base+1*1+0


@pytest.mark.unit
def test_construir_topologia_varios_hypervisores(monkeypatch):
    _entorno_grid_1_sector(monkeypatch)
    monkeypatch.setenv("HYPERVISOR_COUNT", "3")
    monkeypatch.setenv("HYPERVISOR_BASE_PORT", "50300")
    monkeypatch.setenv("HYPERVISOR_PROXY_BASE_PORT", "50400")

    grupos = construir_topologia()
    hypervisores = grupos[3]

    assert [hv.nombre for hv in hypervisores] == ["hv_000", "hv_001", "hv_002"]
    assert hypervisores[1].default_port == 50301
    assert hypervisores[1].extra_env == {
        "HYPERVISOR_ID": "hv_001",
        "HYPERVISOR_PROXY_PORT": "50401",
    }


@pytest.mark.unit
def test_construir_topologia_hypervisor_count_invalido_lanza(monkeypatch):
    _entorno_grid_1_sector(monkeypatch)
    monkeypatch.setenv("HYPERVISOR_COUNT", "0")

    with pytest.raises(ValueError, match="HYPERVISOR_COUNT"):
        construir_topologia()


# ── resolver_env_extra ──────────────────────────────────────────────


def _spec(tipo: str, nombre: str = "x", extra_env=None) -> ComponenteSpec:
    """Fábrica mínima de ComponenteSpec — solo importan tipo y extra_env
    para estos tests, el resto de campos son irrelevantes aquí."""
    return ComponenteSpec(
        nombre=nombre,
        tipo=tipo,
        host_env_var="X_HOST",
        port_env_var="X_PORT",
        default_port=1234,
        extra_env=extra_env or {},
    )


@pytest.mark.unit
def test_resolver_env_extra_sector_no_anade_nada_propio():
    """Un sector solo necesita su propio extra_env (col/row) — no
    depende de direcciones de otros componentes."""
    spec = _spec("sector", extra_env={"SECTOR_COL": "0", "SECTOR_ROW": "1"})
    env = resolver_env_extra(spec, direcciones={})
    assert env == {"SECTOR_COL": "0", "SECTOR_ROW": "1"}


@pytest.mark.unit
def test_resolver_env_extra_gestor_mundo_incluye_logica_y_sectores():
    spec = _spec("gestor_mundo")
    direcciones = {
        "logica_mundo": "10.0.0.1:50250",
        "sector_0_0": "10.0.0.2:50100",
        "sector_1_0": "10.0.0.3:50101",
        "gestor_bots": "10.0.0.4:50051",  # no debe colarse como sector
    }

    env = resolver_env_extra(spec, direcciones)

    assert env["LOGICA_MUNDO_ADDRESS"] == "10.0.0.1:50250"
    assert env["SECTOR_ADDR_C0_R0"] == "10.0.0.2:50100"
    assert env["SECTOR_ADDR_C1_R0"] == "10.0.0.3:50101"
    assert "GESTOR_BOTS_ADDRESS" not in env


@pytest.mark.unit
def test_resolver_env_extra_gestor_bots_solo_logica_mundo():
    spec = _spec("gestor_bots")
    env = resolver_env_extra(spec, {"logica_mundo": "10.0.0.1:50250"})
    assert env == {"LOGICA_MUNDO_ADDRESS": "10.0.0.1:50250"}


@pytest.mark.unit
def test_resolver_env_extra_hypervisor_conserva_extra_env_propio():
    """El HV necesita GESTOR_BOTS_ADDRESS + su propio HYPERVISOR_ID/
    PROXY_PORT ya conocidos de antemano — ambos deben convivir."""
    spec = _spec(
        "hypervisor",
        extra_env={"HYPERVISOR_ID": "hv_00", "HYPERVISOR_PROXY_PORT": "50400"},
    )
    env = resolver_env_extra(spec, {"gestor_bots": "10.0.0.4:50051"})

    assert env["GESTOR_BOTS_ADDRESS"] == "10.0.0.4:50051"
    assert env["HYPERVISOR_ID"] == "hv_00"
    assert env["HYPERVISOR_PROXY_PORT"] == "50400"


@pytest.mark.unit
def test_resolver_env_extra_comunicaciones_remoto_incluye_las_tres_direcciones():
    spec = _spec("comunicaciones_remoto")
    direcciones = {
        "logica_mundo": "10.0.0.1:50250",
        "gestor_mundo": "10.0.0.5:50200",
        "gestor_bots": "10.0.0.4:50051",
    }
    env = resolver_env_extra(spec, direcciones)
    assert env == {
        "LOGICA_MUNDO_ADDRESS": "10.0.0.1:50250",
        "GESTOR_MUNDO_ADDRESS": "10.0.0.5:50200",
        "GESTOR_BOTS_ADDRESS": "10.0.0.4:50051",
    }


@pytest.mark.unit
def test_healthcheck_info_cubre_todos_los_tipos_usados_en_topologia(monkeypatch):
    """
    Cada tipo de componente que construir_topologia() puede producir
    debe tener su entrada en HEALTHCHECK_INFO — si no, remote.py y
    bootstrap.py fallarían con KeyError al arrancar ese componente.
    """
    _entorno_grid_1_sector(monkeypatch)
    grupos = construir_topologia()
    tipos_usados = {spec.tipo for grupo in grupos for spec in grupo}

    assert tipos_usados <= HEALTHCHECK_INFO.keys()
