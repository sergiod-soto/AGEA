# Infraestructura/Gestores/Bootstrap/topologia.py
"""
topologia.py — Fuente única de verdad de la topología de componentes
remotos: qué componentes existen, cuántos, en qué orden deben arrancar,
y qué variable de entorno necesita cada uno para conocer la dirección
de los que arrancaron antes.

Usado por:
  - Bootstrap (modo local): lanza cada componente como subprocess local.
  - remote.py (modo remoto real): lanza cada componente como instancia
    EC2 Spot.

Antes de este módulo, main.py (local) y remote.py (AWS) construían la
topología cada uno por su cuenta, de forma duplicada y desincronizada.
Esto causaba dos bugs concretos:
  1. Los sectores lanzados en AWS real no recibían su SECTOR_COL/ROW
     (remote.py nunca los calculaba, a diferencia de main.py en local).
  2. NINGÚN componente remoto real recibía la dirección de otro
     (ni SECTOR_ADDR_*, ni GESTOR_MUNDO_ADDRESS, ni nada) — cada uno
     caía siempre en su valor por defecto ("localhost:puerto"), que en
     una instancia EC2 real apunta a sí misma, no a otra instancia.
Este módulo resuelve ambos de raíz, con una única función de topología
y una única función de resolución de direcciones, compartidas por
local y remoto.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ComponenteSpec:
    """
    Descripción de una instancia concreta de un componente a arrancar
    (un sector concreto, "el" gestor_mundo, un hypervisor concreto...).

    nombre          : identificador único (ej. "sector_0_1", "hv_00").
    tipo            : familia del componente — determina qué script/
                      healthcheck/stub/tipo de instancia EC2 usar.
                      Uno de: "sector", "logica_mundo", "gestor_mundo",
                      "gestor_bots", "hypervisor", "comunicaciones_remoto".
    host_env_var    : variable de entorno de HOST propia del proceso.
    port_env_var    : variable de entorno de PORT propia del proceso.
    default_port    : puerto que le corresponde a esta instancia concreta.
    extra_env       : variables de entorno fijas conocidas de antemano
                      (ej. SECTOR_COL/SECTOR_ROW de un sector concreto).
    """

    nombre: str
    tipo: str
    host_env_var: str
    port_env_var: str
    default_port: int
    extra_env: dict[str, str] = field(default_factory=dict)


def _sectores(
    grid_w: int, grid_h: int, sector_size: int, base_port: int
) -> list[ComponenteSpec]:
    cols = math.ceil(grid_w / sector_size)
    rows = math.ceil(grid_h / sector_size)
    specs = []
    for col in range(cols):
        for row in range(rows):
            port = base_port + col * rows + row
            specs.append(
                ComponenteSpec(
                    nombre=f"sector_{col}_{row}",
                    tipo="sector",
                    host_env_var="SECTOR_HOST",
                    port_env_var="SECTOR_PORT",
                    default_port=port,
                    extra_env={"SECTOR_COL": str(col), "SECTOR_ROW": str(row)},
                )
            )
    return specs


def construir_topologia() -> list[list[ComponenteSpec]]:
    """
    Devuelve grupos de ComponenteSpec en orden de arranque. Todos los
    componentes de un grupo pueden arrancar en paralelo; el grupo
    siguiente no arranca hasta que el anterior está listo (healthcheck)
    — así, cada grupo puede recibir las direcciones reales de todos los
    grupos anteriores (ver resolver_env_extra).

    Orden: Sectores → Logica_Mundo → [Gestor_Mundo, Gestor_Bots] →
           Hypervisores → Comunicaciones_Remoto

    Cuenta sectores/Hypervisores a partir de las MISMAS variables de
    entorno que ya usaba el modo local (GRID_WIDTH/HEIGHT/SECTOR_SIZE,
    HYPERVISOR_COUNT) — una sola fuente de verdad para local y remoto.
    """
    grid_w = int(os.getenv("GRID_WIDTH", 1000))
    grid_h = int(os.getenv("GRID_HEIGHT", 1000))
    sector_size = int(os.getenv("SECTOR_SIZE", 100))
    sector_base_port = int(os.getenv("SECTOR_BASE_PORT", 50100))
    hv_count = int(os.getenv("HYPERVISOR_COUNT", 1))
    if hv_count < 1:
        raise ValueError(f"HYPERVISOR_COUNT debe ser >= 1, recibido: {hv_count}")
    hv_base_port = int(os.getenv("HYPERVISOR_BASE_PORT", 50300))
    hv_proxy_base_port = int(os.getenv("HYPERVISOR_PROXY_BASE_PORT", 50400))

    sectores = _sectores(grid_w, grid_h, sector_size, sector_base_port)

    logica_mundo = ComponenteSpec(
        nombre="logica_mundo",
        tipo="logica_mundo",
        host_env_var="LOGICA_MUNDO_HOST",
        port_env_var="LOGICA_MUNDO_PORT",
        default_port=int(os.getenv("LOGICA_MUNDO_PORT", 50250)),
    )

    gestor_mundo = ComponenteSpec(
        nombre="gestor_mundo",
        tipo="gestor_mundo",
        host_env_var="GESTOR_MUNDO_HOST",
        port_env_var="GESTOR_MUNDO_PORT",
        default_port=int(os.getenv("GESTOR_MUNDO_PORT", 50200)),
    )

    gestor_bots = ComponenteSpec(
        nombre="gestor_bots",
        tipo="gestor_bots",
        host_env_var="GESTOR_BOTS_HOST",
        port_env_var="GESTOR_BOTS_PORT",
        default_port=int(os.getenv("GESTOR_BOTS_PORT", 50051)),
    )

    hypervisores = [
        ComponenteSpec(
            nombre=f"hv_{i:02d}",
            tipo="hypervisor",
            host_env_var="HYPERVISOR_HOST",
            port_env_var="HYPERVISOR_PORT",
            default_port=hv_base_port + i,
            extra_env={
                "HYPERVISOR_ID": f"hv_{i:02d}",
                "HYPERVISOR_PROXY_PORT": str(hv_proxy_base_port + i),
            },
        )
        for i in range(hv_count)
    ]

    comunicaciones_remoto = ComponenteSpec(
        nombre="comunicaciones_remoto",
        tipo="comunicaciones_remoto",
        host_env_var="COMUNICACIONES_REMOTO_HOST",
        port_env_var="COMUNICACIONES_REMOTO_PORT",
        default_port=int(os.getenv("COMUNICACIONES_REMOTO_PORT", 50500)),
    )

    return [
        sectores,
        [logica_mundo],
        [gestor_mundo, gestor_bots],
        hypervisores,
        [comunicaciones_remoto],
    ]


def resolver_env_extra(
    spec: ComponenteSpec, direcciones: dict[str, str]
) -> dict[str, str]:
    """
    Construye las variables de entorno de DIRECCIÓN AJENA que este
    componente necesita, a partir de las direcciones ya resueltas de
    componentes anteriores.

    direcciones : nombre de componente ya arrancado → "host:puerto".
                  Incluye una entrada por cada sector, bajo su propio
                  nombre (ej. "sector_0_1").

    Escrito explícito por tipo (en vez de una tabla genérica) a
    propósito: la relación de dependencias es fija y pequeña, y así
    queda legible de un vistazo qué necesita cada componente, sin
    indirección adicional.
    """
    env = dict(spec.extra_env)

    if spec.tipo == "gestor_mundo":
        env["LOGICA_MUNDO_ADDRESS"] = direcciones["logica_mundo"]
        for nombre, direccion in direcciones.items():
            if nombre.startswith("sector_"):
                _, col, row = nombre.split("_")
                env[f"SECTOR_ADDR_C{col}_R{row}"] = direccion

    elif spec.tipo == "gestor_bots":
        env["LOGICA_MUNDO_ADDRESS"] = direcciones["logica_mundo"]

    elif spec.tipo == "hypervisor":
        env["GESTOR_BOTS_ADDRESS"] = direcciones["gestor_bots"]

    elif spec.tipo == "comunicaciones_remoto":
        env["LOGICA_MUNDO_ADDRESS"] = direcciones["logica_mundo"]
        env["GESTOR_MUNDO_ADDRESS"] = direcciones["gestor_mundo"]
        env["GESTOR_BOTS_ADDRESS"] = direcciones["gestor_bots"]

    return env


# ─────────────────────────────────────────────────────────────
#  Healthcheck — compartido por local y remoto (mismos módulos Python)
# ─────────────────────────────────────────────────────────────

HEALTHCHECK_INFO: dict[str, dict] = {
    "sector": {
        "stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2_grpc",
        "stub_class": "SectorServiceStub",
        "request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2",
        "request_class": "GetStateRequest",
        "method": "GetState",
    },
    "logica_mundo": {
        "stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion.logica_mundo_service_pb2_grpc",
        "stub_class": "LogicaMundoServiceStub",
        "request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion.logica_mundo_service_pb2",
        "request_class": "GetActiveEventsRequest",
        "method": "GetActiveEvents",
    },
    "gestor_mundo": {
        "stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.gestor_mundo_service_pb2_grpc",
        "stub_class": "GestorMundoServiceStub",
        "request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.gestor_mundo_service_pb2",
        "request_class": "GetSnapshotInfoRequest",
        "method": "GetSnapshotInfo",
    },
    "gestor_bots": {
        "stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Bots.gestor_bots_service_pb2_grpc",
        "stub_class": "GestorBotsServiceStub",
        "request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Bots.gestor_bots_service_pb2",
        "request_class": "ListHypervisorsRequest",
        "method": "ListHypervisors",
    },
    "hypervisor": {
        "stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Bots.hypervisor_service_pb2_grpc",
        "stub_class": "HypervisorServiceStub",
        "request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Bots.hypervisor_service_pb2",
        "request_class": "ListBotsRequest",
        "method": "ListBots",
    },
    "comunicaciones_remoto": {
        "stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion.comunicacion_remota_service_pb2_grpc",
        "stub_class": "ComunicacionRemotaServiceStub",
        "request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion.comunicacion_remota_service_pb2",
        "request_class": "EjecutarRequest",
        "method": "Ejecutar",
    },
}
