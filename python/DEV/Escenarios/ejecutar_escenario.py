# Dev/ejecutar_escenario.py
"""
ejecutar_escenario.py — Lanzador manual mínimo: conecta un
LogicaMundoClient propio, carga un escenario y ejecuta sus estados a
la misma cadencia (estados/segundo) que DEFAULT_TICK_RATE, para que
el ritmo del escenario sea coherente con el del mundo real.

Uso: python -m Dev.ejecutar_escenario elemento_test_unico
"""

import asyncio
import os
import sys
import time

from Config.settings import DEFAULT_TICK_RATE
from Dev.Escenarios.serie_estados import Serie_Estados
from Dev.Escenarios.escenarios import cargar_escenario
from Infraestructura.Gestores.Transporte.logica_mundo_client import LogicaMundoClient


async def main(nombre_escenario: str) -> None:
    address = os.getenv("LOGICA_MUNDO_ADDRESS", "localhost:50250")
    cliente = LogicaMundoClient(address)

    serie = Serie_Estados(cliente)
    cargar_escenario(nombre_escenario, serie)

    # Mismo criterio que GestorMundo.set_tick_rate(): <= 0 significa
    # "sin límite" (se ejecuta tan rápido como pueda).
    intervalo = (1.0 / DEFAULT_TICK_RATE) if DEFAULT_TICK_RATE > 0 else 0.0

    while not serie.finalizado:
        t0 = time.monotonic()
        await serie.do()
        elapsed = time.monotonic() - t0

        if intervalo > 0:
            sobrante = intervalo - elapsed
            if sobrante > 0:
                await asyncio.sleep(sobrante)

    await cliente.close()


if __name__ == "__main__":
    nombre = sys.argv[1] if len(sys.argv) > 1 else "escenario_suelo"
    asyncio.run(main(nombre))
