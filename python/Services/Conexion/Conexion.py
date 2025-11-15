# mundo "fisico", tiene su conexion para que otro programa pueda leer la informacion
# en el puerto y representarla visualmente.


import socket
import time
#from colorama import Fore, Style, init

from Conexion.Exporter import send
from Conexion.Importer import receive_data


print("entrada en conexion satisfactoria")

#
#
#
HOST = "localhost"
PORT = 12345
#
#
#


def run_exporter(shared_data):
    """Envía y recibe datos por socket TCP"""
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("localhost", PORT))
            s.listen(1)

            print(f"[CONEXION] Esperando cliente en puerto {PORT}...")
            conn, addr = s.accept()

            with conn:
                print(f"[CONEXION] Cliente conectado en: {addr}")
                conn.settimeout(0.05)  # pequeña espera, no bloqueante

                while True:
                    try:
                        # --- ENVÍO ---
                        send(shared_data, conn)

                        # --- RECEPCIÓN ---
                        try:
                            receive_data(conn, shared_data)
                        except socket.timeout:
                            pass  # no llegó nada, seguimos

                        time.sleep(0.2)  # evitar usar 100% CPU

                    except (
                        BrokenPipeError,
                        ConnectionResetError,
                        ConnectionAbortedError,
                    ):
                        print(
                            "[CONEXION] Cliente desconectado. Esperando nueva conexión..."
                        )
                        break

                    except Exception as e:
                        print(f"[CONEXION] Error inesperado: {e}")
                        time.sleep(1)
                        break
