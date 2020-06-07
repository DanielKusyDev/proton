import abc
import base64
import json
import os
import sqlite3
import unittest

from backend import crypto
from core import models
import utils
from core.controllers import Controller
from core.messages import Request, Response, ModelResponse


class CryptographyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.plain = "test123123"

    def test_key_generation(self):
        key1 = crypto.generate_key()
        key2 = crypto.generate_key()
        self.assertEqual(key1, key2)

    def test_encryption(self):
        cipher = crypto.encrypt(self.plain)
        self.assertNotEqual(self.plain, cipher)

        cipher2 = crypto.encrypt(self.plain)
        self.assertNotEqual(cipher, cipher2)

    def test_decryption(self):
        cipher = crypto.encrypt(self.plain)
        decrypted_cipher = crypto.decrypt(cipher)
        self.assertEqual(decrypted_cipher, self.plain)

        cipher2 = crypto.encrypt(self.plain)
        decrypted_cipher2 = crypto.decrypt(cipher2)
        self.assertEqual(decrypted_cipher, decrypted_cipher2)

    def test_comparison(self):
        cipher = crypto.encrypt(self.plain)
        self.assertTrue(crypto.compare(self.plain, cipher))


class BaseControllerTest(unittest.TestCase, metaclass=abc.ABCMeta):

    def setUp(self) -> None:
        self.db_name = "test.db"
        with open("requests.json", "r") as file:
            self.requests = json.loads(file.read())
        utils.create_db(self.db_name)
        self.user_model = models.User(self.db_name)
        self.auth_token_model = models.AuthToken(self.db_name)
        self.post_model = models.Post(self.db_name)

    def tearDown(self) -> None:
        os.remove(self.db_name)


class ModelTests(BaseControllerTest):
    def setUp(self) -> None:
        super(ModelTests, self).setUp()
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
        is_valid = self.auth_token_model.is_valid(user_id=auth_token[0])
        self.assertTrue(is_valid)

        with self.assertRaises(utils.ProtonError):
            is_valid = self.auth_token_model.is_valid(user_id=123123123)


class MessageTests(BaseControllerTest):

    def setUp(self) -> None:
        super(MessageTests, self).setUp()
        self.proper_request = """{"action":"register", "params":{"username":"...", "password":"..."}}"""
        self.message = Request(self.proper_request)

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


class ControllerTests(BaseControllerTest):

    @classmethod
    def setUpClass(cls) -> None:
        with open("assets/corgi.jpeg", "rb") as img:
            img_as_str = img.read()
            cls.image_str = base64.b64encode(img_as_str).decode()

    def setUp(self) -> None:
        super(ControllerTests, self).setUp()
        self.controller = Controller(self.db_name)

    def _login(self, request, create_user=True):
        if create_user:
            self._request_action(self.requests[0])
        token = self._request_action(self.requests[1])
        request["opts"]["auth_token"] = token.data[0]["token"]
        return request

    def _request_action(self, request):
        raw_request = json.dumps(request)
        message = Request(raw_request)
        result = getattr(self.controller, message.action)(message)
        return result

    def test_auth_validation(self):
        # try to access controller method with bound validation auth without providing any
        with self.assertRaises(PermissionError):
            self._request_action(self.requests[2])

    def test_register(self):
        request = self.requests[0]
        number_of_users = len(self.user_model.all())
        result = self._request_action(request)
        self.assertIsInstance(result, ModelResponse)
        self.assertGreater(len(result.data), number_of_users)
        self.assertEqual(request["params"]["username"], result.data[0]["username"])
        self.assertNotEqual(request["params"]["password"], result.data[0]["username"])

    def test_getting_token(self):
        user = self._request_action(self.requests[0])

        token = self.controller._get_token(user.data[0]["id"])
        self.assertIsInstance(token, tuple)

        self._request_action(self.requests[1])
        token = self.controller._get_token(user.data[0]["id"])
        self.assertIsInstance(token, tuple)

    def test_login(self):
        user = self._request_action(self.requests[0])
        request = self.requests[1].copy()
        # check valid login
        result = self._request_action(request)
        self.assertIsInstance(result, ModelResponse)
        is_valid = self.auth_token_model.is_valid(user_id=user.data[0]["id"])
        self.assertTrue(is_valid)

        # check invalid login data
        request["params"]["username"] = "wrongusername"
        result = self._request_action(request)
        self.assertFalse(result.status)

    def test_proper_logout(self):
        user = self._request_action(self.requests[0])
        token = self._request_action(self.requests[1])
        logout_request = self.requests[2].copy()
        logout_request["opts"]["auth_token"] = token.data[0]["token"]

        # check if token does not exist anymore
        self._request_action(logout_request)
        self.assertIsNone(self.auth_token_model.first(user_id=user.data[0]["id"]))
        # test attempt of providing invalid token and lack of token in opts field
        with self.assertRaises(PermissionError):
            self._request_action(logout_request)
            logout_request = self.requests[2].copy()
            del logout_request["opts"]["auth_token"]
            self._request_action(logout_request)

    def _create_post(self, create_user=True):
        request = self._login(self.requests[3], create_user)
        request["params"]["image"] = self.image_str
        response = self._request_action(request)
        return response

    def test_create_full_data_post(self):
        response = self._create_post()
        self.assertTrue(response.status)

    def test_getting_post_by_id(self):
        self._create_post()
        request = self._login(self.requests[5], False)
        response = self._request_action(request)
        self.assertIsInstance(response, ModelResponse)
        self.assertTrue(response.status)

    def test_getting_post(self):
        self._create_post(True)
        self._create_post(False)
        request = self._login(self.requests[4], False)
        response = self._request_action(request)
        self.assertIsInstance(response, ModelResponse)
        self.assertEqual(len(response.data), 2)

    def test_post_modify(self):
        post = self._create_post()
        request = self.requests[6]
        title = "NEWTITLE"
        request["params"]["title"] = title
        request = self._login(request, False)
        response = self._request_action(request)
        self.assertIsInstance(response, ModelResponse)
        self.assertNotEqual(post.data[0]["title"], response.data[0]["title"])
        self.assertEqual(title, response.data[0]["title"])

    def test_post_deletion(self):
        post = self._create_post()
        request = self._login(self.requests[7], False)
        response = self._request_action(request)
        self.assertIsInstance(response, Response)
        self.assertListEqual(self.post_model.all(), [])
