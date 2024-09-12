import os

import sys
sys.path.append('线程池框架')

from 日志工具 import 日志
logger = 日志('文件工具', 0)

class 文件工具:
    log: 日志 = logger

    @classmethod
    def 清空记录文件(cls, 路径, 模块名):
        with open(os.path.join(路径, 模块名 + ".txt"), 'w', encoding='utf-8') as 文件:
            文件.write('')
            文件.flush()
        cls.log.info(f'清空记录文件')

    @classmethod
    def 追加写入记录文件(cls, 路径, 文件锁, 模块名, 消费):
        with 文件锁:
            with open(os.path.join(路径, 模块名 + ".txt"), 'a', encoding='utf-8') as 文件:
                消费(文件)
