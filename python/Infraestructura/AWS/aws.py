"""
Operaciones AWS para la gestión del ciclo de vida de la infraestructura.
Todas las funciones que hablan con AWS están aquí; el resto del código no usa boto3 directamente.
"""

import logging
import time
import uuid

import boto3
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Las reglas del SG que gestiona este orquestador se identifican por esta descripción,
# para no tocar otras reglas que pueda haber en el mismo SG.
_DESCRIPCION_SG = "orquestador-local"


# ---------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------

def obtener_ip_publica() -> str:
    resp = requests.get("https://checkip.amazonaws.com", timeout=5)
    resp.raise_for_status()
    return resp.text.strip()


def actualizar_security_group(config: dict, mi_ip: str):
    """
    Actualiza el Security Group para que solo la IP actual del orquestador
    pueda acceder al puerto gRPC de los componentes.
    No toca otras reglas del SG.
    """
    ec2 = boto3.client("ec2", region_name=config["aws"]["region"])
    sg_id = config["aws"]["security_group_id"]
    puerto = config["red"]["puerto_grpc_componentes"]

    sg = ec2.describe_security_groups(GroupIds=[sg_id])["SecurityGroups"][0]

    # Revocar reglas anteriores del orquestador
    reglas_anteriores = [
        r for r in sg.get("IpPermissions", [])
        if any(
            rango.get("Description") == _DESCRIPCION_SG
            for rango in r.get("IpRanges", [])
        )
    ]
    if reglas_anteriores:
        ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=reglas_anteriores)

    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[{
            "IpProtocol": "tcp",
            "FromPort": puerto,
            "ToPort": puerto,
            "IpRanges": [{"CidrIp": f"{mi_ip}/32", "Description": _DESCRIPCION_SG}],
        }],
    )
    logger.info(f"Security Group actualizado: {mi_ip} → puerto {puerto}")


# ---------------------------------------------------------------------------
# Instancias
# ---------------------------------------------------------------------------

def _user_data(componente: str, componente_id: str, session_id: str, config: dict) -> str:
    """
    Script que ejecuta cada instancia al arrancar.
    Redirige stdout/stderr a un log para poder inspeccionar si algo falla.
    """
    bucket = config["aws"]["bucket"]
    return (
        "#!/bin/bash\n"
        "cd /home/ubuntu/proyecto\n"
        f"python main.py"
        f" --modo produccion"
        f" --componente {componente}"
        f" --id {componente_id}"
        f" --sesion {session_id}"
        f" --bucket {bucket}"
        f" >> /var/log/componente.log 2>&1\n"
    )


def lanzar_instancias(config: dict, session_id: str) -> dict[str, str]:
    """
    Lanza todas las instancias Spot necesarias para la sesión.
    Si alguna falla, termina las que ya se lanzaron antes de propagar el error.

    Devuelve: {componente_id: instance_id}
    """
    ec2 = boto3.client("ec2", region_name=config["aws"]["region"])
    ami_id = config["aws"]["ami_id"]
    sg_id = config["aws"]["security_group_id"]
    inst_cfg = config["instancias"]

    lanzadas: dict[str, str] = {}

    def _lanzar(componente: str, tipo: str, comp_id: str):
        resp = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=tipo,
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[sg_id],
            UserData=_user_data(componente, comp_id, session_id, config),
            InstanceMarketOptions={"MarketType": "spot"},
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name",          "Value": f"ia-{comp_id}"},
                    {"Key": "sesion",        "Value": session_id},
                    {"Key": "componente_id", "Value": comp_id},
                ],
            }],
        )
        instance_id = resp["Instances"][0]["InstanceId"]
        lanzadas[comp_id] = instance_id
        logger.info(f"Instancia lanzada: {comp_id} → {instance_id}")

    try:
        _lanzar("gestor_bots",  inst_cfg["gestor_bots"]["tipo"],  "gestor_bots")
        _lanzar("gestor_mundo", inst_cfg["gestor_mundo"]["tipo"], "gestor_mundo")

        for i in range(inst_cfg["hypervisor"]["cantidad"]):
            _lanzar("hypervisor", inst_cfg["hypervisor"]["tipo"], f"hv_{i}")

        for i in range(inst_cfg["sector"]["cantidad"]):
            _lanzar("sector", inst_cfg["sector"]["tipo"], f"sector_{i}")

    except ClientError as e:
        # Limpiar instancias ya lanzadas antes de propagar el error
        if lanzadas:
            logger.error("Fallo al lanzar instancias; terminando las que se lanzaron.")
            terminar_instancias(config, list(lanzadas.values()))
        raise RuntimeError(f"No se pudo lanzar la infraestructura: {e}") from e

    return lanzadas


