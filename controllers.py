import datetime

import models
import crypto
from utils import validate_auth, ProtonError


class Controller(object):

    def __init__(self, db_name="sqlite3.db"):
        self.db_name = db_name
        self.post_model = models.Post(self.db_name)
        self.user_model = models.User(self.db_name)
        self.auth_model = models.AuthToken(self.db_name)

    def _get_token(self, user):
        user_id = user[0]
        token = self.auth_model.first(user_id=user_id)
        if token:
            token = self.auth_model.update(data={"expires": self.auth_model.get_fresh_expiration()},
                                           where={"user_id": user_id})
        else:
            token = self.auth_model.create(user_id=user_id)
        return token

    def register(self, message):
        params = message.params
        users = self.user_model.filter(username=params.get("username"))
        if len(users) > 0:
            raise ProtonError("Given user already exists.")

        username = params.get("username")
        password = params.get("password")
        self.user_model.create(username=username, password=password)
        users = self.user_model.first(username=username)
        return users

    def login(self, message):
        params = message.params
        username = params["username"]
        password = params["password"]
        user = self.user_model.first(username=username)
        if not user or not crypto.compare(password, user[2]):
            raise ProtonError("Incorrect username or/and password.")

        token = self._get_token(user)
        return token

    @validate_auth
    def logout(self, message):
        token = message.opts["auth_token"]
        self.auth_model.delete(token=token)

    @validate_auth
    def create(self, message):
        user_id = self.auth_model.first(token=message.opts["auth_token"])[1]
        post = self.post_model.create(user_id=user_id, **message.params)
        return post

    @validate_auth
    def get(self, message):

        if getattr(message, "params", None) is not None and message.params.get("id", None) is not None:
            post_id = message.params["id"]
            if post_id is not None:
                return self.post_model.first(id=post_id)
        else:
            return self.post_model.all()

    @validate_auth
    def alter(self, message):
        post_id = message.params.pop("id")
        return self.post_model.update(data=message.params, where={"id": post_id})

    @validate_auth
    def delete(self, message):
        post_id = message.params.pop("id")
        return self.post_model.delete(id=post_id)
