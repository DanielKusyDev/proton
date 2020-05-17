from server.utils import validate_auth


def register(message):
    pass


def login(message):
    pass


@validate_auth
def logout(message):
    pass


@validate_auth
def get(message):
    pass


@validate_auth
def create(message):
    pass


@validate_auth
def alter(message):
    pass


@validate_auth
def delete(message):
    pass
