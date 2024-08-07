`leitner-upatate` is a simple project around the leitner learning method used as a pretext to set up a python project

This program should help to learn english vocabulary

# how to use

- install `python3`
- in a terminal launch `cd src ; python3 main.py`

# how it works

- The program check for an existing database
- if not existing, the database is created from `englais_init.json`
- then the program ask 150 questions following the leitner algorithm (cf: https://en.wikipedia.org/wiki/Leitner_system)
- and update database with your answers

# how to develop/contrib

- in a virtual env:
  - to create the virtual env: `python3 -m venv --system-site-packages venv` (issue this command only once)
  - to activate the virtual env: `. venv/bin/activate`
- install dev/test packages: `pip install --requirements requirements_dev.txt`
- place yourself in `src` directory (`cd src`)
- before commit check the following
  - format the source code: `ruff format .`
  - lint the source code: `ruff check .`
  - launch tests: `python3 -m pytest tests.py`
  - write new tests for new code ...