def esperar_ips_publicas(
    config: dict,
    id_por_comp: dict[str, str],  # {componente_id: instance_id}
    timeout: int,
) -> dict[str, str]:
    """
    Espera hasta que todas las instancias tengan IP pública asignada.
    Devuelve: {componente_id: ip_publica}
    """
    ec2 = boto3.client("ec2", region_name=config["aws"]["region"])
    instance_ids = list(id_por_comp.values())
    comp_por_instance = {v: k for k, v in id_por_comp.items()}

    ip_por_comp: dict[str, str] = {}
    inicio = time.monotonic()

    while len(ip_por_comp) < len(instance_ids):
        if time.monotonic() - inicio > timeout:
            pendientes = [
                comp_por_instance[iid]
                for iid in instance_ids
                if comp_por_instance[iid] not in ip_por_comp
            ]
            raise TimeoutError(
                f"Instancias sin IP pública tras {timeout}s: {pendientes}"
            )

        resp = ec2.describe_instances(InstanceIds=instance_ids)
        for reserva in resp["Reservations"]:
            for inst in reserva["Instances"]:
                iid = inst["InstanceId"]
                ip = inst.get("PublicIpAddress")
                comp_id = comp_por_instance[iid]
                if ip and comp_id not in ip_por_comp:
                    ip_por_comp[comp_id] = ip
                    logger.info(f"{comp_id} → {ip}")

        if len(ip_por_comp) < len(instance_ids):
            time.sleep(5)

    return ip_por_comp


def terminar_instancias(config: dict, instance_ids: list[str]):
    if not instance_ids:
        return
    ec2 = boto3.client("ec2", region_name=config["aws"]["region"])
    ec2.terminate_instances(InstanceIds=instance_ids)
    logger.info(f"Instancias terminadas: {instance_ids}")


# ---------------------------------------------------------------------------
# Sesiones en S3
# ---------------------------------------------------------------------------

def nueva_session_id() -> str:
    return str(uuid.uuid4())


def leer_ultima_sesion(config: dict) -> str | None:
    """Devuelve el session_id de la última sesión hibernada, o None si no hay ninguna."""
    s3 = boto3.client("s3", region_name=config["aws"]["region"])
    try:
        obj = s3.get_object(Bucket=config["aws"]["bucket"], Key="ultima_sesion.txt")
        return obj["Body"].read().decode().strip()
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "NoSuchBucket"):
            return None
        raise


def guardar_sesion_activa(config: dict, session_id: str):
    """Registra la sesión actual como la última activa (se llama al iniciar una sesión nueva)."""
    s3 = boto3.client("s3", region_name=config["aws"]["region"])
    s3.put_object(
        Bucket=config["aws"]["bucket"],
        Key="ultima_sesion.txt",
        Body=session_id.encode(),
    )


def borrar_sesion_hibernada(config: dict, session_id: str):
    """
    Elimina los ficheros de hibernación de una sesión tras restaurarla correctamente.
    Si no se borraran, el próximo arranque intentaría restaurar una sesión ya consumida.
    """
    s3 = boto3.client("s3", region_name=config["aws"]["region"])
    bucket = config["aws"]["bucket"]

    resp = s3.list_objects_v2(Bucket=bucket, Prefix=f"sesiones/{session_id}/")
    objetos = [{"Key": obj["Key"]} for obj in resp.get("Contents", [])]

    if objetos:
        s3.delete_objects(Bucket=bucket, Delete={"Objects": objetos})
        logger.info(f"Hibernación de sesión {session_id} eliminada de S3.")
