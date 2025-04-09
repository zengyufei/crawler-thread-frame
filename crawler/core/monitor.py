#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
监控器模块：负责监控爬虫运行状态
"""

import time
from typing import Dict, Any


class CrawlerMonitor:
    """爬虫监控器，负责监控爬虫运行状态"""

    def __init__(self, interval: int = 5):
        """
        初始化监控器

        参数:
            interval: 监控间隔（秒），默认为5秒
        """
        self.start_time = None
        self.interval = interval
        self.last_monitor_time = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    def get_time(self) -> float:
        """
        获取爬虫运行时间（秒）

        返回:
            运行时间（秒）
        """
        if self.start_time is None:
            return 0
        return time.time() - self.start_time

    def monitor(self):
        """执行监控"""
        current_time = time.time()
        # 检查是否达到监控间隔
        if current_time - self.last_monitor_time < self.interval:
            return

        self.last_monitor_time = current_time
        self._do_monitor()

    def _do_monitor(self):
        """执行实际的监控操作"""
        elapsed_time = self.get_time()

        # 计算请求速率
        requests_per_minute = (self.total_requests * 60) / max(1, elapsed_time)

        # 计算成功率
        success_rate = (self.successful_requests / max(1, self.total_requests)) * 100

        # 打印监控信息
        print(f"\n--- 爬虫监控 [{time.strftime('%Y-%m-%d %H:%M:%S')}] ---")
        print(f"运行时间: {elapsed_time:.2f} 秒")
        print(f"总请求数: {self.total_requests}")
        print(f"成功请求: {self.successful_requests}")
        print(f"失败请求: {self.failed_requests}")
        print(f"成功率: {success_rate:.2f}%")
        print(f"请求速率: {requests_per_minute:.2f} 请求/分钟")
        print("-" * 50)

    def monitor_shutdown(self):
        """爬虫关闭时的监控"""
        elapsed_time = self.get_time()

        # 计算总体统计信息
        total_requests = self.total_requests
        requests_per_minute = (total_requests * 60) / max(1, elapsed_time)
        success_rate = (self.successful_requests / max(1, total_requests)) * 100

        # 打印最终监控信息
        print("\n=== 爬虫完成 ===")
        print(f"总运行时间: {elapsed_time:.2f} 秒")
        print(f"总请求数: {total_requests}")
        print(f"成功请求: {self.successful_requests}")
        print(f"失败请求: {self.failed_requests}")
        print(f"成功率: {success_rate:.2f}%")
        print(f"平均请求速率: {requests_per_minute:.2f} 请求/分钟")
        print("=" * 50)

    def update_stats(self, stats: Dict[str, Any]):
        """
        更新统计信息

        参数:
            stats: 统计信息字典
        """
        self.total_requests = stats.get('total_requests', 0)
        self.successful_requests = stats.get('successful_requests', 0)
        self.failed_requests = stats.get('failed_requests', 0)