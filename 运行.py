import threading
import logging
from 线程池框架.线程池框架 import 线程池框架
from 共享参数 import 共享参数
from 页面逻辑 import 页面逻辑
from 章节逻辑 import 章节逻辑

# 设置日志格式
logging.basicConfig(format='[PID %(process)d][TID %(thread)d] %(message)s', level=logging.INFO)

def 主函数(线程数: int):
    共享参数实例 = 共享参数(0, 日志级别=0)  # 设置日志级别为1，只允许警告和错误级别的日志

    页面框架 = 线程池框架(线程数,
                      运行开始=页面逻辑.运行开始,
                      运行结束=页面逻辑.运行结束,
                      循环任务=页面逻辑.循环任务,
                      跳出循环条件=页面逻辑.跳出循环条件)

    章节框架 = 线程池框架(线程数,
                      运行开始=章节逻辑.运行开始,
                      运行结束=章节逻辑.运行结束,
                      循环任务=章节逻辑.循环任务,
                      跳出循环条件=章节逻辑.跳出循环条件)

    页面线程 = threading.Thread(target=页面框架.运行, args=(共享参数实例,))
    章节线程 = threading.Thread(target=章节框架.运行, args=(共享参数实例,))

    页面线程.start()
    章节线程.start()

    页面线程.join()
    章节线程.join()

if __name__ == "__main__":
    线程数 = 10
    主函数(线程数)
