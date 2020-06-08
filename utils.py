import base64
import os
import secrets
import sqlite3
import ssl
import string
from datetime import datetime

import settings
from core import models, messages


class ProtonError(Exception):
    """Proton protocol error base class"""
    pass


def generate_token(length=40):
    result = ''.join((secrets.choice(string.ascii_letters) for _ in range(length)))
    return result


def validate_auth(fn):
    def wrapper(*args, **kwargs):
        controller, message = args
        try:
            token = controller.auth_token
            assert controller.auth_token is not None
            token_model = models.AuthToken(controller.db_name)
            assert token_model.is_valid(token=token)
        except (KeyError, AssertionError, ProtonError):
            raise PermissionError("Permission denied. Authorization required.")
        else:
            return fn(*args, **kwargs)

    return wrapper


def create_conn(db_name=settings.DATABASE):
    try:
        conn = sqlite3.connect(db_name)
        return conn
    except sqlite3.Error as e:
        print(e)


def create_db(db_name=settings.DATABASE):
    conn = create_conn(db_name)
    cursor = conn.cursor()
    with open(os.path.join("core/db/create_db.sql"), "r") as script:
        cursor.executescript(script.read())


def get_image_base64(path):
    with open(path, "rb") as file:
        image = file.read()
        image = base64.b64encode(image).decode()
    return image


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
            last_file = f"{self.log_dir}/{all_log_files[-1]}"
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
        log = self._get_message(message)
        with open(filename, "a") as file:
            file.write(log + "\n")
        print(log)
