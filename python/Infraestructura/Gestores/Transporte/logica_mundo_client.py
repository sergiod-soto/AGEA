# Infraestructura/Gestores/Transporte/logica_mundo_client.py
"""
logica_mundo_client.py — Cliente async gRPC hacia LogicaMundo.

Usado por:
  - Gestor_Mundo   → celdas de región, actualizar celdas, celdas de
                      atmósfera, progreso de ciclos globales, elementos
                      globales, snapshots (ver gestor_mundo.py)
  - Gestor_Bots    → resolver_accion (reenvío de acciones de bots)
  - Comunicacion_Remoto (local) → consultar_representacion, eventos
                      globales, alta/edición/baja de elementos
  - Comunicaciones_Remoto → heartbeat() (ver comunicaciones_remoto_servicer.py)

Mismo patrón que gestor_mundo_client.py / hypervisor_client.py: canal
único, reconexión perezosa, conversión de tipos Python nativos
(tuplas, dicts) a mensajes proto y viceversa, para que quien lo use no
tenga que conocer el formato de transporte.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Optional

import grpc.aio

from Infraestructura.Gestores.tipos_comunes import ActionResult
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2_grpc as pb_grpc,
)

logger = logging.getLogger(__name__)


class LogicaMundoClient:

    def __init__(self, address: str, timeout: float = 10.0):
        self._address = address
        self._timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub = None

    async def _ensure_channel(self) -> None:
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(self._address)
            self._stub = pb_grpc.LogicaMundoServiceStub(self._channel)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None

    def _t(self, timeout: Optional[float]) -> float:
        return timeout if timeout is not None else self._timeout

    @staticmethod
    def _pos_to_pb(pos: tuple[int, int]) -> common_pb.Position:
        x, y = pos
        return common_pb.Position(x=x, y=y)

    @staticmethod
    def _pos_from_pb(pos: common_pb.Position) -> tuple[int, int]:
        return (pos.x, pos.y)

    # ------------------------------------------------------------------
    # Infraestructura
    # ------------------------------------------------------------------

    async def heartbeat(
        self, timeout: float | None = None
    ) -> "pb.LogicaMundoHeartbeatResponse":
        """
        Llama al RPC Heartbeat real de LogicaMundoService. Usado por
        Comunicaciones_Remoto para detectar si este subordinado sigue
        vivo (ver comunicaciones_remoto_servicer.py::Heartbeat).
        """
        await self._ensure_channel()
        return await self._stub.Heartbeat(
            common_pb.HeartbeatRequest(), timeout=self._t(timeout)
        )

    # ------------------------------------------------------------------
    # Identidad
    # ------------------------------------------------------------------

    async def asignar_id(self, timeout: float | None = None) -> int:
        await self._ensure_channel()
        try:
            resp = await self._stub.AsignarId(
                pb.AsignarIdRequest(), timeout=self._t(timeout)
            )
            return resp.id_elemento
        except grpc.aio.AioRpcError as exc:
            logger.error("AsignarId falló: %s", exc)
            raise

    async def ejecutar_comando_consola(
        self, tipo: str, payload: bytes, timeout: float | None = None
    ) -> tuple[bool, str, bytes]:
        await self._ensure_channel()
        req = pb.ComandoConsolaRequest(tipo=tipo, payload=payload)
        try:
            resp = await self._stub.EjecutarComandoConsola(
                req, timeout=self._t(timeout)
            )
            return resp.ok, resp.error, resp.payload
        except grpc.aio.AioRpcError as exc:
            logger.error("EjecutarComandoConsola(%s) falló: %s", tipo, exc)
            return False, str(exc), b""

    # ------------------------------------------------------------------
    # Elementos
    # ------------------------------------------------------------------

    async def crear_elemento(
        self,
        pos: tuple[int, int],
        type_id: str,
        element: bytes,
        timeout: float | None = None,
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.CrearElementoRequest(
            pos=self._pos_to_pb(pos), type_id=type_id, element=element
        )
        try:
            resp = await self._stub.CrearElemento(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("CrearElemento falló: %s", exc)
            return False, str(exc)

    async def modificar_elemento(
        self,
        pos: tuple[int, int],
        element_id: int,
        patch: bytes,
        timeout: float | None = None,
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.ModificarElementoRequest(
            pos=self._pos_to_pb(pos), element_id=element_id, patch=patch
        )
        try:
            resp = await self._stub.ModificarElemento(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("ModificarElemento falló: %s", exc)
            return False, str(exc)

    async def eliminar_elemento(
        self,
        pos: tuple[int, int],
        element_id: int,
        timeout: float | None = None,
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.EliminarElementoRequest(
            pos=self._pos_to_pb(pos), element_id=element_id
        )
        try:
            resp = await self._stub.EliminarElemento(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("EliminarElemento falló: %s", exc)
            return False, str(exc)

    # ------------------------------------------------------------------
    # Acciones de bots
    # ------------------------------------------------------------------

    async def resolver_accion(
        self,
        bot_id: int,
        action_type: str,
        payload: bytes = b"",
        timeout: float | None = None,
    ) -> ActionResult:
        await self._ensure_channel()
        req = pb.ResolverAccionRequest(
            bot_id=bot_id, action_type=action_type, payload=payload
        )
        try:
            resp = await self._stub.ResolverAccion(req, timeout=self._t(timeout))
            return ActionResult(
                ok=resp.ok,
                payload=resp.payload,
                error=resp.error,
                world_tick=resp.world_tick,
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("ResolverAccion falló: %s", exc)
            return ActionResult(ok=False, error=str(exc))

    async def eliminar_avatar_bot(
        self, bot_id: int, timeout: float | None = None
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.EliminarAvatarBotRequest(bot_id=bot_id)
        try:
            resp = await self._stub.EliminarAvatarBot(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("EliminarAvatarBot falló: %s", exc)
            return False, str(exc)

    async def matar_bot(
        self, bot_id: int, cause: str, tick_id: int, timeout: float | None = None
    ) -> tuple[bool, str]:
        # "Blando": el gestor no usa el resultado.
        await self._ensure_channel()
        req = pb.MatarBotRequest(bot_id=bot_id, cause=cause, tick_id=tick_id)
        try:
            resp = await self._stub.MatarBot(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("MatarBot falló: %s", exc)
            return False, str(exc)

    # ------------------------------------------------------------------
    # Eventos globales
    # ------------------------------------------------------------------

    async def spawn_global_event(
        self,
        event_id: str,
        type_: str,
        pos: Optional[tuple[int, int]],
        payload: bytes,
        timeout: float | None = None,
    ) -> tuple[bool, str, str]:
        await self._ensure_channel()
        event = pb.GlobalEvent(
            event_id=event_id,
            type=type_,
            pos=self._pos_to_pb(pos) if pos is not None else common_pb.Position(),
            payload=payload,
        )
        try:
            resp = await self._stub.SpawnGlobalEvent(
                pb.SpawnGlobalEventRequest(event=event), timeout=self._t(timeout)
            )
            return resp.ok, resp.error, resp.event_id
        except grpc.aio.AioRpcError as exc:
            logger.error("SpawnGlobalEvent falló: %s", exc)
            return False, str(exc), ""

    async def despawn_global_event(
        self, event_id: str, reason: str, timeout: float | None = None
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.DespawnGlobalEventRequest(event_id=event_id, reason=reason)
        try:
            resp = await self._stub.DespawnGlobalEvent(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("DespawnGlobalEvent falló: %s", exc)
            return False, str(exc)

    async def get_active_events(self, timeout: float | None = None) -> list:
        await self._ensure_channel()
        try:
            resp = await self._stub.GetActiveEvents(
                pb.GetActiveEventsRequest(), timeout=self._t(timeout)
            )
            return list(resp.events)
        except grpc.aio.AioRpcError as exc:
            logger.error("GetActiveEvents falló: %s", exc)
            return []

    async def get_elementos_globales(
        self, timeout: float | None = None
    ) -> "pb.GetElementosGlobalesResponse":
        await self._ensure_channel()
        try:
            return await self._stub.GetElementosGlobales(
                pb.GetElementosGlobalesRequest(), timeout=self._t(timeout)
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("GetElementosGlobales falló: %s", exc)
            return pb.GetElementosGlobalesResponse(ok=False, error=str(exc))

    # ------------------------------------------------------------------
    # Soporte al mundo
    # ------------------------------------------------------------------

    async def generar_mundo(self, timeout: float | None = None) -> None:
        await self._ensure_channel()
        resp = await self._stub.GenerarMundo(
            pb.GenerarMundoRequest(), timeout=self._t(timeout)
        )
        if not resp.ok:
            raise RuntimeError(f"GenerarMundo: {resp.error}")

    async def esperar_generacion_mundo(
        self, intervalo: float = 1.0, timeout_total: float | None = None
    ) -> None:
        """Sondea EstadoGeneracionMundo hasta COMPLETADA. RuntimeError si ERROR
        o si se agota timeout_total (None = esperar sin límite)."""
        await self._ensure_channel()
        inicio = time.monotonic()
        while True:
            resp = await self._stub.EstadoGeneracionMundo(
                pb.EstadoGeneracionMundoRequest(), timeout=self._t(None)
            )
            estado = pb.EstadoGeneracion.Name(resp.estado)
            if estado == "COMPLETADA":
                return
            if estado == "ERROR":
                raise RuntimeError(f"Generación del mundo fallida: {resp.error}")
            if estado == "NO_INICIADA":
                raise RuntimeError(
                    "La generación no se ha iniciado: llama antes a generar_mundo()."
                )
            logger.info("Generando mundo... %.0f %%", resp.progreso * 100)
            if timeout_total is not None and time.monotonic() - inicio > timeout_total:
                raise RuntimeError("Tiempo agotado esperando la generación del mundo.")
            await asyncio.sleep(intervalo)

    # ------------------------------------------------------------------
    # Soporte al ciclo de tick de Gestor_Mundo
    # ------------------------------------------------------------------

    async def obtener_celdas_en_region(
        self,
        min_pos,
        max_pos,
        excluir_min=None,
        excluir_max=None,
        timeout: float | None = None,
    ) -> list:
        await self._ensure_channel()
        tiene_exclusion = excluir_min is not None and excluir_max is not None
        req = pb.ObtenerCeldasEnRegionRequest(
            min=self._pos_to_pb(min_pos),
            max=self._pos_to_pb(max_pos),
            tiene_exclusion=tiene_exclusion,
        )
        if tiene_exclusion:
            req.excluir_min.CopyFrom(self._pos_to_pb(excluir_min))
            req.excluir_max.CopyFrom(self._pos_to_pb(excluir_max))
        # PROPAGA: [] es un resultado válido ("región vacía") y un fallo no
        # debe confundirse con él. El AioRpcError sube tal cual.
        resp = await self._stub.ObtenerCeldasEnRegion(req, timeout=self._t(timeout))
        if not resp.ok:
            raise RuntimeError(f"ObtenerCeldasEnRegion: {resp.error}")
        return list(resp.cells)

    async def actualizar_celdas(
        self,
        changed_cells: list,
        movimientos_externos: list | None = None,
        timeout: float | None = None,
    ) -> dict[int, tuple[int, int] | None]:
        """Devuelve los movimientos rechazados: {id_elemento: pos a la que se
        devolvió, o None si el elemento se eliminó}. PROPAGA errores."""
        await self._ensure_channel()
        req = pb.ActualizarCeldasRequest(
            changed_cells=changed_cells,
            movimientos_externos=movimientos_externos or [],
        )
        resp = await self._stub.ActualizarCeldas(req, timeout=self._t(timeout))
        if not resp.ok:
            raise RuntimeError(f"ActualizarCeldas: {resp.error}")
        return {
            r.id_elemento: None if r.eliminado else (r.pos_devuelta.x, r.pos_devuelta.y)
            for r in resp.rechazados
        }

    # ---- Sistema atmosférico (NUEVO) ----
    #
    # Mismo trío que obtener_celdas_en_region/actualizar_celdas, en
    # versión atmósfera, más obtener_progreso_ciclos (sin equivalente
    # de terreno -- es un dato global, no por región).

    async def obtener_celdas_atmosfera_en_region(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        excluir_min: Optional[tuple[int, int]] = None,
        excluir_max: Optional[tuple[int, int]] = None,
        timeout: float | None = None,
    ) -> list:
        await self._ensure_channel()

        tiene_exclusion = excluir_min is not None and excluir_max is not None
        req = pb.ObtenerCeldasAtmosferaEnRegionRequest(
            min=self._pos_to_pb(min_pos),
            max=self._pos_to_pb(max_pos),
            tiene_exclusion=tiene_exclusion,
        )
        if tiene_exclusion:
            req.excluir_min.CopyFrom(self._pos_to_pb(excluir_min))
            req.excluir_max.CopyFrom(self._pos_to_pb(excluir_max))

        try:
            resp = await self._stub.ObtenerCeldasAtmosferaEnRegion(
                req, timeout=self._t(timeout)
            )
            if not resp.ok:
                logger.warning(
                    "ObtenerCeldasAtmosferaEnRegion respondió error: %s", resp.error
                )
                return []
            return list(resp.cells)
        except grpc.aio.AioRpcError as exc:
            logger.error("ObtenerCeldasAtmosferaEnRegion falló: %s", exc)
            return []

    async def actualizar_celdas_atmosfera(
        self, changed_atmosphere_cells: list, timeout: float | None = None
    ) -> None:
        await self._ensure_channel()
        req = pb.ActualizarCeldasAtmosferaRequest(
            changed_atmosphere_cells=changed_atmosphere_cells
        )
        resp = await self._stub.ActualizarCeldasAtmosfera(req, timeout=self._t(timeout))
        if not resp.ok:
            raise RuntimeError(f"ActualizarCeldasAtmosfera: {resp.error}")

    async def obtener_progreso_ciclos(
        self, timeout: float | None = None
    ) -> tuple[float, float, float]:
        # PROPAGA: (0, 0, 0) parecía un dato válido (medianoche + equinoccio).
        await self._ensure_channel()
        resp = await self._stub.ObtenerProgresoCiclos(
            pb.ObtenerProgresoCiclosRequest(), timeout=self._t(timeout)
        )
        if not resp.ok:
            raise RuntimeError(f"ObtenerProgresoCiclos: {resp.error}")
        return resp.progreso_solar, resp.progreso_lunar, resp.progreso_anual

    # ------------------------------------------------------------------
    # Representación (Vista_Foco / Unity)
    # ------------------------------------------------------------------

    async def consultar_representacion(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
        timeout: float | None = None,
    ) -> bytes:
        await self._ensure_channel()
        req = pb.ConsultarRepresentacionRequest(
            min=self._pos_to_pb(min_pos),
            max=self._pos_to_pb(max_pos),
            incluir=incluir,
            modo=modo,
        )
        try:
            resp = await self._stub.ConsultarRepresentacion(
                req, timeout=self._t(timeout)
            )
            if not resp.ok:
                logger.warning(
                    "ConsultarRepresentacion respondió error: %s", resp.error
                )
                return b""
            return resp.datos
        except grpc.aio.AioRpcError as exc:
            logger.error("ConsultarRepresentacion falló: %s", exc)
            return b""

    async def obtener_audio(
        self, id_sonido: str, timeout: float | None = None
    ) -> Optional[dict]:
        """
        Devuelve el payload completo (id/duracion/vol/vector/pcm) de un
        id_sonido, o None si no existe o la llamada falla -- mismo patrón
        "blando" que consultar_representacion/obtener_celdas_en_region: un
        fallo aquí no debe tirar a quien lo llama.
        """
        await self._ensure_channel()
        req = pb.ObtenerAudioRequest(id_sonido=id_sonido)
        try:
            resp = await self._stub.ObtenerAudio(req, timeout=self._t(timeout))
            if not resp.ok:
                logger.warning("ObtenerAudio respondió error: %s", resp.error)
                return None
            return json.loads(resp.audio.decode())
        except grpc.aio.AioRpcError as exc:
            logger.error("ObtenerAudio falló: %s", exc)
            return None
        except json.JSONDecodeError as exc:
            logger.error("ObtenerAudio: audio no es JSON válido: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Elementos globales de tick (avanzar ciclo día-noche, lunar...)
    # ------------------------------------------------------------------

    async def avanzar_elementos_globales(
        self, tick_id: int, timeout: float | None = None
    ) -> dict:
        """
        Pide a Logica_Mundo que avance el tick de todos sus elementos
        globales (ciclo día/noche, lunar, clima...) — ver
        LogicaMundo.avanzar_elementos_globales() y su Funciones/
        avanzar_elementos_globales.py, que ya estaban implementados en
        el lado servidor; solo faltaba este método en el cliente.

        Devuelve el dict de cambios agregados (deserializado desde el
        JSON que viaja en resp.cambios). Gestor_Mundo lo llama en su
        _fase_2 pero de momento no hace nada con el resultado más allá
        de recibirlo (ver TODO "distribuir cambios_globales a sectores
        que lo necesiten" en gestor_mundo.py) — eso queda fuera del
        alcance de este método, que solo transporta el dato.

        En caso de error (red o resp.ok=False) devuelve {} en vez de
        propagar la excepción, igual que el resto de métodos "blandos"
        de este cliente (obtener_celdas_en_region, consultar_
        representacion) — un fallo aquí no debe tirar el tick completo
        de Gestor_Mundo, que ya sigue adelante con el resto de fases
        aunque esta llamada falle.
        """
        await self._ensure_channel()
        req = pb.AvanzarElementosGlobalesRequest(tick_id=tick_id)
        try:
            resp = await self._stub.AvanzarElementosGlobales(
                req, timeout=self._t(timeout)
            )
            if not resp.ok:
                logger.warning(
                    "AvanzarElementosGlobales respondió error: %s", resp.error
                )
                return {}
            return json.loads(resp.cambios.decode()) if resp.cambios else {}
        except grpc.aio.AioRpcError as exc:
            logger.error("AvanzarElementosGlobales falló: %s", exc)
            return {}
        except json.JSONDecodeError as exc:
            logger.error("AvanzarElementosGlobales: cambios no es JSON válido: %s", exc)
            return {}

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    async def save_snapshot(
        self, snapshot_id: str, timeout: float | None = None
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.SaveSnapshotRequest(snapshot_id=snapshot_id)
        try:
            resp = await self._stub.SaveSnapshot(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("SaveSnapshot falló: %s", exc)
            return False, str(exc)

    async def load_state(self, snapshot_id: str, timeout: float | None = None) -> None:
        await self._ensure_channel()
        resp = await self._stub.LoadState(
            pb.LoadStateRequest(snapshot_id=snapshot_id), timeout=self._t(timeout)
        )
        if not resp.ok:
            raise RuntimeError(f"LoadState: {resp.error}")
