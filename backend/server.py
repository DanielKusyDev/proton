import socket
import ssl
import threading

from core import messages, controllers
from utils import Logger

logger = Logger()


def recv_all(sock: ssl.SSLSocket) -> str:
    result = ""
    while result[-2:] != "\r\n":
        result += sock.read(1).decode()
    return result


def send(sock: ssl.SSLSocket, response: messages.Response) -> None:
    message_str = response.json_response

    if isinstance(message_str, str):
        message_str = message_str.encode()
    sock.write(message_str)

    host, port = sock.getpeername()
    logger.write(f"{host}:{port} | {response.status}: {response.message} ")


class ClientThread(threading.Thread):
    def __init__(self, secure_socket: ssl.SSLSocket):
        super().__init__()
        self.secure_socket = secure_socket

    def get_request(self):
        raw_message = recv_all(self.secure_socket)
        request = messages.Request(raw_message)
        return request

    def run(self) -> None:
        request = self.get_request()
        try:
            response = getattr(controllers.Controller(), request.action)(request)
        except PermissionError as e:
            response = messages.Response(status="ERROR", message=str(e))
        finally:
            send(self.secure_socket, response)


class Server(object):
    def __init__(self, address=("127.0.0.1", 6666)):
        self.address = address

    def get_raw_socket(self) -> socket.socket:
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_socket.bind(self.address)
        raw_socket.listen(100)
        return raw_socket

    def get_secure_socket(self, raw_socket: socket.socket) -> ssl.SSLSocket:
        ssock = ssl.wrap_socket(raw_socket, server_side=True, ca_certs="backend/certs/client.pem",
                                certfile="backend/certs/server.pem", cert_reqs=ssl.CERT_REQUIRED,
                                ssl_version=ssl.PROTOCOL_TLS)
        cert = ssock.getpeercert()
        if not cert or ("commonName", 'proton') not in cert['subject'][5]:
            raise Exception
        return ssock

    def process(self, server_socket: socket.socket):
        try:
            while True:
                conn, c_addr = server_socket.accept()
                secure_client = self.get_secure_socket(conn)
                secure_client.setblocking(False)
                try:
                    logger.write(f"Connected by {c_addr[0]}:{c_addr[1]}")
                    c = ClientThread(secure_client)
                    c.start()
                except Exception as e:
                    response = messages.Response(status="ERROR", message=str(e))
                    send(secure_client, response)
                    secure_client.close()
        except Exception as e:
            logger.write(str(e))
        finally:
            server_socket.close()

    def runserver(self):
        logger.write(f"Starting server at {self.address[0]}:{self.address[1]}")
        server_socket = self.get_raw_socket()
        self.process(server_socket)
