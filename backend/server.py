import os
import socket
import ssl
import threading
from time import sleep

import settings
from core import messages, controllers, models
from utils import Logger

logger = Logger()


def recv_all(sock: ssl.SSLSocket) -> str:
    try:
        result = ""
        while result[-2:] != "\r\n":
            result += sock.read(1).decode()
    except ssl.SSLWantReadError as e:
        print(e)
    finally:
        return result


def send(sock: ssl.SSLSocket, response: messages.Response) -> None:
    lock = threading.Lock()
    lock.acquire()

    message_str = response.json_response

    if isinstance(message_str, str):
        message_str = message_str.encode()
    sock.write(message_str)
    host, port = sock.getpeername()
    lock.release()

    host = f"{host}:{port}"
    message = response.message if response.message is not None else ""
    log_args = (response.action, message, host)

    if response.status.upper() == "OK":
        logger.success(*log_args)
    elif response.status.upper() == "ERROR":
        logger.warning(*log_args)
    else:
        logger.error(*log_args)


class ClientThread(threading.Thread):
    def __init__(self, secure_socket: ssl.SSLSocket):
        super().__init__()
        self.secure_socket = secure_socket
        self.auth_token = None

    def get_request(self):
        raw_message = recv_all(self.secure_socket)
        request = messages.Request(raw_message)
        return request

    def get_response(self, request) -> messages.Response:
        controller = controllers.Controller(self.auth_token)
        response = getattr(controller, request.action)(request)
        if request.action == "login" and response.status == "OK":
            token_id = response.data[0]["id"]
            token = models.AuthToken().first(id=token_id)[2]
            self.auth_token = token
        elif request.action == "logout" and response.status == "OK":
            self.auth_token = None
        return response

    def run(self) -> None:
        while True:
            try:
                request = self.get_request()
                response = self.get_response(request)
                send(self.secure_socket, response)
            except PermissionError as e:
                response = messages.Response(status="ERROR", message=str(e))
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
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(os.path.join(settings.CERTS_DIR, "server.pem"), os.path.join(settings.CERTS_DIR, "server.key"))

        ssock = context.wrap_socket(raw_socket, server_side=True)
        cert = ssock.getpeercert()
        if not cert or ("commonName", 'proton') not in cert['subject'][5]:
            raise Exception("Wrong CA CommonName.")
        return ssock

    def process(self, server_socket: socket.socket):
        try:
            while True:
                conn, c_addr = server_socket.accept()
                secure_client = self.get_secure_socket(conn)
                try:
                    logger.info(f"Connected by {c_addr[0]}:{c_addr[1]}")
                    c = ClientThread(secure_client)
                    c.start()
                except Exception as e:
                    response = messages.Response(status="ERROR", message=str(e))
                    send(secure_client, response)
                    secure_client.close()
        except Exception as e:
            logger.info(str(e))
        finally:
            server_socket.close()

    def runserver(self):
        logger.info(f"Starting server at {self.address[0]}:{self.address[1]}")
        server_socket = self.get_raw_socket()
        self.process(server_socket)
