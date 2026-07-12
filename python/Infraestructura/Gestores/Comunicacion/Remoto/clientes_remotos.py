# Infraestructura/Gestores/Comunicacion/Remoto/clientes_remotos.py
"""
clientes_remotos.py — Agrupa los clientes async hacia los tres
componentes que Comunicaciones_Remoto puede reenviar peticiones.

Una sola instancia de cada cliente, compartida por todos los handlers
de Funciones/ — evita abrir un canal gRPC nuevo por operación.
"""

from dataclasses import dataclass

from Infraestructura.Gestores.Transporte.logica_mundo_client import LogicaMundoClient
from Infraestructura.Gestores.Transporte.gestor_mundo_client import GestorMundoClient
from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
    GestorBotsClientAsync,
)


@dataclass
class ClientesRemotos:
    logica_mundo: LogicaMundoClient
    gestor_mundo: GestorMundoClient
    gestor_bots: GestorBotsClientAsync

    async def close(self) -> None:
        await self.logica_mundo.close()
        await self.gestor_mundo.close()
        await self.gestor_bots.close()
