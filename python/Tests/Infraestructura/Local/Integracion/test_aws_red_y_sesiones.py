# Tests/Infraestructura/Local/Integracion/test_aws_red_y_sesiones.py
"""
test_aws_red_y_sesiones.py — Complementa test_aws.py (que ya cubre
lanzar_instancias/esperar_ips_publicas/terminar_instancias/sesiones
hibernadas) con las tres funciones de aws.py que se habían quedado sin
ningún test: obtener_ip_publica (HTTP real vía requests),
actualizar_security_group (boto3 EC2) y guardar_sesion_activa (boto3 S3).

Mismo patrón que test_aws.py: botocore.stub.Stubber para boto3, y aquí
además un monkeypatch directo de requests.get (no hay stub equivalente
para peticiones HTTP simples).
"""

import boto3
import pytest
import requests
from botocore.stub import Stubber

from Infraestructura.AWS import aws


@pytest.fixture
def config_aws(config_test: dict) -> dict:
    return config_test


# ── obtener_ip_publica ────────────────────────────────────────────


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        pass


@pytest.mark.integration
def test_obtener_ip_publica_recorta_espacios_en_blanco(monkeypatch):
    monkeypatch.setattr(
        requests, "get", lambda url, timeout: _FakeResponse(" 1.2.3.4 \n")
    )

    assert aws.obtener_ip_publica() == "1.2.3.4"


# ── actualizar_security_group ─────────────────────────────────────


@pytest.mark.integration
def test_actualizar_security_group_revoca_reglas_previas_y_autoriza_la_nueva(
    config_aws, monkeypatch
):
    ec2 = boto3.client("ec2", region_name=config_aws["aws"]["region"])
    stubber = Stubber(ec2)

    regla_previa = {
        "IpProtocol": "tcp",
        "FromPort": config_aws["red"]["puerto_grpc_componentes"],
        "ToPort": config_aws["red"]["puerto_grpc_componentes"],
        "IpRanges": [{"CidrIp": "9.9.9.9/32", "Description": "orquestador-local"}],
    }
    stubber.add_response(
        "describe_security_groups",
        {"SecurityGroups": [{"IpPermissions": [regla_previa]}]},
        expected_params={"GroupIds": [config_aws["aws"]["security_group_id"]]},
    )
    stubber.add_response("revoke_security_group_ingress", {})
    stubber.add_response("authorize_security_group_ingress", {})
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: ec2)

    aws.actualizar_security_group(config_aws, mi_ip="1.2.3.4")

    stubber.assert_no_pending_responses()


@pytest.mark.integration
def test_actualizar_security_group_sin_reglas_previas_no_revoca(
    config_aws, monkeypatch
):
    """
    Si el SG no tiene todavía ninguna regla marcada como
    "orquestador-local" (primer arranque), no debe llamarse a
    revoke_security_group_ingress — solo se revocan reglas PROPIAS.
    """
    ec2 = boto3.client("ec2", region_name=config_aws["aws"]["region"])
    stubber = Stubber(ec2)
    stubber.add_response(
        "describe_security_groups", {"SecurityGroups": [{"IpPermissions": []}]}
    )
    stubber.add_response("authorize_security_group_ingress", {})
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: ec2)

    aws.actualizar_security_group(config_aws, mi_ip="1.2.3.4")

    stubber.assert_no_pending_responses()  # revoke nunca se pidió como respuesta


@pytest.mark.integration
def test_actualizar_security_group_no_toca_reglas_de_otro_origen(
    config_aws, monkeypatch
):
    """
    Reglas con una Description distinta de "orquestador-local" (p.ej.
    puestas a mano por un administrador) no deben tocarse ni contarse
    como "propias" a revocar.
    """
    ec2 = boto3.client("ec2", region_name=config_aws["aws"]["region"])
    stubber = Stubber(ec2)

    regla_ajena = {
        "IpProtocol": "tcp",
        "FromPort": 22,
        "ToPort": 22,
        "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "acceso-ssh-manual"}],
    }
    stubber.add_response(
        "describe_security_groups",
        {"SecurityGroups": [{"IpPermissions": [regla_ajena]}]},
    )
    stubber.add_response("authorize_security_group_ingress", {})
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: ec2)

    aws.actualizar_security_group(config_aws, mi_ip="1.2.3.4")

    stubber.assert_no_pending_responses()  # revoke no se llamó


# ── guardar_sesion_activa ──────────────────────────────────────────


@pytest.mark.integration
def test_guardar_sesion_activa_escribe_el_session_id_en_s3(config_aws, monkeypatch):
    s3 = boto3.client("s3", region_name=config_aws["aws"]["region"])
    stubber = Stubber(s3)
    stubber.add_response(
        "put_object",
        {},
        expected_params={
            "Bucket": config_aws["aws"]["bucket"],
            "Key": "ultima_sesion.txt",
            "Body": b"sesion-123",
        },
    )
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: s3)

    aws.guardar_sesion_activa(config_aws, session_id="sesion-123")

    stubber.assert_no_pending_responses()
