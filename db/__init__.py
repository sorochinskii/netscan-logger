from os import environ

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

DB_NAME = environ.get("DB_NAME")
DB_PASS = environ.get("DB_PASS")
DB_USER = environ.get("DB_USER")
DB_HOST = environ.get("DB_HOST")
