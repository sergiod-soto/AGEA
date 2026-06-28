# main.py
"""
Orquestador del proyecto. Punto de entrada único para local y producción.

Modos:
  LOCAL      — lanza todos los subprocesos en esta máquina.
  PRODUCCION — no lanza nada; cada nodo AWS arranca su _server.py directamente.

Uso:
  python main.py --modo local
  python main.py --modo produccion --componente gestor_mundo
"""

import argparse
import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("main")

# ─────────────────────────────────────────────────────────────
#  Raíz del proyecto (donde vive este fichero)
# ─────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
PYTHON_ROOT = ROOT / "python"  # ⚠ ajustar si la raíz de imports es diferente


# ─────────────────────────────────────────────────────────────
#  Configuración por entorno
# ─────────────────────────────────────────────────────────────

def _cargar_env(modo: str) -> None:
    """Carga el fichero .env.<modo> si existe. No sobreescribe variables ya definidas."""
    env_file = ROOT / f".env.{modo}"
    if not env_file.exists():
        logger.warning("No se encontró %s — usando variables de entorno del sistema.", env_file)
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key not in os.environ:          # no sobreescribir si ya está definida
            os.environ[key] = value.strip()
    logger.info("Entorno cargado desde %s", env_file)


# ─────────────────────────────────────────────────────────────
#  Definición de componentes
# ─────────────────────────────────────────────────────────────

def _build_sector_components() -> list[dict]:
    """
    Genera un componente por sector según GRID_WIDTH, GRID_HEIGHT y SECTOR_SIZE.
    Las direcciones siguen la misma lógica que GestorMundo._sector_address().
    """
    grid_w    = int(os.getenv("GRID_WIDTH",    100))   # ⚠ defaults reducidos para local
    grid_h    = int(os.getenv("GRID_HEIGHT",   100))
    sector_sz = int(os.getenv("SECTOR_SIZE",   100))
    base_port = int(os.getenv("SECTOR_BASE_PORT", 50100))
    host      = os.getenv("SECTOR_HOST", "localhost")

    import math
    cols = math.ceil(grid_w / sector_sz)
    rows = math.ceil(grid_h / sector_sz)

    components = []
    for col in range(cols):
        for row in range(rows):
            port = base_port + col * rows + row
            components.append({
                "nombre":  f"sector_{col}_{row}",
                "script":  PYTHON_ROOT / "Gestores" / "Mundo" / "Sector" / "sector_server.py",
                "healthcheck_address": f"{host}:{port}",
                # ⚠ ajustar el import del stub cuando tengas el proto compilado
                "healthcheck_stub_module": "Gestores.Transporte.Proto_Generated.Sectores.sector_service_pb2_grpc",
                "healthcheck_stub_class":  "SectorServiceStub",
                "env_extra": {
                    f"SECTOR_ADDR_C{col}_R{row}": f"{host}:{port}",
                    "SECTOR_COL":  str(col),
                    "SECTOR_ROW":  str(row),
                    "SECTOR_PORT": str(port),
                },
            })
    return components


