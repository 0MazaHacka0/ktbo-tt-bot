# -*- coding: utf-8 -*-
import sqlite3


class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def check_user(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM users WHERE user_id = '{}'".format(user_id)).fetchall()
            if len(result) == 0:
                return False
            else:
                return True

    def save_group(self, user_id, user_name, group):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM users WHERE user_id = '{}'".format(user_id)).fetchall()
            if len(result) == 0:
                self.cursor.execute(
                    "INSERT INTO users(user_id, user_name, group_name) VALUES ('{}', '{}', '{}')".format(
                        user_id, user_name, group))
            else:
                self.cursor.execute("UPDATE users SET group_name = '{}' WHERE user_id = '{}'".format(group, user_id))

    def get_group(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT group_name FROM users WHERE user_id = '{}'".format(user_id)).fetchall()
            if len(result) == 0:
                return False
            else:
                return result[0][0]

    def close(self):
        self.connection.close()
