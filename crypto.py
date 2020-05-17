import os

import settings
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_key():
    password_provided = settings.SECRET_KEY
    password = password_provided.encode()
    salt = settings.SALT
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encrypt(message):
    key = generate_key()
    message = message.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(message)
    return encrypted_message.decode()


def compare(raw, encrypted):
    return raw == decrypt(encrypted)


def decrypt(encrypted_message):
    key = generate_key()
    encrypted_message = encrypted_message.encode()
    f = Fernet(key)
    message = f.decrypt(encrypted_message)
    return message.decode()