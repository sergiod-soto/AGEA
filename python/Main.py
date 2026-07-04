# main.py
"""
Orquestador del proyecto. Punto de entrada único para local y producción.

Modos:
  LOCAL      — lanza todos los subprocesos en esta máquina.
  PRODUCCION — no lanza nada; cada nodo AWS arranca su _server.py directamente.

Uso:
  $env:FRESH="true"; python main.py --modo local
  python main.py --modo produccion --componente gestor_mundo --id gestor_mundo --sesion <id> --bucket <bucket>
"""

import argparse
import importlib
import logging
import math
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("main")

from Config.rutas import (
    ROOT,
    SCRIPT_SECTOR,
    SCRIPT_GESTOR_MUNDO,
    SCRIPT_GESTOR_BOTS,
    SCRIPT_HYPERVISOR,
)

# ─────────────────────────────────────────────────────────────
#  Configuración por entorno
# ─────────────────────────────────────────────────────────────


def _cargar_env(modo: str) -> None:
    """Carga el fichero .env.<modo> si existe. No sobreescribe variables ya definidas."""
    env_file = ROOT / f".env.{modo}"
    if not env_file.exists():
        logger.warning(
            "No se encontró %s — usando variables de entorno del sistema.", env_file
        )
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key not in os.environ:
            os.environ[key] = value.strip()
    logger.info("Entorno cargado desde %s", env_file)


# ─────────────────────────────────────────────────────────────
#  Definición de componentes
# ─────────────────────────────────────────────────────────────


def _build_sector_components() -> list[dict]:
    grid_w = int(os.getenv("GRID_WIDTH", 100))  # defaults reducidos para local
    grid_h = int(os.getenv("GRID_HEIGHT", 100))
    sector_sz = int(os.getenv("SECTOR_SIZE", 100))
    base_port = int(os.getenv("SECTOR_BASE_PORT", 50100))
    host = os.getenv("SECTOR_HOST", "localhost")

    cols = math.ceil(grid_w / sector_sz)
    rows = math.ceil(grid_h / sector_sz)

    components = []
    for col in range(cols):
        for row in range(rows):
            port = base_port + col * rows + row
            components.append(
                {
                    "nombre": f"sector_{col}_{row}",
                    "script": SCRIPT_SECTOR,
                    "healthcheck_address": f"{host}:{port}",
                    "healthcheck_stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2_grpc",
                    "healthcheck_stub_class": "SectorServiceStub",
                    "healthcheck_request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2",
                    "healthcheck_request_class": "GetStateRequest",
                    "healthcheck_method": "GetState",
                    "env_extra": {
                        f"SECTOR_ADDR_C{col}_R{row}": f"{host}:{port}",
                        "SECTOR_COL": str(col),
                        "SECTOR_ROW": str(row),
                        "SECTOR_PORT": str(port),
                    },
                }
            )
    return components


