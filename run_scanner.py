import asyncio
import sys
from datetime import datetime

import sqlalchemy.orm as orm
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import db
import scanner
from db import models, settings
from scanner import scanner


def scan_and_commit():
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
    metadata = models.Base.metadata

    devices_gen = scanner.Devices()

    start_time = datetime.now()
    with Session(engine) as session:
        scan = models.Scan(start=start_time)
        session.add(scan)
        session.commit()

    while True:
        try:
            devices = devices_gen.next_chunk()
        except StopIteration as e:
            break

        with Session(engine) as session:
            scan = session.query(models.Scan).order_by(
                models.Scan.id.desc()).first()
            devices_bulk = [
                models.Device(
                    ip=device["ip"],
                    mac=device["mac"],
                    hostname=device["hostname"],
                    vendor=device["vendor"],
                    scan_id=scan.id,
                )
                for device in devices
            ]
            session.bulk_save_objects(devices_bulk)
            scan.finish = datetime.now()
            session.add(scan)
            session.commit()


if __name__ == "__main__":
    scan_and_commit()
