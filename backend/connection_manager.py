import queue
import select
import socket
import ssl

import utils
from core import messages

logger = utils.Logger()


def recv_all(sock: ssl.SSLSocket) -> str:
    try:
        result = ""
        while result[-2:] != "\r\n":
            result += sock.read(1).decode()
    finally:
        return result


def send(sock: ssl.SSLSocket, response: messages.Response) -> None:
    message_str = response.json_response

    if isinstance(message_str, str):
        message_str = message_str.encode()
    sock.write(message_str)

    host, port = sock.getpeername()
    logger.write(f"{host}:{port} | {response.status}: {response.message} ")


class ConnectionManager(object):
    def __init__(self, server_socket):
        self.server_socket = server_socket
        self.inputs = [server_socket]
        self.outputs = []
        self.message_queue = {}

        self.readable, self.writable, _ = (None, None, None)

    def get_secure_socket(self, raw_socket: socket.socket) -> ssl.SSLSocket:
        ssock = ssl.wrap_socket(raw_socket, server_side=True, ca_certs="backend/certs/client.pem",
                                certfile="backend/certs/server.pem", cert_reqs=ssl.CERT_REQUIRED,
                                ssl_version=ssl.PROTOCOL_TLS)
        cert = ssock.getpeercert()
        if not cert or ("commonName", 'proton') not in cert['subject'][5]:
            raise Exception
        return ssock


    def handle_unexpected_error(self, e):
        for conn, val in self.message_queue.items():
            error_response = messages.Response(status="ERROR", message="SERVER ERROR")
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
                    secure_client = self.get_secure_socket(conn)
                    self.inputs.append(secure_client)
                    self.message_queue[secure_client] = queue.Queue()
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
                message = messages.Response(status="ERROR", message="SYNTAX ERROR")
                send(sock, message)

    def write_output(self):
        for sock in self.writable:
            try:
                raw_message = self.message_queue[sock].get_nowait()
                response = messages.Response(status="OK", message=raw_message)
            except queue.Empty:
                self.outputs.remove(sock)
            else:
                send(sock, response)
