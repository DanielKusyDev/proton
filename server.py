import socket

from message import Message
from utils import ProtonError
from controllers import Controller


class Server(object):
    def __init__(self, address=("127.0.0.1", 2553)):
        self.address = address

    def recv_all(self, sock):
        result = ""
        while result[-2:] != "\r\n":
            result += sock.recv(1).decode()
        return result

    def dispatch(self, message):
        action = message.action
        try:
            urlpatterns[action](message)
        except KeyError as e:
            print(e)

    def runserver(self):
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        sock.bind(self.address)
        sock.listen(10)
        try:
            while True:
                conn, addr = sock.accept()
                with conn:
                    raw_message = self.recv_all(conn)
                    try:
                        message = Message(raw_message)

                    except ProtonError as e:
                        str(e)
                    self.dispatch(message)
        except socket.error as e:
            print(e)


if __name__ == "__main__":
    s = Server()
    r = """{
        "action": "update",
        "params": {
            "username": "daniel",
            "password": "pass"
        }
    }"""
    message = Message(r)
    controller = Controller()
    result = getattr(controller, message.action)(message)
    print(result)