def _build_components() -> list[dict]:
    """
    Orden de arranque: sectores → gestor_mundo → gestor_bots → hypervisores.
    Cada grupo espera healthcheck antes de arrancar el siguiente.
    """
    gm_host   = os.getenv("GESTOR_MUNDO_HOST", "localhost")
    gm_port   = int(os.getenv("GESTOR_MUNDO_PORT", 50200))
    gb_host   = os.getenv("GESTOR_BOTS_HOST", "localhost")
    gb_port   = int(os.getenv("GESTOR_BOTS_PORT", 50051))
    hv_host   = os.getenv("HYPERVISOR_HOST", "localhost")
    hv_port   = int(os.getenv("HYPERVISOR_BASE_PORT", 50300))
    hv_count  = int(os.getenv("HYPERVISOR_COUNT", 1))          # ⚠ ajustar para local

    sectores = _build_sector_components()

    gestor_mundo = {
        "nombre": "gestor_mundo",
        "script": PYTHON_ROOT / "Gestores" / "Mundo" / "Gestor_Mundo" / "gestor_mundo_server.py",
        "healthcheck_address": f"{gm_host}:{gm_port}",
        "healthcheck_stub_module": "Gestores.Transporte.Proto_Generated.Sectores.gestor_mundo_service_pb2_grpc",
        "healthcheck_stub_class":  "GestorMundoStub",
        "env_extra": {
            "GESTOR_MUNDO_HOST": gm_host,
            "GESTOR_MUNDO_PORT": str(gm_port),
        },
    }

    gestor_bots = {
        "nombre": "gestor_bots",
        "script": PYTHON_ROOT / "Gestores" / "Bots" / "Gestor_Bots" / "gestor_bots_server.py",
        "healthcheck_address": f"{gb_host}:{gb_port}",
        "healthcheck_stub_module": "Gestores.Transporte.Proto_Generated.Bots.gestor_bots_service_pb2_grpc",
        "healthcheck_stub_class":  "GestorBotsStub",
        "env_extra": {
            "GESTOR_BOTS_HOST":    gb_host,
            "GESTOR_BOTS_PORT":    str(gb_port),
            "GESTOR_MUNDO_ADDRESS": f"{gm_host}:{gm_port}",
        },
    }

    hypervisores = []
    for i in range(hv_count):
        port       = hv_port + i
        proxy_port = int(os.getenv("HYPERVISOR_PROXY_BASE_PORT", 50400)) + i
        hv_id      = f"hv_{i:02d}"
        hypervisores.append({
            "nombre": f"hypervisor_{i:02d}",
            "script": PYTHON_ROOT / "Gestores" / "Bots" / "Hypervisor" / "hypervisor_server.py",
            "healthcheck_address": f"{hv_host}:{port}",
            "healthcheck_stub_module": "Gestores.Transporte.Proto_Generated.Bots.hypervisor_service_pb2_grpc",
            "healthcheck_stub_class":  "HypervisorServiceStub",
            "env_extra": {
                "HYPERVISOR_ID":           hv_id,
                "HYPERVISOR_HOST":         hv_host,
                "HYPERVISOR_PORT":         str(port),
                "HYPERVISOR_PROXY_PORT":   str(proxy_port),
                "GESTOR_BOTS_ADDRESS":     f"{gb_host}:{gb_port}",
                "GESTOR_MUNDO_ADDRESS":    f"{gm_host}:{gm_port}",
            },
        })

    # Grupos ordenados: cada lista es una "barrera" — todos deben estar listos antes del siguiente grupo
    return [
        *sectores,
        gestor_mundo,
        gestor_bots,
        *hypervisores,
    ]


# ─────────────────────────────────────────────────────────────
#  Healthcheck gRPC
# ─────────────────────────────────────────────────────────────

def _healthcheck(address: str, stub_module: str, stub_class: str, timeout_s: int = 30) -> bool:
    """
    Intenta conectar al servicio gRPC en `address` hasta que responde o se agota timeout_s.
    Usa el stub real — si el canal abre, el proceso está listo.
    """
    import importlib

    deadline = time.monotonic() + timeout_s
    mod  = importlib.import_module(stub_module)
    Stub = getattr(mod, stub_class)

    while time.monotonic() < deadline:
        try:
            with grpc.insecure_channel(address) as channel:
                grpc.channel_ready_future(channel).result(timeout=2)
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
        cwd=str(PYTHON_ROOT),   # ⚠ los _server.py hacen imports relativos a PYTHON_ROOT
    )
    logger.info("Lanzado %s (pid %d)", componente["nombre"], proc.pid)
    return proc


