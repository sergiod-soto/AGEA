# Infraestructura/Gestores/tipos_comunes.py
"""
tipos_comunes.py — Tipos de datos compartidos entre componentes.

Estas clases no tienen lógica de negocio (son contenedores de datos) y
cruzan fronteras entre componentes que deben poder evolucionar por
separado (Logica_Mundo, Gestor_Bots, Hypervisor, Bot). Viven aquí para
que ningún componente tenga que importar el módulo de dominio de otro
solo para conocer la forma de un resultado.

Equivalente, en Python puro, a lo que common.proto ya hace para los
mensajes gRPC compartidos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────────────────────
#  Acciones
# ─────────────────────────────────────────────────────────────


class ActionResult:
    """
    Resultado de resolver una acción (de bot, o administrativa).

    Antes vivía en gestor_mundo.py. Se centraliza aquí porque la
    producen tanto Logica_Mundo como Gestor_Mundo/Gestor_Bots, y la
    consumen Hypervisor, BotClient y los servicers gRPC — cruza más
    fronteras de componente que ningún otro tipo del proyecto.
    """

    __slots__ = ("ok", "payload", "error", "world_tick")

    def __init__(
        self, ok: bool, payload: bytes = b"", error: str = "", world_tick: int = 0
    ):
        self.ok = ok
        self.payload = payload
        self.error = error
        self.world_tick = world_tick

    def __repr__(self):
        return f"ActionResult(ok={self.ok}, error={self.error!r})"


# ─────────────────────────────────────────────────────────────
#  Bots — vistas compartidas entre Gestor_Bots y Hypervisor
# ─────────────────────────────────────────────────────────────


class BotInfo:
    """
    Resultado de una operación de ciclo de vida sobre un bot
    (spawn_bot, principalmente). Antes vivía en hypervisor.py.
    """

    __slots__ = ("bot_id", "hypervisor_id", "proxy_address", "ok", "error")

    def __init__(self, bot_id, hypervisor_id, proxy_address, ok, error):
        self.bot_id = bot_id
        self.hypervisor_id = hypervisor_id
        self.proxy_address = proxy_address
        self.ok = ok
        self.error = error

    def __repr__(self):
        return f"BotInfo(bot_id={self.bot_id!r}, ok={self.ok}, error={self.error!r})"


class BotStats:
    """
    Estadísticas de un bot vistas por el Hypervisor/Gestor_Bots
    (presupuesto restante, vivo/muerto). Antes vivía en hypervisor.py.
    """

    __slots__ = ("bot_id", "hypervisor_id", "points_left", "alive", "uptime_s")

    def __init__(self, bot_id, hypervisor_id, points_left, alive, uptime_s=0.0):
        self.bot_id = bot_id
        self.hypervisor_id = hypervisor_id
        self.points_left = points_left
        self.alive = alive
        self.uptime_s = uptime_s


class BotList:
    """Lista de BotStats — antes en hypervisor.py."""

    __slots__ = ("bots",)

    def __init__(self, bots):
        self.bots = bots


class BotStatusHV:
    """
    Estado mínimo de un bot tal como lo gestiona el Hypervisor
    internamente (alive + budget). Antes: hypervisor.py.BotStatus.

    NOTA: distinto de BotStatusPropio — mismo nombre original
    ("BotStatus") en el código previo, pero campos y propósito
    diferentes. Ver aviso en el mensaje de texto sobre esta colisión.
    """

    __slots__ = ("bot_id", "alive", "budget")

    def __init__(self, bot_id, alive, budget):
        self.bot_id = bot_id
        self.alive = alive
        self.budget = budget


@dataclass
class BotStatusPropio:
    """
    Estado completo que recibe el propio bot al consultar GetStatus
    (posición, rotación, salud...). Antes: bot_client.py.BotStatus.
    """

    bot_id: str
    x: int
    y: int
    rotation: float
    health: float
    points_left: int
    world_tick: int
    alive: bool


# ─────────────────────────────────────────────────────────────
#  Hypervisores — vista compartida entre Gestor_Bots y su cliente
# ─────────────────────────────────────────────────────────────


@dataclass
class HypervisorInfo:
    """
    Metadata de un Hypervisor registrado.

    Antes duplicada: dataclass en gestor_bots.py y clase con __slots__
    en gestor_bots_client.py, con los mismos campos. Unificada aquí.
    """

    hypervisor_id: str
    address: str
    port: int
    proxy_port: int
    capacity: int
    current_load: int = 0
    online: bool = True


@dataclass
class HypervisorList:
    hypervisors: list[HypervisorInfo] = field(default_factory=list)
