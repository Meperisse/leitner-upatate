import datetime
import json
import logging
import os
import sqlite3


logger = logging.getLogger(__name__)


## to be moved in config file
LOGLEVEL = logging.INFO
DATABASE_FILENAME = 'david.db'
JSON_FILENAME = 'data/anglais_init.json'
## end
## sql default
SQL_CREATE = """
CREATE TABLE IF NOT EXISTS anglais_v2(
    category INTEGER NOT NULL DEFAULT 0,
    last_update INTEGER DEFAULT NULL,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    example TEXT NOT NULL
)
"""
SQL_IS_EMPTY = """
SELECT count(*) FROM anglais_v2
"""
SQL_INSERT_MANY = """
INSERT INTO anglais_v2('question', 'response', 'example') VALUES (?, ?, ?)
"""
SQL_CATEGORY = """
SELECT * FROM anglais_v2
WHERE category = {cat}
ORDER BY last_update ASC
LIMIT {limit}
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
        logger.info("create database")
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
        logger.info("attempt to fill database")
        with open(self.json_filename) as json_file:
            json_data = json.load(json_file)
        init_data = [
            (
                english_word,
                value['translation'],
                json.dumps(value['examples'])
            )
            for english_word, value in json_data.items()
        ]
        self.cur.executemany(SQL_INSERT_MANY, init_data)
        self.conn.commit()
    
    def open_database(self):
        logger.info("open database")
        db_exists = self.database_file_exists()
        self.conn = sqlite3.connect(self.database_filename)
        self.cur = self.conn.cursor()
        return db_exists

    def close_database(self):
        logger.info("close database")
        if self.cur is not None:
            self.cur.close()
        self.cur = None
        if self.conn is not None:
            self.conn.close()
        self.conn = None

    def remove_database(self):
        logger.info("remove database")
        self.close_database()
        if self.database_file_exists():
            os.remove(self.database_filename)

    def reset_database(self):
        logger.info("reset database")
        self.remove_database()
        self.open_database()
        self.create_database()
        self.fill_database()

class MyTable:
    def __init__(self, my_db):
        self.db = my_db

    def get_category(self, cat, limit=30):
        self.db.cur.execute(SQL_CATEGORY.format(cat=cat, limit=limit))
        return self.db.cur.fetchall()


class MyRow:
    def __init__(self, row):
        (
            self.category,
            self.last_update,
            self.question,
            self.response,
            dict_example
        ) = row
        self.dict_example = json.loads(dict_example)

    def __repr__(self):
        return f"<datarow: {str(self)}>"

    def __str__(self):
        return f"{self.category}|{self.age_from_now()}|{self.question}"

    def example(self, lang, num):
        res = self.dict_example.get(lang)
        if res is None:
            return None
        return res[num % 3]

    def age(self, date_time):
        if self.last_update is None:
            return None
        return date_time - self.last_update

    def age_from_now(self):
        return self.age(datetime.datetime.now())


def main_loop(my_db):
    # recuperer les fiches (critere de categorie, d'age et de nombre)
    # pour chaque fiche, poser la question
    # mettre a jour la fiche en fonction de la reponse
    my_table = MyTable(my_db)
    rows = my_table.get_category(0)
    data = MyRow(rows[0])
    breakpoint()


def main():
    logging.basicConfig(level=LOGLEVEL)
    my_db = Database(DATABASE_FILENAME)
    my_db.ready()
    main_loop(my_db)
    my_db.close_database()


if __name__ == '__main__':
    main()
