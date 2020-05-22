import random
import secrets
import sqlite3
import string

import models


class ProtonError(BaseException):
    """Proton protocol error base class"""
    pass


def generate_token(length=40):
    result = ''.join((secrets.choice(string.ascii_letters) for _ in range(length)))
    return result


def validate_auth(fn):
    def wrapper(*args, **kwargs):
        controller, message = args
        try:
            token = message.opts["auth_token"]
            token_model = models.AuthToken(controller.db_name)
            assert token_model.is_valid(token=token)
        except (KeyError, AssertionError, ProtonError):
            raise PermissionError("Permission denied. Authorization required.")
        return fn(*args, **kwargs)

    return wrapper


def create_conn(db_name="sqlite3.db"):
    try:
        conn = sqlite3.connect(db_name)
        return conn
    except sqlite3.Error as e:
        print(e)


def create_db(db_name="sqlite3.db"):
    conn = create_conn(db_name)
    cursor = conn.cursor()
    with open("create_db.sql", "r") as script:
        cursor.executescript(script.read())
