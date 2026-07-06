"""
Arranque y ciclo de vida de una sesión en AWS (modo remoto).

Responsabilidades:
  - Determinar si la sesión es nueva o reanudación desde hibernación.
  - Actualizar el Security Group con la IP local actual.
  - Lanzar instancias Spot y esperar que estén operativas.
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
from Infraestructura.Gestores.Log.log_servicer import LogServicer
from Infraestructura.Gestores.Log.log_poller import LogPoller
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
#  Mapping tipo de componente → módulos gRPC
# ─────────────────────────────────────────────────────────────

_STUB_INFO: dict[str, dict] = {
    "gestor_bots": {
        "stub_module": "Gestores.Transporte.Proto_Generated.Bots.gestor_bots_service_pb2_grpc",
        "stub_class": "GestorBotsServiceStub",
        "hc_req_module": "Gestores.Transporte.Proto_Generated.Bots.gestor_bots_service_pb2",
        "hc_req_class": "ListHypervisorsRequest",
        "hc_method": "ListHypervisors",
    },
    "gestor_mundo": {
        "stub_module": "Gestores.Transporte.Proto_Generated.Sectores.gestor_mundo_service_pb2_grpc",
        "stub_class": "GestorMundoServiceStub",
        "hc_req_module": "Gestores.Transporte.Proto_Generated.Sectores.gestor_mundo_service_pb2",
        "hc_req_class": "GetGlobalStateRequest",
        "hc_method": "GetGlobalState",
    },
    "hypervisor": {
        "stub_module": "Gestores.Transporte.Proto_Generated.Bots.hypervisor_service_pb2_grpc",
        "stub_class": "HypervisorServiceStub",
        "hc_req_module": "Gestores.Transporte.Proto_Generated.Bots.hypervisor_service_pb2",
        "hc_req_class": "ListBotsRequest",
        "hc_method": "ListBots",
    },
    "sector": {
        "stub_module": "Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2_grpc",
        "stub_class": "SectorServiceStub",
        "hc_req_module": "Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2",
        "hc_req_class": "GetStateRequest",
        "hc_method": "GetState",
    },
}


def _tipo(comp_id: str) -> str:
    """Infiere el tipo de componente a partir de su ID."""
    if comp_id == "gestor_bots":
        return "gestor_bots"
    if comp_id == "gestor_mundo":
        return "gestor_mundo"
    if comp_id.startswith("hv_"):
        return "hypervisor"
    if comp_id.startswith("sector_"):
        return "sector"
    raise ValueError(f"No se puede inferir tipo de componente para: {comp_id!r}")


# ─────────────────────────────────────────────────────────────
#  Healthcheck remoto
# ─────────────────────────────────────────────────────────────


def _healthcheck_remoto(comp_id: str, ip: str, config: dict) -> bool:
    """
    Llama a un RPC real del componente hasta que responde o se agota el timeout.
    El polling usa intervalos de 2s para dar tiempo al boot desde AMI.
    """
    puerto = config["red"]["puerto_grpc_componentes"]
    timeout = config["timeouts"]["arranque_segundos"]
    address = f"{ip}:{puerto}"
    info = _STUB_INFO[_tipo(comp_id)]

    StubClass = getattr(
        importlib.import_module(info["stub_module"]), info["stub_class"]
    )
    Request = getattr(
        importlib.import_module(info["hc_req_module"]), info["hc_req_class"]
    )
    method = info["hc_method"]

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with grpc.insecure_channel(address) as canal:
                stub = StubClass(canal)
                getattr(stub, method)(Request(), timeout=2)
            logger.info("  ✓ %s (%s) listo", comp_id, address)
            return True
        except Exception:
            time.sleep(2)

    logger.error("  ✗ Timeout esperando %s (%s)", comp_id, address)
    return False


# ─────────────────────────────────────────────────────────────
#  Stubs persistentes
# ─────────────────────────────────────────────────────────────


def _crear_stubs(
    ip_por_comp: dict[str, str],
    config: dict,
) -> tuple[dict, dict, list[grpc.Channel]]:
    """
    Crea un canal gRPC persistente por componente, y sobre cada canal dos
    stubs: el del servicio principal (varía por tipo de componente) y el
    de LogPullService (idéntico en los cuatro tipos — mismo .proto, mismo
    servidor y puerto que el servicio principal).
    """
    puerto = config["red"]["puerto_grpc_componentes"]
    stubs = {}
    log_stubs = {}
    canales = []

    for comp_id, ip in ip_por_comp.items():
        canal = grpc.insecure_channel(f"{ip}:{puerto}")
        canales.append(canal)

        info = _STUB_INFO[_tipo(comp_id)]
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
#  Arranque remoto
# ─────────────────────────────────────────────────────────────


def arrancar_remoto(config: dict, fresh: bool) -> None:
    # Importados aquí para no acoplar este módulo a los stubs
    # si se ejecuta en un entorno sin los protos generados.
    from common_pb2 import HeartbeatRequest  # type: ignore

    timeout_shutdown = config["timeouts"]["shutdown_segundos"]

    # ── 1. Determinar sesión ──────────────────────────────────
    session_id_anterior = None if fresh else leer_ultima_sesion(config)
    session_id = session_id_anterior or nueva_session_id()
    modo = "reanudación" if session_id_anterior else "nueva"
    logger.info("Sesión %s: %s", modo, session_id)

    # ── 2. Actualizar Security Group ──────────────────────────
    mi_ip = obtener_ip_publica()
    actualizar_security_group(config, mi_ip)

    # ── 3. Lanzar instancias Spot ─────────────────────────────
    logger.info("Lanzando instancias Spot...")
    try:
        id_por_comp = lanzar_instancias(config, session_id)
    except RuntimeError as e:
        logger.error("No se pudo arrancar la infraestructura: %s", e)
        sys.exit(1)

    guardar_sesion_activa(config, session_id)

    # ── 4. Esperar IPs públicas ───────────────────────────────
    logger.info("Esperando IPs públicas...")
    try:
        ip_por_comp = esperar_ips_publicas(
            config,
            id_por_comp,
            timeout=config["timeouts"]["arranque_segundos"],
        )
    except TimeoutError as e:
        logger.error("%s", e)
        terminar_instancias(config, list(id_por_comp.values()))
        sys.exit(1)

    # ── 5. Healthcheck de todos los componentes ───────────────
    logger.info("Esperando que los componentes estén listos...")

    def _check(item: tuple[str, str]) -> tuple[str, bool]:
        comp_id, ip = item
        return comp_id, _healthcheck_remoto(comp_id, ip, config)

    with ThreadPoolExecutor(max_workers=len(ip_por_comp)) as executor:
        resultados = dict(executor.map(_check, ip_por_comp.items()))

    fallidos = [c for c, ok in resultados.items() if not ok]
    if fallidos:
        logger.error("Componentes que no respondieron: %s. Abortando.", fallidos)
        terminar_instancias(config, list(id_por_comp.values()))
        sys.exit(1)

    logger.info("Todos los componentes listos.")

    # ── 6. Crear stubs persistentes ───────────────────────────
    stubs, log_stubs, canales = _crear_stubs(ip_por_comp, config)

    # ── 6.1 Recolección de logs (modelo pull) ─────────────────
    # Cada componente remoto acumula sus logs en memoria y los expone vía
    # PullLogs; aquí, en la máquina local, se pregunta periódicamente y se
    # escriben a disco con LogServicer (misma estructura de carpetas que
    # en modo local — ver log_categorias.py).
    log_servicer = LogServicer(log_dir=LOG_DIR)
    log_poller = LogPoller(
        intervalo_segundos=LOG_PULL_INTERVAL_SEGUNDOS,
        escribir=log_servicer.escribir,
    )
    for comp_id, log_stub in log_stubs.items():
        log_poller.registrar(
            comp_id,
            # Valores por defecto en el lambda para capturar log_stub por
            # closure correctamente — mismo problema (y misma solución)
            # que _make_shutdown_fn más abajo: sin esto, todas las
            # llamadas usarían el último stub del bucle.
            lambda req=log_pull_service_pb2.PullLogsRequest(), stub=log_stub: (
                stub.PullLogs(req, timeout=5).records
            ),
        )
    log_poller.iniciar()

    # ── 7. Si es reanudación, borrar hibernación de S3 ────────
    # Se borra después de que los componentes están listos, no antes,
    # para poder reintentar con los mismos datos si el arranque falla.
    if session_id_anterior:
        borrar_sesion_hibernada(config, session_id_anterior)

    # ── 8. Evento de cierre ───────────────────────────────────
    # Señala al bucle principal que el shutdown ha terminado.
    shutdown_completado = threading.Event()
    exit_code = 0  # 0 = usuario, 1 = fallo

    # ── 9. Shutdown coordinator ───────────────────────────────
    hv_ids = [c for c in ip_por_comp if c.startswith("hv_")]
    sector_ids = [c for c in ip_por_comp if c.startswith("sector_")]

    coord = ShutdownCoordinator(
        config=config,
        session_id=session_id,
        instance_ids=id_por_comp,
        shutdown_gestor_bots=_make_shutdown_fn(stubs["gestor_bots"], timeout_shutdown),
        shutdown_gestor_mundo=_make_shutdown_fn(
            stubs["gestor_mundo"], timeout_shutdown
        ),
        shutdown_hv={
            hv: _make_shutdown_fn(stubs[hv], timeout_shutdown) for hv in hv_ids
        },
        shutdown_sector={
            sec: _make_shutdown_fn(stubs[sec], timeout_shutdown) for sec in sector_ids
        },
    )

    # ── 10. Monitor ───────────────────────────────────────────
    # Solo los dos gestores entran en el monitor; ellos informan
    # del estado de sus hijos (HVs / sectores) en la respuesta de heartbeat.
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
        lambda: stubs["gestor_bots"].Heartbeat(HeartbeatRequest(), timeout=5),
    )
    monitor.registrar(
        "gestor_mundo",
        lambda: stubs["gestor_mundo"].Heartbeat(HeartbeatRequest(), timeout=5),
    )
    monitor.iniciar()

    # ── 11. Señales ───────────────────────────────────────────
    def _on_signal(sig, frame) -> None:
        logger.info("Señal %s recibida — iniciando shutdown.", sig)
        monitor.detener()
        log_poller.detener()
        coord.ejecutar(reason="user")
        shutdown_completado.set()

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    # ── 12. TODO: servidor WebSocket para Unity ───────────────
    # Se implementará en el siguiente bloque.
    # El servidor correrá en un hilo daemon y recibirá peticiones
    # de arranque/parada/estado desde Unity.

    # ── 13. Bucle principal ───────────────────────────────────
    logger.info("Sesión activa. Ctrl+C para cerrar.")
    shutdown_completado.wait()

    logger.info("Cerrando canales gRPC...")
    for canal in canales:
        canal.close()

    sys.exit(exit_code)
