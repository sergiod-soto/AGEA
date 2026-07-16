# Infraestructura/AWS/remote.py
"""
Arranque y ciclo de vida de una sesión en AWS (modo remoto).

Responsabilidades:
  - Determinar si la sesión es nueva o reanudación desde hibernación.
  - Actualizar el Security Group con la IP local actual.
  - Lanzar instancias Spot POR FASES (siguiendo topologia.py), de forma
    que cada fase pueda incluir las direcciones reales de las fases
    anteriores — antes se lanzaba todo de golpe y ningún componente
    recibía la dirección de otro.
  - Monitorizar los gestores (heartbeat) y coordinar el shutdown
    si cualquier componente cae o el usuario cierra la sesión.

La comunicación con Unity se implementa en un módulo separado
(pendiente) que se integrará en el bucle principal.
"""

import importlib
import logging
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from Config.settings import LOG_DIR, LOG_PULL_INTERVAL_SEGUNDOS
from Infraestructura.Gestores.Bootstrap.topologia import (
    HEALTHCHECK_INFO,
    ComponenteSpec,
    construir_topologia,
    resolver_env_extra,
)
from Infraestructura.Gestores.Log.log_servicer import LogServicer
from Infraestructura.Gestores.Log.log_poller import LogPoller
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2,
    log_pull_service_pb2_grpc,
)

import grpc

from Infraestructura.AWS.aws import (
    actualizar_security_group,
    borrar_sesion_hibernada,
    esperar_ips_publicas,
    guardar_sesion_activa,
    lanzar_instancias,
    leer_ultima_sesion,
    nueva_session_id,
    obtener_ip_publica,
    terminar_instancias,
)
from Infraestructura.AWS.monitor import MonitorComponentes
from Infraestructura.AWS.shutdown import ShutdownCoordinator

logger = logging.getLogger("remoto")


# ─────────────────────────────────────────────────────────────
#  Healthcheck remoto
# ─────────────────────────────────────────────────────────────


def _healthcheck_remoto(tipo: str, ip: str, config: dict) -> bool:
    """
    Llama a un RPC real del componente hasta que responde o se agota el
    timeout. El polling usa intervalos de 2s para dar tiempo al boot
    desde AMI.

    Recibe `tipo` directamente (de topologia.HEALTHCHECK_INFO) en vez
    de inferirlo del comp_id por convención de nombre — más robusto,
    y ya no depende de que "hv_" o "sector_" sean siempre el prefijo.
    """
    puerto = config["red"]["puerto_grpc_componentes"]
    timeout = config["timeouts"]["arranque_segundos"]
    address = f"{ip}:{puerto}"
    info = HEALTHCHECK_INFO[tipo]

    StubClass = getattr(
        importlib.import_module(info["stub_module"]), info["stub_class"]
    )
    Request = getattr(
        importlib.import_module(info["request_module"]), info["request_class"]
    )
    method = info["method"]

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with grpc.insecure_channel(address) as canal:
                stub = StubClass(canal)
                getattr(stub, method)(Request(), timeout=2)
            logger.info("  ✓ %s (%s) listo", tipo, address)
            return True
        except Exception:
            time.sleep(2)

    logger.error("  ✗ Timeout esperando %s (%s)", tipo, address)
    return False


# ─────────────────────────────────────────────────────────────
#  Stubs persistentes
# ─────────────────────────────────────────────────────────────


def _crear_stubs(
    ip_por_comp: dict[str, str],
    tipo_por_comp: dict[str, str],
    config: dict,
) -> tuple[dict, dict, list[grpc.Channel]]:
    """
    Crea un canal gRPC persistente por componente, y sobre cada canal dos
    stubs: el del servicio principal (varía por tipo de componente) y el
    de LogPullService (idéntico en todos los tipos — mismo .proto, mismo
    servidor y puerto que el servicio principal).
    """
    puerto = config["red"]["puerto_grpc_componentes"]
    stubs = {}
    log_stubs = {}
    canales = []

    for comp_id, ip in ip_por_comp.items():
        canal = grpc.insecure_channel(f"{ip}:{puerto}")
        canales.append(canal)

        info = HEALTHCHECK_INFO[tipo_por_comp[comp_id]]
        StubClass = getattr(
            importlib.import_module(info["stub_module"]), info["stub_class"]
        )
        stubs[comp_id] = StubClass(canal)
        log_stubs[comp_id] = log_pull_service_pb2_grpc.LogPullServiceStub(canal)

    return stubs, log_stubs, canales


def _make_shutdown_fn(stub, timeout: int):
    """
    Construye el callable de shutdown para un componente.
    Función auxiliar para evitar el problema de captura de variables
    en bucles con lambdas (closure-in-loop).
    """
    return lambda req: stub.Shutdown(req, timeout=timeout)


