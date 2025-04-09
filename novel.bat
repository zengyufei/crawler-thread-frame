python -m crawler.examples.novel_crawler ^
    --url "http://m.biqu5200.net/wapbook-204448_1/" ^
    --chapter-list "body > div.cover > ul > li > a" ^
    --pagination "body > div:nth-child(6) > a" ^
    --title "#content > div.title" ^
    --content "#content > div.text" ^
    --encoding gbk ^
    --delay 1.0 ^
    --threads 30