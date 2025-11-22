from socket import socket
from Serializaciones.Bots import serializar_bots, serializacion_completa_bot
from Serializaciones.Mundo import serializar_mundo
from Services.Conexion.ProcesadoSalidaMensaje import procesar_mensaje_salida


def estimate_tcpip_bits(
    payload_bytes: int, mtu=1500, ip_header=20, tcp_header=20, include_ethernet=False
):
    # MSS: bytes útiles por paquete (IPv4 sin opciones)
    mss = mtu - ip_header - tcp_header
    if mss <= 0:
        raise ValueError("MTU demasiado pequeña para cabeceras")
    packets = (payload_bytes + mss - 1) // mss if payload_bytes > 0 else 1
    headers_total = packets * (ip_header + tcp_header)
    bytes_with_ip_tcp = payload_bytes + headers_total
    bits_with_ip_tcp = bytes_with_ip_tcp * 8

    if include_ethernet:
        # aproximación por trama Ethernet (preamble+IFG+HDR+FCS)
        eth_overhead_per_frame = 38
        bytes_with_eth = bytes_with_ip_tcp + packets * eth_overhead_per_frame
        return {
            "payload_bytes": payload_bytes,
            "payload_bits": payload_bytes * 8,
            "packets": packets,
            "bytes_with_ip_tcp": bytes_with_ip_tcp,
            "bits_with_ip_tcp": bits_with_ip_tcp,
            "bytes_with_ethernet": bytes_with_eth,
            "bits_with_ethernet": bytes_with_eth * 8,
        }

    return {
        "payload_bytes": payload_bytes,
        "payload_bits": payload_bytes * 8,
        "packets": packets,
        "bytes_with_ip_tcp": bytes_with_ip_tcp,
        "bits_with_ip_tcp": bits_with_ip_tcp,
        "bytes_with_ethernet": None,
        "bits_with_ethernet": None,
    }


def serializacion_basica(shared_data):

    #   Bots casilla + rotacion
    #
    def serializar_bots_data(bots_data):
        return serializar_bots(bots_data)

    #   Other
    #
    def serializar_other(other):
        # print(Fore.RED + "type(other.items()):\n" + str(type(other.items())) + Style.RESET_ALL)

        other_copy = {
            k: dict(v) if isinstance(v, (dict)) else v for k, v in other.items()
        }
        if len(other_copy) == 0:
            return "{}"

        paused = "false"
        if other_copy["paused"] == True:
            paused = "true"
        json = f"""
            {{
               \"paused\": {paused}
            }}
            """

        return json

    #   DEV
    #
    def serializar_dev(dev):
        return '""'

    shared_data_copy = {
        k: dict(v) if isinstance(v, dict) else list(v) if isinstance(v, list) else v
        for k, v in shared_data.items()
    }

    return f"""
    {{
        "tipo": "actualizacion",
        "bots": {serializar_bots_data(shared_data_copy["bots_data"])},
        "mundo": {serializar_mundo(None)}
    }}
    """


#   Bots completa
#
def serializar_bot_completo(bot):
    return f"""
        {{
            "tipo": "dato",
            "bot": {serializacion_completa_bot(bot)},
        }}
        """


def formatear(texto: str) -> str:
    return (
        texto.replace("\n", "")
        .replace("\r", "")
        .replace("'", '"')
        .replace('"{', "{")
        .replace('}"', "}")
        .replace('"[', "[")
        .replace(']"', "]")
    )


def send(shared_data, entrada, conn: socket):
    procesar_mensaje_salida(entrada, shared_data, conn)
