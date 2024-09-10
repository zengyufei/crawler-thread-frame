import logging

class 日志级别过滤器(logging.Filter):
    def __init__(self, 日志级别):
        super().__init__()
        self.日志级别 = 日志级别

    def filter(self, record):
        if self.日志级别 == 0:
            return True
        elif self.日志级别 == 1:
            return record.levelno >= logging.WARNING
        elif self.日志级别 == 2:
            return record.levelno >= logging.ERROR
        return False