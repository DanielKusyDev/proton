import socket, select
import queue

from message import Message
import utils
from controllers import Controller


class Server(object):
    def __init__(self, address=("127.0.0.1", 2553)):
        self.address = address

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

    def dispatch(self, raw_message):
        message = Message(raw_message)
        controller = Controller()
        try:
            result = getattr(controller, message.action)(message)
            # if isinstance(result, tuple):

        except PermissionError as e:
            result = "Permission denied. Authorization required."
        finally:
            return result

    def _process_writable_connections(self, writable, output_conns, message_queue):
        for sock in writable:
            try:
                message = message_queue[sock].get()
            except queue.Empty:
                output_conns.remove(sock)
                raise queue.Empty

            # try:
            self.dispatch(sock, message)
            # except utils.ProtonError as e:
            #     self.send()

        return writable, output_conns, message_queue

    @staticmethod
    def _process_exceptional_connections(exceptional, input_conns, output_conns, message_queue):
        for sock in exceptional:
            input_conns.remove(sock)
            if sock in output_conns:
                output_conns.remove(sock)
            sock.close()
            del message_queue[sock]
        return exceptional, input_conns, output_conns, message_queue

    @staticmethod
    def _process_input_connections(server_socket, readable, input_conns, output_conns, message_queue):
        for sock in readable:
            if sock is server_socket:
                conn, c_addr = sock.accept()
                conn.setblocking(0)
                input_conns.append(conn)
                message_queue[conn] = queue.Queue()
            else:
                message = sock.recv(1024)
                if message:
                    message_queue[sock].put(message)
                    if sock not in output_conns:
                        output_conns.append(sock)

                else:
                    if sock in output_conns:
                        output_conns.remove(sock)
                    input_conns.remove(sock)
                    sock.close()
                    del message_queue[sock]
        return server_socket, readable, input_conns, output_conns, message_queue

    def runserver(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setblocking(False)
        server_socket.bind(addr)
        server_socket.listen()

        input_conns = [server_socket]
        output_conns = []

        message_queue = {}
        while input_conns:
            readable, writable, exceptional = select.select(input_conns, output_conns, input_conns)

            server_socket, readable, input_conns, output_conns, message_queue = self._process_input_connections(
                server_socket, readable, input_conns,
                output_conns, message_queue)
            writable, output_conns, message_queue = self._process_writable_connections(writable, output_conns,
                                                                                       message_queue)
            exceptional, input_conns, output_conns, message_queue = self._process_exceptional_connections(exceptional,
                                                                                                          input_conns,
                                                                                                          output_conns,
                                                                                                          message_queue)
        server_socket.close()


if __name__ == "__main__":
    s = Server()
    addr = ("127.0.0.1", 6666)
