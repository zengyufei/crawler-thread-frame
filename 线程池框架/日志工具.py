import logging
import threading


class 日志:
    traceId线程类 = threading.local()

    @staticmethod
    def getTraceId():
        return getattr(日志.traceId线程类, 'trace_id', 'no')

    @staticmethod
    def setTraceId(trace_id):
        日志.traceId线程类.trace_id = trace_id

    class TraceIdFormatter(logging.Formatter):
        def format(self, record):
            # 在日志记录的格式中插入 traceId
            record.trace_id = 日志.getTraceId()
            return super().format(record)

    def __init__(self, name='my_logger', level=0):
        self.logger = logging.getLogger(name)
        if level == 0:
            self.logger.setLevel(logging.INFO)
        elif level == 1:
            self.logger.setLevel(logging.WARNING)
        elif level == 2:
            self.logger.setLevel(logging.ERROR)

        # 创建控制台处理器
        self.控制台处理器 = logging.StreamHandler()

        str = '[%(name)s][PID %(process)d][TID %(thread)d][%(levelname)s][%(trace_id)s] %(message)s'
        # 创建自定义格式化器，并设置格式化模板
        self.formatter = 日志.TraceIdFormatter(str)
        self.控制台处理器.setFormatter(self.formatter)

        # 将处理器添加到 logger
        self.logger.addHandler(self.控制台处理器)

    def 设置日志名(self, name):
        self.logger.name = name
        
    def 设置日志级别(self, level: int):
        if level == 0:
            self.logger.setLevel(logging.INFO)
        elif level == 1:
            self.logger.setLevel(logging.WARNING)
        elif level == 2:
            self.logger.setLevel(logging.ERROR)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)

#
# # 示例使用
# if __name__ == '__main__':
#     # 创建日志记录器实例
#     logger = TraceIdLogger('日志过滤器', 0)
#
#     # 设置 traceId
#     TraceIdLogger.set_trace_id('12345')
#     logger.debug('This is a debug message with traceId.')
#     logger.info('This is an info message with traceId.')
#
#     # 更改 traceId
#     TraceIdLogger.set_trace_id('67890')
#     logger.warning('This is a warning message with a different traceId.')
