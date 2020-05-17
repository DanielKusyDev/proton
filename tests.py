import unittest

import crypto
import models

class ProtonTestCase(unittest.TestCase):
    def setUpClass(cls) -> None:
        db_name = "test_db.db"


class ModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user_model = models.User()
        self.auth_token_model = models.AuthToken()
        self.post_model = models.Post()
        self.user_data = {
            "username": "test_username",
            "password": "test_pass"
        }

    def test_user_creation(self):
        user = self.user_model.create(**self.user_data)
        self.assertIsInstance(user, tuple)
        self.assertEquals(self.user_data["username"], user[1])
        self.assertTrue(crypto.compare(self.user_data["password"], user[2]))


class ControllerTests(unittest.TestCase):
    # def test_user_creation(self):
    pass
