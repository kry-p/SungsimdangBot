import sqlite3


class DBManager:
    def __init__(self):
        data = './common_data.db'

        database = sqlite3.connect(data)
        cursor = database.cursor()

