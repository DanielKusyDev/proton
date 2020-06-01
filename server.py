import os
import socket, select
import queue
import ssl
from datetime import datetime

from message import Message
import utils
from controllers import Controller


class Logger(object):
    def __init__(self, log_dir="logs", max_log_dir_size=5 * 10 ** 6):
        self.log_dir = log_dir
        self.log_template = "[%d/%b/%Y %H:%M:%S] {message}"
        self.max_log_dir_size = max_log_dir_size
        self.filename_prefix = "proton_std"

    def get_log_filename(self):
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        all_log_files = sorted(filter(lambda path: self.filename_prefix in path, os.listdir(self.log_dir)))
        if not all_log_files:
            filename = f"{self.log_dir}/{self.filename_prefix}.log"
        else:
            last_file = all_log_files[-1]
            if os.stat(last_file).st_size < self.max_log_dir_size:
                filename = last_file
            else:
                last_file_name_without_ext, _ = last_file.split(".")
                try:
                    file_number = int(last_file_name_without_ext[-1])
                except ValueError:
                    file_number = 1
                filename = f"{self.log_dir}/{self.filename_prefix}{file_number}.log"
        return filename

    def _get_message(self, message):
        now = datetime.now()
        log_without_date = self.log_template.format(message=message)
        full_log = now.strftime(log_without_date)
        return full_log

    def write(self, message):
        filename = self.get_log_filename()
        with open(filename, "a") as file:
            log = self._get_message(message)
            file.write(log)


class Server(object):
    def __init__(self, address=("127.0.0.1", 2553)):
        self.logger = Logger()
        self.address = address
        self.inputs = []
        self.outputs = []
        self.message_queue = {}
        self.server_socket = None


    @staticmethod
    def recv_all(sock):
        result = ""
        while result[-2:] != "\r\n":
            result += sock.recv(1).decode()
        return result

    @staticmethod
    def send(sock, message):
        if isinstance(message, str):
            message = message.encode()
        sock.sendall(message)

    def get_secure_socket(self, raw_socket):
        raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_socket.setblocking(False)
        raw_socket.bind(addr)
        raw_socket.listen()

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(certfile=".cert/server.pem", keyfile=".cert/server.key")

        if ssl.HAS_SNI:
            secure_socket = context.wrap_socket(raw_socket, server_side=True)
        else:
            secure_socket = context.wrap_socket(raw_socket, server_side=True)
        return secure_socket

    def read_connections(self, connections):
        for sock in connections:
            if sock is self.server_socket:
                conn, c_addr = sock.accept()
                conn.setblocking(0)
                self.inputs.append(conn)
                self.message_queue[conn] = queue.Queue()
                self.logger.write(f"Connected by {c_addr}")

            else:
                message = sock.recv(1024)
                if message:
                    message_queue[sock].put(message)
                    if sock not in outputs:
                        outputs.append(sock)

                else:
                    if sock in outputs:
                        outputs.remove(sock)
                    inputs.remove(sock)
                    sock.close()
                    del message_queue[sock]

    def runserver(self):
        raw_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        try:
            server_socket = self.get_secure_socket(raw_socket)
            self.inputs = [server_socket]
            self.server_socket = server_socket
            readable, writable, _ = select.select(self.inputs, self.outputs, [])



        except socket.error as e:
            raise e
        finally:
            raw_socket.close()


if __name__ == "__main__":
    s = Server()
    addr = ("127.0.0.1", 6666)
