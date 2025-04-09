#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小说爬虫示例：根据章节列表页面URL，抓取所有章节列表分页，获取所有章节内容并保存
"""

import os
import re
import time
import argparse
from urllib.parse import urljoin, urlparse
import json

import requests
from bs4 import BeautifulSoup

from crawler.core.manager import CrawlerManager
from crawler.core.producer import BaseProducer
from crawler.core.consumer import BaseConsumer
from crawler.core.monitor import CrawlerMonitor
from crawler.utils.http_utils import extract_urls_from_html, get_random_user_agent


class NovelCrawlerConfig:
    """小说爬虫配置类"""

    def __init__(self,
                 start_url,
                 chapter_list_selector="",
                 pagination_selector="",
                 chapter_title_selector="",
                 chapter_content_selector="",
                 encoding="utf-8",
                 save_dir="novels",
                 novel_name="",
                 delay=1.0,
                 thread_count=3):
        """
        初始化小说爬虫配置

        参数:
            start_url: 起始URL（章节列表的第一页）
            chapter_list_selector: 章节列表的CSS选择器
            pagination_selector: 分页链接的CSS选择器
            chapter_title_selector: 章节标题的CSS选择器
            chapter_content_selector: 章节内容的CSS选择器
            encoding: 网页编码
            save_dir: 保存目录
            novel_name: 小说名称（如果为空，则从URL中提取）
            delay: 请求延迟（秒）
            thread_count: 消费者线程数
        """
        self.start_url = start_url
        self.chapter_list_selector = chapter_list_selector
        self.pagination_selector = pagination_selector
        self.chapter_title_selector = chapter_title_selector
        self.chapter_content_selector = chapter_content_selector
        self.encoding = encoding

        # 如果没有指定小说名称，则从URL中提取
        if not novel_name:
            domain = urlparse(start_url).netloc
            path = urlparse(start_url).path
            novel_name = path.strip('/').split('/')[-1]
            # 如果路径末尾是数字，可能是分页，取前一个部分
            if novel_name.isdigit():
                novel_name = path.strip('/').split('/')[-2]

        self.novel_name = novel_name
        self.save_dir = os.path.join(save_dir, self.novel_name)
        self.delay = delay
        self.thread_count = thread_count

        # 确保保存目录存在
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)


class NovelUrlProducer(BaseProducer):
    """小说URL生产者，负责生成URL任务，包括章节列表页和章节页"""

    def __init__(self, config):
        """
        初始化小说URL生产者

        参数:
            config: 小说爬虫配置
        """
        super().__init__()
        self.config = config

        # 初始化三个队列，分别用于章节列表页、章节页
        self.chapter_list_queue = [config.start_url]  # 章节列表页队列
        self.chapter_page_queue = []  # 章节页队列

        # 记录已访问的URL，避免重复爬取
        self.visited_urls = set()

        # 统计信息
        self.total_count = 1  # 总任务数（初始为1，即起始URL）
        self.published_count = 0  # 已发布任务数
        self.chapter_list_count = 0  # 章节列表页数量
        self.chapter_count = 0  # 章节页数量

        # 生产间隔时间
        self.interval = config.delay

    def produce(self):
        """生产URL任务"""
        # 如果已经请求关闭
        if self.should_stop:
            return

        # 优先处理章节列表页
        if self.chapter_list_queue:
            url = self.chapter_list_queue.pop(0)

            # 如果已经访问过，则跳过
            if url in self.visited_urls:
                return

            # 标记为已访问
            self.visited_urls.add(url)

            # 构建任务
            task = {
                'url': url,
                'timestamp': time.time(),
                'retry': 0,
                'type': 'chapter_list'  # 标记任务类型为章节列表页
            }

            # 发布任务
            self.publish(task)
            self.published_count += 1
            self.chapter_list_count += 1

            # 如果设置了间隔时间，则等待
            if self.interval > 0:
                time.sleep(self.interval)

            return

        # 其次处理章节页
        if self.chapter_page_queue:
            url = self.chapter_page_queue.pop(0)

            # 如果已经访问过，则跳过
            if url in self.visited_urls:
                return

            # 标记为已访问
            self.visited_urls.add(url)

            # 构建任务
            task = {
                'url': url,
                'timestamp': time.time(),
                'retry': 0,
                'type': 'chapter'  # 标记任务类型为章节页
            }

            # 发布任务
            self.publish(task)
            self.published_count += 1
            self.chapter_count += 1

            # 如果设置了间隔时间，则等待
            if self.interval > 0:
                time.sleep(self.interval)

            return

        # 如果所有队列都为空且没有正在处理的任务，表示爬虫已完成工作
        if not self.task_queue.empty():
            # 还有任务在处理中，等待一会
            time.sleep(0.1)
        else:
            # 所有任务都完成了，关闭生产者
            print("所有URL任务已生成，等待消费者处理完毕...")
            self.shutdown_now()

    def add_chapter_list_url(self, url):
        """
        添加章节列表页URL

        参数:
            url: 章节列表页URL
        """
        if url not in self.visited_urls and url not in self.chapter_list_queue:
            self.chapter_list_queue.append(url)
            self.total_count += 1
            return True
        return False

    def add_chapter_url(self, url):
        """
        添加章节页URL

        参数:
            url: 章节页URL
        """
        if url not in self.visited_urls and url not in self.chapter_page_queue:
            self.chapter_page_queue.append(url)
            self.total_count += 1
            return True
        return False

    def get_stats(self):
        """获取统计信息"""
        return {
            'total': self.total_count,
            'published': self.published_count,
            'chapter_list_count': self.chapter_list_count,
            'chapter_count': self.chapter_count,
            'chapter_list_queue': len(self.chapter_list_queue),
            'chapter_page_queue': len(self.chapter_page_queue)
        }


class NovelContentConsumer(BaseConsumer):
    """小说内容消费者，负责解析章节列表页和章节页，并保存章节内容"""

    def __init__(self, producer, config):
        """
        初始化小说内容消费者

        参数:
            producer: 小说URL生产者
            config: 小说爬虫配置
        """
        super().__init__()
        self.producer = producer
        self.config = config
        self.successful_requests = 0
        self.failed_requests = 0
        self.saved_chapters = 0
        self.chapters_info = []  # 保存章节信息，用于生成目录

        # 请求头
        self.headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        }

    def get_exec_frequency_limit(self):
        """获取执行频率限制，这里不做限制，由生产者控制"""
        return -1

    def process(self, task):
        """
        处理任务

        参数:
            task: 任务数据
        """
        url = task.get('url')
        task_type = task.get('type')

        if not url:
            print(f"任务缺少URL: {task}")
            return

        try:
            # 发送HTTP请求
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            # 设置正确的编码
            response.encoding = self.config.encoding

            # 检查响应状态
            if response.status_code == 200:
                # 根据任务类型处理不同页面
                if task_type == 'chapter_list':
                    self.handle_chapter_list(url, response.text)
                elif task_type == 'chapter':
                    self.handle_chapter(url, response.text)

                self.successful_requests += 1
            else:
                # 处理失败的请求
                self.handle_failure(url, f"状态码错误: {response.status_code}", task)
                self.failed_requests += 1

        except requests.RequestException as e:
            # 处理请求异常
            self.handle_failure(url, f"请求异常: {str(e)}", task)
            self.failed_requests += 1

    def handle_chapter_list(self, url, html):
        """
        处理章节列表页

        参数:
            url: 章节列表页URL
            html: 章节列表页HTML内容
        """
        print(f"正在处理章节列表页: {url}")
        soup = BeautifulSoup(html, 'html.parser')

        # 提取分页链接
        if self.config.pagination_selector:
            pagination_links = soup.select(self.config.pagination_selector)
            for link in pagination_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(url, href)
                    if self.producer.add_chapter_list_url(full_url):
                        print(f"添加章节列表分页: {full_url}")

        # 提取章节链接
        if self.config.chapter_list_selector:
            chapter_links = soup.select(self.config.chapter_list_selector)
            for link in chapter_links:
                href = link.get('href')
                if href:
                    # 构建完整URL
                    full_url = urljoin(url, href)
                    # 有些网站的章节链接可能有特殊标记，需要过滤
                    if self.is_valid_chapter_url(full_url):
                        if self.producer.add_chapter_url(full_url):
                            chapter_title = link.text.strip()
                            print(f"添加章节: [{chapter_title}] - {full_url}")
        else:
            # 如果没有指定选择器，则尝试提取所有可能的章节链接
            all_links = soup.find_all('a')
            for link in all_links:
                href = link.get('href')
                if href and self.is_chapter_url(href):
                    full_url = urljoin(url, href)
                    if self.producer.add_chapter_url(full_url):
                        chapter_title = link.text.strip()
                        print(f"添加章节: [{chapter_title}] - {full_url}")

    def handle_chapter(self, url, html):
        """
        处理章节页

        参数:
            url: 章节页URL
            html: 章节页HTML内容
        """
        soup = BeautifulSoup(html, 'html.parser')

        # 提取章节标题
        chapter_title = "未知章节"
        if self.config.chapter_title_selector:
            title_element = soup.select_one(self.config.chapter_title_selector)
            if title_element:
                chapter_title = title_element.text.strip()

        # 提取章节内容
        content = ""
        if self.config.chapter_content_selector:
            content_element = soup.select_one(self.config.chapter_content_selector)
            if content_element:
                # 获取纯文本内容
                content = content_element.get_text('\n', strip=True)
                # 处理内容，去除广告等
                content = self.clean_content(content)

        # 保存章节内容
        if content:
            # 清理章节标题，用作文件名
            safe_title = self.safe_filename(chapter_title)
            # 生成章节序号，用于排序
            chapter_index = self.saved_chapters + 1
            # 文件名格式：序号_章节名.txt
            filename = f"{chapter_index:04d}_{safe_title}.txt"
            filepath = os.path.join(self.config.save_dir, filename)

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"{chapter_title}\n\n")
                    f.write(content)

                print(f"已保存章节: [{chapter_title}] 到 {filepath}")
                self.saved_chapters += 1

                # 记录章节信息
                self.chapters_info.append({
                    'index': chapter_index,
                    'title': chapter_title,
                    'url': url,
                    'filename': filename
                })

                # 保存目录信息
                self.save_toc()
            except Exception as e:
                print(f"保存章节 [{chapter_title}] 失败: {str(e)}")
        else:
            print(f"获取章节内容失败: {url}")

    def handle_failure(self, url, error, task):
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
        if retry_count < 3:  # 最多重试3次
            # 重新加入队列，增加重试次数
            task['retry'] = retry_count + 1
            task['timestamp'] = time.time()

            if self.task_queue:
                print(f"重试 {url} ({retry_count + 1}/3)")
                self.task_queue.put(task)

    def is_valid_chapter_url(self, url):
        """
        判断URL是否是有效的章节URL

        参数:
            url: 要判断的URL

        返回:
            是否是有效的章节URL
        """
        # 这里可以根据具体网站添加过滤规则
        # 例如，过滤掉一些广告链接、评论链接等
        path = urlparse(url).path

        # 排除一些常见的非章节链接
        exclude_patterns = [
            '/index.html', '/list.html', '/category/', '/tag/',
            '/search', '/author', '/about', '/contact', '/login',
            '/register', '/profile', '/setting'
        ]

        for pattern in exclude_patterns:
            if pattern in path:
                return False

        return True

    def is_chapter_url(self, href):
        """
        判断URL是否看起来像章节URL

        参数:
            href: 要判断的URL

        返回:
            是否可能是章节URL
        """
        # 通常章节URL包含数字，或者有特定的模式
        patterns = [
            r'/\d+\.html', r'/chapter_\d+', r'/chapter/\d+',
            r'/chap_\d+', r'/c\d+', r'/read/\d+', r'/\d+/\d+'
        ]

        for pattern in patterns:
            if re.search(pattern, href):
                return True

        return False

    def safe_filename(self, filename):
        """
        生成安全的文件名

        参数:
            filename: 原始文件名

        返回:
            安全的文件名
        """
        # 替换不允许出现在文件名中的字符
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # 限制文件名长度
        if len(filename) > 100:
            filename = filename[:100]

        return filename

    def clean_content(self, content):
        """
        清理章节内容，去除广告等

        参数:
            content: 原始内容

        返回:
            清理后的内容
        """
        # 去除常见广告文本
        ad_patterns = [
            r'(http|https)://\S+',  # 网址
            r'微信[公众号|搜索]\S+',  # 微信公众号
            r'加入书签.*',  # 书签提示
            r'手机阅读.*',  # 手机阅读提示
            r'推荐阅读.*',  # 推荐阅读
            r'章节目录.*',  # 章节目录提示
            r'请记住本书首发域名.*',  # 网站宣传
            r'本章未完.*',  # 未完提示
            r'天才一秒记住.*',  # 常见广告
        ]

        for pattern in ad_patterns:
            content = re.sub(pattern, '', content)

        # 去除多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content

    def save_toc(self):
        """保存目录信息"""
        if self.chapters_info:
            # 保存为JSON格式
            toc_path = os.path.join(self.config.save_dir, "toc.json")
            try:
                with open(toc_path, 'w', encoding='utf-8') as f:
                    json.dump(self.chapters_info, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存目录信息失败: {str(e)}")

            # 保存为纯文本格式
            txt_toc_path = os.path.join(self.config.save_dir, "目录.txt")
            try:
                with open(txt_toc_path, 'w', encoding='utf-8') as f:
                    f.write(f"《{self.config.novel_name}》目录\n\n")
                    for chapter in self.chapters_info:
                        f.write(f"{chapter['index']:04d}. {chapter['title']}\n")
            except Exception as e:
                print(f"保存文本目录失败: {str(e)}")

    def get_stats(self):
        """获取统计信息"""
        stats = super().get_stats()
        stats.update({
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'saved_chapters': self.saved_chapters
        })
        return stats


class NovelCrawlerMonitor(CrawlerMonitor):
    """小说爬虫监控器，更详细地监控爬虫运行状态"""

    def __init__(self, producer, consumers, interval=5):
        """
        初始化小说爬虫监控器

        参数:
            producer: 生产者对象
            consumers: 消费者对象列表
            interval: 监控间隔（秒）
        """
        super().__init__(interval)
        self.producer = producer
        self.consumers = consumers

    def _do_monitor(self):
        """执行实际的监控操作"""
        elapsed_time = self.get_time()

        # 获取生产者统计信息
        producer_stats = self.producer.get_stats()

        # 获取消费者统计信息
        total_processed = 0
        saved_chapters = 0

        for consumer in self.consumers:
            consumer_stats = consumer.get_stats()
            total_processed += consumer_stats.get('processed_count', 0)
            saved_chapters += consumer_stats.get('saved_chapters', 0)

        # 更新监控统计信息
        self.total_requests = total_processed
        self.successful_requests = sum(c.get_stats().get('successful_requests', 0) for c in self.consumers)
        self.failed_requests = sum(c.get_stats().get('failed_requests', 0) for c in self.consumers)

        # 计算请求速率
        requests_per_minute = (self.total_requests * 60) / max(1, elapsed_time)

        # 计算成功率
        success_rate = (self.successful_requests / max(1, self.total_requests)) * 100

        # 打印监控信息
        print(f"\n--- 小说爬虫监控 [{time.strftime('%Y-%m-%d %H:%M:%S')}] ---")
        print(f"运行时间: {elapsed_time:.2f} 秒")
        print(f"总URL数: {producer_stats.get('total', 0)}")
        print(f"已发布URL数: {producer_stats.get('published', 0)}")
        print(f"章节列表页数: {producer_stats.get('chapter_list_count', 0)}")
        print(f"章节页数: {producer_stats.get('chapter_count', 0)}")
        print(f"队列中章节列表页: {producer_stats.get('chapter_list_queue', 0)}")
        print(f"队列中章节页: {producer_stats.get('chapter_page_queue', 0)}")
        print(f"总请求数: {self.total_requests}")
        print(f"成功请求: {self.successful_requests}")
        print(f"失败请求: {self.failed_requests}")
        print(f"成功率: {success_rate:.2f}%")
        print(f"请求速率: {requests_per_minute:.2f} 请求/分钟")
        print(f"已保存章节: {saved_chapters}")
        print("-" * 50)


def load_config_from_args():
    """从命令行参数加载配置"""
    parser = argparse.ArgumentParser(description='小说爬虫')
    parser.add_argument('--url', required=True, help='章节列表的第一页URL')
    parser.add_argument('--chapter-list', default='', help='章节列表的CSS选择器')
    parser.add_argument('--pagination', default='', help='分页链接的CSS选择器')
    parser.add_argument('--title', default='', help='章节标题的CSS选择器')
    parser.add_argument('--content', default='', help='章节内容的CSS选择器')
    parser.add_argument('--encoding', default='utf-8', help='网页编码')
    parser.add_argument('--save-dir', default='novels', help='保存目录')
    parser.add_argument('--novel-name', default='', help='小说名称')
    parser.add_argument('--delay', type=float, default=1.0, help='请求延迟（秒）')
    parser.add_argument('--threads', type=int, default=3, help='消费者线程数')

    args = parser.parse_args()

    return NovelCrawlerConfig(
        start_url=args.url,
        chapter_list_selector=args.chapter_list,
        pagination_selector=args.pagination,
        chapter_title_selector=args.title,
        chapter_content_selector=args.content,
        encoding=args.encoding,
        save_dir=args.save_dir,
        novel_name=args.novel_name,
        delay=args.delay,
        thread_count=args.threads
    )


def main():
    """主函数"""
    # 加载配置
    config = load_config_from_args()

    print(f"开始爬取小说，起始URL: {config.start_url}")
    print(f"保存目录: {config.save_dir}")

    # 创建生产者
    producer = NovelUrlProducer(config)

    # 创建消费者
    consumers = [NovelContentConsumer(producer, config) for _ in range(config.thread_count)]

    # 创建监控器
    monitor = NovelCrawlerMonitor(producer, consumers)

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

    print("小说爬虫任务完成")


if __name__ == "__main__":
    import requests  # 导入requests模块
    main()