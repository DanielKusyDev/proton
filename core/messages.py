import json

import utils


class RequestMessage(object):

    def __init__(self, json_string):
        self.required_action_params = {
            "register": ["username", "password"],
            "login": ["username", "password"],
            "logout": None,
            "get": None,
            "create": ["content", "title"],
            "alter": ["id"],
            "delete": ["id"],
        }
        json_string = json_string
        self.json_string = json_string
        self.obj = self.deserialize_json()
        try:
            self.action = self.get_action()
            self.params = self.get_params()
            self.opts = self.get_opts()
        except (KeyError, AssertionError):
            raise utils.ProtonError("Syntax Error")

    def deserialize_json(self):
        try:
            obj = json.loads(self.json_string)
        except json.JSONDecodeError as e:
            raise utils.ProtonError("Syntax Error")
        return obj

    def get_action(self):
        action = self.obj["action"]
        assert action in self.required_action_params.keys()
        return action

    def get_params(self):
        params = self.obj.get("params", None)
        if isinstance(params, dict):
            if self.required_action_params[self.action] is not None:
                for param in self.required_action_params[self.action]:
                    assert param in params.keys()
        else:
            assert params is None
            assert self.required_action_params.get(self.action, None) is None
        return params

    def get_opts(self):
        opts = self.obj.get("opts", None)
        assert isinstance(opts, dict) or opts is None
        return opts


class ResponseMessage(object):
    def __init__(self):
        self.status = None
        self.message = None
        self.data = None
        self.request_str = None

    def construct_json(self):
        _request = {
            "status": self.status,
            "message": self.message,
            "data": self.data
        }
        request = {key: val for key, val in _request.items() if val is not None}
        self.request_str = json.dumps(request)

    def __repr__(self):
        return self.request_str


class ErrorResponseMessage(ResponseMessage):
    def __init__(self, error):
        super(ErrorResponseMessage, self).__init__()
        self.message = error
        self.status = "ERROR"
        self.construct_json()


class SuccessResponseMessage(ResponseMessage):
    def __init__(self):
        super(SuccessResponseMessage, self).__init__()
        self.status = "OK"
