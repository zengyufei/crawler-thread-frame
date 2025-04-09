#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主程序示例：展示如何使用爬虫框架
"""

import time
from crawler.core.manager import CrawlerManager
from crawler.core.producer import UrlProducer
from crawler.core.consumer import HtmlConsumer
from crawler.core.monitor import CrawlerMonitor

def main():
    # 创建要抓取的URL列表
    urls = [
        'https://www.baidu.com',
        'https://www.sina.com.cn',
        'https://www.sohu.com',
        'https://www.163.com',
        'https://www.qq.com',
        # 可以添加更多URL
    ]

    # 创建生产者
    producer = UrlProducer(urls)

    # 创建多个消费者
    consumers = [HtmlConsumer() for _ in range(5)]  # 创建5个消费者线程

    # 创建监控器
    monitor = CrawlerMonitor()

    # 创建并启动爬虫管理器
    manager = CrawlerManager()
    manager.add_producer(producer)
    for consumer in consumers:
        manager.add_consumer(consumer)
    manager.add_monitor(monitor)

    # 启动爬虫
    manager.start()

    try:
        # 等待爬虫完成
        while manager.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("用户中断爬虫运行")
        manager.shutdown()

    print("爬虫任务完成")

if __name__ == "__main__":
    main()