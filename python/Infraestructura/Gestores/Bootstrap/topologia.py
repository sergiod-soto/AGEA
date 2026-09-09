# Infraestructura/Gestores/Bootstrap/topologia.py


from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Optional

import Config.settings as config


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

    El tamaño del mundo (ANCHO/ALTO) sale de Config.settings — es dato
    de mundo, igual en local y en AWS. El resto (SECTOR_SIZE, puertos,
    HYPERVISOR_COUNT) sigue siendo config de despliegue, en entorno.
    """
    grid_w = config.GRID_WIDTH
    grid_h = config.GRID_HEIGHT
    if config.HYPERVISOR_COUNT < 1:
        raise ValueError(
            f"HYPERVISOR_COUNT debe ser >= 1, recibido: {config.HYPERVISOR_COUNT}"
        )

    sectores = _sectores(grid_w, grid_h, config.SECTOR_SIZE, config.SECTOR_BASE_PORT)

    logica_mundo = ComponenteSpec(
        nombre="logica_mundo",
        tipo="logica_mundo",
        host_env_var="LOGICA_MUNDO_HOST",
        port_env_var="LOGICA_MUNDO_PORT",
        default_port=config.LOGICA_MUNDO_PORT,
    )

    gestor_mundo = ComponenteSpec(
        nombre="gestor_mundo",
        tipo="gestor_mundo",
        host_env_var="GESTOR_MUNDO_HOST",
        port_env_var="GESTOR_MUNDO_PORT",
        default_port=config.GESTOR_MUNDO_PORT,
    )

    gestor_bots = ComponenteSpec(
        nombre="gestor_bots",
        tipo="gestor_bots",
        host_env_var="GESTOR_BOTS_HOST",
        port_env_var="GESTOR_BOTS_PORT",
        default_port=config.GESTOR_BOTS_PORT,
    )

    hypervisores = [
        ComponenteSpec(
            nombre=f"hv_{i:03d}",
            tipo="hypervisor",
            host_env_var="HYPERVISOR_HOST",
            port_env_var="HYPERVISOR_PORT",
            default_port=config.HYPERVISOR_BASE_PORT + i,
            extra_env={
                "HYPERVISOR_ID": f"hv_{i:03d}",
                "HYPERVISOR_PROXY_PORT": str(config.HYPERVISOR_PROXY_BASE_PORT + i),
            },
        )
        for i in range(config.HYPERVISOR_COUNT)
    ]

    comunicaciones_remoto = ComponenteSpec(
        nombre="comunicaciones_remoto",
        tipo="comunicaciones_remoto",
        host_env_var="COMUNICACIONES_REMOTO_HOST",
        port_env_var="COMUNICACIONES_REMOTO_PORT",
        default_port=config.COMUNICACIONES_REMOTO_PORT,
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
