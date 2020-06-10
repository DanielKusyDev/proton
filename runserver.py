from backend.server import Server
import settings

server = Server(("localhost", 6666))
server.runserver()
