from typing import List

import sqlalchemy
from db import models, settings
from db.settings import database as db
from fastapi import FastAPI

from . import crud
from .schemas import Scan

app = FastAPI()


@app.get("/scans/")
def read_scans():
    with db.session() as session:
        scans = crud.get_scans(db=session)
    return scans
