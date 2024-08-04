from leitner_sqlite import Database, MyTable, MyRow
import logging


logger = logging.getLogger(__name__)


## to be moved in config file
LOGLEVEL = logging.INFO
DATABASE_FILENAME = "david.db"
JSON_FILENAME = "data/anglais_init.json"
## end


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
    my_db = Database(DATABASE_FILENAME, JSON_FILENAME)
    my_db.ready()
    try:
        main_loop(my_db)
    except Exception as err:
        raise err
    finally:
        my_db.close_database()


if __name__ == "__main__":
    main()
