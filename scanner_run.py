import asyncio
import logging
import logging.config
import sys
import typing
from datetime import datetime

import sqlalchemy.orm as orm

import scanner
from db import models
from db.settings import database as db
from log_settings.settings import logger_config
from scanner import scanner

logging.config.dictConfig(logger_config)
logger = logging.getLogger("scanner")


def scan_and_commit(starter: str = "manual"):
    """
    Скрипт запуска сканирования и записи результатов в БД.
    В базу устройства записываются порциями.
    """
    devices_gen = scanner.Devices()

    start_time = datetime.now()
    logger.debug(f"Scan started at {start_time}")
    with db.session() as session:
        scan = models.Scan(start=start_time, starter=starter)
        session.add(scan)
        session.commit()

    while True:
        try:
            devices = devices_gen.next_chunk()
        except StopIteration as e:
            break

        with db.session() as session:
            scan = (
                session.query(models.Scan)
                .order_by(models.Scan.id.desc())
                .first()
            )
            scan_id = scan.id
            logger.debug(f"Scan id = {scan_id}")
            devices_bulk = [
                models.Device(
                    ip=device["ip"],
                    mac=device["mac"],
                    hostname=device["hostname"],
                    vendor=device["vendor"],
                    scan_id=scan_id,
                )
                for device in devices
            ]
            session.bulk_save_objects(devices_bulk)
            scan.finish = datetime.now()
            session.add(scan)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                logger.exception()
    logger.debug(f"Scan finished at {datetime.now()}")


if __name__ == "__main__":
    scan_and_commit()
