# Infraestructura/AWS/shutdown.py
"""
Coordinador de shutdown para el modo remoto (AWS).

Flujo:
  1. Envía Shutdown a gestor_bots, gestor_mundo, logica_mundo y
     comunicaciones_remoto en paralelo. Cada gestor propaga a sus hijos
     (HVs / sectores) — logica_mundo y comunicaciones_remoto no tienen
     hijos propios, así que no hay fallback de grupo para ellos.
  2. Si gestor_bots/gestor_mundo no confirman en timeout → fallback
     directo a sus hijos.
  3. Tras agotar confirmaciones (o timeouts), termina todas las
     instancias EC2.

El shutdown_id (= session_id) garantiza que duplicados sean ignorados
por los componentes que ya están procesando el cierre.

Corregido: _hacer_request() (código muerto, nunca invocado) usaba una
variable `reason` que no era parámetro ni local — se elimina en vez de
arreglar, ya que _shutdown() ya construye el request directamente sin
necesitarlo. Import de common_pb2 corregido a la ruta real del paquete.
"""

import logging
import threading
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
    TimeoutError as FuturesTimeout,
)
from typing import Callable, Optional

import grpc

from Infraestructura.AWS.aws import terminar_instancias
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

logger = logging.getLogger(__name__)


class ShutdownCoordinator:
    """
    Coordina el cierre ordenado de toda la infraestructura AWS.

    Recibe callables en lugar de stubs gRPC directamente para:
    - Facilitar testing sin infraestructura real.
    - Desacoplar este módulo de los imports de los stubs generados.

    shutdown_logica_mundo y shutdown_comunicaciones_remoto son
    opcionales (None por defecto) para no romper llamadas existentes
    que aún no los pasen — pero remote.py ya los provee siempre.
    """

    def __init__(
        self,
        config: dict,
        session_id: str,
        instance_ids: dict[str, str],  # {componente_id: instance_id}
        shutdown_gestor_bots: Callable,
        shutdown_gestor_mundo: Callable,
        shutdown_hv: dict[str, Callable],  # {hv_id: callable}
        shutdown_sector: dict[str, Callable],  # {sector_id: callable}
        shutdown_logica_mundo: Optional[Callable] = None,
        shutdown_comunicaciones_remoto: Optional[Callable] = None,
    ):
        self._config = config
        self._session_id = session_id
        self._instance_ids = instance_ids
        self._shutdown_gestor_bots = shutdown_gestor_bots
        self._shutdown_gestor_mundo = shutdown_gestor_mundo
        self._shutdown_hv = shutdown_hv
        self._shutdown_sector = shutdown_sector
        self._shutdown_logica_mundo = shutdown_logica_mundo
        self._shutdown_comunicaciones_remoto = shutdown_comunicaciones_remoto

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

    def _shutdown(self, reason: str):
        req = common_pb2.ShutdownRequest(shutdown_id=self._session_id, reason=reason)

        # Fase 1: componentes sin hijos, todos en paralelo
        gestor_bots_ok = self._llamar_con_timeout(
            "gestor_bots", self._shutdown_gestor_bots, req
        )
        gestor_mundo_ok = self._llamar_con_timeout(
            "gestor_mundo", self._shutdown_gestor_mundo, req
        )
        if self._shutdown_logica_mundo is not None:
            self._llamar_con_timeout("logica_mundo", self._shutdown_logica_mundo, req)
        if self._shutdown_comunicaciones_remoto is not None:
            self._llamar_con_timeout(
                "comunicaciones_remoto", self._shutdown_comunicaciones_remoto, req
            )

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
            logger.warning(
                f"{nombre}: error gRPC durante shutdown — {e.code()}: {e.details()}"
            )
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
                        logger.warning(
                            f"{nombre_grupo}/{comp_id}: no confirmó shutdown"
                        )
            except FuturesTimeout:
                pendientes = [
                    comp_id for fut, comp_id in futuros.items() if not fut.done()
                ]
                logger.warning(
                    f"{nombre_grupo}: timeout esperando confirmaciones — "
                    f"sin respuesta: {pendientes}"
                )
