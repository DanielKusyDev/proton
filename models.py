import datetime
import sqlite3
import abc
from time import strptime

import crypto
import settings
import utils


class Model(abc.ABC):
    fields = []

    def __init__(self, db_name="sqlite3.db"):
        self.table_name = self.__class__.__name__.lower()
        self.db_name = db_name
        self.conn = utils.create_conn(db_name=db_name)

    def __del__(self):
        self.conn.close()

    def get_fields(self):
        return ",".join(self.fields)

    def get_table_cols(self):
        sql = f"PRAGMA table_info({self.table_name})"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        raw_cols = cursor.fetchall()

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
        users = cursor.fetchall()
        return users

    def first(self, **kwargs):
        if kwargs:
            conditions = self.get_conditions(kwargs)
            sql = f"SELECT * FROM {self.table_name} WHERE {conditions} LIMIT 1"
        else:
            sql = f"SELECT * FROM {self.table_name} LIMIT 1"
        cursor = self.execute_sql(sql, kwargs)
        return cursor.fetchone()

    def last(self, **kwargs):
        if kwargs:
            conditions = self.get_conditions(kwargs)
            sql = f"SELECT * FROM {self.table_name} WHERE {conditions} ORDER BY id DESC LIMIT 1"
        else:
            sql = f"SELECT * FROM {self.table_name} ORDER BY id DESC LIMIT 1"
        cursor = self.execute_sql(sql, kwargs)
        return cursor.fetchone()

    def filter(self, **kwargs):
        conditions = self.get_conditions(kwargs)
        sql = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        cursor = self.execute_sql(sql, kwargs)
        objects = cursor.fetchall()
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

    def create(self, **kwargs):
        kwargs["password"] = crypto.encrypt(kwargs.get("password"))
        return super(User, self).create(**kwargs)


class AuthToken(Model):
    fields = ["token", "user_id", "expires"]

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
