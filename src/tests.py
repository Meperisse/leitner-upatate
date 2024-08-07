import pytest
from leitner_sqlite import Database, MyTable, MyRow


# This fixture simplify create/destroy test database
@pytest.fixture(scope="class")
def db_test():
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
        row = MyRow(rows[0])
        assert row.category == 2


def test_ma_fixture(db_test):
    my_table = MyTable(db_test)
    rows = my_table.get_category(1)
    assert len(rows) == 1


def test_ma_2_fixture(db_test):
    assert True


class TestDbTest:
    def test_yolo(self, db_test):
        assert True

    def test_yolo2(self, db_test):
        assert True
