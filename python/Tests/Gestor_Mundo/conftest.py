"""
conftest.py
-----------
Fixtures compartidas para Tests/Gestor_Mundo/E2E/ (y reutilizables en Integration).

Qué proporciona:
  - FakeGestorBotsServicer : stub gRPC mínimo que simula el Gestor_Bots.
                             Implementa solo los 4 métodos que usa GestorMundo:
                             FreezeAll, ResumeAll, ResetBudgets, SaveSnapshot.
  - fake_bots_server       : fixture que levanta FakeGestorBotsServicer en
                             un puerto aleatorio y devuelve su dirección.
  - sector_server_factory  : levanta un SectorServicer real en puerto aleatorio.
  - mundo_con_sectores     : GestorMundo cableado con N sectores reales y el
                             fake Gestor_Bots. Listo para llamar _run_tick().
  - mundo_2x2              : grid 2x2 (4 sectores, SECTOR_SIZE=10). Caso
                             estándar para la mayoría de tests E2E.

Colocar este fichero en: Tests/Gestor_Mundo/conftest.py
(pytest lo descubre automáticamente para todos los subdirectorios)

Requisitos:
    pip install pytest pytest-asyncio grpcio grpcio-tools
    pytest.ini → asyncio_mode = auto
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

import grpc
import pytest

# ── Variables de entorno base (deben estar antes de importar módulos del proyecto) ──
# Los tests individuales pueden sobreescribir col/row/size según necesiten.
os.environ.setdefault("SECTOR_COL", "0")
os.environ.setdefault("SECTOR_ROW", "0")
os.environ.setdefault("SECTOR_SIZE", "10")
os.environ.setdefault("MAX_VISION_DISTANCE", "3")
os.environ.setdefault("TICK_TIMEOUT_MS", "5000")
os.environ.setdefault("TICKS_ANTES_DE_DORMIR", "999")   # desactivar anti-thrashing en tests
os.environ.setdefault("UNITY_FRAME_EVERY_N_TICKS", "999")
os.environ.setdefault("SNAPSHOT_INTERVAL_TICKS", "999")
os.environ.setdefault("DEEP_SAVE_INTERVAL_TICKS", "9999")

from Gestores.Mundo.Sector.sector import Sector, SectorMode
from Gestores.Mundo.Sector.sector_servicer import SectorServicer
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo, SectorInfo

from Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2_grpc as sector_grpc,
)
from Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as bots_pb,
    gestor_bots_service_pb2_grpc as bots_grpc,
    common_pb2,
)


# ═══════════════════════════════════════════════════════════════════════════
#  FakeGestorBotsServicer
#  Stub mínimo síncrono — implementa solo los métodos que GestorMundo llama.
#  Registra las llamadas para que los tests puedan inspeccionarlas.
# ═══════════════════════════════════════════════════════════════════════════


class FakeGestorBotsServicer(bots_grpc.GestorBotsServiceServicer):
    """
    Implementa los 4 métodos que GestorMundo usa activamente:
      - FreezeAll      (llamado en freeze())
      - ResumeAll      (llamado en resume())
      - ResetBudgets   (llamado al final de cada _fase_2)
      - SaveSnapshot   (llamado en _deep_save)

    Los demás métodos no se implementan — si GestorMundo los llama
    en un test, el test fallará con UNIMPLEMENTED (señal clara de bug).

    Atributos públicos para asserts:
      .freeze_count     : veces que se llamó FreezeAll
      .resume_count     : veces que se llamó ResumeAll
      .reset_count      : veces que se llamó ResetBudgets
      .snapshot_ids     : lista de snapshot_ids recibidos en SaveSnapshot
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
#  Levanta FakeGestorBotsServicer en un puerto aleatorio.
#  Yield: (address, servicer) — dirección gRPC y referencia al servicer.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
async def fake_bots_server() -> AsyncGenerator[tuple[str, FakeGestorBotsServicer], None]:
    servicer = FakeGestorBotsServicer()
    server = grpc.aio.server()
    bots_grpc.add_GestorBotsServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port("[::]:0")
    await server.start()

    address = f"localhost:{port}"
    yield address, servicer

    await server.stop(grace=0)


# ═══════════════════════════════════════════════════════════════════════════
#  Helper: levantar un SectorServicer real en puerto aleatorio
# ═══════════════════════════════════════════════════════════════════════════


