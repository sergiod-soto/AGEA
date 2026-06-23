"""
conftest.py
-----------
Fixtures compartidas para Tests/Gestor_Mundo/E2E/ (y reutilizables en Integration).

Qué proporciona:
  - FakeGestorBotsServicer : stub gRPC mínimo que simula el Gestor_Bots.
  - fake_bots_server       : levanta FakeGestorBotsServicer en puerto aleatorio.
  - mundo_con_sectores     : GestorMundo cableado con N sectores reales y fake Gestor_Bots.
  - mundo_2x2              : grid 2x2 (4 sectores, SECTOR_SIZE=10). Caso estándar.

Colocar en: Tests/Gestor_Mundo/conftest.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

import grpc
import pytest

# ── Variables de entorno base ────────────────────────────────────────────────
os.environ.setdefault("SECTOR_COL", "0")
os.environ.setdefault("SECTOR_ROW", "0")
os.environ.setdefault("SECTOR_SIZE", "10")
os.environ.setdefault("MAX_VISION_DISTANCE", "3")
os.environ.setdefault("TICK_TIMEOUT_MS", "5000")
os.environ.setdefault("TICKS_ANTES_DE_DORMIR", "999")
os.environ.setdefault("UNITY_FRAME_EVERY_N_TICKS", "999")
os.environ.setdefault("SNAPSHOT_INTERVAL_TICKS", "999")
os.environ.setdefault("DEEP_SAVE_INTERVAL_TICKS", "9999")

from Gestores.Mundo.Sector.sector import Sector, SectorMode
from Gestores.Mundo.Sector.sector_servicer import SectorServicer
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo, SectorInfo

from Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2_grpc as sector_grpc,
    sector_service_pb2 as sector_pb,
)
from Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as bots_pb,
    gestor_bots_service_pb2_grpc as bots_grpc,
    common_pb2,
)

# ═══════════════════════════════════════════════════════════════════════════
#  FakeGestorBotsServicer
# ═══════════════════════════════════════════════════════════════════════════


class FakeGestorBotsServicer(bots_grpc.GestorBotsServiceServicer):
    """
    Implementa solo los métodos que GestorMundo llama activamente.
    Los demás fallan con UNIMPLEMENTED — señal clara de bug si se llaman.

    Atributos para asserts:
      .freeze_count   : veces que se llamó FreezeAll
      .resume_count   : veces que se llamó ResumeAll
      .reset_count    : veces que se llamó ResetBudgets
      .snapshot_ids   : lista de snapshot_ids recibidos en SaveSnapshot
    """

    def __init__(self):
        self.freeze_count: int = 0
        self.resume_count: int = 0
        self.reset_count: int = 0
        self.snapshot_ids: list[str] = []

    def FreezeAll(self, request, context):
        self.freeze_count += 1
        return common_pb2.Ack(ok=True)

    def ResumeAll(self, request, context):
        self.resume_count += 1
        return common_pb2.Ack(ok=True)

    def ResetBudgets(self, request, context):
        self.reset_count += 1
        return common_pb2.Ack(ok=True)

    def SaveSnapshot(self, request, context):
        self.snapshot_ids.append(request.snapshot_id)
        return bots_pb.SaveSnapshotResponse(
            ok=True,
            snapshot_id=request.snapshot_id,
        )


# ═══════════════════════════════════════════════════════════════════════════
#  Fixture: fake_bots_server
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
async def fake_bots_server() -> (
    AsyncGenerator[tuple[str, FakeGestorBotsServicer], None]
):
    """Levanta FakeGestorBotsServicer en puerto aleatorio."""
    servicer = FakeGestorBotsServicer()
    server = grpc.aio.server()
    bots_grpc.add_GestorBotsServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port("[::]:0")
    await server.start()

    yield f"localhost:{port}", servicer

    await server.stop(grace=0)


# ═══════════════════════════════════════════════════════════════════════════
#  Helper: levantar un SectorServicer real en puerto aleatorio
# ═══════════════════════════════════════════════════════════════════════════


async def _start_sector_server(
    col: int, row: int
) -> tuple[int, grpc.aio.Server, Sector]:
    """
    Crea un Sector con col/row dados, lo envuelve en SectorServicer,
    lo registra en un servidor gRPC en puerto aleatorio.
    Devuelve (port, server, sector).
    """
    sector = Sector()
    sector._col = col
    sector._row = row

    servicer = SectorServicer(sector)
    server = grpc.aio.server()
    sector_grpc.add_SectorServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port("[::]:0")
    await server.start()
    return port, server, sector


# ═══════════════════════════════════════════════════════════════════════════
#  Fixture: mundo_con_sectores
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
async def mundo_con_sectores():
    """
    Factory async. Crea un GestorMundo con n_cols × n_rows sectores reales
    y un fake Gestor_Bots. No llama a start() — el test controla el ciclo de vida.

    Uso:
        async def test_algo(mundo_con_sectores, fake_bots_server, tmp_path):
            bots_addr, bots_svc = fake_bots_server
            gestor, sectores = await mundo_con_sectores(
                n_cols=2, n_rows=2,
                bots_address=bots_addr,
                snapshot_dir=tmp_path,
            )
    """
    _servers: list[grpc.aio.Server] = []
    _channels: list[grpc.aio.Channel] = []

    async def _factory(
        n_cols: int,
        n_rows: int,
        bots_address: str,
        snapshot_dir: Path,
        sector_size: int = 10,
        modo_inicial: SectorMode = SectorMode.ACTIVO,
    ) -> tuple[GestorMundo, dict[tuple[int, int], Sector]]:
        """
        Devuelve:
          gestor   : GestorMundo configurado con variables de entorno del test.
          sectores : dict[(col, row)] → Sector para asserts directos.
        """
        # Configurar entorno antes de instanciar GestorMundo.
        # GestorMundo lee del entorno en __init__, así que esto es suficiente
        # y no requiere parchear constantes de módulo.
        os.environ["SECTOR_SIZE"] = str(sector_size)
        os.environ["GRID_WIDTH"] = str(n_cols * sector_size)
        os.environ["GRID_HEIGHT"] = str(n_rows * sector_size)
        os.environ["SNAPSHOT_DIR"] = str(snapshot_dir)
        os.environ["TICK_TIMEOUT_MS"] = "5000"
        os.environ["TICKS_ANTES_DE_DORMIR"] = "999"
        os.environ["GESTOR_BOTS_ADDRESS"] = bots_address

        gestor = GestorMundo()

        # Canal hacia el fake Gestor_Bots
        bots_channel = grpc.aio.insecure_channel(bots_address)
        _channels.append(bots_channel)
        gestor._bots_channel = bots_channel
        gestor._bots_stub = bots_grpc.GestorBotsServiceStub(bots_channel)

        sectores: dict[tuple[int, int], Sector] = {}

        for col in range(n_cols):
            for row in range(n_rows):
                port, server, sector = await _start_sector_server(col, row)
                _servers.append(server)

                address = f"localhost:{port}"
                channel = grpc.aio.insecure_channel(address)
                _channels.append(channel)
                stub = sector_grpc.SectorServiceStub(channel)

                info = SectorInfo(
                    col=col,
                    row=row,
                    address=address,
                    mode=SectorMode.INACTIVO,
                    channel=channel,
                    stub=stub,
                )
                gestor._sectores[(col, row)] = info
                sectores[(col, row)] = sector

                if modo_inicial != SectorMode.INACTIVO:
                    await stub.SetSectorMode(
                        sector_pb.SetSectorModeRequest(mode=modo_inicial.value)
                    )
                    info.mode = modo_inicial

        return gestor, sectores

    yield _factory

    for ch in _channels:
        await ch.close()
    for srv in _servers:
        await srv.stop(grace=0)


# ═══════════════════════════════════════════════════════════════════════════
#  Fixture: mundo_2x2
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
async def mundo_2x2(
    mundo_con_sectores, fake_bots_server, tmp_path
) -> AsyncGenerator[tuple[GestorMundo, dict, FakeGestorBotsServicer], None]:
    """
    Grid 2×2. Todos los sectores en modo ACTIVO.
    Yield: (gestor, sectores_dict, fake_bots_servicer)

    sectores_dict: {(0,0): Sector, (0,1): Sector, (1,0): Sector, (1,1): Sector}
    """
    bots_addr, bots_svc = fake_bots_server

    gestor, sectores = await mundo_con_sectores(
        n_cols=2,
        n_rows=2,
        bots_address=bots_addr,
        snapshot_dir=tmp_path,
        sector_size=10,
        modo_inicial=SectorMode.ACTIVO,
    )

    yield gestor, sectores, bots_svc