def _build_components() -> list[list[dict]]:
    """
    Devuelve grupos de componentes ordenados por arranque.
    Todos los componentes de un grupo se lanzan en paralelo;
    el grupo siguiente no empieza hasta que todos los del anterior
    hayan superado el healthcheck.

    Orden: sectores → gestor_mundo → gestor_bots → hypervisores
    """
    gm_host = os.getenv("GESTOR_MUNDO_HOST", "localhost")
    gm_port = int(os.getenv("GESTOR_MUNDO_PORT", 50200))
    gb_host = os.getenv("GESTOR_BOTS_HOST", "localhost")
    gb_port = int(os.getenv("GESTOR_BOTS_PORT", 50051))
    hv_host = os.getenv("HYPERVISOR_HOST", "localhost")
    hv_port = int(os.getenv("HYPERVISOR_BASE_PORT", 50300))
    hv_count = int(os.getenv("HYPERVISOR_COUNT", 1))  #  ajustar para local

    sectores = _build_sector_components()

    gestor_mundo = {
        "nombre": "gestor_mundo",
        "script": SCRIPT_GESTOR_MUNDO,
        "healthcheck_address": f"{gm_host}:{gm_port}",
        "healthcheck_stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.gestor_mundo_service_pb2_grpc",
        "healthcheck_stub_class": "GestorMundoServiceStub",
        "healthcheck_request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Sectores.gestor_mundo_service_pb2",
        "healthcheck_request_class": "GetGlobalStateRequest",
        "healthcheck_method": "GetGlobalState",
        "env_extra": {
            "GESTOR_MUNDO_HOST": gm_host,
            "GESTOR_MUNDO_PORT": str(gm_port),
        },
    }

    gestor_bots = {
        "nombre": "gestor_bots",
        "script": SCRIPT_GESTOR_BOTS,
        "healthcheck_address": f"{gb_host}:{gb_port}",
        "healthcheck_stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Bots.gestor_bots_service_pb2_grpc",
        "healthcheck_stub_class": "GestorBotsServiceStub",
        "healthcheck_request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Bots.gestor_bots_service_pb2",
        "healthcheck_request_class": "ListHypervisorsRequest",
        "healthcheck_method": "ListHypervisors",
        "env_extra": {
            "GESTOR_BOTS_HOST": gb_host,
            "GESTOR_BOTS_PORT": str(gb_port),
            "GESTOR_MUNDO_ADDRESS": f"{gm_host}:{gm_port}",
        },
    }

    hypervisores = []
    for i in range(hv_count):
        port = hv_port + i
        proxy_port = int(os.getenv("HYPERVISOR_PROXY_BASE_PORT", 50400)) + i
        hv_id = f"hv_{i:02d}"
        hypervisores.append(
            {
                "nombre": f"hypervisor_{i:02d}",
                "script": SCRIPT_HYPERVISOR,
                "healthcheck_address": f"{hv_host}:{port}",
                "healthcheck_stub_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Bots.hypervisor_service_pb2_grpc",
                "healthcheck_stub_class": "HypervisorServiceStub",
                "healthcheck_request_module": "Infraestructura.Gestores.Transporte.Proto_Generated.Bots.hypervisor_service_pb2",
                "healthcheck_request_class": "ListBotsRequest",
                "healthcheck_method": "ListBots",
                "env_extra": {
                    "HYPERVISOR_ID": hv_id,
                    "HYPERVISOR_HOST": hv_host,
                    "HYPERVISOR_PORT": str(port),
                    "HYPERVISOR_PROXY_PORT": str(proxy_port),
                    "GESTOR_BOTS_ADDRESS": f"{gb_host}:{gb_port}",
                    "GESTOR_MUNDO_ADDRESS": f"{gm_host}:{gm_port}",
                },
            }
        )

    return [
        sectores,
        [gestor_mundo],
        [gestor_bots],
        hypervisores,
    ]


# ─────────────────────────────────────────────────────────────
#  Healthcheck gRPC
# ─────────────────────────────────────────────────────────────


def _healthcheck(comp: dict, timeout_s: int = 30) -> bool:
    """
    Llama a un RPC real del componente hasta que responde o se agota timeout_s.
    Verificar que el canal TCP abre (channel_ready_future) no es suficiente:
    el servidor puede aceptar conexiones mientras aún inicializa sus servicios.
    """
    address = comp["healthcheck_address"]
    Stub = getattr(
        importlib.import_module(comp["healthcheck_stub_module"]),
        comp["healthcheck_stub_class"],
    )
    Request = getattr(
        importlib.import_module(comp["healthcheck_request_module"]),
        comp["healthcheck_request_class"],
    )
    method = comp["healthcheck_method"]

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with grpc.insecure_channel(address) as channel:
                stub = Stub(channel)
                getattr(stub, method)(Request(), timeout=2)
            logger.info("  ✓ %s listo", address)
            return True
        except Exception:
            time.sleep(0.5)

    logger.error("  ✗ Timeout esperando %s", address)
    return False


# ─────────────────────────────────────────────────────────────
#  Arranque de procesos
# ─────────────────────────────────────────────────────────────


def _lanzar_proceso(componente: dict) -> subprocess.Popen:
    env = os.environ.copy()
    env.update(componente.get("env_extra", {}))

    script = componente["script"]
    if not script.exists():
        raise FileNotFoundError(f"Script no encontrado: {script}")

    proc = subprocess.Popen(
        [sys.executable, str(script)],
        env=env,
        cwd=str(ROOT),
    )
    logger.info("Lanzado %s (pid %d)", componente["nombre"], proc.pid)
    return proc


def _lanzar_grupo(grupo: list[dict]) -> tuple[list[subprocess.Popen], list[str]]:
    """
    Lanza todos los componentes del grupo y espera healthcheck de todos en paralelo.
    Los procesos se lanzan primero para que inicialicen en paralelo mientras
    esperamos sus healthchecks.
    Devuelve (procesos, nombres de los que fallaron el healthcheck).
    """

    hv_count = int(os.getenv("HYPERVISOR_COUNT", 1))
    if hv_count < 1:
        raise ValueError(f"HYPERVISOR_COUNT debe ser >= 1, recibido: {hv_count}")

    procs = [_lanzar_proceso(comp) for comp in grupo]

    # executor.map preserva el orden de entrada, por lo que zip es seguro
    with ThreadPoolExecutor(max_workers=len(grupo)) as executor:
        oks = list(executor.map(_healthcheck, grupo))

    fallidos = [comp["nombre"] for comp, ok in zip(grupo, oks) if not ok]
    return procs, fallidos


