from os import environ
from pathlib import Path

from dotenv import load_dotenv

from .database import Database

load_dotenv()

DB_NAME = environ.get("DB_NAME")
DB_PASS = environ.get("DB_PASS")
DB_USER = environ.get("DB_USER")
DB_HOST = environ.get("DB_HOST")
DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"
)

database = Database(db_url=DATABASE_URL)
