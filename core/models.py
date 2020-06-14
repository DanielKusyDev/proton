import base64
import datetime
import os
import sqlite3
import abc
from time import strptime
from uuid import uuid4

from backend import crypto
import settings
import utils


class Model(abc.ABC):
    fields = []
    write_only = []

    def __init__(self, db_name=settings.DATABASE):
        self.table_name = self.__class__.__name__.lower()
        self.conn = utils.create_conn(db_name=db_name)

    def __del__(self):
        self.conn.close()

    def fetch(self, cursor, many=True):
        results = cursor.fetchall() if many else cursor.fetchone()
        return results

    def get_fields(self):
        return ",".join(self.fields)

    def get_table_cols(self):
        sql = f"PRAGMA table_info({self.table_name})"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        raw_cols = self.fetch(cursor, True)

        def map_col_type(col):
            c_type = col[2].lower()
            if "integer" in c_type:
                return c_type
            elif "char" in c_type:
                return str
            elif "datetime" in c_type:
                return datetime.timedelta

        cols = {col[1]: map_col_type(col) for col in raw_cols}
        return cols

    def get_conditions(self, filters):
        conditions = [f"{key}=:{key}" for key, val in filters.items()]
        conditions = f" and ".join(conditions)
        return conditions

    def execute_sql(self, sql, params=()) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor

    def create(self, **kwargs):
        placeholder = ",".join("?" * len(self.fields))
        params = [kwargs[field] for field in self.fields]
        sql = f"""INSERT INTO {self.table_name}({self.get_fields()}) VALUES({placeholder})"""
        self.execute_sql(sql, params)
        return self.last()

    def all(self):
        sql = f"SELECT * FROM {self.table_name}"
        cursor = self.execute_sql(sql)
        users = self.fetch(cursor)
        return users

    def first(self, **kwargs):
        if kwargs:
            conditions = self.get_conditions(kwargs)
            sql = f"SELECT * FROM {self.table_name} WHERE {conditions} LIMIT 1"
        else:
            sql = f"SELECT * FROM {self.table_name} LIMIT 1"
        cursor = self.execute_sql(sql, kwargs)
        return self.fetch(cursor, False)

    def last(self, **kwargs):
        if kwargs:
            conditions = self.get_conditions(kwargs)
            sql = f"SELECT * FROM {self.table_name} WHERE {conditions} ORDER BY id DESC LIMIT 1"
        else:
            sql = f"SELECT * FROM {self.table_name} ORDER BY id DESC LIMIT 1"
        cursor = self.execute_sql(sql, kwargs)
        return self.fetch(cursor, False)

    def filter(self, **kwargs):
        conditions = self.get_conditions(kwargs)
        sql = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        cursor = self.execute_sql(sql, kwargs)
        objects = self.fetch(cursor, True)
        return objects

    def update(self, data: dict, where: dict):
        data_placeholder = " = ?, ".join(data.keys()) + " = ?"
        where_placeholder = " = ?, ".join(where.keys()) + " = ?"
        sql = f"UPDATE {self.table_name} SET {data_placeholder} WHERE {where_placeholder}"
        params = list(data.values()) + list(where.values())
        cursor = self.execute_sql(sql, params)
        return self.first(**data)

    def delete(self, **kwargs):
        obj = self.first(**kwargs)
        conditions = self.get_conditions(kwargs)
        sql = f"DELETE FROM {self.table_name} WHERE {conditions}"
        self.execute_sql(sql, kwargs)
        return obj


class Post(Model):
    fields = ["image", "content", "title", "user_id"]


class User(Model):
    fields = ["username", "password"]
    write_only = ["password"]

    def create(self, **kwargs):
        kwargs["password"] = crypto.encrypt(kwargs.get("password"))
        return super(User, self).create(**kwargs)


class AuthToken(Model):
    fields = ["token", "user_id", "expires"]
    write_only = ["token", "expires"]

    def get_fresh_expiration(self):
        expires = datetime.datetime.now() + datetime.timedelta(**settings.EXPIRATION)
        return expires

    def create(self, user_id):
        token = utils.generate_token()
        expires = self.get_fresh_expiration()
        return super(AuthToken, self).create(token=token, user_id=user_id, expires=expires)

    def is_valid(self, **kwargs):
        token = self.first(**kwargs)
        if token is None:
            raise utils.ProtonError("Not found.")
        expires_date = strptime(token[3], "%Y-%m-%d %H:%M:%S.%f")
        expires = datetime.datetime(year=expires_date.tm_year, month=expires_date.tm_mon, day=expires_date.tm_mday,
                                    hour=expires_date.tm_hour, minute=expires_date.tm_min, second=expires_date.tm_sec)
        return datetime.datetime.now() < expires
