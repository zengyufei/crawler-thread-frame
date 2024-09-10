from abc import ABC, abstractmethod
from typing import Any
import logging
from 线程池框架.日志过滤器 import 日志级别过滤器

class 逻辑基类(ABC):
    模块名: str
    log: logging.Logger = None

    @classmethod
    def 初始化日志器(cls, 日志级别: int):
        cls.log = logging.getLogger(cls.__name__)
        cls.log.addFilter(日志级别过滤器(日志级别))

    @classmethod
    @abstractmethod
    def 运行开始(cls, 参数: Any) -> Any:
        pass

    @classmethod
    @abstractmethod
    def 运行结束(cls, 参数: Any) -> Any:
        pass

    @classmethod
    @abstractmethod
    def 循环任务(cls, 参数: Any) -> Any:
        pass

    @classmethod
    @abstractmethod
    def 跳出循环条件(cls, 参数: Any) -> bool:
        pass