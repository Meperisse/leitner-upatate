import json
import os
import sqlite3


## to be moved in config file
DATABASE_FILE = 'david.db'
JSON_FILENAME = 'anglais_init.json'
## end
## sql default
SQL_CREATE = """
CREATE TABLE anglais_v2(category, last_update, question, response, example) 
"""
SQL_IS_EMPTY = """
SELECT count(*) from anglais_v2
"""
SQL_INSERT_MANY = """
INSERT INTO anglais_v2('category', 'last_update', 'question', 'response', 'example') VALUES (?, ?, ?, ?, ?)
"""
## end

class Database:
    conn = None
    cur = None
    json_filename = None
    database_filename = None

    def __init__(self, database_filename, json_filename=None):
        self.database_filename = database_filename
        self.json_filename = json_filename or JSON_FILENAME

    def ready(self):
        db_exists = self.open_database()
        if not db_exists:
            self.create_database()
        if not db_exists or self.database_is_empty():
            self.fill_database()

    def create_database(self):
        self.cur.execute(SQL_CREATE)

    def database_file_exists(self):
        "check if sqlite3 file exists"
        try:
            os.stat(self.database_filename)
        except FileNotFoundError:
            return False
        return True
    
    def database_is_empty(self):
        self.cur.execute(SQL_IS_EMPTY)
        row = self.cur.fetchone()
        return row[0] == 0
    
    def fill_database(self):
        with open(self.json_filename) as json_file:
            json_data = json.load(json_file)
        init_data = [
            (
                0,
                None,
                english_word,
                value['translation'],
                json.dumps(value['examples'])
            )
            for english_word, value in json_data.items()
        ]
        self.cur.executemany(SQL_INSERT_MANY, init_data)

    
    def open_database(self):
        db_exists = self.database_file_exists()
        self.conn = sqlite3.connect(self.database_filename)
        self.cur = self.conn.cursor()
        return db_exists

    def close_database(self):
        if self.cur is not None:
            self.cur.close()
        self.cur = None
        if self.conn is not None:
            self.conn.close()
        self.conn = None

    def remove_database(self):
        self.close_database()
        if self.database_file_exists():
            os.remove(self.database_filename)

    def reset_database(self):
        self.remove_database()
        self.open_database()
        self.create_database()
        self.fill_database()


def main_loop(my_db):
    pass


def main():
    my_db = Database(DATABASE_FILE)
    my_db.ready()
    main_loop(my_db)
    my_db.close_database()


if __name__ == '__main__':
    main()
