import models
import crypto
from utils import validate_auth, ProtonError


class Controller(object):

    @classmethod
    def register(cls, message):
        params = message.params
        user_model = models.User()
        users = user_model.filter(username=params.get("username"))
        if len(users) > 0:
            raise ProtonError("Given user already exists.")

        username = params.get("username")
        password = params.get("password")
        user_model.create(username=username, password=password)
        users = user_model.filter(username=username)
        return users

    @classmethod
    def login(cls, message):
        params = message.params
        username = params["username"]
        password = params["password"]
        user_model = models.User()
        users = user_model.filter(username=username)
        if len(users) != 1 or not crypto.compare(password, users[0][2]):
            raise ProtonError("Incorrect username or/and password.")

        user_id = users[0][0]
        auth_token_model = models.AuthToken()
        tokens = auth_token_model.filter(user_id=user_id)
        if len(tokens) == 1:
            auth_token = tokens[0]
            # auth_token
        #     auth_token = auth_token_model.create()
        # return auth_token

    @classmethod
    @validate_auth
    def logout(cls, message):
        pass

    @classmethod
    @validate_auth
    def get(cls, message):
        pass

    @classmethod
    @validate_auth
    def create(cls, message):
        pass

    @classmethod
    @validate_auth
    def alter(cls, message):
        pass

    @classmethod
    @validate_auth
    def delete(cls, message):
        pass
