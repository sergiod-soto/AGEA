import socket

def fake_server():
    s = socket.socket()
    s.bind(("localhost", 5001))
    s.listen()
    print("Fake server listening on 5001")

    conn, _ = s.accept()
    while True:
        data = conn.recv(1024).decode().strip()
        if not data:
            break
        print("[FAKE] Recibí:", data)
        conn.sendall(b"FAKE_RESPONSE\n")
