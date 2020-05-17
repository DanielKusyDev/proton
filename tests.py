import os
import sqlite3
import unittest

import crypto
import models
import utils


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


class ControllerTests(unittest.TestCase):
    def test_register(self):
        pass