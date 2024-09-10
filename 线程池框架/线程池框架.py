import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any

class 线程池框架:
    def __init__(self, 线程数: int,
                 运行开始: Callable[[Any], Any]=lambda _: None,
                 运行结束: Callable[[Any], Any]=lambda _: None,
                 循环任务: Callable[[Any], Any]=lambda _: None,
                 跳出循环条件: Callable[[Any], bool]=lambda _: False):
        self.线程数 = 线程数
        self.运行开始 = 运行开始
        self.运行结束 = 运行结束
        self.循环任务 = 循环任务
        self.跳出循环条件 = 跳出循环条件
        self.线程池执行器 = ThreadPoolExecutor(max_workers=线程数)
        self.锁 = threading.Lock()
        self.运行中任务 = 0
        self.已提交任务 = 0
        self.已完成任务 = 0
        self.失败任务 = 0
        self.异常任务 = 0
        self.重试任务 = 0
        self.监控停止标志 = threading.Event()

    def 监控(self):
        while True:
            logging.info(f"运行中任务: {self.运行中任务}, 已提交任务: {self.已提交任务}, "
                         f"完成任务: {self.已完成任务}, 失败任务: {self.失败任务}, "
                         f"异常任务: {self.异常任务}, 重试任务: {self.重试任务}")
            # if self.运行中任务 == 0 and self.已提交任务 == self.已完成任务 + self.失败任务:
            #     break
            if self.监控停止标志.is_set():
                break
            threading.Event().wait(0.3)  # 每秒更新一次

    def 执行任务(self, 参数: Any):
        with self.锁:
            self.运行中任务 += 1

        try:
            结果 = self.循环任务(参数)
            with self.锁:
                self.已完成任务 += 1
        except Exception as 异常:
            logging.error(f"任务执行异常: {str(异常)}")
            with self.锁:
                self.异常任务 += 1
                self.失败任务 += 1
        finally:
            with self.锁:
                self.运行中任务 -= 1

    def 检查并提交新任务(self, 参数: Any):
        with self.锁:
            if self.运行中任务 < self.线程数 and not self.跳出循环条件(参数):
                self.线程池执行器.submit(self.执行任务, 参数)
                self.已提交任务 += 1

    def 运行(self, 参数: Any):
        监控线程 = threading.Thread(target=self.监控)
        监控线程.start()

        self.运行开始(参数)
        while not self.跳出循环条件(参数):
            self.检查并提交新任务(参数)
            threading.Event().wait(0.01)

        self.线程池执行器.shutdown(wait=True)
        self.监控停止标志.set()
        监控线程.join()
        self.运行结束(参数)