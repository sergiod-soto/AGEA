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

tests: list[str] = [
    # # ──────────────────────────────────────────────────────────
    # # ── Entities/Comportamientos ──────────────────────────────
    # #
    # "Tests/Entities/Comportamientos/test_comportamiento.py",
    # "Tests/Entities/Comportamientos/test_stat.py",
    # "Tests/Entities/Comportamientos/test_tiene_stats.py",
    # #
    # # ── Entities/Elementos ────────────────────────────────────
    # # ──
    # "Tests/Entities/Elementos/test_elemento.py",
    # "Tests/Entities/Elementos/test_registry.py",
    # "Tests/Entities/Elementos/test_registry_coherencia.py",
    #
    # # ── Sonido
    # "Tests/Entities/Elementos/Sonido/test_biblioteca_sonidos.py",
    # "Tests/Entities/Elementos/Sonido/test_desde_audio_dict.py",
    # "Tests/Entities/Elementos/Sonido/test_logica_mundo_audio.py",
    # "Tests/Entities/Elementos/Sonido/test_sonido.py",
    # "Tests/Entities/Elementos/Sonido/test_sonoro_modos.py",
    # #
    # # ── Integracion
    # #
    # # ──────────────────────────────────────────────────────────
    # # ── Infraestructura / Remoto ──────────────────────────────
    # #
    # # ── Unitarios
    "Tests/Infraestructura/Remoto/Unitarios/test_logica_mundo.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_gestor_bots.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_gestor_mundo.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_campos_para_creacion.py",  
    # "Tests/Infraestructura/Remoto/Unitarios/test_gestor_mundo_ciclo_vida.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_hypervisor.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_sector.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_transporte_clients_errores.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_bus_eventos.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_mirar.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_api_acciones.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_world_proxy_servicer.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_transporte_clients_async_errores.py",
    # "Tests/Infraestructura/Remoto/Unitarios/test_vista_foco.py",
    # # #
    # # ── Integracion
    # "Tests/Infraestructura/Remoto/Integracion/test_ayuda.py",  # ------------------
    # "Tests/Infraestructura/Remoto/Integracion/test_gestor_bots_servicer.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_remoto.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_remoto_ejecutar.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_consola_loop.py",  # ------------------
    # "Tests/Infraestructura/Remoto/Integracion/test_crear_elemento_accion.py",  # ------------------
    # "Tests/Infraestructura/Remoto/Integracion/test_sector_servicer.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_logica_mundo_servicer.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_gestor_mundo_servicer.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_comunicaciones_local_roundtrip.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_hypervisor_servicer.py",
    # "Tests/Infraestructura/Remoto/Integracion/test_world_proxy_servicer_grpc.py",
    # #
    # # ── E2E
    # "Tests/Infraestructura/Remoto/E2E/test_stack_local.py",
    # #
    # # ──────────────────────────────────────────────────────────
    # # ── Infraestructura / Local ───────────────────────────────
    # #
    # # ── E2E
    # #
    # # ── Integracion
    # "Tests/Infraestructura/Local/Integracion/test_aws.py",
    # "Tests/Infraestructura/Local/Integracion/test_aws_red_y_sesiones.py",
    # #
    # # ── Unitarios
    # "Tests/Infraestructura/Local/Unitarios/test_topologia.py",
    # "Tests/Infraestructura/Local/Unitarios/test_monitor.py",
    # "Tests/Infraestructura/Local/Unitarios/test_shutdown.py",
    # "Tests/Infraestructura/Local/Unitarios/test_log_categorias.py",
    # "Tests/Infraestructura/Local/Unitarios/test_buffered_log_handler.py",
    # "Tests/Infraestructura/Local/Unitarios/test_log_servicer.py",
    # "Tests/Infraestructura/Local/Unitarios/test_log_poller.py",
    # "Tests/Infraestructura/Local/Unitarios/test_bootstrap.py",
    # "Tests/Infraestructura/Local/Unitarios/test_remote_helpers.py",
    # "Tests/Infraestructura/Local/Unitarios/test_tipos_comunes_y_clientes_remotos.py",
    # "Tests/Infraestructura/Local/Unitarios/test_local_logging_y_log_pull_servicer.py",
    # #
    # # ── Otros ───────────────────────────────------------------
    # "Tests/Otros/test_salida_representacion_unity.py",
    # "Tests/Otros/ejemplo_tick_completo.py",
    # #
    # Salida a consola:
    # "-s",
]

if __name__ == "__main__":
    if not tests:
        print("No hay tests descomentados en Tests/ejecutar.py — nada que correr.")
    else:
        pytest.main(tests)
