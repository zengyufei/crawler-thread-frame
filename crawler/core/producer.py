#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生产者模块：负责生成抓取任务
"""

import queue
import time
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

class BaseProducer(ABC):
    """生产者基类"""

    def __init__(self):
        """初始化生产者"""
        self.task_queue = None
        self.should_stop = False

    def set_queue(self, task_queue: queue.Queue):
        """
        设置任务队列

        参数:
            task_queue: 任务队列
        """
        self.task_queue = task_queue

    def publish(self, task: Any):
        """
        将任务发布到队列

        参数:
            task: 任务数据
        """
        if self.task_queue is None:
            raise RuntimeError("任务队列未设置")

        # 如果队列已满，则等待
        while True:
            try:
                self.task_queue.put(task, block=True, timeout=1)
                break
            except queue.Full:
                # 队列已满，等待一会再试
                time.sleep(0.1)
                # 如果已经请求关闭，则停止发布
                if self.should_stop:
                    break

    def shutdown_now(self):
        """请求关闭生产者"""
        self.should_stop = True

    def should_shutdown(self) -> bool:
        """判断是否应该关闭"""
        return self.should_stop

    @abstractmethod
    def produce(self):
        """
        生产任务的抽象方法，子类必须实现
        """
        pass


class UrlProducer(BaseProducer):
    """URL生产者，负责生成URL抓取任务"""

    def __init__(self, urls: List[str], interval: float = 0):
        """
        初始化URL生产者

        参数:
            urls: URL列表
            interval: 生产间隔时间（秒），默认为0（不等待）
        """
        super().__init__()
        self.urls = list(urls)  # 创建副本
        self.interval = interval
        self.total_count = len(urls)
        self.published_count = 0

    def produce(self):
        """生产URL任务"""
        if not self.urls:
            # URL列表为空，生产工作完成
            self.shutdown_now()
            return

        # 取出一个URL
        url = self.urls.pop(0)

        # 构建任务
        task = {
            'url': url,
            'timestamp': time.time(),
            'retry': 0  # 重试次数
        }

        # 发布任务
        self.publish(task)
        self.published_count += 1

        # 如果设置了间隔时间，则等待
        if self.interval > 0:
            time.sleep(self.interval)

    def add_urls(self, urls: List[str]):
        """
        添加更多URL到队列

        参数:
            urls: 要添加的URL列表
        """
        self.urls.extend(urls)
        self.total_count += len(urls)

    def get_progress(self) -> Dict[str, int]:
        """获取进度信息"""
        return {
            'total': self.total_count,
            'published': self.published_count,
            'remaining': len(self.urls)
        }