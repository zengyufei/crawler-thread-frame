# 小说爬虫使用说明

这个小说爬虫可以从小说网站抓取章节内容，支持分页列表和章节抓取。爬虫会按照以下步骤工作：

1. 从给定的起始URL（章节列表页）开始
2. 提取章节列表分页链接
3. 提取章节链接
4. 抓取每个章节的内容并保存为文本文件
5. 生成目录文件

## 运行方式

```bash
python -m crawler.examples.novel_crawler --url <章节列表起始URL> [其他参数]
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--url` | 章节列表的第一页URL（必需） | - |
| `--chapter-list` | 章节列表的CSS选择器 | 空（自动识别） |
| `--pagination` | 分页链接的CSS选择器 | 空（自动识别） |
| `--title` | 章节标题的CSS选择器 | 空（自动识别） |
| `--content` | 章节内容的CSS选择器 | 空（自动识别） |
| `--encoding` | 网页编码 | utf-8 |
| `--save-dir` | 保存目录 | novels |
| `--novel-name` | 小说名称 | 从URL提取 |
| `--delay` | 请求延迟（秒） | 1.0 |
| `--threads` | 消费者线程数 | 3 |

## 使用示例

### 基本使用

最简单的使用方式只需提供章节列表的起始URL：

```bash
python -m crawler.examples.novel_crawler --url https://www.example.com/novel/12345/
```

### 指定CSS选择器

如果网站有特殊的HTML结构，可以指定CSS选择器：

```bash
python -m crawler.examples.novel_crawler \
    --url https://www.example.com/novel/12345/ \
    --chapter-list ".chapter-list a" \
    --pagination ".pagination a" \
    --title ".chapter-title" \
    --content ".chapter-content"
```

### 完整配置示例

```bash
python -m crawler.examples.novel_crawler \
    --url https://www.example.com/novel/12345/ \
    --chapter-list ".chapter-list a" \
    --pagination ".pagination a" \
    --title ".chapter-title" \
    --content ".chapter-content" \
    --encoding gbk \
    --save-dir my_novels \
    --novel-name "我的小说" \
    --delay 2.0 \
    --threads 5
```

## 常见网站的CSS选择器参考

不同的小说网站有不同的HTML结构，下面是一些常见网站的CSS选择器参考：

### 某小说网站示例1

```
--chapter-list ".chapter-list li a"
--pagination ".pagination a"
--title ".reader-title h1"
--content "#content"
```

### 某小说网站示例2

```
--chapter-list "#list dl dd a"
--pagination ".listpage a"
--title ".bookname h1"
--content "#content"
```

## 输出文件

爬虫会在保存目录下创建以下文件：

1. 章节文件：`0001_章节标题.txt`、`0002_章节标题.txt` 等
2. 目录文件：`目录.txt`
3. 元数据文件：`toc.json`（包含所有章节的信息）

## 注意事项

1. 请控制爬取频率，避免对目标网站造成过大负担
2. 一些网站可能有反爬措施，如果频繁请求可能会被封IP
3. 仅用于个人学习使用，请勿用于非法用途
4. 如果网站更新了HTML结构，可能需要更新CSS选择器
5. 建议先使用较小的线程数和较长的延迟进行测试，确认一切正常后再调整参数