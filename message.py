import json

import utils


class Message(object):

    def __init__(self, json_string):
        self.required_action_params = {
            "register": ["username", "password"],
            "login": ["username", "password"],
            "logout": None,
            "get": None,
            "create": ["image", "content", "header"],
            "alter": ["id"],
            "delete": ["id"],
        }
        json_string = json_string.lower()
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
