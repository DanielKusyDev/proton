from backend.server import Server

server = Server(("localhost", 6666))
server.runserver()
