# Tests/conftest.py
"""
conftest.py — Fixtures compartidas por toda la suite de Tests/.

Filosofía:
  - Unitarios: no tocan red ni disco real. Los dobles de aquí (FakeStub,
    FakeLogicaClient) sirven para eso.
  - Integracion: levantan un grpc.aio.server real en un puerto efímero
    (port=0, el SO asigna uno libre) dentro del MISMO proceso de pytest,
    y lo golpean con un cliente real del proyecto. Sin subprocess.
  - E2E: usan bootstrap.ejecutar_modo_local() de verdad, con variables
    de entorno aisladas (SNAPSHOT_DIR/puertos en tmp_path) para no pisar
    una sesión local real que puedas tener abierta a la vez.

Todas las fixtures de aquí son pytest-asyncio-compatibles (asyncio_mode
= auto en pytest.ini, así que no hace falta el decorador @pytest.mark.asyncio
en cada test — cualquier `async def test_...` ya se ejecuta correctamente).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import grpc
import grpc.aio
import pytest

# ─────────────────────────────────────────────────────────────
#  Config mínima de pruebas — evita depender de config.yaml real
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def config_test() -> dict:
    """
    dict mínimo con la forma de config.yaml, solo con las claves que
    los módulos bajo prueba realmente leen. Se amplía según haga falta
    en tests concretos (nunca se muta esta fixture directamente — cada
    test que necesite una variante hace config_test | {"clave": valor}).
    """
    return {
        "aws": {
            "region": "us-east-1",
            "ami_id": "ami-test",
            "bucket": "bucket-test",
            "security_group_id": "sg-test",
        },
        "instancias": {
            "sector": {"tipo": "t3.small"},
            "gestor_mundo": {"tipo": "t3.small"},
            "gestor_bots": {"tipo": "t3.small"},
            "hypervisor": {"tipo": "t3.medium"},
            "logica_mundo": {"tipo": "t3.small"},
            "comunicaciones_remoto": {"tipo": "t3.small"},
        },
        "red": {"puerto_grpc_componentes": 50051},
        "timeouts": {
            "arranque_segundos": 5,
            "shutdown_segundos": 5,
            "heartbeat_intervalo": 1,
            "heartbeat_perdidos_max": 3,
        },
    }


# ─────────────────────────────────────────────────────────────
#  Dobles falsos — para tests UNITARIOS (sin red real)
# ─────────────────────────────────────────────────────────────


class FakeAsyncCallResult:
    """
    Envuelve un valor para que awaitearlo funcione, igual que un stub
    gRPC real. Usar como: FakeAsyncCallResult(mi_respuesta_proto).
    """

    def __init__(self, value: Any):
        self._value = value

    def __await__(self):
        async def _coro():
            return self._value

        return _coro().__await__()


@dataclass
class FakeStub:
    """
    Doble genérico de un stub gRPC async. Se configura con un dict
    {nombre_metodo: valor_o_excepcion}; cualquier atributo accedido que
    coincida con una clave del dict se convierte en un callable async
    que devuelve ese valor (o lanza esa excepción, si el valor es una
    instancia de Exception).

    Uso:
        stub = FakeStub(GetState=mi_response_proto)
        resp = await stub.GetState(request)  # devuelve mi_response_proto

        stub_con_fallo = FakeStub(Heartbeat=grpc.aio.AioRpcError(...))
        await stub_con_fallo.Heartbeat(request)  # lanza la excepción
    """

    respuestas: dict = field(default_factory=dict)

    def __init__(self, **respuestas):
        self.respuestas = respuestas
        self.llamadas: dict[str, int] = {}

    def __getattr__(self, nombre: str) -> Callable:
        if nombre not in self.respuestas:
            raise AttributeError(
                f"FakeStub no tiene configurada una respuesta para '{nombre}'"
            )

        async def _metodo(*args, **kwargs):
            self.llamadas[nombre] = self.llamadas.get(nombre, 0) + 1
            valor = self.respuestas[nombre]
            if isinstance(valor, Exception):
                raise valor
            return valor

        return _metodo


@pytest.fixture
def fake_stub_factory():
    """Devuelve el constructor FakeStub, para instanciarlo con kwargs en cada test."""
    return FakeStub


# ─────────────────────────────────────────────────────────────
#  Servidor real en proceso — para tests de INTEGRACION
# ─────────────────────────────────────────────────────────────


@dataclass
class ServidorEnProceso:
    """
    Resultado de levantar_servidor(): dirección real ("localhost:PUERTO")
    y el propio grpc.aio.Server, para poder detenerlo explícitamente si
    un test lo necesita (normalmente lo hace el finalizer de la fixture).
    """

    address: str
    server: grpc.aio.Server


@pytest.fixture
async def levantar_servidor():
    """
    Factory fixture: devuelve una función async que registra un
    servicer en un grpc.aio.server real, en un puerto libre (":0" — el
    SO elige uno), y lo arranca. Usar así en un test de integración:

        async def test_algo(levantar_servidor):
            servidor = await levantar_servidor(
                lambda s: pb_grpc.add_GestorBotsServiceServicer_to_server(
                    Gestor_Bots_Servicer(gestor_real), s
                )
            )
            client = GestorBotsClientAsync(servidor.address)
            ...

    Se detiene automáticamente al final del test (yield + cleanup),
    sin que cada test tenga que acordarse de hacerlo.
    """
    servidores: list[grpc.aio.Server] = []

    async def _levantar(
        registrar_fn: Callable[[grpc.aio.Server], None],
    ) -> ServidorEnProceso:
        server = grpc.aio.server()
        registrar_fn(server)
        puerto = server.add_insecure_port("localhost:0")
        await server.start()
        servidores.append(server)
        return ServidorEnProceso(address=f"localhost:{puerto}", server=server)

    yield _levantar

    for server in servidores:
        await server.stop(grace=1)


# ─────────────────────────────────────────────────────────────
#  Aislamiento de entorno — para tests que leen os.getenv()
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def snapshot_dir_aislado(tmp_path, monkeypatch):
    """
    Redirige SNAPSHOT_DIR (leído vía os.getenv en varios módulos:
    Logica_Mundo, GestorMundo) a un directorio temporal propio de este
    test, para que los tests de snapshot/save/load no escriban en el
    SNAPSHOT_DIR real de desarrollo ni interfieran entre tests que
    corren en paralelo.
    """
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path))
    return tmp_path
