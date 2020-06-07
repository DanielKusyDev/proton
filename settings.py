import codecs
from configparser import RawConfigParser

parser = RawConfigParser()
parser.read_file(codecs.open("config.ini", "r", "utf-8"))

SECRET_KEY = parser.get("SECRET", "KEY")
SALT = parser.get("SECRET", "SALT").encode()

EXPIRATION = {
    "minutes": 15
}
DATABASE = "core/db/sqlite3.db"
