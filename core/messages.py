import json
from typing import Union

import utils
from core import models


class Request(object):

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
        try:
            self.obj = self.deserialize_json()
            self.action = self.get_action()
            self.params = self.get_params()
        except (KeyError, AssertionError, json.JSONDecodeError) as e:
            raise utils.ProtonError("Syntax Error")

    def deserialize_json(self):
        obj = json.loads(self.json_string)
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

class Response(object):
    def __init__(self, status, message=None, data=None):
        self.message = message
        self.status = status
        self.data = data
        self.json_response = None

        self.construct_json()

    def construct_json(self):
        _request = {
            "status": self.status,
            "message": self.message,
            "data": self.data
        }
        request = {key: val for key, val in _request.items() if val is not None}
        self.json_response = json.dumps(request)
        self.json_response += "\r\n"

    def __repr__(self):
        return self.json_response


class ModelResponse(Response):
    def __init__(self, status, model, raw_instance: Union[list, tuple], message=""):

        if not isinstance(model, models.Model):
            model = model()
        self.model = model

        if raw_instance and not isinstance(raw_instance[0], tuple):
            raw_instance = [raw_instance]
        self.raw_instance = raw_instance

        data = self.create_data()
        super(ModelResponse, self).__init__(status, message, data=data)

    def get_record(self, instance, table_schema):
        return {col_name: val for col_name, val in zip(table_schema, instance) if
                               col_name not in self.model.write_only}

    def create_data(self):
        table_schema = self.model.get_table_cols()
        data = []
        for instance in self.raw_instance:
            single_obj_data = self.get_record(instance, table_schema)
            data.append(single_obj_data)
        return data


class PostModelResponse(ModelResponse):
    def get_record(self, instance, table_schema):

        record_data = {}
        for col_name, val in zip(table_schema, instance):
            if col_name not in self.model.write_only:
                if col_name == "image":
                    val = utils.get_image_base64(val)
                record_data[col_name] = val
        return record_data

