import socket
import threading
import time
from queue import Queue, Empty


class FakeClientThread:
    def __init__(self, host="127.0.0.1", port=5069, reconnect=True):
        self.host = host
        self.port = port
        self.reconnect = reconnect

        self._sock = None
        self._sock_lock = threading.Lock()

        self._receiver_thread = None
        self._sender_thread = None
        self._stop = threading.Event()

        # cola thread-safe para mensajes
        self._send_queue = Queue()

    def _ensure_connected(self, create_if_missing=True):
        """Asegura que self._sock apunta a una conexión válida (thread-safe)."""
        with self._sock_lock:
            if self._sock:
                return True
            if not create_if_missing:
                return False
            try:
                s = socket.create_connection((self.host, self.port), timeout=3)
                s.settimeout(1.0)
                self._sock = s
                print(f"[FAKE CLIENT] conectado a {self.host}:{self.port}\n")
                return True
            except Exception as e:
                # no conectó ahora, dejar _sock = None
                print(f"[FAKE CLIENT] fallo al conectar en _ensure_connected: {e}")
                self._sock = None
                return False

    def _receiver_loop(self):
        try:
            while not self._stop.is_set():
                # intentar tener socket
                if not self._ensure_connected(create_if_missing=self.reconnect):
                    # sleep antes de reintentar para no spam
                    time.sleep(0.2)
                    continue

                try:
                    data = self._sock.recv(4096)
                except socket.timeout:
                    # no imprimir cada timeout para evitar spam; simplemente seguir
                    continue
                except Exception as e:
                    print(f"[FAKE CLIENT] error recv -> cerrar socket: {e}")
                    with self._sock_lock:
                        try:
                            if self._sock:
                                self._sock.close()
                        except Exception:
                            pass
                        self._sock = None
                    # esperar un poco antes de reconectar
                    time.sleep(0.2)
                    continue

                if not data:
                    # servidor cerró la conexión
                    print(
                        "[FAKE CLIENT] servidor cerró la conexión (recv returned b'')"
                    )
                    with self._sock_lock:
                        try:
                            if self._sock:
                                self._sock.close()
                        except Exception:
                            pass
                        self._sock = None
                    if not self.reconnect:
                        break
                    time.sleep(0.2)
                    continue

                print("[FAKE CLIENT] Recibido:", data.decode(errors="ignore").strip())

        finally:
            with self._sock_lock:
                try:
                    if self._sock:
                        self._sock.close()
                except Exception:
                    pass
                self._sock = None
            print("[FAKE CLIENT] receiver loop finalizado")

    def _sender_loop(self):
        while not self._stop.is_set():
            try:
                msg = self._send_queue.get(timeout=0.1)
            except Empty:
                continue

            if msg is None:
                # señal de parada
                break

            # enviar bytes seguro
            self._send_bytes(msg)

    def _send_bytes(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        # asegurar socket antes de enviar
        if not self._ensure_connected(create_if_missing=True):
            print("[FAKE CLIENT] no conectado, mensaje descartado")
            return

        with self._sock_lock:
            try:
                self._sock.sendall(data)
            except Exception as e:
                print("[FAKE CLIENT] Error al enviar:", e)
                try:
                    if self._sock:
                        self._sock.close()
                except Exception:
                    pass
                self._sock = None

    # API pública
    def start(self, daemon=True):
        if self._receiver_thread and self._receiver_thread.is_alive():
            return
        self._stop.clear()
        self._receiver_thread = threading.Thread(
            target=self._receiver_loop, daemon=daemon, name="FakeClientReceiver"
        )
        self._receiver_thread.start()
        self._sender_thread = threading.Thread(
            target=self._sender_loop, daemon=daemon, name="FakeClientSender"
        )
        self._sender_thread.start()

    def stop(self, timeout=2.0):
        print("[FAKE CLIENT] deteniendo...")
        self._stop.set()
        # wake sender
        self._send_queue.put(None)
        # cerrar socket para desbloquear recv/accept
        with self._sock_lock:
            try:
                if self._sock:
                    self._sock.close()
            except Exception:
                pass
            self._sock = None
        if self._receiver_thread:
            self._receiver_thread.join(timeout)
        if self._sender_thread:
            self._sender_thread.join(timeout)
        print("[FAKE CLIENT] detenido")

    def queue_message(self, message: str):
        """Agrega un mensaje a la cola para enviar (thread-safe)."""
        self._send_queue.put(message)

    def send_now(self, message: str, timeout_connect=3.0):
        """Intento sin cola: bloqueante, asegura conexión temporal y envía."""
        if isinstance(message, str):
            data = message.encode("utf-8")
        else:
            data = message
        # try to ensure connection (short timeout)
        with self._sock_lock:
            if not self._ensure_connected(create_if_missing=True):
                print("[FAKE CLIENT] send_now: no se pudo conectar")
                return
            try:
                print("[FAKE CLIENT] Enviando:\n" + str(data))
                self._sock.sendall(data)
                print("[FAKE CLIENT] send_now: enviado")
            except Exception as e:
                print("[FAKE CLIENT] send_now error:", e)
                try:
                    if self._sock:
                        self._sock.close()
                except Exception:
                    pass
                self._sock = None


# helper
def start_fake_client(host="127.0.0.1", port=5069):
    print(f"[FAKE CLIENT] Iniciando cliente en {host}:{port} ...")
    c = FakeClientThread(host, port)
    c.start()
    return c


def run_demo(n=500, delay=2.0):
    c = start_fake_client()
    try:
        for _ in range(n):
            m = b'{"tipo":"actualizacion"}'
            c.queue_message(m)
            time.sleep(delay)
    finally:
        c.stop()
