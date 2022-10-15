import logging
import os
import sys

from dotenv import dotenv_values, find_dotenv, load_dotenv

load_dotenv(find_dotenv())
LEVEL = os.environ.get("SCAN_LOGLEVEL", "WARNING")

logger_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "std_format": {
            "format": "{asctime} - {levelname} - {name} - {message}",
            "style": "{",
        }
    },
    "handlers": {
        "file_handler": {
            "class": "logging.FileHandler",
            "level": LEVEL,
            "formatter": "std_format",
            "filename": "log.log",
        },
    },
    "loggers": {
        "scanner": {
            "level": LEVEL,
            "handlers": [
                "file_handler",
            ],
        },
        "runner": {
            "level": LEVEL,
            "handlers": [
                "file_handler",
            ],
        },
        "scheduler": {
            "level": "INFO",
            "handlers": [
                "file_handler",
            ],
        },
    },
}


class LoggingContext:
    def __init__(self, logger, level=None, handler=None, close=True, fmt=None):
        self.logger = logger
        self.level = level
        self.handler = handler
        self.fmt = fmt
        self.close = close

    def __enter__(self):
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            self.logger.addHandler(self.handler)
        if self.fmt:
            self.handler.setFormatter(self.fmt)

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.handler:
            self.logger.removeHandler(self.handler)
        if self.handler and self.close:
            self.handler.close()