async def _start_sector_server(col: int, row: int) -> tuple[int, grpc.aio.Server, Sector]:
    """
    Crea un Sector con col/row dados, lo envuelve en SectorServicer,
    lo registra en un servidor gRPC en puerto aleatorio.
    Devuelve (port, server, sector).
    """
    sector = Sector()
    # Sobreescribir col/row en runtime (las constantes del módulo ya están fijadas,
    # pero el objeto Sector permite reasignarlas directamente)
    sector._col = col
    sector._row = row

    servicer = SectorServicer(sector)
    server = grpc.aio.server()

    from Gestores.Transporte.Proto_Generated.Sectores import (
        sector_service_pb2_grpc as pb_grpc,
    )
    pb_grpc.add_SectorServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port("[::]:0")
    await server.start()
    return port, server, sector


# ═══════════════════════════════════════════════════════════════════════════
#  Fixture: mundo_con_sectores
#  Devuelve una función factory async para crear un GestorMundo con
#  n_cols × n_rows sectores reales + fake Gestor_Bots.
#
#  Uso en test:
#      async def test_algo(mundo_con_sectores, fake_bots_server, tmp_path):
#          bots_addr, bots_svc = fake_bots_server
#          gestor, sectores, servers = await mundo_con_sectores(
#              n_cols=2, n_rows=2,
#              bots_address=bots_addr,
#              snapshot_dir=tmp_path,
#          )
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mundo_con_sectores():
    """
    Factory async. Gestiona internamente la lista de servidores
    para que el test solo tenga que llamar a la función.
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
    ) -> tuple[GestorMundo, dict[tuple[int, int], Sector], list[grpc.aio.Server]]:
        """
        Crea y cableα un GestorMundo con n_cols × n_rows sectores reales.

        Devuelve:
          gestor   : GestorMundo configurado (sin llamar a start())
          sectores : dict[(col, row)] → Sector (objeto Python, para asserts directos)
          servers  : lista de grpc.aio.Server (para parar en teardown si hace falta)
        """
        import Gestores.Mundo.Gestor_Mundo.gestor_mundo as gm_module

        # Parchar constantes del módulo para este test
        gm_module.SECTOR_SIZE = sector_size
        gm_module.COLS = n_cols
        gm_module.ROWS = n_rows
        gm_module.SNAPSHOT_DIR = snapshot_dir
        gm_module.TICK_TIMEOUT_MS = 5000
        gm_module.TICKS_ANTES_DE_DORMIR = 999

        gestor = GestorMundo()

        # Inicializar _pending_sounds (bug conocido: no está en __init__)
        gestor._pending_sounds = {}

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

                # Calcular región correcta para este sector
                x0 = col * sector_size
                y0 = row * sector_size
                sector._col = col
                sector._row = row
                # Parchear las constantes de región del sector
                import Gestores.Mundo.Sector.sector as sector_module
                sector_module.REGION_X0 = x0
                sector_module.REGION_Y0 = y0
                sector_module.REGION_X1 = x0 + sector_size
                sector_module.REGION_Y1 = y0 + sector_size

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

                # Poner en modo inicial vía gRPC real
                if modo_inicial != SectorMode.INACTIVO:
                    await stub.SetSectorMode(
                        __import__(
                            "Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2",
                            fromlist=["SetSectorModeRequest"],
                        ).SetSectorModeRequest(mode=modo_inicial.value)
                    )
                    info.mode = modo_inicial

        return gestor, sectores, _servers

    yield _factory

    # Teardown: parar todos los servidores y cerrar canales
    import asyncio

    async def _teardown():
        for ch in _channels:
            await ch.close()
        for srv in _servers:
            await srv.stop(grace=0)

    asyncio.get_event_loop().run_until_complete(_teardown())


# ═══════════════════════════════════════════════════════════════════════════
#  Fixture: mundo_2x2
#  Caso estándar para E2E: grid 20×20, 4 sectores de 10×10, todos ACTIVOS.
#  Yield: (gestor, sectores, bots_servicer)
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

    gestor, sectores, _ = await mundo_con_sectores(
        n_cols=2,
        n_rows=2,
        bots_address=bots_addr,
        snapshot_dir=tmp_path,
        sector_size=10,
        modo_inicial=SectorMode.ACTIVO,
    )

    yield gestor, sectores, bots_svc
