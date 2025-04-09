#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTTP工具模块：提供HTTP相关的工具函数
"""

import random
import time
from typing import Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session(
    retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: List[int] = None,
    timeout: int = 10
) -> requests.Session:
    """
    创建一个带有重试机制的Session对象

    参数:
        retries: 重试次数
        backoff_factor: 重试间隔因子
        status_forcelist: 需要重试的HTTP状态码列表
        timeout: 超时时间（秒）

    返回:
        requests.Session: 配置好的Session对象
    """
    if status_forcelist is None:
        status_forcelist = [500, 502, 503, 504]

    # 配置重试策略
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST", "HEAD"]
    )

    # 创建适配器
    adapter = HTTPAdapter(max_retries=retry_strategy)

    # 创建Session并挂载适配器
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def get_random_user_agent() -> str:
    """
    获取随机User-Agent

    返回:
        随机的User-Agent字符串
    """
    user_agents = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    ]
    return random.choice(user_agents)


def get_with_retry(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Tuple[Optional[requests.Response], Optional[str]]:
    """
    发送GET请求并自动重试

    参数:
        url: 请求的URL
        headers: 请求头
        timeout: 超时时间（秒）
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）

    返回:
        Tuple[Optional[Response], Optional[str]]: (响应对象, 错误信息)
    """
    # 设置默认请求头
    if headers is None:
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        }

    # 创建Session
    session = create_session(
        retries=0,  # 关闭自动重试，改为手动控制
        timeout=timeout
    )

    # 手动重试
    error_msg = None
    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=timeout)
            return response, None
        except requests.RequestException as e:
            error_msg = f"请求异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
            if attempt < max_retries - 1:
                sleep_time = retry_delay * (2 ** attempt)  # 指数退避
                print(f"{error_msg}，将在 {sleep_time:.2f} 秒后重试...")
                time.sleep(sleep_time)

    return None, error_msg


def extract_urls_from_html(html: str, base_url: str = "") -> List[str]:
    """
    从HTML中提取所有链接

    参数:
        html: HTML文本
        base_url: 基础URL，用于转换相对链接

    返回:
        提取的URL列表
    """
    try:
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin

        soup = BeautifulSoup(html, 'html.parser')
        urls = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            if href and not href.startswith(('#', 'javascript:')):
                if base_url:
                    url = urljoin(base_url, href)
                else:
                    url = href
                urls.append(url)

        return urls
    except ImportError:
        print("请安装 BeautifulSoup4: pip install beautifulsoup4")
        return []
    except Exception as e:
        print(f"提取链接异常: {str(e)}")
        return []