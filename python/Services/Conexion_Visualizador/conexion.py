# Services/Conexion_Visualizador/conexion.py

import multiprocessing
import socket

from Config import settings
from Services.Conexion_Visualizador import protocolo
from Services.Conexion_Visualizador.importer import receive_data


def _manejar_cliente(conn: socket.socket, addr, shared_data) -> None:
    """Gestiona la sesión completa de un cliente conectado."""
    print(f"[CONEXION] Cliente conectado: {addr}")
    with conn:
        while True:
            try:
                recibido = protocolo.recibir(conn)

                if recibido is None:
                    print("[CONEXION] Cliente cerró la conexión.")
                    break

                respuesta = receive_data(recibido, shared_data)

                if respuesta is not None:
                    protocolo.enviar(conn, respuesta)

            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                print("[CONEXION] Cliente desconectado durante recepción.")
                break
            except Exception as e:
                print(f"[CONEXION] Error inesperado: {e}")
                break


def run_exporter(shared_data) -> None:
    """
    Servidor TCP bloqueante. Acepta una conexión cada vez.
    Cuando un cliente se desconecta, espera el siguiente.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((settings.UNITY_HOST, settings.UNITY_PORT))
        s.listen(1)
        print(f"[CONEXION] Esperando cliente en {settings.UNITY_HOST}:{settings.UNITY_PORT}...")

        while True:
            conn, addr = s.accept()
            _manejar_cliente(conn, addr, shared_data)
            print("[CONEXION] Cliente desconectado. Esperando nueva conexión...")


def thread_exporter(shared_data) -> multiprocessing.Process:
    """Lanza run_exporter en un proceso independiente."""
    p = multiprocessing.Process(target=run_exporter, args=(shared_data,), daemon=True)
    p.start()
    return p
