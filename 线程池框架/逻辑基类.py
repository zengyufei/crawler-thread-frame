from abc import ABC, abstractmethod
from typing import Any


class 逻辑基类(ABC):
    模块名: str

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