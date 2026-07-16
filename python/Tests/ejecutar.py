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
    # ── Entities ──────────────────────────────────────────────
    # "Tests/Entities/Unitarios/test_elemento.py",
    # "Tests/Entities/Unitarios/test_registry.py",

    # ── Infraestructura / Remoto ──────────────────────────────
    # "Tests/Infraestructura/Remoto/Unitarios/test_logica_mundo.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_gestor_bots.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_gestor_mundo.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_hypervisor.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_gestor_bots_servicer.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_remoto.py",
    # "Tests/Infraestructura/Remoto/E2E/test_stack_local.py",

    # ── Infraestructura / Local ───────────────────────────────
    # "Tests/Infraestructura/Local/Unitarios/test_topologia.py",
    # "Tests/Infraestructura/Local/Unitarios/test_monitor.py",
    # "Tests/Infraestructura/Local/Unitarios/test_shutdown.py",
]

if __name__ == "__main__":
    if not tests:
        print("No hay tests descomentados en Tests/ejecutar.py — nada que correr.")
    else:
        pytest.main(tests)