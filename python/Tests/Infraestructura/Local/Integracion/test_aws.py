# Tests/Infraestructura/Local/Integracion/test_aws.py
"""
test_aws.py — Prueba de integración de aws.py usando botocore.stub.Stubber:
valida que las llamadas a boto3 (run_instances, describe_instances,
terminate_instances, S3...) se construyen con la forma correcta de
parámetros, sin tocar AWS real ni credenciales.

Por qué "integración" y no "unitario": Stubber intercepta a nivel del
cliente boto3 real (no mockea aws.py por dentro) — se ejercita la
llamada real a la API tal como boto3 la construiría, solo que la
respuesta http se sustituye por una fija. Es la forma más fiel de
probar código AWS sin red real.
"""

import pytest
import boto3
from botocore.stub import Stubber, ANY

from Infraestructura.AWS import aws


@pytest.fixture
def config_aws(config_test: dict) -> dict:
    # config_test ya trae aws/instancias/red/timeouts — se reusa tal cual.
    return config_test


@pytest.mark.integration
def test_lanzar_instancias_ok(config_aws, monkeypatch):
    """
    lanzar_instancias() debe llamar a run_instances una vez por
    especificación, con ImageId/InstanceType/SecurityGroupIds correctos
    y UserData conteniendo las env vars de env_extra.
    """
    ec2 = boto3.client("ec2", region_name=config_aws["aws"]["region"])
    stubber = Stubber(ec2)

    especificaciones = [
        {
            "componente": "gestor_mundo",
            "comp_id": "gestor_mundo",
            "env_extra": {"LOGICA_MUNDO_ADDRESS": "10.0.0.5:50250"},
        },
        {
            "componente": "sector",
            "comp_id": "sector_0_0",
            "env_extra": {"SECTOR_COL": "0", "SECTOR_ROW": "0"},
        },
    ]

    for spec in especificaciones:
        stubber.add_response(
            "run_instances",
            {"Instances": [{"InstanceId": f"i-{spec['comp_id']}"}]},
            expected_params={
                "ImageId": config_aws["aws"]["ami_id"],
                "InstanceType": config_aws["instancias"][spec["componente"]]["tipo"],
                "MinCount": 1,
                "MaxCount": 1,
                "SecurityGroupIds": [config_aws["aws"]["security_group_id"]],
                "UserData": ANY,
                "InstanceMarketOptions": {"MarketType": "spot"},
                "TagSpecifications": ANY,
            },
        )

    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: ec2)

    resultado = aws.lanzar_instancias(
        config_aws, session_id="sesion-test", especificaciones=especificaciones
    )

    stubber.assert_no_pending_responses()
    assert resultado == {"gestor_mundo": "i-gestor_mundo", "sector_0_0": "i-sector_0_0"}


@pytest.mark.integration
def test_lanzar_instancias_user_data_incluye_env_extra(config_aws, monkeypatch):
    """
    Verifica el contenido REAL de UserData (no solo que sea ANY) —
    esto es justo el bug que corregimos: env_extra debía volcarse como
    export en el script de arranque, y antes se ignoraba.
    """
    ec2 = boto3.client("ec2", region_name=config_aws["aws"]["region"])
    stubber = Stubber(ec2)

    especificacion = [
        {
            "componente": "gestor_mundo",
            "comp_id": "gestor_mundo",
            "env_extra": {"LOGICA_MUNDO_ADDRESS": "10.0.0.5:50250"},
        }
    ]

    capturado = {}

    stubber.add_response("run_instances", {"Instances": [{"InstanceId": "i-123"}]})
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: ec2)

    # Interceptar la llamada real para poder inspeccionar UserData
    # (Stubber valida contra expected_params si se le pasan, pero no
    # expone directamente los kwargs ya construidos — se envuelve
    # run_instances para capturarlos antes de que Stubber conteste).
    original = ec2.run_instances

    def _wrapper(**kwargs):
        capturado.update(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(ec2, "run_instances", _wrapper)

    aws.lanzar_instancias(
        config_aws, session_id="sesion-test", especificaciones=especificacion
    )

    assert 'export LOGICA_MUNDO_ADDRESS="10.0.0.5:50250"' in capturado["UserData"]
    assert "--componente gestor_mundo" in capturado["UserData"]
    assert "--sesion sesion-test" in capturado["UserData"]


@pytest.mark.integration
def test_lanzar_instancias_termina_las_ya_lanzadas_si_falla_una(
    config_aws, monkeypatch
):
    """
    Si la segunda especificación falla, la primera instancia (ya
    lanzada con éxito) debe terminarse antes de propagar el error —
    ver comportamiento documentado en aws.py::lanzar_instancias.
    """
    ec2 = boto3.client("ec2", region_name=config_aws["aws"]["region"])
    stubber = Stubber(ec2)

    especificaciones = [
        {"componente": "gestor_mundo", "comp_id": "gestor_mundo", "env_extra": {}},
        {"componente": "sector", "comp_id": "sector_0_0", "env_extra": {}},
    ]

    stubber.add_response(
        "run_instances", {"Instances": [{"InstanceId": "i-gestor_mundo"}]}
    )
    stubber.add_client_error(
        "run_instances", service_error_code="InsufficientInstanceCapacity"
    )
    # terminar_instancias() llamado en el except — se espera para i-gestor_mundo
    stubber.add_response("terminate_instances", {})

    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: ec2)

    with pytest.raises(RuntimeError, match="No se pudo lanzar la infraestructura"):
        aws.lanzar_instancias(
            config_aws, session_id="sesion-test", especificaciones=especificaciones
        )

    stubber.assert_no_pending_responses()


