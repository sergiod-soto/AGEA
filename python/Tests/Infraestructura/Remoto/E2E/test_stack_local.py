# Tests/Infraestructura/Remoto/E2E/test_stack_local.py
"""
test_stack_local.py — E2E real: arranca "python main.py --modo local"
como subprocess de verdad (mismo mecanismo que usarías tú a mano),
espera a que el log confirme arranque completo, y comprueba un
apagado limpio por SIGTERM.

ASUNCIONES que dependen de tu entorno, verificadas aquí de forma
explícita en vez de asumidas en silencio:
  - Puertos: se sobreescriben todos por variables de entorno propias
    de este test (no se reutilizan los de .env.local), para no chocar
    con una sesión local que puedas tener abierta en la misma máquina.
  - GRID_WIDTH/HEIGHT/SECTOR_SIZE se fuerzan a un mundo de 1 solo
    sector (100x100) para que el arranque sea rápido — probar N
    sectores reales es responsabilidad de un test de integración
    aparte, no de este E2E de humo.
  - SNAPSHOT_DIR apunta a tmp_path — no toca tus snapshots reales.
  - Este test es LENTO (arranca ~6 procesos Python reales) y no se
    incluye en un "pytest" por defecto sin filtro — correr
    explícitamente con: pytest -m e2e
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

ROOT = (
    Path(__file__).resolve().parents[4]
)  # Tests/Infraestructura/Remoto/E2E/ → raíz proyecto


def _entorno_aislado(tmp_path: Path) -> dict:
    """
    Construye el entorno completo para el subprocess, con puertos y
    directorios propios de este test — no depende de que .env.local
    tenga (o no tenga) estos valores, para que el test sea determinista
    sin importar la máquina donde corra.
    """
    env = os.environ.copy()
    env.update(
        {
            "FRESH": "true",
            "GRID_WIDTH": "100",
            "GRID_HEIGHT": "100",
            "SECTOR_SIZE": "100",
            "SECTOR_HOST": "localhost",
            "SECTOR_BASE_PORT": "58100",
            "GESTOR_MUNDO_HOST": "localhost",
            "GESTOR_MUNDO_PORT": "58200",
            "GESTOR_BOTS_HOST": "localhost",
            "GESTOR_BOTS_PORT": "58051",
            "GESTOR_BOTS_ADDRESS": "localhost:58051",
            "LOGICA_MUNDO_HOST": "localhost",
            "LOGICA_MUNDO_PORT": "58250",
            "LOGICA_MUNDO_ADDRESS": "localhost:58250",
            "HYPERVISOR_HOST": "localhost",
            "HYPERVISOR_BASE_PORT": "58300",
            "HYPERVISOR_PROXY_BASE_PORT": "58400",
            "HYPERVISOR_COUNT": "1",
            "COMUNICACIONES_REMOTO_HOST": "localhost",
            "COMUNICACIONES_REMOTO_PORT": "58500",
            "SNAPSHOT_DIR": str(tmp_path / "snapshots"),
            "LOG_DIR": str(tmp_path / "logs"),
        }
    )
    return env


@pytest.mark.e2e
def test_stack_local_arranca_y_se_apaga_limpio(tmp_path):
    env = _entorno_aislado(tmp_path)

    # En Windows, CREATE_NEW_PROCESS_GROUP es imprescindible: sin él,
    # CTRL_BREAK_EVENT se propagaría también a este proceso de test
    # (comparten grupo de consola por defecto) y se mataría a sí mismo.
    # En Linux no hace falta ningún flag especial para SIGTERM.
    creationflags = (
        subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    proceso = subprocess.Popen(
        [sys.executable, "main.py", "--modo", "local"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=creationflags,
    )

    try:
        arranco = _esperar_linea(proceso, "Stack local completo arrancado", timeout=60)
        assert arranco, (
            "El stack no confirmó arranque completo en 60s — revisar stdout "
            "del subprocess para el motivo (puerto ocupado, healthcheck fallido, etc.)"
        )

        # Apagado ordenado — señal "nativa" de cada SO:
        # - Windows: CTRL_BREAK_EVENT (requiere CREATE_NEW_PROCESS_GROUP arriba).
        #   proceso.terminate() en Windows NO sirve para esto: llama a
        #   TerminateProcess y fuerza código de salida 1 sin dar opción
        #   a limpieza — por eso fallaba este test.
        # - Linux: SIGTERM real, capturable con signal.signal().
        if sys.platform == "win32":
            proceso.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            proceso.terminate()
        try:
            proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait(timeout=5)

        codigo = proceso.wait(timeout=15)
        assert codigo == 0, f"El proceso no terminó limpiamente (código {codigo})"

    finally:
        if proceso.poll() is None:
            proceso.kill()
            proceso.wait(timeout=5)


def _esperar_linea(
    proceso: subprocess.Popen, fragmento: str, timeout: float
) -> tuple[bool, str]:
    inicio = time.monotonic()
    lineas_leidas: list[str] = []
    while time.monotonic() - inicio < timeout:
        linea = proceso.stdout.readline()
        if not linea:
            if proceso.poll() is not None:
                break  # el proceso murió antes de arrancar
            continue
        lineas_leidas.append(linea)
        if fragmento in linea:
            return True, "".join(lineas_leidas)
    return False, "".join(lineas_leidas)
