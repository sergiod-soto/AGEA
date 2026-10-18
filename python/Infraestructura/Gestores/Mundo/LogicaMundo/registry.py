# Infraestructura/Gestores/Mundo/LogicaMundo/registry.py

from Infraestructura.Gestores.Mundo.LogicaMundo.Funciones import (
    asignar_id,
    actualizar_celdas,
    avanzar_elementos_globales,
    consultar_representar,
    avanzar_tick,
    construir_elemento,
    crear_elemento,
    despawn_global_event,
    eliminar_avatar_bot,
    eliminar_elemento,
    emitir_eventos,
    get_active_events,
    get_elementos_globales,
    heartbeat,
    load_state,
    matar_bot,
    modificar_elemento,
    obtener_audio,
    obtener_bots_en_region,
    obtener_celdas_en_region,
    resolver_accion,
    save_snapshot,
    shutdown,
    spawn_global_event,
)
from Infraestructura.Gestores.Mundo.LogicaMundo.Funciones import (
    obtener_celdas_atmosfera_en_region,
    actualizar_celdas_atmosfera,
    obtener_progreso_ciclos,
    tomar_parches_atmosfera,
)

from Infraestructura.Gestores.Mundo.LogicaMundo.Funciones import (
    estado_generacion_mundo,
    generar_mundo,
)

FUNCIONES = [
    asignar_id,
    crear_elemento,
    construir_elemento,
    modificar_elemento,
    eliminar_elemento,
    eliminar_avatar_bot,
    resolver_accion,
    spawn_global_event,
    despawn_global_event,
    get_active_events,
    obtener_bots_en_region,
    obtener_celdas_en_region,
    actualizar_celdas,
    consultar_representar,
    obtener_audio,
    avanzar_elementos_globales,
    avanzar_tick,
    save_snapshot,
    load_state,
    heartbeat,
    get_elementos_globales,
    shutdown,
    matar_bot,
    emitir_eventos,
    #
    # ----- sistema atmosférico --------
    obtener_celdas_atmosfera_en_region,
    actualizar_celdas_atmosfera,
    obtener_progreso_ciclos,
    tomar_parches_atmosfera,
    #
    # ----- generacion del mundo --------
    estado_generacion_mundo,
    generar_mundo,
]
