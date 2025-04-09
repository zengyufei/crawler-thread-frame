#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
高级爬虫示例：演示如何创建一个具有链接提取和递归抓取功能的爬虫
"""

import os
import time
import argparse
from urllib.parse import urlparse

from crawler.core.manager import CrawlerManager
from crawler.core.producer import UrlProducer, BaseProducer
from crawler.core.consumer import HtmlConsumer, BaseConsumer
from crawler.core.monitor import CrawlerMonitor
from crawler.utils.http_utils import extract_urls_from_html

# 创建保存目录
if not os.path.exists('downloads'):
    os.makedirs('downloads')


class LinkExtractorProducer(BaseProducer):
    """链接提取生产者，负责从已下载的页面中提取新的链接"""

    def __init__(self, seed_urls, max_depth=2, same_domain_only=True):
        """
        初始化链接提取生产者

        参数:
            seed_urls: 种子URL列表
            max_depth: 最大抓取深度
            same_domain_only: 是否只抓取相同域名的链接
        """
        super().__init__()
        self.url_queue = list(seed_urls)  # URL队列
        self.visited_urls = set()  # 已访问的URL集合
        self.max_depth = max_depth
        self.same_domain_only = same_domain_only
        self.domains = set(urlparse(url).netloc for url in seed_urls)  # 允许的域名
        self.url_depth = {url: 0 for url in seed_urls}  # URL深度字典
        self.total_count = len(seed_urls)
        self.published_count = 0

    def produce(self):
        """生产URL任务"""
        if not self.url_queue or self.should_stop:
            # 没有更多URL或者已经请求关闭
            time.sleep(0.1)  # 避免CPU空转
            return

        # 取出一个URL
        url = self.url_queue.pop(0)

        # 如果已经访问过，则跳过
        if url in self.visited_urls:
            return

        # 标记为已访问
        self.visited_urls.add(url)

        # 获取当前URL的深度
        depth = self.url_depth.get(url, 0)

        # 构建任务
        task = {
            'url': url,
            'timestamp': time.time(),
            'retry': 0,
            'depth': depth
        }

        # 发布任务
        self.publish(task)
        self.published_count += 1

        # 如果队列为空并且没有正在处理的任务，表示爬虫已完成工作
        if not self.url_queue and self.task_queue.empty():
            self.shutdown_now()

    def add_extracted_urls(self, source_url, urls):
        """
        添加从页面中提取的URL

        参数:
            source_url: 源URL
            urls: 提取的URL列表
        """
        if not urls:
            return

        source_depth = self.url_depth.get(source_url, 0)
        new_depth = source_depth + 1

        # 如果已经达到最大深度，则不再添加新的URL
        if new_depth > self.max_depth:
            return

        # 过滤URL
        filtered_urls = []
        for url in urls:
            # 过滤已访问的URL
            if url in self.visited_urls:
                continue

            # 如果只抓取相同域名，则过滤不同域名的URL
            if self.same_domain_only:
                domain = urlparse(url).netloc
                if domain not in self.domains:
                    continue

            filtered_urls.append(url)

        # 为新URL设置深度
        for url in filtered_urls:
            if url not in self.url_depth:
                self.url_depth[url] = new_depth

        # 将过滤后的URL添加到队列
        self.url_queue.extend(filtered_urls)
        self.total_count += len(filtered_urls)

        print(f"从 {source_url} 提取了 {len(filtered_urls)} 个新URL（深度 {new_depth}）")


class PageSavingConsumer(HtmlConsumer):
    """页面保存消费者，保存页面内容并提取链接"""

    def __init__(self, link_producer, save_dir='downloads', **kwargs):
        """
        初始化页面保存消费者

        参数:
            link_producer: 链接提取生产者
            save_dir: 保存目录
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.link_producer = link_producer
        self.save_dir = save_dir

        # 确保保存目录存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def handle_success(self, url, response):
        """
        处理成功的请求

        参数:
            url: 请求的URL
            response: 响应对象
        """
        # 调用父类方法
        super().handle_success(url, response)

        # 获取任务深度
        task_depth = getattr(response, 'task_depth', 0)

        # 保存页面内容
        html = response.text
        filename = self._get_filename(url)
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"已保存 {url} 到 {filename}")
        except Exception as e:
            print(f"保存 {url} 失败: {str(e)}")

        # 提取链接
        if self.link_producer:
            urls = extract_urls_from_html(html, base_url=url)
            self.link_producer.add_extracted_urls(url, urls)

    def process(self, task):
        """
        处理任务

        参数:
            task: 任务数据
        """
        # 从任务中获取深度信息
        depth = task.get('depth', 0)

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

            # 将深度信息附加到响应对象
            response.task_depth = depth

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

    def _get_filename(self, url):
        """
        根据URL生成保存文件名

        参数:
            url: URL

        返回:
            保存文件名
        """
        # 解析URL
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path

        # 处理路径
        if not path or path == '/':
            path = '/index.html'
        if path.endswith('/'):
            path += 'index.html'
        if '.' not in os.path.basename(path):
            path += '.html'

        # 构建保存路径
        filename = os.path.join(self.save_dir, domain + path.replace('/', '_'))

        # 创建目录
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        return filename


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='高级爬虫示例')
    parser.add_argument('--urls', nargs='+', required=True, help='要抓取的URL列表')
    parser.add_argument('--depth', type=int, default=2, help='最大抓取深度')
    parser.add_argument('--same-domain', action='store_true', help='是否只抓取相同域名的链接')
    parser.add_argument('--threads', type=int, default=5, help='消费者线程数')
    parser.add_argument('--timeout', type=int, default=10, help='请求超时时间（秒）')
    parser.add_argument('--save-dir', default='downloads', help='页面保存目录')

    args = parser.parse_args()

    # 创建链接提取生产者
    producer = LinkExtractorProducer(
        args.urls,
        max_depth=args.depth,
        same_domain_only=args.same_domain
    )

    # 创建多个页面保存消费者
    consumers = [
        PageSavingConsumer(
            producer,
            save_dir=args.save_dir,
            timeout=args.timeout
        ) for _ in range(args.threads)
    ]

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
    import requests  # 导入requests模块，放在这里防止循环导入
    main()