# Tests/ejecutar.py
"""
ejecutar.py — Punto de entrada manual para correr un subconjunto
concreto de tests, sin memorizar rutas de pytest.

Uso: descomentar la(s) línea(s) que se quieran correr, y ejecutar:
    python Tests/ejecutar.py

Se puede apuntar a un fichero completo o a un test suelto con
"archivo.py::nombre_test". Por debajo es pytest.main() normal — todas
las fixtures de conftest.py, asyncio_mode y markers de pytest.ini
siguen aplicando igual que si se invocara pytest desde la terminal.
"""

import pytest

tests = [
    # ──────────────────────────────────────────────────────────
    # ── Entities ──────────────────────────────────────────────
    #
    # ── Unitarios
    # "Tests/Entities/Unitarios/test_elemento.py",
    # "Tests/Entities/Unitarios/test_registry.py",
    #
    # ── Integracion
    #
    # ──────────────────────────────────────────────────────────
    # ── Infraestructura / Remoto ──────────────────────────────
    #
    # ── Unitarios
    # "Tests/Infraestructura/Remoto/Unitarios/test_logica_mundo.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_gestor_bots.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_gestor_mundo.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_gestor_mundo_ciclo_vida.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_hypervisor.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_sector.py",
    #
    # ── Integracion
    # "Tests/Infraestructura/Remoto/Integracion/test_gestor_bots_servicer.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_remoto.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_sector_servicer.py",
    #
    # ── E2E
    # "Tests/Infraestructura/Remoto/E2E/test_stack_local.py",
    #
    # ──────────────────────────────────────────────────────────
    # ── Infraestructura / Local ───────────────────────────────
    #
    # ── E2E
    #
    # ── Integracion
    # "Tests/Infraestructura/Local/Integracion/test_aws.py", # PASA
    #
    # ── Unitarios
    # "Tests/Infraestructura/Local/Unitarios/test_topologia.py", # PASA
    # "Tests/Infraestructura/Local/Unitarios/test_monitor.py", # PASA
    # "Tests/Infraestructura/Local/Unitarios/test_shutdown.py", # PASA
    #
]

if __name__ == "__main__":
    if not tests:
        print("No hay tests descomentados en Tests/ejecutar.py — nada que correr.")
    else:
        pytest.main(tests)
