import asyncio
import datetime
import logging
import logging.config
import os
import time
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

import log_settings
import scanner
import scanner_run
from log_settings import settings

logging.config.dictConfig(settings.logger_config)
logger = logging.getLogger("scheduler")


def tick():
    logger.info(f"Scheduled scan started at {datetime.now()}")
    scanner_run.scan_and_commit(starter='scheduler')


if __name__ == "__main__":
    logger.info(f"Running scheduler script {datetime.now()}")
    now = datetime.now()
    local_now = now.astimezone()
    local_tz = local_now.tzinfo
    local_tzname = local_tz.tzname(local_now)
    scheduler = BlockingScheduler()
    scheduler.add_job(tick, "cron", minute="*/1")
    scheduler.start()
