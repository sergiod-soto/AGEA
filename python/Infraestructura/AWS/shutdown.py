"""
Coordinador de shutdown para el modo remoto (AWS).

Flujo:
  1. Envía Shutdown a gestor_bots y gestor_mundo en paralelo.
     Cada gestor propaga a sus hijos (HVs / sectores).
  2. Si un gestor no confirma en timeout → fallback directo a sus hijos.
  3. Tras agotar confirmaciones (o timeouts), termina todas las instancias EC2.

El shutdown_id (= session_id) garantiza que duplicados sean ignorados
por los componentes que ya están procesando el cierre.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from typing import Callable

import grpc

from Infraestructura.AWS.aws import terminar_instancias

logger = logging.getLogger(__name__)

# Importados en tiempo de ejecución para no acoplar este módulo
# a los stubs generados si no están disponibles en el entorno local.
# Se inyectan como callables desde main.py (ver ShutdownCoordinator.__init__).


class ShutdownCoordinator:
    """
    Coordina el cierre ordenado de toda la infraestructura AWS.

    Recibe callables en lugar de stubs gRPC directamente para:
    - Facilitar testing sin infraestructura real.
    - Desacoplar este módulo de los imports de los stubs generados.

    Ejemplo de uso desde main.py:

        coord = ShutdownCoordinator(
            config=config,
            session_id=session_id,
            instance_ids=instance_ids,
            shutdown_gestor_bots=lambda req: gestor_bots_stub.Shutdown(req, timeout=...),
            shutdown_gestor_mundo=lambda req: gestor_mundo_stub.Shutdown(req, timeout=...),
            shutdown_hv={
                "hv_0": lambda req: hv_stubs["hv_0"].Shutdown(req, timeout=...),
                ...
            },
            shutdown_sector={
                "sector_0": lambda req: sector_stubs["sector_0"].Shutdown(req, timeout=...),
                ...
            },
        )
        coord.ejecutar(reason="user")
    """

    def __init__(
        self,
        config: dict,
        session_id: str,
        instance_ids: dict[str, str],          # {componente_id: instance_id}
        shutdown_gestor_bots: Callable,
        shutdown_gestor_mundo: Callable,
        shutdown_hv: dict[str, Callable],       # {hv_id: callable}
        shutdown_sector: dict[str, Callable],   # {sector_id: callable}
    ):
        self._config = config
        self._session_id = session_id
        self._instance_ids = instance_ids
        self._shutdown_gestor_bots = shutdown_gestor_bots
        self._shutdown_gestor_mundo = shutdown_gestor_mundo
        self._shutdown_hv = shutdown_hv
        self._shutdown_sector = shutdown_sector

        self._timeout_shutdown: int = config["timeouts"]["shutdown_segundos"]

        # Garantiza que ejecutar() solo corra una vez aunque se llame
        # desde varios hilos (monitor + señal SIGTERM, por ejemplo).
        self._lock = threading.Lock()
        self._ejecutado = False

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def ejecutar(self, reason: str):
        """
        Punto de entrada único. Thread-safe: llamadas concurrentes
        tras la primera son ignoradas silenciosamente.
        """
        with self._lock:
            if self._ejecutado:
                return
            self._ejecutado = True

        logger.info(f"Iniciando shutdown — razón: {reason}")
        self._shutdown(reason)

    # ------------------------------------------------------------------
    # Implementación
    # ------------------------------------------------------------------

    def _hacer_request(self):
        """Construye el ShutdownRequest. Importado aquí para no acoplar
        este módulo a los stubs si no están generados en el entorno local."""
        from common_pb2 import ShutdownRequest  # type: ignore
        return ShutdownRequest(shutdown_id=self._session_id, reason=reason)

    def _shutdown(self, reason: str):
        from common_pb2 import ShutdownRequest  # type: ignore
        req = ShutdownRequest(shutdown_id=self._session_id, reason=reason)

        # Fase 1: gestores en paralelo
        gestor_bots_ok  = self._llamar_con_timeout("gestor_bots",  self._shutdown_gestor_bots,  req)
        gestor_mundo_ok = self._llamar_con_timeout("gestor_mundo", self._shutdown_gestor_mundo, req)

        # Fase 2 fallback: si un gestor no confirmó, cerramos sus hijos directamente
        if not gestor_bots_ok:
            logger.warning("gestor_bots no confirmó — shutdown directo a HVs")
            self._shutdown_grupo("HVs", self._shutdown_hv, req)

        if not gestor_mundo_ok:
            logger.warning("gestor_mundo no confirmó — shutdown directo a sectores")
            self._shutdown_grupo("sectores", self._shutdown_sector, req)

        # Fase 3: terminar instancias EC2 sin importar qué confirmó
        logger.info("Terminando instancias EC2")
        try:
            terminar_instancias(self._config, list(self._instance_ids.values()))
        except Exception as e:
            # No es recuperable desde aquí; se registra y se continúa.
            logger.error(f"Error al terminar instancias EC2: {e}")

        logger.info("Shutdown completado")

    def _llamar_con_timeout(self, nombre: str, fn: Callable, req) -> bool:
        """
        Llama a fn(req) con timeout.
        Devuelve True si la llamada confirmó ok, False en cualquier otro caso.
        """
        try:
            resp = fn(req)
            if resp.ok:
                logger.info(f"{nombre}: shutdown confirmado")
                return True
            else:
                logger.warning(f"{nombre}: shutdown respondió ok=False — {resp.error}")
                return False
        except grpc.RpcError as e:
            logger.warning(f"{nombre}: error gRPC durante shutdown — {e.code()}: {e.details()}")
            return False
        except Exception as e:
            logger.warning(f"{nombre}: excepción inesperada durante shutdown — {e}")
            return False

    def _shutdown_grupo(self, nombre_grupo: str, grupo: dict[str, Callable], req):
        """
        Envía shutdown en paralelo a un grupo de componentes (HVs o sectores).
        Registra qué confirmó y qué no, pero nunca bloquea indefinidamente.
        """
        if not grupo:
            return

        with ThreadPoolExecutor(max_workers=len(grupo)) as executor:
            futuros = {
                executor.submit(self._llamar_con_timeout, comp_id, fn, req): comp_id
                for comp_id, fn in grupo.items()
            }
            try:
                for futuro in as_completed(futuros, timeout=self._timeout_shutdown):
                    comp_id = futuros[futuro]
                    ok = futuro.result()
                    if not ok:
                        logger.warning(f"{nombre_grupo}/{comp_id}: no confirmó shutdown")
            except FuturesTimeout:
                pendientes = [
                    comp_id for fut, comp_id in futuros.items()
                    if not fut.done()
                ]
                logger.warning(
                    f"{nombre_grupo}: timeout esperando confirmaciones — "
                    f"sin respuesta: {pendientes}"
                )
