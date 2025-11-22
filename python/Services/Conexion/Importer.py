from socket import socket
from Conexion.ProcesadoSalidaMensaje import procesar_mensaje_salida



def receive_data(conn: socket, shared_data):
    recibido = conn.recv(4096)
    if recibido:
        mensaje = recibido.decode(errors="ignore").strip()
        return procesar_mensaje_salida(mensaje, shared_data, conn)




