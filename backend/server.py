import queue
import select
import socket
import ssl

from core import messages
from utils import Logger

logger = Logger()


def recv_all(sock: ssl.SSLSocket) -> str:
    result = ""
    while result[-2:] != "\r\n":
        result += sock.read(1).decode()
    return result


def send(sock: ssl.SSLSocket, message: messages.ResponseMessage) -> None:
    message_str = message.request_str

    if isinstance(message_str, str):
        message_str = message_str.encode()
    sock.write(message_str)

    host, port = sock.getpeername()
    logger.write(f"{host}:{port} | {message.status}: {message.message} ")


class ConnectionManager(object):
    def __init__(self, server_socket):
        self.server_socket = server_socket
        self.inputs = [server_socket]
        self.outputs = []
        self.message_queue = {}

        self.readable, self.writable, _ = (None, None, None)

    def handle_unexpected_error(self, e):
        for conn, val in self.message_queue.items():
            error_response = messages.ErrorResponseMessage(error=str(e))
            send(conn, error_response)
            logger.write(error_response.message)

    def process(self):
        while self.inputs:
            self.readable, self.writable, _ = select.select(self.inputs, self.outputs, self.inputs)
            try:
                self.read_input()
                self.write_output()
            except Exception as e:
                self.handle_unexpected_error(e)
                break

    def read_input(self):
        for sock in self.readable:
            try:
                if sock is self.server_socket:
                    conn, c_addr = sock.accept()
                    conn.setblocking(False)
                    self.inputs.append(conn)
                    self.message_queue[conn] = queue.Queue()
                    logger.write(f"Connected by {c_addr[0]}:{c_addr[1]}")
                else:
                    message = recv_all(sock)
                    if message:
                        self.message_queue[sock].put(message)
                        if sock not in self.outputs:
                            self.outputs.append(sock)
                    else:
                        if sock in self.outputs:
                            self.outputs.remove(sock)
                        self.inputs.remove(sock)
                        sock.close()
                        del self.message_queue[sock]
            except ssl.SSLWantReadError:
                message = messages.ErrorResponseMessage("Syntax Error")
                send(sock, message)

    def write_output(self):
        for sock in self.writable:
            try:
                raw_message = self.message_queue[sock].get_nowait()
                # sleep(10)
            except queue.Empty:
                self.outputs.remove(sock)
            else:
                # todo
                sock.sendall(raw_message)


class Server(object):
    def __init__(self, address=("127.0.0.1", 6666)):
        self.address = address

    def get_secure_socket(self, raw_socket: socket.socket) -> ssl.SSLSocket:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.load_cert_chain(certfile="/etc/ssl/certs/proton.pem")
        secure_socket = context.wrap_socket(raw_socket, server_side=True)
        return secure_socket

    def get_raw_socket(self, raw_socket: socket.socket) -> socket.socket:
        raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_socket.setblocking(False)
        raw_socket.bind(self.address)
        raw_socket.listen(5)
        return raw_socket

    def runserver(self) -> None:
        logger.write(f"Starting server at {self.address[0]}:{self.address[1]}")
        raw_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

        try:
            raw_socket = self.get_raw_socket(raw_socket)
            server_socket = self.get_secure_socket(raw_socket)
            connections = ConnectionManager(server_socket)
            connections.process()
        except socket.error as e:
            print("todo")
            raise e
        finally:
            raw_socket.close()
