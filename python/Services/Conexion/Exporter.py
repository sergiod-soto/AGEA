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


def serializar(shared_data):

    #   bots data
    #
    def serializar_bots_data(bots_data):
        # print(Fore.RED + "type(bots_data):\n" + str(type(bots_data)) + Style.RESET_ALL)
        bots_data_copy = list(bots_data)

        if len(bots_data_copy) == 0:
            return "[]"

        json = ""
        partes = []
        partes.append("[")
        for i in range(len(bots_data_copy)):
            bot = bots_data_copy[i]
            es_ultimo = i == len(bots_data_copy) - 1
            partes.append(f"{str(bot)}")
            if not es_ultimo:
                partes.append(",")
        partes.append("]")
        json = json.join(partes)
        return json

    #   new bots
    #
    def serializar_bots_vivos(bots_vivos):

        bots_vivos_copy = list(bots_vivos)
        if len(bots_vivos_copy) == 0:
            return "[]"

        json = ""
        partes = []
        partes.append("[")
        for i in range(len(bots_vivos_copy)):
            bot = bots_vivos_copy[i]
            es_ultimo = i == len(bots_vivos_copy) - 1
            partes.append(f"\"{str(bot['id'])}\"")
            if not es_ultimo:
                partes.append(",")
        partes.append("]")
        json = json.join(partes)

        return json

    #   other
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
    # print("\n\n\nAAAAA\n\n\n")
    return f"""
    {{
    "bots_data": {serializar_bots_data(shared_data_copy["bots_data"])},
    "other": {serializar_other(shared_data_copy["other"])},
    "dev": {serializar_dev(shared_data_copy["dev"])}
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


def send(shared_data, conn):
    data = formatear(serializar(shared_data)).encode() + b"\n<END>\n"
    payload_bytes = len(data)
    payload_bits = payload_bytes * 8

    print("[EXPORTER] DATA A ENVIAR (bytes):", payload_bytes)
    print("[EXPORTER] DATA A ENVIAR (bits):", payload_bits)
    print("[EXPORTER] DATA A ENVIAR:\n" + str(data))
    conn.sendall(data)
