from os import environ
from pathlib import Path

import databases
from dotenv import load_dotenv

load_dotenv()

DB_NAME = environ.get("DB_NAME")
DB_PASS = environ.get("DB_PASS")
DB_USER = environ.get("DB_USER")
DB_HOST = environ.get("DB_HOST")
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"
)
database = databases.Database(SQLALCHEMY_DATABASE_URL)
