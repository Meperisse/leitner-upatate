from leitner_sqlite import Database, MyTable
import random
import logging


logger = logging.getLogger(__name__)


## to be moved in config file
LOGLEVEL = logging.INFO
DATABASE_FILENAME = "david.db"
JSON_FILENAME = "data/anglais_init.json"
CATEGORY_SCORE = [
    # age in day, score coefficient
    (1, 60),
    (2, 40),
    (4, 28),
    (8, 20),
    (16, 15),
    (32, 12),
    (64, 10),
]
OVERWRITE = False
TOTAL_WORD = 100
REQ2_PCENT = 80
REQ3_PCENT = 4
HIDE_INPUT_MESSAGE = True
## end


def update_i_know(row, recto, idx_example, idx):
    print("\n\n")
    if row.category == 0:
        row.category = 2
    elif row.category != 8:
        row.category += 1
    row.last_update = MyTable.get_daystamp_from_date()
    row.save()
    return 1, recto


def update_i_dont_know(row, recto, idx_example, idx):
    print("\n\n")
    row.category = 1
    row.last_update = MyTable.get_daystamp_from_date()
    row.save()
    return 1, recto


def show_translation(row, recto, idx_example, idx):
    recto ^= True
    display(row, recto, idx_example, idx)
    return 0, recto


def delete_card(row, recto, idx_example, idx):
    resp=input("Are you sure to delete it? (y/n) : ")
    if resp =="y":
        row.delete()
        return 1, recto
    else:
        return 0,recto


def exit_game(row, recto, idx_example, idx):
    exit()


MTX_FUNC = {
    "y": update_i_know,
    "n": update_i_dont_know,
    "s": show_translation,
    "d": delete_card,
    "q": exit_game,
}


def display(row, recto, idx_example, idx):
    if recto:
        print(f"\n{idx+1}) Question: {row.question}")
        print(f"Example: {row.dict_example['fr'][idx_example]}")
    else:
        print(f"\nResponse: {row.response}")
        print(f"Example: {row.dict_example['en'][idx_example]}")


def main_loop(my_db):
    # recuperer les fiches (critere de categorie, d'age et de nombre)
    # pour chaque fiche, poser la question
    # mettre a jour la fiche en fonction de la reponse
    if HIDE_INPUT_MESSAGE:
        input_message="y,n,s,d,q : "
    else:
        input_message = "Yes, No, Show, Delete, Quit (y,n,s,d, q): "
    my_table = MyTable(my_db)
    rows = my_table.get_all_selection()
    idx = 0
    increment = 1
    len_rows = len(rows)
    while idx < len_rows:
        row = rows[idx]
        if increment == 1:
            recto = True
            idx_example = random.randint(0, row.len_example - 1)
            display(row, recto, idx_example, idx)
        res = input(input_message).strip().lower()
        increment, recto = MTX_FUNC.get(res, lambda x, y, z, t: (0, y))(
            row, recto, idx_example, idx
        )
        idx += increment
    #Affiche le nombre d'éléments par liste
    for i in range(1,9):
        print("Il y a "+str(MyTable(my_db).count_category(i))+" éléments dans la table "+str(i))


def main():
    logging.basicConfig(level=LOGLEVEL)
    my_db = Database(
        DATABASE_FILENAME,
        JSON_FILENAME,
        CATEGORY_SCORE,
        OVERWRITE,
        TOTAL_WORD,
        REQ2_PCENT,
        REQ3_PCENT,
    )
    my_db.ready()
    try:
        main_loop(my_db)
    except Exception as err:
        raise err
    finally:
        my_db.close_database()


if __name__ == "__main__":
    main()
