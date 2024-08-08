import datetime
import json
import logging
import os
import sqlite3


logger = logging.getLogger(__name__)


## sql default
SQL_CREATE = """
CREATE TABLE IF NOT EXISTS anglais_v2(
    id INTEGER NOT NULL PRIMARY KEY,
    category INTEGER NOT NULL DEFAULT 0,
    last_update INTEGER DEFAULT NULL,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    example TEXT NOT NULL
)
"""
SQL_CREATE_SCORE = """
CREATE TABLE IF NOT EXISTS score(
    id INTEGER NOT NULL,
    age INTEGER NOT NULL,
    coef INTEGER NOT NULL
)
"""
SQL_IS_EMPTY = """
SELECT count(*) FROM anglais_v2
"""
SQL_INSERT_MANY = """
INSERT INTO anglais_v2('category', 'last_update', 'question', 'response', 'example') VALUES (?, ?, ?, ?, ?)
"""
SQL_INSERT_SCORE_MANY = """
INSERT INTO score('id', 'age', 'coef') VALUES (?, ?, ?)
"""
SQL_ALL = """
SELECT id, category, last_update, question, response, example FROM anglais_v2
"""
SQL_CATEGORY = """
SELECT id, category, last_update, question, response, example FROM anglais_v2
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

    def __init__(
        self,
        database_filename,
        json_filename=None,
        category_score=None,
        overwrite=False,
    ):
        self.database_filename = database_filename
        self.json_filename = json_filename
        self.overwrite = overwrite
        if category_score is None:
            category_score = [(2**x, 2 ** (6 - x)) for x in range(7)]
        category_score = [(0, 0)] + category_score + [(0, 0)]
        self.category_score = [
            (idx, val[0], val[1]) for idx, val in enumerate(category_score)
        ]

    def ready(self):
        if self.overwrite:
            self.remove_database()
        db_exists = self.open_database()
        if not db_exists:
            self.create_database()
        if not db_exists or self.database_is_empty():
            self.fill_database()

    def create_database(self):
        logger.info("create database")
        self.cur.execute(SQL_CREATE)
        self.cur.execute(SQL_CREATE_SCORE)

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
        fif = datetime.datetime.fromisoformat
        init_data = [
            (
                value.get("category", 0),
                (fif(value.get("last_update")).timestamp() // 86400)
                if value.get("last_update")
                else None,
                english_word,
                value["translation"],
                json.dumps(value.get("examples", "")),
            )
            for english_word, value in json_data.items()
        ]
        self.cur.executemany(SQL_INSERT_MANY, init_data)
        self.cur.executemany(SQL_INSERT_SCORE_MANY, self.category_score)
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

    def all(self):
        self.db.cur.execute(SQL_ALL)
        return self.db.cur.fetchall()

    def get_category(self, cat, limit=30):
        self.db.cur.execute(SQL_CATEGORY.format(cat=cat, limit=limit))
        return self.db.cur.fetchall()


class MyRow:
    id = None
    category = 0
    last_update = None
    question = ""
    response = ""
    dict_example = None

    def __init__(self, row=None):
        if row is None:
            self.dict_example = {}
            return
        (
            self.id,
            self.category,
            self.last_update,
            self.question,
            self.response,
            dict_example,
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
