# ...existing code...
import multiprocessing
import select
import socket
import time
from Services.Conexion_Visualizador.importer import receive_data
import main

#
#
#
HOST = "127.0.0.1"
PORT = 5069 if main.debug else 5001


def run_exporter(shared_data):
    """
    Envía y recibe datos por socket TCP.

    Parámetros:
    - shared_data: manager.dict() con el estado compartido
    """

    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(1)

            print(f"[CONEXION] Esperando cliente en puerto {PORT}...")
            conn, addr = s.accept()

            with conn:
                print(f"[CONEXION] Cliente conectado en: {addr}")
                conn.settimeout(None)  # usar select para esperar, no timeouts cortos

                while True:
                    # esperar hasta 1s a que haya datos para leer
                    ready, _, _ = select.select([conn], [], [], 1.0)
                    if not ready:
                        # no hay datos en este ciclo (equivalente a timeout)
                        # puedes quitar el print o mantener para depuración
                        # print("no data ready (select timeout)")
                        continue

                    try:
                        recibido = conn.recv(4096)
                        # si recv devuelve b'' -> cliente cerró la conexión
                        if not recibido:
                            print("[CONEXION] cliente cerró la conexión")
                            break
                        # responde a la peticion
                        respuesta = receive_data(recibido, shared_data)
                        if respuesta == "None":
                            continue
                        conn.sendall(respuesta)
                    except (
                        BrokenPipeError,
                        ConnectionResetError,
                        ConnectionAbortedError,
                    ):
                        print(
                            "[CONEXION] Cliente desconectado durante recepción. Rompiendo."
                        )
                        break
                    except Exception as e:
                        print(
                            f"[CONEXION] Error inesperado en recepción: {e}, entrada:\n{recibido}"
                        )
                        time.sleep(1)
                        break

                    # pequeño sleep para evitar bucle ocupado (opcional)
                    time.sleep(0.01)

            # aquí se cierra la conexión aceptada y volvemos a esperar otra
            print("[CONEXION] Cliente desconectado. Esperando nueva conexión...")


def thread_exporter(shared_data):
    p = multiprocessing.Process(target=run_exporter, args=(shared_data,))
    p.start()

    return p
