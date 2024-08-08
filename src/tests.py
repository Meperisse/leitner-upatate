import pytest
import datetime
from leitner_sqlite import Database, MyTable


# This fixture simplify create/destroy test database
@pytest.fixture(scope="class")
def db_test():
    """
    Create/destroy test database.
    The test database contains 9 elements one on each category (0 to 8) named after
    their category
    with 2024-03-06 as "today" each item in each category should trigger:
    item "category_7" last_update 2024-01-02 ; today - last_update = 64 days
    item "category_6" last_update 2024-02-03 ; today - last_update = 32 days
    etc.
    item "category_0" last_update null
    item "category_8" last_update 2024-01-01
    """
    print("__ init DB")
    my_db = Database("data_test/test.db", "data_test/test.json", overwrite=True)
    my_db.ready()
    yield my_db
    my_db.close_database()
    print("__ close DB")


# but before use this fixture, we should test that
# Database class works correctly ...
class TestDatabase:
    def test_empty_db(self):
        my_db = Database("data_test/test.db", "data_test/empty.json", overwrite=True)
        my_db.ready()
        assert my_db.database_is_empty()
        my_db.close_database()

    def test_simple_db(self):
        my_db = Database("data_test/test.db", "data_test/simple.json", overwrite=True)
        my_db.ready()
        assert not my_db.database_is_empty()
        my_db.cur.execute("UPDATE anglais_v2 SET category = 2")
        my_db.conn.commit()

    # check that db contain now a category = 2
    def test_remaining_db(self):
        my_db = Database("data_test/test.db", "data_test/simple.json", overwrite=False)
        my_db.ready()
        my_table = MyTable(my_db)
        rows = my_table.all()
        row = rows[0]
        assert row.category == 2


class TestMyTable:
    def test_get_daystamp_from_date_null(self):
        assert isinstance(MyTable.get_daystamp_from_date(None), int)

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (datetime.date(2024, 1, 1), 19722),
            (datetime.datetime(2024, 1, 1), 19722),
            ("2024-01-01", 19722),
        ],
    )
    def test_get_daystamp_from_date(self, test_input, expected):
        assert MyTable.get_daystamp_from_date(test_input) == expected

    @pytest.mark.parametrize(
        "date, expected_res",
        [
            ("2024-03-06", [64, 32, 16, 8, 4, 2, 1]),
            ("2024-03-07", [128, 64, 32, 16, 8, 4, 2]),
        ],
    )
    def test_get_selection_with_score(self, db_test, date, expected_res):
        my_table = MyTable(db_test)
        my_qs = my_table.get_selection_with_score(date=date)
        assert len(my_qs) == 7
        for row, res in zip(my_qs, expected_res):
            assert row.computed_score == res

    def test_get_selection_known_words(self, db_test):
        my_table = MyTable(db_test)
        my_qs = my_table.get_selection_known_words()
        assert len(my_qs) == 1
        assert my_qs[0].category == 8

    def test_get_selection_new_words(self, db_test):
        my_table = MyTable(db_test)
        my_qs = my_table.get_selection_new_words(150)
        assert len(my_qs) == 1
        assert my_qs[0].category == 0

    def test_get_all_selection(self, db_test):
        my_table = MyTable(db_test)
        my_qs = my_table.get_all_selection()
        assert len(my_qs) == 9
