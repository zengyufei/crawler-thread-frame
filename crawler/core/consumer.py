#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
消费者模块：负责处理生产者生成的任务
"""

import time
import queue
import uuid
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor


class BaseConsumer(ABC):
    """消费者基类"""

    def __init__(self):
        """初始化消费者"""
        self.task_queue = None
        self.consumer_id = self.init_id()
        self.processed_count = 0
        self.last_process_time = 0

    def set_queue(self, task_queue: queue.Queue):
        """
        设置任务队列

        参数:
            task_queue: 任务队列
        """
        self.task_queue = task_queue

    def init_id(self) -> str:
        """
        初始化消费者ID

        返回:
            消费者唯一ID
        """
        return str(uuid.uuid4())

    def get_exec_frequency_limit(self) -> float:
        """
        获取执行频率限制（每秒请求数）
        返回负数表示无限制

        返回:
            执行频率限制
        """
        return -1  # 默认无限制

    def consume(self, task: Any):
        """
        消费任务

        参数:
            task: 任务数据
        """
        # 检查频率限制
        frequency_limit = self.get_exec_frequency_limit()
        if frequency_limit > 0:
            # 计算应该等待的时间
            current_time = time.time()
            elapsed = current_time - self.last_process_time
            wait_time = (1.0 / frequency_limit) - elapsed

            if wait_time > 0:
                time.sleep(wait_time)

        # 处理任务
        self.process(task)

        # 更新计数和时间
        self.processed_count += 1
        self.last_process_time = time.time()

    @abstractmethod
    def process(self, task: Any):
        """
        处理任务的抽象方法，子类必须实现

        参数:
            task: 任务数据
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """
        获取消费者统计信息

        返回:
            统计信息字典
        """
        return {
            'consumer_id': self.consumer_id,
            'processed_count': self.processed_count,
            'last_process_time': self.last_process_time
        }


class HtmlConsumer(BaseConsumer):
    """HTML消费者，负责获取网页内容"""

    def __init__(self, timeout: int = 10, max_retries: int = 3, headers: Optional[Dict[str, str]] = None):
        """
        初始化HTML消费者

        参数:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            headers: 请求头
        """
        super().__init__()
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.successful_requests = 0
        self.failed_requests = 0

    def get_exec_frequency_limit(self) -> float:
        """
        获取执行频率限制

        返回:
            执行频率限制，这里设置为每秒2个请求
        """
        return 2  # 每秒2个请求

    def process(self, task: Dict[str, Any]):
        """
        处理任务，获取网页内容

        参数:
            task: 任务数据，包含url等信息
        """
        url = task.get('url')
        retry_count = task.get('retry', 0)

        if not url:
            print(f"任务缺少URL: {task}")
            return

        try:
            # 发送HTTP请求
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            # 检查响应状态
            if response.status_code == 200:
                # 处理成功的请求
                self.handle_success(url, response)
                self.successful_requests += 1
            else:
                # 处理失败的请求
                self.handle_failure(url, f"状态码错误: {response.status_code}", task)
                self.failed_requests += 1

        except requests.RequestException as e:
            # 处理请求异常
            self.handle_failure(url, f"请求异常: {str(e)}", task)
            self.failed_requests += 1

    def handle_success(self, url: str, response: requests.Response):
        """
        处理成功的请求

        参数:
            url: 请求的URL
            response: 响应对象
        """
        # 默认实现只打印状态，子类可以重写此方法以处理HTML内容
        html = response.text
        content_length = len(html)
        print(f"成功获取 {url} - 内容长度: {content_length} 字节")

        # 这里可以进一步处理HTML，如解析、提取链接等
        # 示例：打印HTML前100个字符
        print(f"HTML预览: {html[:100]}...")

    def handle_failure(self, url: str, error: str, task: Dict[str, Any]):
        """
        处理失败的请求

        参数:
            url: 请求的URL
            error: 错误信息
            task: 原始任务
        """
        print(f"获取 {url} 失败: {error}")

        # 检查是否需要重试
        retry_count = task.get('retry', 0)
        if retry_count < self.max_retries:
            # 重新加入队列，增加重试次数
            task['retry'] = retry_count + 1
            task['timestamp'] = time.time()

            if self.task_queue:
                print(f"重试 {url} ({retry_count + 1}/{self.max_retries})")
                self.task_queue.put(task)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取消费者统计信息

        返回:
            统计信息字典
        """
        stats = super().get_stats()
        stats.update({
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.successful_requests / max(1, self.processed_count) * 100
        })
        return stats