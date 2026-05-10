import socket
import threading
from config import AppConfig

class ProxyServer:
    def __init__(self):
        self.server_socket = None
        self.is_running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((AppConfig.local_host, AppConfig.local_proxy_port))
        self.server_socket.listen(256)
        self.is_running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self.is_running:
            try:
                client, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except OSError:
                break

    def _handle_client(self, client):
        try:
            handshake = client.recv(256)
            if handshake[0] != 0x05:
                client.close()
                return
            n_methods = handshake[1]
            client.recv(n_methods + 1)
            client.sendall(b"\x05\x00")
            req = client.recv(256)
            if req[0] != 0x05 or req[1] != 0x01:
                client.close()
                return
            atyp = req[3]
            if atyp == 0x01:
                dest_ip = socket.inet_ntoa(req[4:8])
                dest_port = int.from_bytes(req[8:10], "big")
            elif atyp == 0x03:
                dest_len = req[4]
                dest_ip = req[5:5 + dest_len].decode()
                dest_port = int.from_bytes(req[5 + dest_len:7 + dest_len], "big")
            else:
                client.close()
                return
            client.sendall(b"\x05\x00\x00\x01\x7f\x00\x00\x01" + req[8:10])
            tor = socket.create_connection((AppConfig.local_host, AppConfig.tor_socks_port), timeout=10)
            threading.Thread(target=self._relay, args=(client, tor), daemon=True).start()
            threading.Thread(target=self._relay, args=(tor, client), daemon=True).start()
        except Exception:
            client.close()

    def _relay(self, src, dst):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                dst.sendall(data)
        except Exception:
            pass
        finally:
            src.close()
            dst.close()

    def stop(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()