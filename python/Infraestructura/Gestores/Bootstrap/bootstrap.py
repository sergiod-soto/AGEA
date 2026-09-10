# Infraestructura/Gestores/Bootstrap/bootstrap.py
"""
bootstrap.py — Arranque y supervisión en modo local, y arranque de
componente único en modo producción.

Antes vivía todo esto en main.py. Se mueve aquí para que main.py quede
reducido a un punto de entrada CLI mínimo (parseo de argumentos +
despacho), sin lógica de arranque propia.

Usa topologia.py como fuente única de verdad de qué componentes
existen y cuántos — en local, todas las direcciones son "localhost:puerto"
y se conocen de antemano (a diferencia de AWS real, donde hay que
esperar a que cada instancia tenga IP pública asignada — ver remote.py).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import logging.handlers
import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import grpc

from Config.rutas import (
    ROOT,
    SCRIPT_SECTOR,
    SCRIPT_LOGICA_MUNDO,
    SCRIPT_GESTOR_MUNDO,
    SCRIPT_GESTOR_BOTS,
    SCRIPT_HYPERVISOR,
    SCRIPT_COMUNICACIONES_REMOTO,
    SCRIPT_CONSOLA,
)
from Infraestructura.Gestores.Bootstrap.topologia import (
    HEALTHCHECK_INFO,
    ComponenteSpec,
    construir_topologia,
    resolver_env_extra,
)

logger = logging.getLogger("bootstrap")

_SCRIPT_POR_TIPO = {
    "sector": SCRIPT_SECTOR,
    "logica_mundo": SCRIPT_LOGICA_MUNDO,
    "gestor_mundo": SCRIPT_GESTOR_MUNDO,
    "gestor_bots": SCRIPT_GESTOR_BOTS,
    "hypervisor": SCRIPT_HYPERVISOR,
    "comunicaciones_remoto": SCRIPT_COMUNICACIONES_REMOTO,
}


# ─────────────────────────────────────────────────────────────
#  Configuración de entorno y logging del propio orquestador
# ─────────────────────────────────────────────────────────────


def configurar_entorno(modo: str) -> None:
    """
    Carga el fichero .env.<modo> (si existe) y configura el logging del
    propio proceso orquestador. Se llama siempre, independientemente del
    modo — en --modo produccion, _arrancar_componente_produccion() hace
    os.execv() justo después, que reemplaza el proceso entero (y con él,
    este logging), así que no hay conflicto con el logging propio que
    configura cada *_server.py.
    """
    log_dir_local = ROOT / "Logs" / "Local"
    log_dir_local.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                log_dir_local / "main.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            ),
        ],
    )

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
#  Modo local — simula el stack remoto completo en esta máquina
# ─────────────────────────────────────────────────────────────


def _host_puerto_local(spec: ComponenteSpec) -> tuple[str, str]:
    """
    Host y puerto de BIND para un componente en modo local. Única
    fuente de verdad: tanto _env_extra_local (lo que el propio proceso
    usa para escuchar) como _direcciones_locales (lo que los demás
    usan para conectarse a él) llaman aquí, así que no pueden divergir
    en modo local — a diferencia de producción/AWS, donde host de bind
    y dirección de conexión sí son cosas distintas (ver remote.py).
    """
    return "localhost", str(spec.default_port)


def _direcciones_locales(grupos: list[list[ComponenteSpec]]) -> dict[str, str]:
    """
    En local, todas las direcciones se conocen de antemano (los puertos
    son deterministas, no hay que esperar a que AWS asigne una IP) —
    a diferencia de remote.py, que sí tiene que esperar por fases.
    """
    resultado: dict[str, str] = {}
    for grupo in grupos:
        for spec in grupo:
            host, port = _host_puerto_local(spec)
            resultado[spec.nombre] = f"{host}:{port}"
    return resultado


def _env_extra_local(
    spec: ComponenteSpec, direcciones: dict[str, str]
) -> dict[str, str]:
    """Variables propias del proceso (host/puerto de sí mismo) + las
    direcciones ajenas que necesite (ver topologia.resolver_env_extra)."""
    host, port = _host_puerto_local(spec)
    propio = {spec.host_env_var: host, spec.port_env_var: port}
    return {**propio, **resolver_env_extra(spec, direcciones)}


def _lanzar_proceso(
    spec: ComponenteSpec, env_extra: dict[str, str]
) -> subprocess.Popen:
    script = _SCRIPT_POR_TIPO[spec.tipo]
    if not script.exists():
        raise FileNotFoundError(f"Script no encontrado: {script}")

    env = os.environ.copy()
    env.update(env_extra)

    proc = subprocess.Popen([sys.executable, str(script)], env=env, cwd=str(ROOT))
    logger.info("Lanzado %s (pid %d)", spec.nombre, proc.pid)
    return proc


def _healthcheck(spec: ComponenteSpec, timeout_s: int = 30) -> bool:
    """
    Llama a un RPC real del componente hasta que responde o se agota
    timeout_s. Verificar que el canal TCP abre no es suficiente: el
    servidor puede aceptar conexiones mientras aún inicializa servicios.
    """
    import importlib

    address = f"localhost:{spec.default_port}"
    info = HEALTHCHECK_INFO[spec.tipo]
    Stub = getattr(importlib.import_module(info["stub_module"]), info["stub_class"])
    Request = getattr(
        importlib.import_module(info["request_module"]), info["request_class"]
    )
    method = info["method"]

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with grpc.insecure_channel(address) as channel:
                stub = Stub(channel)
                getattr(stub, method)(Request(), timeout=2)
            logger.info("  ✓ %s (%s) listo", spec.nombre, address)
            return True
        except Exception:
            time.sleep(0.5)

    logger.error("  ✗ Timeout esperando %s (%s)", spec.nombre, address)
    return False


def _lanzar_grupo(
    grupo: list[ComponenteSpec], direcciones: dict[str, str]
) -> tuple[list[subprocess.Popen], list[str]]:
    """
    Lanza todos los componentes del grupo y espera su healthcheck en
    paralelo. Devuelve (procesos, nombres de los que fallaron).
    """
    procs = [
        _lanzar_proceso(spec, _env_extra_local(spec, direcciones)) for spec in grupo
    ]

    with ThreadPoolExecutor(max_workers=len(grupo)) as executor:
        oks = list(executor.map(_healthcheck, grupo))

    fallidos = [spec.nombre for spec, ok in zip(grupo, oks) if not ok]
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


def ejecutar_modo_local(escenario: str | None = None) -> None:
    """
    Arranca TODO el stack (lo que en producción corre en AWS: sectores,
    Logica_Mundo, Gestor_Mundo, Gestor_Bots, Hypervisores, y
    Comunicaciones_Remoto) como subprocesos en esta máquina, para poder
    desarrollar/probar sin necesitar AWS real.

    Tras arrancar todo, deja preparado un ComunicacionesLocal apuntando
    al Comunicaciones_Remoto recién lanzado — disponible para cuando
    Vista_Foco/Vision_Unity (aún no implementados) lo necesiten. No se
    fuerza ninguna llamada de prueba a través de él aquí.
    """
    logger.info("=== Modo LOCAL ===")

    if escenario:
        os.environ["ESCENARIO_INICIAL"] = escenario
        logger.info("Escenario inicial: %s", escenario)

    grupos = construir_topologia()
    direcciones = _direcciones_locales(grupos)

    todos_procesos: list[subprocess.Popen] = []
    for grupo in grupos:
        procs, fallidos = _lanzar_grupo(grupo, direcciones)
        todos_procesos.extend(procs)
        if fallidos:
            logger.error("Componentes no arrancaron: %s. Abortando.", fallidos)
            _apagar_procesos(todos_procesos)
            sys.exit(1)

    # Disponible para el resto de módulos locales — ver docstring.
    from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
        ComunicacionesLocal,
    )

    comunicaciones_local = ComunicacionesLocal(direcciones["comunicaciones_remoto"])
    logger.info(
        "ComunicacionesLocal listo, apuntando a %s",
        direcciones["comunicaciones_remoto"],
    )

    _lanzar_consola(direcciones["comunicaciones_remoto"])

    def _shutdown(sig, frame):
        logger.info("Señal %s recibida. Apagando...", sig)
        apagar_solicitado.set()

    apagar_solicitado = threading.Event()

    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, _shutdown)
    else:
        signal.signal(signal.SIGINT, _shutdown)

    logger.info("Stack local completo arrancado y operativo.")

    while True:
        if apagar_solicitado.is_set():
            logger.info("Apagando stack local...")
            _apagar_procesos(todos_procesos)
            sys.exit(0)

        for proc in todos_procesos:
            if proc.poll() is not None:
                logger.error("Proceso (pid %d) ha muerto. Apagando todo.", proc.pid)
                _apagar_procesos(todos_procesos)
                sys.exit(1)

        time.sleep(1)


def _lanzar_consola(comunicaciones_remoto_address: str) -> None:
    """
    Abre la consola de administración como ventana APARTE en Windows,
    invocando python.exe directamente (sin envolver en cmd.exe — ver
    historial: un wrapper "cmd /c" causaba un bug de doble escapado de
    comillas, y además dejaba abierta la posibilidad de un prompt de
    shell real, que es justo lo que no se quiere aquí).

    No soportado fuera de Windows por ahora (ver decisión explícita):
    no hay equivalente fiable a "ventana nueva" sin adivinar qué
    emulador de terminal hay instalado.
    """
    if sys.platform != "win32":
        logger.warning(
            "Consola de administración no soportada fuera de Windows por "
            "ahora — no se lanzará ninguna ventana. (Ver decisión: "
            "solo Windows.)"
        )
        return

    if not SCRIPT_CONSOLA.exists():
        logger.error(
            "SCRIPT_CONSOLA no existe en %s — revisa Config/rutas.py. "
            "El stack seguirá arrancando sin consola.",
            SCRIPT_CONSOLA,
        )
        return

    env = os.environ.copy()
    env["COMUNICACIONES_REMOTO_ADDRESS"] = comunicaciones_remoto_address

    proc = subprocess.Popen(
        [sys.executable, str(SCRIPT_CONSOLA)],
        env=env,
        cwd=str(ROOT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    logger.info(
        "Consola de administración lanzada en ventana aparte (pid %d).", proc.pid
    )


# ─────────────────────────────────────────────────────────────
#  Modo producción — arranque de componente único
# ─────────────────────────────────────────────────────────────


def ejecutar_componente_produccion(args: argparse.Namespace) -> None:

    if args.id:
        os.environ["COMPONENT_ID"] = args.id
    if args.sesion:
        os.environ["SESSION_ID"] = args.sesion
    if args.bucket:
        os.environ["S3_BUCKET"] = args.bucket
    if args.escenario:
        os.environ["ESCENARIO_INICIAL"] = args.escenario

    script = _SCRIPT_POR_TIPO.get(args.componente)
    if script is None:
        logger.error(
            "Componente desconocido: '%s'. Válidos: %s",
            args.componente,
            list(_SCRIPT_POR_TIPO),
        )
        sys.exit(1)

    if not script.exists():
        raise FileNotFoundError(f"Script no encontrado: {script}")

    logger.info(
        "Producción: arrancando %s (id=%s, escenario=%s)",
        args.componente,
        args.id,
        args.escenario,
    )
    os.execv(sys.executable, [sys.executable, str(script)])