def _arrancar_local() -> list[subprocess.Popen]:
    """
    Lanza todos los componentes en orden, con barrera de healthcheck entre grupos.
    Devuelve la lista de procesos para poder apagarlos limpiamente.
    """
    componentes = _build_components()
    procesos: list[tuple[dict, subprocess.Popen]] = []

    # ⚠ Los sectores son el grupo más numeroso. Si GRID=1000 y SECTOR=100 → 100 procesos.
    # Para desarrollo local reduce GRID_WIDTH/GRID_HEIGHT en .env.local.

    for comp in componentes:
        proc = _lanzar_proceso(comp)
        procesos.append((comp, proc))

        ok = _healthcheck(
            comp["healthcheck_address"],
            comp["healthcheck_stub_module"],
            comp["healthcheck_stub_class"],
        )
        if not ok:
            logger.error("Componente %s no arrancó. Abortando.", comp["nombre"])
            _apagar_procesos(procesos)
            sys.exit(1)

    return [p for _, p in procesos]


def _apagar_procesos(procesos: list) -> None:
    """Apaga todos los procesos limpiamente (SIGTERM → SIGKILL tras 5s)."""
    for item in reversed(procesos):
        proc = item[1] if isinstance(item, tuple) else item
        if proc.poll() is None:
            proc.terminate()

    deadline = time.monotonic() + 5
    for item in procesos:
        proc = item[1] if isinstance(item, tuple) else item
        remaining = max(0, deadline - time.monotonic())
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            proc.kill()


# ─────────────────────────────────────────────────────────────
#  Modo producción — arranque de componente único
# ─────────────────────────────────────────────────────────────

def _arrancar_componente_produccion(nombre: str) -> None:
    """
    En producción cada máquina AWS arranca su propio componente.
    Este main.py actúa como wrapper que carga el .env y lanza el _server.py correcto.
    """
    scripts = {
        "gestor_mundo":  PYTHON_ROOT / "Gestores" / "Mundo"  / "Gestor_Mundo" / "gestor_mundo_server.py",
        "gestor_bots":   PYTHON_ROOT / "Gestores" / "Bots"   / "Gestor_Bots"  / "gestor_bots_server.py",
        "hypervisor":    PYTHON_ROOT / "Gestores" / "Bots"   / "Hypervisor"   / "hypervisor_server.py",
        "sector":        PYTHON_ROOT / "Gestores" / "Mundo"  / "Sector"       / "sector_server.py",
    }

    # Normalizar: "sector_0_1" → "sector"
    tipo = nombre.split("_")[0] if "_" in nombre else nombre

    script = scripts.get(tipo)
    if script is None:
        logger.error("Componente desconocido: %s. Opciones: %s", nombre, list(scripts))
        sys.exit(1)

    if not script.exists():
        raise FileNotFoundError(f"Script no encontrado: {script}")

    logger.info("Producción: arrancando %s desde %s", nombre, script)
    os.execv(sys.executable, [sys.executable, str(script)])   # reemplaza este proceso


# ─────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Orquestador del proyecto.")
    parser.add_argument(
        "--modo",
        choices=["local", "produccion"],
        default="local",
        help="Entorno de ejecución.",
    )
    parser.add_argument(
        "--componente",
        default=None,
        help="(Solo producción) Componente a arrancar: gestor_mundo, gestor_bots, hypervisor, sector.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Partida nueva (ignora snapshots existentes).",
    )
    args = parser.parse_args()

    _cargar_env(args.modo)

    if args.fresh:
        os.environ["FRESH_START"] = "1"

    if args.modo == "local":
        logger.info("=== Modo LOCAL ===")
        procesos = _arrancar_local()

        # Apagar limpiamente con Ctrl+C o SIGTERM
        def _shutdown(sig, frame):
            logger.info("Señal %s recibida. Apagando...", sig)
            _apagar_procesos([(None, p) for p in procesos])
            sys.exit(0)

        signal.signal(signal.SIGINT,  _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        # Supervisión: si algún proceso muere, apagar todo
        while True:
            for proc in procesos:
                if proc.poll() is not None:
                    logger.error("Proceso (pid %d) ha muerto. Apagando todo.", proc.pid)
                    _apagar_procesos([(None, p) for p in procesos])
                    sys.exit(1)
            time.sleep(1)

    else:  # produccion
        if args.componente is None:
            logger.error("--componente es obligatorio en modo produccion.")
            sys.exit(1)
        _arrancar_componente_produccion(args.componente)


if __name__ == "__main__":
    main()