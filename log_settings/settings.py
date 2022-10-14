import logging


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
