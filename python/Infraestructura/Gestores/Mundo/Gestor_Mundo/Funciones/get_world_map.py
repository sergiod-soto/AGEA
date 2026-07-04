from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import (
    GestorMundo,
    SectorMode,
)

NAME = "GetWorldMap"
IS_STREAMING = True


async def handle(gestor: GestorMundo, request, context):
    BATCH = 1000
    async with gestor._gold_lock:
        gold_snapshot = dict(gestor._gold_cells)
        sectores = dict(gestor._sectores)
    if request.only_active_sectors:
        celdas_validas = set()
        for (col, row), info in sectores.items():
            if info.mode in (SectorMode.ACTIVO, SectorMode.DORMIDO):
                x0, y0 = col * gestor.SECTOR_SIZE, row * gestor.SECTOR_SIZE
                x1, y1 = x0 + gestor.SECTOR_SIZE, y0 + gestor.SECTOR_SIZE
                for x, y in gold_snapshot:
                    if x0 <= x < x1 and y0 <= y < y1:
                        celdas_validas.add((x, y))
    else:
        celdas_validas = set(gold_snapshot.keys())
    batch = []
    for x, y in celdas_validas:
        batch.append(
            common_pb2.Cell(
                pos=common_pb2.Position(x=x, y=y), element=gold_snapshot[(x, y)]
            )
        )
        if len(batch) >= BATCH:
            yield pb.GetWorldMapResponse(cells=batch)
            batch = []
    if batch:
        yield pb.GetWorldMapResponse(cells=batch)
