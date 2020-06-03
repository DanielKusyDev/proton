import queue
import select
import socket
import ssl
from time import sleep

from utils import Logger


class ReadWriteSocketController(object):
    def __init__(self):
        self.logger = Logger()
        self.inputs = []
        self.outputs = []
        self.message_queue = {}

    @staticmethod
    def recv_all(sock):
        result = ""
        while result[-2:] != "\r\n":
            result += sock.read(1).decode()
        return result

    @staticmethod
    def send(sock, message):
        if isinstance(message, str):
            message = message.encode()
        sock.write(message)

    def read_connections(self, connections, server_socket):
        for sock in connections:
            try:
                if sock is server_socket:
                    conn, c_addr = sock.accept()
                    conn.setblocking(0)
                    self.inputs.append(conn)
                    self.message_queue[conn] = queue.Queue()
                    self.logger.write(f"Connected by {c_addr}")
                else:
                    message = self.recv_all(sock)
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
                self.send(sock, "")

    def write_to_connections(self, connections):
        for sock in connections:
            try:
                message = self.message_queue[sock].get_nowait()
                sleep(10)
            except queue.Empty:
                self.outputs.remove(sock)
            else:
                sock.sendall(message)

    def read_or_write(self, server_socket):
        while self.inputs:
            readable, writable, _ = select.select(self.inputs, self.outputs, [])
            self.read_connections(connections=readable, server_socket=server_socket)
            self.write_to_connections(connections=writable)


class Server(object):
    def __init__(self, address=("127.0.0.1", 6666)):
        self.logger = Logger()
        self.address = address

    def get_secure_socket(self, raw_socket):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.load_cert_chain(certfile="/etc/ssl/certs/proton.pem")
        secure_socket = context.wrap_socket(raw_socket, server_side=True)
        return secure_socket

    def get_raw_socket(self, raw_socket):
        raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_socket.setblocking(False)
        raw_socket.bind(self.address)
        raw_socket.listen(5)
        return raw_socket

    def runserver(self):
        self.logger.write(f"Starting server at {self.address[0]}:{self.address[1]}")
        raw_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        rw_controller = ReadWriteSocketController()

        try:
            raw_socket = self.get_raw_socket(raw_socket)
            server_socket = self.get_secure_socket(raw_socket)
            rw_controller.inputs = [server_socket]
            rw_controller.read_or_write(server_socket)

        except socket.error as e:
            print("todo")
            raise e
        finally:
            raw_socket.close()


if __name__ == "__main__":
    s = Server(("localhost", 6666))
    s.runserver()
