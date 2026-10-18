# Infraestructura/Gestores/Mundo/Sector/sector_mode.py

from enum import Enum


class SectorMode(Enum):
    """
    Modo de un Sector.

    Vive en su propio módulo para que GestorMundo pueda usarlo sin importar
    sector (que arrastra Core.Entities, la física atmosférica, etc.:
    dependencias que el proceso del Gestor no necesita).

    Los valores son IGUALES a los del enum SectorMode de sector_service.proto:
    GestorMundo envía `mode.value` tal cual por gRPC.
    """

    INACTIVO = 0
    DORMIDO = 1
    ACTIVO = 2
