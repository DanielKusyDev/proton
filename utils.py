import random
import secrets
import string


class ProtonError(BaseException):
    pass


def generate_token(length=40):
    result = ''.join((secrets.choice(string.ascii_letters) for _ in range(length)))
    return result


def validate_auth(fn):
    def wrapper(*args, **kwargs):
        message = args[0]
        # tu walidacja tokenu z message
        return fn(*args, **kwargs)

    return wrapper