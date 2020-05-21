import json
import os
import sqlite3
import unittest

import crypto
import models
import utils
from message import Message


class ProtonTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.db_name = "test.db"

    def tearDown(self) -> None:
        os.remove(self.db_name)


class ModelTests(ProtonTestCase):
    def setUp(self) -> None:
        utils.create_db(self.db_name)
        self.user_model = models.User(self.db_name)
        self.auth_token_model = models.AuthToken(self.db_name)
        self.post_model = models.Post(self.db_name)
        self.user_data = {
            "username": "test_username",
            "password": "test_pass"
        }

    def test_user_creation(self):
        users_counter = len(self.user_model.all())
        user = self.user_model.create(**self.user_data)
        self.assertIsInstance(user, tuple)
        self.assertEqual(self.user_data["username"], user[1])
        self.assertTrue(crypto.compare(self.user_data["password"], user[2]))
        self.assertGreater(len(self.user_model.all()), users_counter)

    def test_user_deletion(self):
        users_counter = len(self.user_model.all())
        user = self.user_model.create(username="test123123", password="test53525")
        self.user_model.delete(id=user[0])
        self.assertEqual(len(self.user_model.all()), users_counter)

    def test_user_update(self):
        user = self.user_model.create(**self.user_data)
        new_username = "newusername123123"
        updated_user = self.user_model.update(data={"username": new_username}, where={"id": user[0]})
        self.assertEqual(new_username, updated_user[1])
        with self.assertRaises(sqlite3.OperationalError):
            updated_user = self.user_model.update(data={}, where={"id": user[0]})

    def test_select(self):
        self.assertListEqual(self.user_model.all(), [])
        user = self.user_model.create(**self.user_data)
        self.assertEqual(len(self.user_model.all()), 1)
        self.assertEqual(user[0], self.user_model.first(id=user[0])[0])
        self.assertEqual(user[0], self.user_model.first(id=user[0])[0])
        self.assertListEqual(self.user_model.filter(username="wrongusernameforsure", password="wrongpass"), [])
        with self.assertRaises(sqlite3.OperationalError):
            self.user_model.filter(x="d")

    def test_auth_token_creation(self):
        user = self.user_model.create(**self.user_data)
        auth_token = self.auth_token_model.create(user_id=user[0])
        self.assertEqual(user[0], auth_token[1])
        self.assertTrue(self.auth_token_model.is_valid(auth_token[0]))


class MessageTests(unittest.TestCase):

    def setUp(self) -> None:
        self.proper_request = """{"action":"register", "params":{"username":"...", "password":"..."}}"""
        self.message = Message(self.proper_request)

    def test_deserialization(self):
        request = """{
            "action": "",
            """
        self.message.json_string = request
        with self.assertRaises(utils.ProtonError):
            self.message.deserialize_json()

    def test_getting_action(self):
        self.message.obj["action"] = "nonexistingactionfortests"
        with self.assertRaises(AssertionError):
            self.message.get_action()

    def test_required_params(self):
        # delete required parameter "username"
        del self.message.obj["params"]["username"]
        with self.assertRaises(AssertionError):
            self.message.get_params()

    def test_empty_params(self):
        # remove params from message object
        del self.message.obj["params"]
        with self.assertRaises(AssertionError):
            self.message.get_params()

        # remove params from required_params field of message
        self.message.required_action_params[self.message.action] = None
        self.assertIsNone(self.message.get_params())

    def test_opts(self):
        self.assertIsNone(self.message.get_opts())
        self.message.obj["opts"] = {"example": "test"}
        self.assertIsInstance(self.message.get_opts(), dict)


class ControllerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        with open("requests.json", "r") as file:
            cls.requests = json.loads(file.read())

    def test_register(self):
        request = self.requests[0]
        raw_request = json.dumps(request)
