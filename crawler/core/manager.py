#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫管理器：负责协调生产者、消费者和监控器
"""

import threading
import queue
import time
from typing import List, Callable, Optional

class CrawlerManager:
    """爬虫管理器，负责协调生产者、消费者和监控器的工作"""

    def __init__(self, queue_size: int = 100):
        """
        初始化爬虫管理器

        参数:
            queue_size: 任务队列大小，默认为100
        """
        self.task_queue = queue.Queue(maxsize=queue_size)
        self.producer = None
        self.consumers = []
        self.monitor = None
        self.shutdown_callbacks = []
        self.is_shutdown = False
        self.producer_thread = None
        self.consumer_threads = []
        self.monitor_thread = None

    def add_producer(self, producer):
        """
        添加生产者

        参数:
            producer: 生产者对象
        """
        self.producer = producer
        producer.set_queue(self.task_queue)
        return self

    def add_consumer(self, consumer):
        """
        添加消费者

        参数:
            consumer: 消费者对象
        """
        self.consumers.append(consumer)
        consumer.set_queue(self.task_queue)
        return self

    def add_monitor(self, monitor):
        """
        添加监控器

        参数:
            monitor: 监控器对象
        """
        self.monitor = monitor
        return self

    def listen_shutdown(self, callback: Callable):
        """
        添加关闭回调函数

        参数:
            callback: 回调函数
        """
        self.shutdown_callbacks.append(callback)
        return self

    def start(self):
        """启动爬虫管理器"""
        # 重置关闭标志
        self.is_shutdown = False

        # 启动生产者线程
        if self.producer:
            self.producer_thread = threading.Thread(
                target=self._run_producer,
                name="Producer-Thread"
            )
            self.producer_thread.daemon = True
            self.producer_thread.start()

        # 启动消费者线程
        for i, consumer in enumerate(self.consumers):
            thread = threading.Thread(
                target=self._run_consumer,
                args=(consumer,),
                name=f"Consumer-Thread-{i}"
            )
            thread.daemon = True
            thread.start()
            self.consumer_threads.append(thread)

        # 启动监控器线程
        if self.monitor:
            self.monitor.start_time = time.time()
            self.monitor_thread = threading.Thread(
                target=self._run_monitor,
                name="Monitor-Thread"
            )
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

        return self

    def _run_producer(self):
        """运行生产者"""
        try:
            while not self.is_shutdown:
                self.producer.produce()
                # 判断是否应该关闭
                if self.producer.should_shutdown():
                    self.shutdown()
                    break
        except Exception as e:
            print(f"生产者异常: {e}")
            self.shutdown()

    def _run_consumer(self, consumer):
        """
        运行消费者

        参数:
            consumer: 消费者对象
        """
        try:
            while not self.is_shutdown:
                try:
                    # 尝试从队列获取任务，设置超时时间为1秒
                    task = self.task_queue.get(timeout=1)
                    consumer.consume(task)
                    self.task_queue.task_done()
                except queue.Empty:
                    # 队列为空，继续等待
                    continue
        except Exception as e:
            print(f"消费者异常: {e}")

    def _run_monitor(self):
        """运行监控器"""
        try:
            while not self.is_shutdown:
                self.monitor.monitor()
                time.sleep(1)  # 监控间隔1秒
        except Exception as e:
            print(f"监控器异常: {e}")
        finally:
            if self.is_shutdown:
                self.monitor.monitor_shutdown()

    def shutdown(self):
        """关闭爬虫管理器"""
        if self.is_shutdown:
            return

        self.is_shutdown = True

        # 等待任务队列清空
        self.task_queue.join()

        # 执行关闭回调
        for callback in self.shutdown_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"关闭回调异常: {e}")

        print("爬虫管理器已关闭")

    def is_running(self):
        """检查爬虫是否仍在运行"""
        # 检查生产者是否还活着或队列是否有任务
        if self.producer_thread and self.producer_thread.is_alive():
            return True

        # 如果队列不为空，说明还有任务要处理
        if not self.task_queue.empty():
            return True

        # 所有工作都完成了
        return False