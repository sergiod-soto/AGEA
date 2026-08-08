# Infraestructura/Gestores/tipos_comunes.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import time


class ActionResult:
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


class BotInfo:
    __slots__ = ("bot_id", "hypervisor_id", "proxy_address", "ok", "error")

    def __init__(self, bot_id: int, hypervisor_id, proxy_address, ok, error):
        self.bot_id = bot_id
        self.hypervisor_id = hypervisor_id
        self.proxy_address = proxy_address
        self.ok = ok
        self.error = error

    def __repr__(self):
        return f"BotInfo(bot_id={self.bot_id!r}, ok={self.ok}, error={self.error!r})"


class BotStats:
    __slots__ = ("bot_id", "hypervisor_id", "points_left", "alive", "uptime_s")

    def __init__(self, bot_id: int, hypervisor_id, points_left, alive, uptime_s=0.0):
        self.bot_id = bot_id
        self.hypervisor_id = hypervisor_id
        self.points_left = points_left
        self.alive = alive
        self.uptime_s = uptime_s


class BotList:
    __slots__ = ("bots",)

    def __init__(self, bots):
        self.bots = bots


class BotStatusHV:
    __slots__ = ("bot_id", "alive", "budget")

    def __init__(self, bot_id: int, alive, budget):
        self.bot_id = bot_id
        self.alive = alive
        self.budget = budget


@dataclass
class BotStatusPropio:
    bot_id: int
    x: int
    y: int
    rotation: float
    health: float
    points_left: int
    world_tick: int
    alive: bool


@dataclass
class HypervisorInfo:
    hypervisor_id: str
    address: str
    port: int
    proxy_port: int
    capacity: int
    current_load: int = 0
    online: bool = True
    last_seen: float = field(default_factory=time.monotonic)


@dataclass
class HypervisorList:
    hypervisors: list[HypervisorInfo] = field(default_factory=list)
