from dataclasses import dataclass, field
from typing import Any
import queue
import threading

@dataclass
class 共享参数:
    """共享参数类"""
    值: Any
    下载存储路径: str = r'd:\gongxiang\电影'
    页面队列: queue.Queue = field(default_factory=queue.Queue)
    页面字典: dict = field(default_factory=dict)
    页面锁: threading.Lock = field(default_factory=threading.Lock)
    章节队列: queue.Queue = field(default_factory=queue.Queue)
    章节字典: dict = field(default_factory=dict)
    章节锁: threading.Lock = field(default_factory=threading.Lock)
    日志级别: int = 0  # 新增日志级别属性，默认为0
