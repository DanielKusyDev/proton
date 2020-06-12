import os

import utils
from backend.server import Server
import settings

if not os.path.exists(settings.DATABASE):
    utils.create_db(settings.DATABASE)
server = Server(("localhost", 6666))
server.runserver()
