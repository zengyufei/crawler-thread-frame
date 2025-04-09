# 多线程爬虫框架

基于生产者-消费者模型的多线程爬虫框架，主要应用于爬虫方面多线程并发请求获取HTML内容。

## 特点

- 基于生产者-消费者模型设计
- 支持多线程并发请求
- 可自定义请求频率限制
- 内置监控系统
- 支持链接提取和递归抓取
- 可扩展性强

## 安装

安装所需依赖：

```bash
pip install -r requirements.txt
```

## 框架结构

```
crawler/
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── manager.py          # 爬虫管理器
│   ├── producer.py         # 生产者模块
│   ├── consumer.py         # 消费者模块
│   └── monitor.py          # 监控器模块
├── utils/                  # 工具模块
│   ├── __init__.py
│   └── http_utils.py       # HTTP工具类
├── examples/               # 示例模块
│   ├── __init__.py
│   └── advanced_crawler.py # 高级爬虫示例
├── __init__.py
└── main.py                 # 主程序
```

## 快速开始

### 基本用法

```python
import time
from crawler.core.manager import CrawlerManager
from crawler.core.producer import UrlProducer
from crawler.core.consumer import HtmlConsumer
from crawler.core.monitor import CrawlerMonitor

# 创建URL列表
urls = [
    'https://www.baidu.com',
    'https://www.sina.com.cn',
    'https://www.sohu.com',
]

# 创建生产者
producer = UrlProducer(urls)

# 创建消费者
consumers = [HtmlConsumer() for _ in range(3)]

# 创建监控器
monitor = CrawlerMonitor()

# 创建并启动爬虫管理器
manager = CrawlerManager()
manager.add_producer(producer)
for consumer in consumers:
    manager.add_consumer(consumer)
manager.add_monitor(monitor)
manager.start()

# 等待爬虫完成
while manager.is_running():
    time.sleep(1)
```

### 运行高级爬虫示例

```bash
python -m crawler.examples.advanced_crawler --urls https://www.example.com --depth 2 --threads 5
```

## 自定义扩展

### 创建自定义生产者

```python
from crawler.core.producer import BaseProducer

class MyProducer(BaseProducer):
    def __init__(self, data_source):
        super().__init__()
        self.data_source = data_source

    def produce(self):
        # 从数据源获取数据
        data = self.data_source.get_data()

        # 发布数据
        if data:
            self.publish(data)
        else:
            # 数据源耗尽，关闭生产者
            self.shutdown_now()
```

### 创建自定义消费者

```python
from crawler.core.consumer import BaseConsumer

class MyConsumer(BaseConsumer):
    def get_exec_frequency_limit(self):
        # 限制每秒最多处理5个任务
        return 5

    def process(self, task):
        # 处理任务的具体逻辑
        result = self.process_task(task)

        # 保存结果
        self.save_result(result)
```

## 注意事项

- 请遵守网站的robots.txt规则
- 设置合理的请求频率，避免对目标网站造成过大压力
- 处理异常情况，提高爬虫的稳定性
- 使用代理IP可以避免IP被封

## 许可证

MIT