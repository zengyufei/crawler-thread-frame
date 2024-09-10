import logging
import time

class 重试工具:
    log = logging.getLogger(__name__)

    @classmethod
    def 重试执行(cls, 操作, 最大重试次数=5, 超时时间=5):
        重试次数 = 0
        while 重试次数 < 最大重试次数:
            try:
                return 操作()
            except Exception as 异常:
                cls.log.error(f"操作执行失败: {异常}")
                重试次数 += 1
                cls.log.info(f"重试操作，当前重试次数：{重试次数}")
                if 重试次数 < 最大重试次数:
                    time.sleep(超时时间)
        return None