@pytest.mark.integration
def test_esperar_ips_publicas_ok(config_aws, monkeypatch):
    ec2 = boto3.client("ec2", region_name=config_aws["aws"]["region"])
    stubber = Stubber(ec2)

    stubber.add_response(
        "describe_instances",
        {
            "Reservations": [
                {
                    "Instances": [
                        {"InstanceId": "i-abc", "PublicIpAddress": "1.2.3.4"},
                    ]
                }
            ]
        },
        expected_params={"InstanceIds": ["i-abc"]},
    )
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: ec2)

    resultado = aws.esperar_ips_publicas(
        config_aws, id_por_comp={"gestor_mundo": "i-abc"}, timeout=5
    )

    assert resultado == {"gestor_mundo": "1.2.3.4"}


@pytest.mark.integration
def test_esperar_ips_publicas_timeout_si_nunca_aparece(config_aws, monkeypatch):
    """
    describe_instances siempre responde sin PublicIpAddress — debe
    agotar el timeout (usamos 0.3s para no ralentizar la suite) y
    lanzar TimeoutError con el componente pendiente identificado.
    """
    ec2 = boto3.client("ec2", region_name=config_aws["aws"]["region"])
    stubber = Stubber(ec2)

    # Varias respuestas posibles porque el bucle reintenta cada 5s —
    # con timeout tan corto, probablemente solo consuma una, pero se
    # deja margen por si el reloj del test es lento.
    for _ in range(3):
        stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [{"InstanceId": "i-abc"}]}]},
        )
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: ec2)

    with pytest.raises(TimeoutError, match="gestor_mundo"):
        aws.esperar_ips_publicas(
            config_aws, id_por_comp={"gestor_mundo": "i-abc"}, timeout=0.3
        )


@pytest.mark.integration
def test_terminar_instancias_con_lista_vacia_no_llama_a_aws(config_aws, monkeypatch):
    """
    Guard explícito en aws.py: instance_ids vacío no debe intentar
    llamar a terminate_instances (evita una llamada AWS innecesaria/
    potencialmente inválida con InstanceIds=[]).
    """
    llamado = {"veces": 0}

    class ClienteQueNuncaDebeLlamarse:
        def terminate_instances(self, **kwargs):
            llamado["veces"] += 1
            return {}

    monkeypatch.setattr(boto3, "client", lambda *a, **kw: ClienteQueNuncaDebeLlamarse())

    aws.terminar_instancias(config_aws, instance_ids=[])

    assert llamado["veces"] == 0


@pytest.mark.integration
def test_leer_ultima_sesion_devuelve_none_si_no_existe(config_aws, monkeypatch):
    s3 = boto3.client("s3", region_name=config_aws["aws"]["region"])
    stubber = Stubber(s3)
    stubber.add_client_error("get_object", service_error_code="NoSuchKey")
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: s3)

    resultado = aws.leer_ultima_sesion(config_aws)

    assert resultado is None


@pytest.mark.integration
def test_leer_ultima_sesion_propaga_otros_errores(config_aws, monkeypatch):
    """
    Solo NoSuchKey/NoSuchBucket deben tratarse como "no hay sesión" —
    cualquier otro ClientError (p.ej. AccessDenied) debe propagarse,
    no esconderse silenciosamente como None.
    """
    from botocore.exceptions import ClientError

    s3 = boto3.client("s3", region_name=config_aws["aws"]["region"])
    stubber = Stubber(s3)
    stubber.add_client_error("get_object", service_error_code="AccessDenied")
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: s3)

    with pytest.raises(ClientError):
        aws.leer_ultima_sesion(config_aws)


@pytest.mark.integration
def test_borrar_sesion_hibernada_sin_objetos_no_llama_delete(config_aws, monkeypatch):
    """
    Guard explícito: si list_objects_v2 no devuelve Contents, no debe
    llamarse a delete_objects (evita DeleteObjectsRequest vacío).
    """
    s3 = boto3.client("s3", region_name=config_aws["aws"]["region"])
    stubber = Stubber(s3)
    stubber.add_response("list_objects_v2", {})  # sin "Contents"
    stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: s3)

    aws.borrar_sesion_hibernada(config_aws, session_id="sesion-vieja")

    stubber.assert_no_pending_responses()  # delete_objects NUNCA se pidió como response
