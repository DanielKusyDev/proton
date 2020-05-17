class ProtonError(BaseException):
    pass


def validate_auth(fn):
    def wrapper(*args, **kwargs):
        message = args[0]
        # tu walidacja tokenu z message
        return fn(*args, **kwargs)
    return wrapper
