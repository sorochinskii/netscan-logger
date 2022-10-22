from db import models
from sqlalchemy.orm import Session

from . import schemas


def get_scans(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Scan).offset(skip).limit(limit).all()