# ─────────────────────────────────────────────────────────────
#  Arranque por fases
# ─────────────────────────────────────────────────────────────


def _lanzar_fase(
    grupo: list[ComponenteSpec],
    direcciones_resueltas: dict[str, str],
    config: dict,
    session_id: str,
) -> dict[str, str]:
    """
    Lanza un grupo completo de topologia.construir_topologia(), con el
    env_extra de cada componente ya resuelto contra las direcciones de
    fases anteriores. Devuelve {comp_id: instance_id} de este grupo.
    """
    especificaciones = [
        {
            "componente": spec.tipo,
            "comp_id": spec.nombre,
            "env_extra": resolver_env_extra(spec, direcciones_resueltas),
        }
        for spec in grupo
    ]
    return lanzar_instancias(config, session_id, especificaciones)


def _esperar_y_registrar_direcciones(
    id_por_comp_fase: dict[str, str],
    config: dict,
    direcciones_resueltas: dict[str, str],
) -> None:
    """
    Espera IPs públicas de esta fase y las añade a direcciones_resueltas
    (mutando el dict) con el formato "host:puerto" que topologia.py
    espera para construir el env_extra de la fase siguiente.
    """
    puerto = config["red"]["puerto_grpc_componentes"]
    ip_por_comp = esperar_ips_publicas(
        config, id_por_comp_fase, timeout=config["timeouts"]["arranque_segundos"]
    )
    for comp_id, ip in ip_por_comp.items():
        direcciones_resueltas[comp_id] = f"{ip}:{puerto}"


# ─────────────────────────────────────────────────────────────
#  Arranque remoto
# ─────────────────────────────────────────────────────────────


