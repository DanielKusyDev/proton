import settings
from core import models
from backend import crypto
from utils import validate_auth

from core.messages import ModelResponse, Response


class Controller(object):

    def __init__(self, auth_token, db_name=settings.DATABASE):
        self.auth_token = auth_token
        self.db_name = db_name
        self.post_model = models.Post(self.db_name)
        self.user_model = models.User(self.db_name)
        self.auth_model = models.AuthToken(self.db_name)

    def _get_token(self, user_id):
        token = self.auth_model.first(user_id=user_id)
        if token:
            token = self.auth_model.update(data={"expires": self.auth_model.get_fresh_expiration()},
                                           where={"user_id": user_id})
        else:
            token = self.auth_model.create(user_id=user_id)
        return token

    def register(self, request):
        params = request.params
        users = self.user_model.filter(username=params.get("username"))
        if len(users) > 0:
            return Response(status="ERROR", message="Given user already exists.", action="register")

        username = params.get("username")
        password = params.get("password")
        self.user_model.create(username=username, password=password)
        users = self.user_model.first(username=username)
        return ModelResponse("OK", self.user_model, users, action="register")

    def login(self, request):
        params = request.params
        username = params["username"]
        password = params["password"]
        user = self.user_model.first(username=username)
        if not user or not crypto.compare(password, user[2]):
            return Response(status="ERROR", message="Incorrect username or/and password.", action="login")

        token = self._get_token(user[0])
        return ModelResponse("OK", self.auth_model, token, action="login")

    @validate_auth
    def logout(self, request):
        token = self.auth_token
        self.auth_model.delete(token=token)
        return Response("OK", action="logout")

    @validate_auth
    def create(self, request):
        user_id = self.auth_model.first(token=self.auth_token)[1]
        post = self.post_model.create(user_id=user_id, **request.params)
        return ModelResponse(status="OK", model=self.post_model, raw_instance=post, action="create")

    @validate_auth
    def get(self, request):
        instance = None
        if getattr(request, "params", None) is not None and request.params.get("id", None) is not None:
            post_id = request.params["id"]
            if post_id is not None:
                instance = self.post_model.filter(id=post_id)
        else:
            instance = self.post_model.all()
        if instance:
            return ModelResponse("OK", self.post_model, raw_instance=instance, action="get")
        return Response("WRONG", "Not Found.", action="get")

    @validate_auth
    def alter(self, request):
        post_id = request.params.pop("id")
        instance = self.post_model.update(data=request.params, where={"id": post_id})
        if instance:
            return ModelResponse("OK", self.post_model, instance, action="alter")
        return Response("WRONG", "Not Found.", action="alter")

    @validate_auth
    def delete(self, request):
        post_id = request.params.pop("id")
        obj = self.post_model.delete(id=post_id)
        if obj is None:
            return Response("WRONG", "Not Found.", action="delete")
        return Response("OK", data={"id": post_id}, action="delete")

