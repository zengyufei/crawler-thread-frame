import threading
import queue
from lxml import etree
import requests
from typing import Any
from 线程池框架.逻辑基类 import 逻辑基类
from 共享参数 import 共享参数
from 线程池框架.文件工具 import 文件工具
from 线程池框架.重试工具类 import 重试工具
from 线程池框架.日志工具 import 日志

log = 日志('分页', 0)

class 页面逻辑(逻辑基类):
    模块名 = '分页'
    分页记录锁 = threading.Lock()
    分页章节记录锁 = threading.Lock()

    @classmethod
    def 运行开始(cls, 参数: 共享参数) -> Any:
        log.设置日志级别(参数.日志级别)

        页面下标 = 1
        初始链接 = "http://m.biqu5200.net/wapbook-204448_1/"
        参数.页面队列.put((页面下标, 初始链接))

        文件工具.清空记录文件(参数.下载存储路径, cls.模块名 + '分页')
        文件工具.清空记录文件(参数.下载存储路径, cls.模块名 + '章节')

    @classmethod
    def 运行结束(cls, 参数: 共享参数) -> Any:
        已处理页面 = [页面 for 页面, 状态 in 参数.页面字典.items() if 状态 == 2]
        章节页面数量 = [页面 for 页面, 状态 in 参数.章节字典.items() if 状态 == 1]
        log.info(f"已处理页面: {len(已处理页面)}, 章节页面数量: {len(章节页面数量)}")

    @classmethod
    def 循环任务(cls, 参数: 共享参数) -> Any:
        try:
            页面下标, 页面链接 = 参数.页面队列.get(timeout=1)
        except queue.Empty:
            return False

        def 请求页面():
            log.info(f"开始请求页面：{页面链接}")
            响应 = requests.get(页面链接, timeout=5)
            if 响应.status_code == 200:
                log.info(f"页面请求成功：{页面链接}")
                cls.处理响应内容(响应, 页面下标, 页面链接, 参数)
                参数.页面字典[页面链接] = 2
                return True
            else:
                log.warning(f"请求页面 {页面链接} 失败，状态码: {响应.status_code}")
                return False

        结果 = 重试工具.重试执行(请求页面)
        if 结果:
            return True
        else:
            参数.页面队列.put((页面下标, 页面链接))
            return False

    @classmethod
    def 跳出循环条件(cls, 参数: 共享参数) -> bool:
        待处理页面 = [页面 for 页面, 状态 in 参数.页面字典.items() if 状态 == 1]
        已处理页面 = [页面 for 页面, 状态 in 参数.页面字典.items() if 状态 == 2]
        return 参数.页面队列.qsize() == 0 and len(待处理页面) == 0 and len(已处理页面) > 0

    @classmethod
    def 处理响应内容(cls, 响应, 页面下标, 页面链接, 参数):
        网页 = etree.HTML(响应.text)

        下一页链接 = 网页.xpath('/html/body/div[6]/a/@href')
        log.info(f"找到 {len(下一页链接)} 个下一页链接")
        新页面下标 = 页面下标
        for 页面 in 下一页链接:
            完整链接 = f"http://m.biqu5200.net{页面}"
            新页面下标 += 1
            if 完整链接 not in 参数.页面字典:
                参数.页面字典[完整链接] = 1
                参数.页面队列.put((新页面下标, 完整链接))
                log.info(f"新页面链接已添加到队列：{完整链接}")

        分页章节下标计数 = 0
        章节列表 = 网页.xpath('/html/body/div[4]/ul/li/a')
        log.info(f"找到 {len(章节列表)} 个章节")
        for 章节 in 章节列表:
            章节链接 = f"http://m.biqu5200.net{章节.get('href')}"
            章节标题 = 章节.text
            log.info(f"新章节已添加：{章节标题}")
            参数.章节字典[章节标题] = 1
            分页章节下标计数 += 1
            参数.章节队列.put((页面下标, 章节标题, 章节链接, 分页章节下标计数))

            文件工具.追加写入记录文件(参数.下载存储路径, cls.分页章节记录锁, cls.模块名 + '章节', lambda 文件: (
                文件.write(f'{页面下标}_{分页章节下标计数}\t{章节标题}\t{章节链接}'),
                文件.write('\n'),
            ))

        try:
            文件工具.追加写入记录文件(参数.下载存储路径, cls.分页记录锁, cls.模块名 + '分页', lambda 文件: (
                文件.write(f'{页面下标}\t{页面链接}'),
                文件.write('\n'),
            ))
        except Exception as 异常:
            log.error(f"追加写入记录文件 出现错误: {页面链接} == {异常}")
