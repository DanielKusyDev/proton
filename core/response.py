from typing import Union

from core import models


class Response(object):
    def __init__(self, status, message=None):
        self.message = message
        self.status = status.upper() == "OK"


class ModelResponse(Response):
    def __init__(self, status, model, raw_instance: Union[list, tuple], message=None):
        super(ModelResponse, self).__init__(status=status, message=message)
        if not isinstance(model, models.Model):
            model = model()
        if not isinstance(raw_instance[0], tuple):
            raw_instance = [raw_instance]

        self.model = model
        self.raw_instance = raw_instance
        self.message = message
        self.data = self.create_data()

    def __str__(self):
        return "xd"

    def create_data(self):
        table_schema = self.model.get_table_cols()
        data = []
        for instance in self.raw_instance:
            single_obj_data = {col_name: val for col_name, val in zip(table_schema, instance)}
            data.append(single_obj_data)
        return data
