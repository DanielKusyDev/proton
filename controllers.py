import datetime

import models
import crypto
from utils import validate_auth, ProtonError


class Controller(object):

    def __init__(self, db_name="sqlite3.db"):
        self.db_name = db_name

    def _get_token(self, user):
        user_id = user[0]
        auth_token_model = models.AuthToken(self.db_name)
        token = auth_token_model.first(user_id=user_id)
        if token:
            token = auth_token_model.update(data={"expires": auth_token_model.get_fresh_expiration()},
                                            where={"user_id": user_id})
        else:
            token = auth_token_model.create(user_id=user_id)
        return token

    def register(self, message):
        params = message.params
        user_model = models.User(self.db_name)
        users = user_model.filter(username=params.get("username"))
        if len(users) > 0:
            raise ProtonError("Given user already exists.")

        username = params.get("username")
        password = params.get("password")
        user_model.create(username=username, password=password)
        users = user_model.first(username=username)
        return users

    def login(self, message):
        params = message.params
        username = params["username"]
        password = params["password"]
        user_model = models.User(self.db_name)
        user = user_model.first(username=username)
        if not user or not crypto.compare(password, user[2]):
            raise ProtonError("Incorrect username or/and password.")

        token = self._get_token(user)
        return token

    @validate_auth
    def logout(self, message):
        try:
            token = message.opts["auth_token"]
        except KeyError:
            raise ProtonError
        auth_model = models.AuthToken(self.db_name)
        auth_model.delete(token=token)

    @validate_auth
    def get(self, message):
        pass

    @validate_auth
    def create(self, message):
        pass

    @validate_auth
    def alter(self, message):
        pass

    @validate_auth
    def delete(self, message):
        pass
