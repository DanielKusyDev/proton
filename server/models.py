import sqlite3
import abc


class Model(abc.ABC):
    fields = []

    def __init__(self, db_name="sqlite3.db"):
        self.db_name = db_name
        self.table_name = self.__class__.__name__.lower()
        self.conn = sqlite3.connect(self.db_name)

    def __del__(self):
        self.conn.close()

    def get_fields(self):
        return ",".join(self.fields)

    def get_conditions(self, filters):
        conditions = [f"{key}=:{key}" for key, val in filters.items()]
        conditions = " and ".join(conditions)
        return conditions

    def execute_sql(self, sql, args=()) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        cursor.execute(sql, args)
        self.conn.commit()
        return cursor

    def create(self, *args):
        values_placeholder = ",".join(["?" for _ in range(len(self.fields))])
        sql = f"""INSERT INTO {self.table_name}({self.get_fields()}) VALUES({values_placeholder})"""
        self.execute_sql(sql, args)

    def all(self):
        sql = f"SELECT * FROM {self.table_name}"
        cursor = self.execute_sql(sql)
        users = cursor.fetchall()
        return users

    def filter(self, **kwargs):
        conditions = self.get_conditions(kwargs)
        sql = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        cursor = self.execute_sql(sql, kwargs)
        objects = cursor.fetchall()
        return objects

    def delete(self, **kwargs):
        conditions = self.get_conditions(kwargs)
        sql = f"DELETE FROM {self.table_name} WHERE {conditions}"
        self.execute_sql(sql, kwargs)
        return True


class Post(Model):
    fields = ["image", "description", "header"]


class User(Model):
    fields = ["username", "password"]


class AuthToken(Model):
    pass
