"""
Tests para Infraestructura/AWS/aws.py.

Todos los tests mockean boto3 y requests para no requerir
credenciales AWS ni conexión de red.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from Infraestructura.AWS.aws import (
    actualizar_security_group,
    borrar_sesion_hibernada,
    esperar_ips_publicas,
    guardar_sesion_activa,
    lanzar_instancias,
    leer_ultima_sesion,
    nueva_session_id,
    terminar_instancias,
)

# ─────────────────────────────────────────────────────────────
#  Config mínima válida para los tests
# ─────────────────────────────────────────────────────────────

CFG = {
    "aws": {
        "region":            "us-east-1",
        "ami_id":            "ami-test",
        "bucket":            "test-bucket",
        "security_group_id": "sg-test",
    },
    "instancias": {
        "gestor_bots":  {"tipo": "t3.small"},
        "gestor_mundo": {"tipo": "t3.small"},
        "hypervisor":   {"tipo": "t3.medium", "cantidad": 1},
        "sector":       {"tipo": "t3.small",  "cantidad": 1},
    },
    "red":      {"puerto_grpc_componentes": 50051},
    "timeouts": {"arranque_segundos": 10},
}


# ─────────────────────────────────────────────────────────────
#  actualizar_security_group
# ─────────────────────────────────────────────────────────────

class TestActualizarSecurityGroup:
    def _mock_ec2(self, reglas_existentes=None):
        mock = MagicMock()
        mock.describe_security_groups.return_value = {
            "SecurityGroups": [{"IpPermissions": reglas_existentes or []}]
        }
        return mock

    def test_revoca_regla_anterior_del_orquestador(self):
        """Las reglas previas marcadas como 'orquestador-local' se revocan."""
        regla = {
            "IpProtocol": "tcp",
            "FromPort": 50051,
            "ToPort": 50051,
            "IpRanges": [{"CidrIp": "1.2.3.4/32", "Description": "orquestador-local"}],
        }
        mock_ec2 = self._mock_ec2([regla])

        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_ec2):
            actualizar_security_group(CFG, "9.9.9.9")

        mock_ec2.revoke_security_group_ingress.assert_called_once_with(
            GroupId="sg-test", IpPermissions=[regla]
        )

    def test_autoriza_nueva_ip(self):
        """Siempre autoriza la IP actual con la descripción correcta."""
        mock_ec2 = self._mock_ec2()

        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_ec2):
            actualizar_security_group(CFG, "9.9.9.9")

        call_kwargs = mock_ec2.authorize_security_group_ingress.call_args[1]
        ip_range = call_kwargs["IpPermissions"][0]["IpRanges"][0]
        assert ip_range["CidrIp"] == "9.9.9.9/32"
        assert ip_range["Description"] == "orquestador-local"

    def test_no_toca_reglas_de_otros(self):
        """Las reglas sin descripción 'orquestador-local' no se revocan."""
        regla_ajena = {
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "ssh-manual"}],
        }
        mock_ec2 = self._mock_ec2([regla_ajena])

        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_ec2):
            actualizar_security_group(CFG, "9.9.9.9")

        mock_ec2.revoke_security_group_ingress.assert_not_called()


# ─────────────────────────────────────────────────────────────
#  lanzar_instancias
# ─────────────────────────────────────────────────────────────

class TestLanzarInstancias:
    def _run_response(self, instance_id: str) -> dict:
        return {"Instances": [{"InstanceId": instance_id}]}

    def test_lanza_todas_las_instancias(self):
        """Lanza gestor_bots, gestor_mundo, HV y sector; devuelve mapa comp→instance_id."""
        mock_ec2 = MagicMock()
        mock_ec2.run_instances.side_effect = [
            self._run_response("i-001"),  # gestor_bots
            self._run_response("i-002"),  # gestor_mundo
            self._run_response("i-003"),  # hv_0
            self._run_response("i-004"),  # sector_0
        ]

        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_ec2):
            resultado = lanzar_instancias(CFG, "sesion-1")

        assert resultado == {
            "gestor_bots":  "i-001",
            "gestor_mundo": "i-002",
            "hv_0":         "i-003",
            "sector_0":     "i-004",
        }

    def test_termina_instancias_ya_lanzadas_si_falla_una(self):
        """Si falla el lanzamiento de una instancia, las anteriores se terminan."""
        mock_ec2 = MagicMock()
        mock_ec2.run_instances.side_effect = [
            self._run_response("i-001"),
            ClientError({"Error": {"Code": "InsufficientInstanceCapacity", "Message": ""}}, "RunInstances"),
        ]

        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_ec2):
            with pytest.raises(RuntimeError, match="No se pudo lanzar"):
                lanzar_instancias(CFG, "sesion-1")

        mock_ec2.terminate_instances.assert_called_once_with(InstanceIds=["i-001"])

    def test_instancias_reciben_session_id_en_tags(self):
        """Cada instancia recibe el session_id como tag para trazabilidad."""
        mock_ec2 = MagicMock()
        mock_ec2.run_instances.return_value = self._run_response("i-001")

        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_ec2):
            lanzar_instancias(CFG, "sesion-xyz")

        call_kwargs = mock_ec2.run_instances.call_args_list[0][1]
        tags = {t["Key"]: t["Value"] for t in call_kwargs["TagSpecifications"][0]["Tags"]}
        assert tags["sesion"] == "sesion-xyz"


# ─────────────────────────────────────────────────────────────
#  esperar_ips_publicas
# ─────────────────────────────────────────────────────────────

class TestEsperarIpsPublicas:
    def test_devuelve_ips_cuando_disponibles(self):
        """Devuelve el mapa comp_id → IP cuando todas las instancias tienen IP."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {"Instances": [{"InstanceId": "i-001", "PublicIpAddress": "1.2.3.4"}]},
                {"Instances": [{"InstanceId": "i-002", "PublicIpAddress": "5.6.7.8"}]},
            ]
        }

        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_ec2):
            with patch("Infraestructura.AWS.aws.time.sleep"):
                resultado = esperar_ips_publicas(
                    CFG,
                    {"gestor_bots": "i-001", "gestor_mundo": "i-002"},
                    timeout=10,
                )

        assert resultado == {"gestor_bots": "1.2.3.4", "gestor_mundo": "5.6.7.8"}

    def test_timeout_si_no_aparecen_ips(self):
        """Lanza TimeoutError si una instancia no obtiene IP en el tiempo límite."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"InstanceId": "i-001"}]}]  # sin IP
        }

        # monotonic: inicio=0, primera comprobación=0 (ok), segunda=999 (timeout)
        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_ec2):
            with patch("Infraestructura.AWS.aws.time.sleep"):
                with patch("Infraestructura.AWS.aws.time.monotonic", side_effect=[0, 0, 999]):
                    with pytest.raises(TimeoutError, match="sin IP pública"):
                        esperar_ips_publicas(CFG, {"gestor_bots": "i-001"}, timeout=5)


# ─────────────────────────────────────────────────────────────
#  Sesiones S3
# ─────────────────────────────────────────────────────────────

class TestSesionesS3:
    def test_leer_ultima_sesion_devuelve_id(self):
        mock_s3 = MagicMock()
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=b"sesion-abc"))
        }
        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_s3):
            assert leer_ultima_sesion(CFG) == "sesion-abc"

    def test_leer_ultima_sesion_devuelve_none_si_no_existe(self):
        mock_s3 = MagicMock()
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": ""}}, "GetObject"
        )
        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_s3):
            assert leer_ultima_sesion(CFG) is None

    def test_nueva_session_id_es_uuid_valido(self):
        sid = nueva_session_id()
        uuid.UUID(sid)  # lanza ValueError si no es UUID válido

    def test_borrar_sesion_elimina_todos_sus_objetos(self):
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "sesiones/abc/hv_0/bot_0.criu"},
                {"Key": "sesiones/abc/hv_0/bot_1.criu"},
            ]
        }
        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_s3):
            borrar_sesion_hibernada(CFG, "abc")

        mock_s3.delete_objects.assert_called_once_with(
            Bucket="test-bucket",
            Delete={"Objects": [
                {"Key": "sesiones/abc/hv_0/bot_0.criu"},
                {"Key": "sesiones/abc/hv_0/bot_1.criu"},
            ]},
        )

    def test_borrar_sesion_sin_objetos_no_llama_delete(self):
        """Si la sesión no tiene objetos en S3, no se llama a delete_objects."""
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.return_value = {"Contents": []}
        with patch("Infraestructura.AWS.aws.boto3.client", return_value=mock_s3):
            borrar_sesion_hibernada(CFG, "abc")

        mock_s3.delete_objects.assert_not_called()