def _apagar_procesos(procesos: list[subprocess.Popen]) -> None:
    """Apaga todos los procesos limpiamente (SIGTERM → SIGKILL tras 5s)."""
    for proc in reversed(procesos):
        if proc.poll() is None:
            proc.terminate()

    deadline = time.monotonic() + 5
    for proc in procesos:
        remaining = max(0.0, deadline - time.monotonic())
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            proc.kill()


def _arrancar_local() -> list[subprocess.Popen]:
    grupos = _build_components()
    todos_procesos: list[subprocess.Popen] = []

    for grupo in grupos:
        procs, fallidos = _lanzar_grupo(grupo)
        todos_procesos.extend(procs)
        if fallidos:
            logger.error("Componentes no arrancaron: %s. Abortando.", fallidos)
            _apagar_procesos(todos_procesos)
            sys.exit(1)

    return todos_procesos


# ─────────────────────────────────────────────────────────────
#  Modo producción — arranque de componente único
# ─────────────────────────────────────────────────────────────


def _arrancar_componente_produccion(args: argparse.Namespace) -> None:
    """
    En producción, main.py recibe el tipo de componente a arrancar y sus
    metadatos (id, sesión, bucket). Los metadatos se exponen como variables
    de entorno para que el server script los lea con os.getenv.
    """
    if args.id:
        os.environ["COMPONENT_ID"] = args.id
    if args.sesion:
        os.environ["SESSION_ID"] = args.sesion
    if args.bucket:
        os.environ["S3_BUCKET"] = args.bucket

    scripts = {
        "gestor_mundo": SCRIPT_GESTOR_MUNDO,
        "gestor_bots": SCRIPT_GESTOR_BOTS,
        "hypervisor": SCRIPT_HYPERVISOR,
        "sector": SCRIPT_SECTOR,
    }

    script = scripts.get(args.componente)
    if script is None:
        logger.error(
            "Componente desconocido: '%s'. Válidos: %s",
            args.componente,
            list(scripts),
        )
        sys.exit(1)

    if not script.exists():
        raise FileNotFoundError(f"Script no encontrado: {script}")

    logger.info("Producción: arrancando %s (id=%s)", args.componente, args.id)
    os.execv(sys.executable, [sys.executable, str(script)])


# ─────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Orquestador del proyecto.")
    parser.add_argument(
        "--modo",
        choices=["local", "produccion", "remoto"],
        default="local",
        help="Entorno de ejecución.",
    )
    parser.add_argument(
        "--componente",
        default=None,
        help="(Solo producción) Tipo de componente: gestor_mundo, gestor_bots, hypervisor, sector.",
    )
    parser.add_argument(
        "--id",
        default=None,
        help="(Solo producción) ID único de esta instancia del componente (ej: hv_00, sector_0_1).",
    )
    parser.add_argument(
        "--sesion",
        default=None,
        help="(Solo producción) ID de sesión de la partida activa.",
    )
    parser.add_argument(
        "--bucket",
        default=None,
        help="(Solo producción) Nombre del bucket S3.",
    )

    args = parser.parse_args()

    _cargar_env(args.modo)

    if args.modo == "local":
        logger.info("=== Modo LOCAL ===")
        procesos = _arrancar_local()

        def _shutdown(sig, frame):
            logger.info("Señal %s recibida. Apagando...", sig)
            _apagar_procesos(procesos)
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        while True:
            for proc in procesos:
                if proc.poll() is not None:
                    logger.error("Proceso (pid %d) ha muerto. Apagando todo.", proc.pid)
                    _apagar_procesos(procesos)
                    sys.exit(1)
            time.sleep(1)

    elif args.modo == "remoto":
        logger.info("=== Modo REMOTO ===")
        import yaml

        config_path = ROOT / "config.yaml"
        if not config_path.exists():
            logger.error("No se encontró config.yaml en %s", ROOT)
            sys.exit(1)
        with open(config_path) as f:
            config = yaml.safe_load(f)
        from Infraestructura.AWS.remote import arrancar_remoto

        arrancar_remoto(config, args.fresh)

    else:  # produccion
        if args.componente is None:
            logger.error("--componente es obligatorio en modo produccion.")
            sys.exit(1)
        _arrancar_componente_produccion(args)


if __name__ == "__main__":
    main()
