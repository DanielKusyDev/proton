import socket

from message import Message
import utils
from controllers import Controller


class Server(object):
    def __init__(self, address=("127.0.0.1", 2553)):
        self.address = address

    def recv_all(self, sock):
        result = ""
        while result[-2:] != "\r\n":
            result += sock.recv(1).decode()
        return result

    def dispatch(self, raw_message):
        message = Message(raw_message)
        controller = Controller()
        try:
            result = getattr(controller, message.action)(message)
        except PermissionError as e:
            self.send("Permission denied. Authorization required.")
        return result

    def runserver(self):
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        sock.bind(self.address)
        sock.listen(10)
        try:
            while True:
                conn, addr = sock.accept()
                with conn:
                    raw_message = self.recv_all(conn)
                    request_result = self.dispatch(raw_message)
        except (socket.error, utils.ProtonError) as e:
            print(e)


if __name__ == "__main__":
    s = Server()