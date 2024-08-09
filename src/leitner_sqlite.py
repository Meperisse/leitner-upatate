import datetime
import json
import logging
import os
import random
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
SQL_SEL_SCORE = """
SELECT
    anglais_v2.id,
    anglais_v2.category,
    anglais_v2.last_update,
    anglais_v2.question,
    anglais_v2.response,
    anglais_v2.example,
    CASE
       WHEN ({day_from_epoch} - anglais_v2.last_update - score.age) < 0 THEN 0
       ELSE ({day_from_epoch} - anglais_v2.last_update - score.age + 1) * score.coef
    END computed_score

FROM anglais_v2 INNER JOIN score ON anglais_v2.category = score.id
WHERE category IN (1,2,3,4,5,6,7)
ORDER BY computed_score DESC
LIMIT {limit}
"""
SQL_SEL_KNOWN_WORDS = """
SELECT
    id,
    category,
    last_update,
    question,
    response,
    example
FROM anglais_v2
WHERE category = 8
ORDER BY last_update DESC
LIMIT {limit}
"""
SQL_SEL_NEW_WORDS = """
SELECT
    anglais_v2.id,
    anglais_v2.category,
    anglais_v2.last_update,
    anglais_v2.question,
    anglais_v2.response,
    anglais_v2.example
FROM anglais_v2
WHERE category = 0
ORDER BY random()
LIMIT {limit}
"""
SQL_UPDATE_ENTRY = """
UPDATE anglais_v2 SET
     category = ?,
     last_update = ?,
     question = ?,
     response = ?,
     example = ?
WHERE
     id = ?
"""
SQL_DELETE_ENTRY = """
DELETE FROM anglais_v2
WHERE id = {id}
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
        total_word=150,
        req2_pcent=70,
        req3_pcent=4,
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
        self.total_word = total_word
        self.req2_limit = int(total_word * (req2_pcent / 100))
        self.req3_limit = int(total_word * (req3_pcent / 100))

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
                value["translation"],
                english_word,
                json.dumps(value.get("examples", {})),
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
        return [MyRow(self.db, elm) for elm in self.db.cur.fetchall()]

    @staticmethod
    def get_daystamp_from_date(date=None):
        """staticmethod permet de faire une methode sans 'self' donc
        cette methode peut donc etre utilise depuis une classe ou
        une instance indifferemment
        """
        if date is None:
            date = datetime.datetime.now()
        elif isinstance(date, datetime.date):
            date = datetime.datetime(date.year, date.month, date.day)
        elif isinstance(date, str):
            date = datetime.datetime.fromisoformat(date)
        if not isinstance(date, datetime.datetime):
            raise ValueError(
                "Date format error, must be None, Date, Datetime or string"
            )
        day_from_epoch = int(date.timestamp() // 86400)  # day in seconds
        return day_from_epoch

    def get_selection_with_score(self, date=None):
        day_from_epoch = self.get_daystamp_from_date(date)
        self.db.cur.execute(
            SQL_SEL_SCORE.format(
                day_from_epoch=day_from_epoch, limit=self.db.req2_limit
            )
        )
        return [MyRow(self.db, elm) for elm in self.db.cur.fetchall()]

    def get_selection_known_words(self):
        self.db.cur.execute(SQL_SEL_KNOWN_WORDS.format(limit=self.db.req3_limit))
        return [MyRow(self.db, elm) for elm in self.db.cur.fetchall()]

    def get_selection_new_words(self, limit):
        self.db.cur.execute(SQL_SEL_NEW_WORDS.format(limit=limit))
        return [MyRow(self.db, elm) for elm in self.db.cur.fetchall()]

    def get_all_selection(self):
        req2 = self.get_selection_with_score()
        req3 = self.get_selection_known_words()
        limit_req1 = self.db.total_word - (len(req2) + len(req3))
        req1 = self.get_selection_new_words(limit_req1)
        res = req1 + req2 + req3
        random.shuffle(res)
        return res


class MyRow:
    id = None
    category = 0
    last_update = None
    question = ""
    response = ""
    dict_example = None

    def __init__(self, my_db, row=None):
        self.db = my_db
        if row is None:
            self.dict_example = {}
            return
        rowlen = len(row)
        if rowlen == 6:
            (
                self.id,
                self.category,
                self.last_update,
                self.question,
                self.response,
                self.json_example,
            ) = row
            # add a dummy placeholder in order to
            # return the same type of object
            self.computed_score = None
        elif rowlen == 7:
            (
                self.id,
                self.category,
                self.last_update,
                self.question,
                self.response,
                self.json_example,
                self.computed_score,
            ) = row
        else:
            self.json_example = "{}"
        self.dict_example = json.loads(self.json_example)
        self.len_example = len(self.dict_example.get("fr", ""))

    def save(self):
        data = [
            self.category,
            self.last_update,
            self.question,
            self.response,
            self.json_example,
        ]
        if self.id is None:
            # insert
            save_request = SQL_INSERT_MANY
        else:
            # update
            data.append(self.id)
            save_request = SQL_UPDATE_ENTRY
        self.db.cur.executemany(save_request, [data])
        self.db.conn.commit()

    def delete(self):
        if self.id is not None:
            self.db.cur.execute(SQL_DELETE_ENTRY.format(id=self.id))

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
        "return age of last update in day"
        if self.last_update is None:
            return None
        daystamp = int(date_time.timestamp() // 86400)
        return daystamp - self.last_update

    def age_from_now(self):
        return self.age(datetime.datetime.now())