def arrancar_remoto(config: dict) -> None:
    """
    fresh se lee de la variable de entorno FRESH (Config.settings.FRESH),
    igual que ya hace el resto del sistema — antes se recibía como
    argumento args.fresh, que argparse nunca definía (AttributeError
    garantizado en cuanto se ejecutaba --modo remoto).
    """
    from Config.settings import FRESH

    timeout_shutdown = config["timeouts"]["shutdown_segundos"]

    # ── 1. Determinar sesión ──────────────────────────────────
    session_id_anterior = None if FRESH else leer_ultima_sesion(config)
    session_id = session_id_anterior or nueva_session_id()
    modo = "reanudación" if session_id_anterior else "nueva"
    logger.info("Sesión %s: %s", modo, session_id)

    # ── 2. Actualizar Security Group ──────────────────────────
    mi_ip = obtener_ip_publica()
    actualizar_security_group(config, mi_ip)

    # ── 3. Lanzar instancias Spot POR FASES ───────────────────
    # Cada fase espera la IP pública de la anterior antes de construir
    # el user_data de la siguiente — así cada componente puede recibir
    # ya la dirección real de los que le preceden (ver topologia.py).
    logger.info("Lanzando instancias Spot por fases...")
    grupos = construir_topologia()

    id_por_comp: dict[str, str] = {}
    tipo_por_comp: dict[str, str] = {}
    direcciones_resueltas: dict[str, str] = {}

    try:
        for grupo in grupos:
            id_por_comp_fase = _lanzar_fase(
                grupo, direcciones_resueltas, config, session_id
            )
            id_por_comp.update(id_por_comp_fase)
            for spec in grupo:
                tipo_por_comp[spec.nombre] = spec.tipo

            _esperar_y_registrar_direcciones(
                id_por_comp_fase, config, direcciones_resueltas
            )

    except (RuntimeError, TimeoutError) as e:
        logger.error("No se pudo arrancar la infraestructura: %s", e)
        terminar_instancias(config, list(id_por_comp.values()))
        sys.exit(1)

    guardar_sesion_activa(config, session_id)

    # ── 4. Healthcheck de todos los componentes ───────────────
    # Ya se esperó la IP pública de cada fase; aquí se confirma que el
    # servicio gRPC de cada componente responde de verdad (aceptar
    # conexiones TCP no basta — el proceso puede seguir inicializando).
    logger.info("Esperando que los componentes estén listos...")

    def _check(item: tuple[str, str]) -> tuple[str, bool]:
        comp_id, direccion = item
        ip = direccion.rsplit(":", 1)[0]
        return comp_id, _healthcheck_remoto(tipo_por_comp[comp_id], ip, config)

    with ThreadPoolExecutor(max_workers=len(direcciones_resueltas)) as executor:
        resultados = dict(executor.map(_check, direcciones_resueltas.items()))

    fallidos = [c for c, ok in resultados.items() if not ok]
    if fallidos:
        logger.error("Componentes que no respondieron: %s. Abortando.", fallidos)
        terminar_instancias(config, list(id_por_comp.values()))
        sys.exit(1)

    logger.info("Todos los componentes listos.")

    # ── 5. Crear stubs persistentes ───────────────────────────
    ip_por_comp = {
        comp_id: direccion.rsplit(":", 1)[0]
        for comp_id, direccion in direcciones_resueltas.items()
    }
    stubs, log_stubs, canales = _crear_stubs(ip_por_comp, tipo_por_comp, config)

    # ── 5.1 Recolección de logs (modelo pull) ─────────────────
    log_servicer = LogServicer(log_dir=LOG_DIR)
    log_poller = LogPoller(
        intervalo_segundos=LOG_PULL_INTERVAL_SEGUNDOS,
        escribir=log_servicer.escribir,
    )
    for comp_id, log_stub in log_stubs.items():
        log_poller.registrar(
            comp_id,
            lambda req=log_pull_service_pb2.PullLogsRequest(), stub=log_stub: (
                stub.PullLogs(req, timeout=5).records
            ),
        )
    log_poller.iniciar()

    # ── 6. Si es reanudación, borrar hibernación de S3 ────────
    if session_id_anterior:
        borrar_sesion_hibernada(config, session_id_anterior)

    # ── 7. Evento de cierre ───────────────────────────────────
    shutdown_completado = threading.Event()
    exit_code = 0  # 0 = usuario, 1 = fallo

    # ── 8. Shutdown coordinator ───────────────────────────────
    hv_ids = [c for c, t in tipo_por_comp.items() if t == "hypervisor"]
    sector_ids = [c for c, t in tipo_por_comp.items() if t == "sector"]

    coord = ShutdownCoordinator(
        config=config,
        session_id=session_id,
        instance_ids=id_por_comp,
        shutdown_gestor_bots=_make_shutdown_fn(stubs["gestor_bots"], timeout_shutdown),
        shutdown_gestor_mundo=_make_shutdown_fn(
            stubs["gestor_mundo"], timeout_shutdown
        ),
        shutdown_logica_mundo=_make_shutdown_fn(
            stubs["logica_mundo"], timeout_shutdown
        ),
        shutdown_comunicaciones_remoto=_make_shutdown_fn(
            stubs["comunicaciones_remoto"], timeout_shutdown
        ),
        shutdown_hv={
            hv: _make_shutdown_fn(stubs[hv], timeout_shutdown) for hv in hv_ids
        },
        shutdown_sector={
            sec: _make_shutdown_fn(stubs[sec], timeout_shutdown) for sec in sector_ids
        },
    )

    # ── 9. Monitor ────────────────────────────────────────────
    def _heartbeat_o_falla(resp):
        if not resp.ok:
            raise RuntimeError(resp.error or "heartbeat respondió ok=False")
        return resp

    def _on_fallo(comp_id: str) -> None:
        nonlocal exit_code
        exit_code = 1
        logger.error("Componente caído: %s — iniciando shutdown.", comp_id)
        log_poller.detener()
        coord.ejecutar(reason="component_failure")
        shutdown_completado.set()

    monitor = MonitorComponentes(config, on_fallo=_on_fallo)
    monitor.registrar(
        "gestor_bots",
        lambda: _heartbeat_o_falla(
            stubs["gestor_bots"].Heartbeat(common_pb2.HeartbeatRequest(), timeout=5)
        ),
    )
    monitor.registrar(
        "gestor_mundo",
        lambda: _heartbeat_o_falla(
            stubs["gestor_mundo"].Heartbeat(common_pb2.HeartbeatRequest(), timeout=5)
        ),
    )
    monitor.registrar(
        "logica_mundo",
        lambda: _heartbeat_o_falla(
            stubs["logica_mundo"].Heartbeat(common_pb2.HeartbeatRequest(), timeout=5)
        ),
    )
    monitor.registrar(
        "comunicaciones_remoto",
        lambda: _heartbeat_o_falla(
            stubs["comunicaciones_remoto"].Heartbeat(
                common_pb2.HeartbeatRequest(), timeout=5
            )
        ),
    )
    monitor.iniciar()

    # ── 10. Señales ───────────────────────────────────────────
    def _on_signal(sig, frame) -> None:
        logger.info("Señal %s recibida — iniciando shutdown.", sig)
        monitor.detener()
        log_poller.detener()
        coord.ejecutar(reason="user")
        shutdown_completado.set()

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    # ── 11. TODO: servidor WebSocket para Unity ───────────────
    # Se implementará en el siguiente bloque.

    # ── 12. Bucle principal ───────────────────────────────────
    logger.info("Sesión activa. Ctrl+C para cerrar.")
    shutdown_completado.wait()

    logger.info("Cerrando canales gRPC...")
    for canal in canales:
        canal.close()

    sys.exit(exit_code)
