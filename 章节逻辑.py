import threading
import queue
from lxml import etree
import requests
from typing import Any
from 线程池框架.逻辑基类 import 逻辑基类
from 共享参数 import 共享参数
from 线程池框架.文件工具 import 文件工具
from 线程池框架.重试工具类 import 重试工具

class 章节逻辑(逻辑基类):
    模块名 = '章节'
    章节记录锁 = threading.Lock()
    章节内容锁 = threading.Lock()

    @classmethod
    def 运行开始(cls, 参数: 共享参数) -> Any:
        cls.初始化日志器(参数.日志级别)

    @classmethod
    def 运行结束(cls, 参数: 共享参数) -> Any:
        pass

    @classmethod
    def 循环任务(cls, 参数: 共享参数) -> Any:
        try:
            页面下标, 章节标题, 章节链接, 分页章节下标计数 = 参数.章节队列.get(timeout=1)
        except queue.Empty:
            return False

        def 请求章节():
            cls.log.info(f"开始请求章节：{章节标题}")
            响应 = requests.get(章节链接, timeout=5)
            if 响应.status_code == 200:
                cls.log.info(f"章节请求成功：{章节标题}")
                cls.处理响应内容(响应, 页面下标, 章节标题, 分页章节下标计数, 参数)
                参数.章节字典[章节标题] = 2
                return True
            else:
                cls.log.warning(f"请求章节 {章节标题} 失败，状态码: {响应.status_code}")
                return False

        结果 = 重试工具.重试执行(请求章节)
        if not 结果:
            参数.章节队列.put((页面下标, 章节标题, 章节链接, 分页章节下标计数))
        return True

    @classmethod
    def 跳出循环条件(cls, 参数: 共享参数) -> bool:
        待处理章节 = [章节 for 章节, 状态 in 参数.章节字典.items() if 状态 == 1]
        已处理章节 = [章节 for 章节, 状态 in 参数.章节字典.items() if 状态 == 2]
        return 参数.章节队列.qsize() == 0 and len(待处理章节) == 0 and len(已处理章节) > 0

    @classmethod
    def 处理响应内容(cls, 响应, 页面下标, 章节标题, 分页章节下标计数, 参数):
        网页 = etree.HTML(响应.text)
        内容 = 网页.xpath("//div[contains(@class,'text')]/p")
        内容 = '\n'.join([行.text for 行 in 内容 if 行.text])
        cls.log.info(f"获取章节内容: {章节标题}, 内容长度: {len(内容)}")

        文件工具.追加写入记录文件(参数.下载存储路径, cls.章节记录锁, cls.模块名 + '列表', lambda 文件: (
                    文件.write(f'{页面下标}_{分页章节下标计数}\t{章节标题}'),
                    文件.write('\n'),
                ))

        文件工具.追加写入记录文件(参数.下载存储路径, cls.章节内容锁, 章节标题, lambda 文件: (
                    文件.write(f'{内容}'),
                ))
