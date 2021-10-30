Python 生成器很酷，但是它是什么？它可以做什么？这就是本文章要探讨的内容。我们的目标是从**[系统程序设计](https://en.wikipedia.org/wiki/Systems_programming)**的角度来探索生成器的实际应用，其中包括文件、文件系统、网络和线程等。

> 本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'08 发表的[Generator Tricks for Systems Programmers](https://dabeaz.com/generators/index.html)一文。

目录
{: .h2}

[TOC]

## 有趣的文件和目录

### 编程问题

你有数百个分散在不同目录的 web 服务器日志文件。此外，有些日志文件还是被压缩过的。如何写一个程序可以让你能轻松的来读取这些日志文件？

```shell
foo/
	access-log-012007.gz
 	access-log-022007.gz
 	access-log-032007.gz
 	...
 	access-log-012008
bar/
	access-log-092007.bz2
	...
	access-log-022008
```

我们还是采用[上节](/posts/python-xi-tong-cheng-xu-she-ji-zhi-sheng-cheng-qi-ji-qiao-yi)中提到的[声明式编程](https://en.wikipedia.org/wiki/Declarative_programming)思路来解决该问题，用生成器做为“管道”声明单个操作，让它来一步步地处理日志文件。

### 搜索文件

从给定目录中搜索全部指定类别的文件

```python
from pathlib import Path

for filename in Path("/").rglob("*.py")
    print(filename)

# 事实上Path().rglob()方法会创建一个生成器，就像这样
>>>from pathlib import Path
>>>Path("/").rglob("*.py")
<generator object Path.rglob at 0x10e3e0b88>
>>>
# 所以我们可以直接用它来做为搜索文件的管道
```

### 打开文件

读取文件路径来打开文件

```python
# 传入日志文件的路径序列来打开文件
import gzip, bz2

def gen_open(paths):
  	for path in paths:
      	if path.suffix == ".gz":
          	yield gzip.open(path, "rt")
        elif path.suffix == ".bz2":
          	yield bz2.open(path, "rt")
        else:
          	yield open(path, "rt")

```

### 连接数据

把打开的文件序列连接到一起

```python
def gen_cat(sources):
  	for src in sources:
      	for item in src:
        		yield item

# 或者
def gen_cat(sources):
  	for src in sources:
      	yield from src

# `yield from`关键字可以用来委托迭代，就像这样
def countdown(n):
  	while n > 0:
      	yield n
        n -= 1

def countup(n):
  	n = 1
    while n < stop:
      	yield n
        n += 1

def up_and_down(n):
  	yield from countup(n)
    yield from countdown(n)

>>>for x in up_and_down(3):
...    print(x)
...
1
2
3
2
1
>>>
```

### 查找文本

根据给定的正则表达式从行序列中查找某行

```python
import re

def gen_grep(pat, lines):
  	patc = re.compile(pat)
    return (line for line in lines if patc.search(line))
```

现在我们可以把这些“管道”组织到一起，从整个目录的日志文件中找出符合某个特定表达式的日志行到底传输了多少字节的数据。

```python
pat = r"somepattern"
logdir = "/some/dir/"

filenames = Path(logdir).rglob("access-log*")
logfiles = gen_open(filenmaes)
loglines = gen_cat(logfiles)
patlines = gen_grep(pat, loglines)
bytecolumn = (line.rsplit(None,1)[1] for line in patlines)
bytes_sent = (int(x) for x in bytecolumn if x != "-")

print("Total", sum(bytes_sent))
```

这样我们就完美的解决了该问题。可以看出：**生成器会将迭代与使用迭代结果的代码进行解耦，所以我们可以将任意数量的能生成序列的组件插入到一起来共同完成工作**。

## 解析和处理数据

### 编程问题

web 服务器日志由不同的数据列组成，如何将每行日志解析为有用的数据结构，以便我们能够轻松检查数据列中不同的字段？

```shell
81.107.39.38 - - [24/Feb/2008:00:08:59 -0600] "GET ..." 200 7587
# 可以解析为
host referrer user [datetime] "request" status bytes
```

### 通过正则表达式解析日志

让我们通过正则表达式来解析这些行

```python
logpats = r"(\S+) (\S+) (\S+) \[(.*?)\]" \
          r"\"(\S+) (\S+) (\S+)\" (\S+) (\S+)"
# “S+”意味着匹配非空字符串
logpat = re.compile(logpats)

groups = (logpat.match(line) for line in loglines)
tuples = (g.groups() for g in groups if g)
```

生成的 tuples 序列是这样的

```python
("71.201.176.194", "-", "-", "26/Feb/2008:10:30:08 -0600",
"GET", "/ply/ply.html", "HTTP/1.1", "200", "97238")
```

我不太喜欢用元组上处理数据，因为：

1. 元组是不可变的，所以你不能修改它
2. 要取特定字段必须要记住列号，如果有很多列数据的话这会很烦人
3. 如果你更改了字段的序号代码就会出错

所以我们应该把它转成字典

### 将元组转换为字典

```python
columns = ("host", "referrer", "user", "datetime",
          "method", "request", "proto", "status", "bytes")
log = (dict(zip(columns, t)) for t in tuples)
```

它会生成像这样的命名序列

```python
{
    "status" : "200",
    "proto" : "HTTP/1.1",
    "referrer": "-",
    "request" : "/ply/ply.html",
    "bytes" : "97238",
    "datetime": "24/Feb/2008:00:08:59 -0600",
    "host" : "140.180.132.213",
    "user" : "-",
    "method" : "GET"
}
```

### 字段类型转换

你也许想通过转换函数（例如：int(), float()）处理特定的字典字段，可以这样做：

```python
def field_map(dictseq, name, func):
    for d in dcitseq:
      	d[name] = func(d[name])
        yield d

log = field_map(log, "status", int)
log = field_map(log, "bytes", lambda s: int(s) if s != "-" else 0)
```

转换后的字典变成了这样

```python
{
  	"status": 200,
  	"proto": "HTTP/1.1",
    "referrer": "-",
    "request": "/ply/ply.html",
    "datetime": "24/Feb/2008:00:08:59 -0600",
    "bytes": 97238,
    "host": "140.180.132.213",
    "user": "-",
    "method": "GET"
}
```

可以看到，status 和 bytes 字段被转成了 int。

### 结构化代码

随着数据管道的不断增长，我们可以尝试将管道中的某些部分独立为有用的组件，可以通过 python 函数简单的把函数封装起来，例如：

```python
from pathlib import Path

# 从目录中读取特定的行
def lines_from_dir(filepat, dirname):
  	names = Path(dirname).rglob(filepat)
    files = gen_open(names)
    lines = gen_cat(files)
    return lines

# 解析Apache日志为字典
def apache_log(lines):
  	groups = (logpat.match(line) for line in lines)
    tuples = (g.groups() for g in groups if g)

    columns = ("host", "referrer", "user", "datetime",
          "method", "request", "proto", "status", "bytes")
		log = field_map(log, "status", int)
		log = field_map(log, "bytes", lambda s: int(s) if s != "-" else 0)
    return log
```

这样，函数做为一个普通的组件就可以很方便的在其他管道内使用。

### 查询日志

**在创建管道组件时，关注组件的输入和输出是非常重要的事**。当你使用像字典这种标准的结构化数据类型时就可以获得最大的代码自由度，例如当我们想查询所有响应状态为 404 的文档时我们就可以这样做：

```python
status404 = {r["request"] for r in log if r["status"] == 404}
```

当想输出所有传输字节大于 1M 的请求时可以这样做：

```python
large = (r for r in log if r["bytes"] > 1000000)

for r in large:
    print(r["request"], r["bytes"])
```

当想找出最高传输了多少字节时可以这样做：

```python
print("%d %s" % max((r["bytes"], r["request"]) for r in log))
```

当想找出所有不同的 IP 地址时可以这样做：

```python
hosts = {r["host"] for r in log}
```

当想找出某文件的下载数时可以这样做：

```python
sum(1 for r in log if r["request"] == "/ply/ply-2.3.tar.gz")
```

当想找出谁一直在获取 robots.txt 可以这样做：

```python
addrs = {r["host"] for r in log if "robots.txt" in r["request"]}

import socket
for addr in addrs:
  	try:
      	print(socket.gethostbyaddr(addr)[0])
    except stocket.herror:
      	print(addr)
```

看来使用生成器表达式来做为管道查询语言是个很不错的想法，这有些像 SQL 语句，我们可以灵活的查询各种有用的数据。通过管道传输这种类型为字典或对象的数据结构能让组件变的更为强大。

## 处理无尽的数据

### 编程问题

你之前在 Unix 系统中使用过“tail -f”命令吗？它会输出文件末尾的行，这一般是查看日志的“标准”方式。跟踪日志文件你会得到一个“无限的流”，并且日志文件通常很大，让我们尝试写一个函数来代替“tail -f”跟踪日志流。

### 跟踪日志流

我们可以查找文件末尾的行并不断的读取新行，如果新数据被写入，那么就可以第一时间获取它：

```python
import time
import os

def follow(thefile):
  	# 文件的末尾
  	thefile.seek(0, os.SEEK_END)
    while True:
      	line = thefile.readline()
        if not line:
          	time.sleep(0.1)
            continue
        yield line
```

使用方法：

```python
logfile = open("access-log")
loglines = follow(logfile)

for line in loglines:
  	print(line, end=" ")
```

这将生成和“tail -f”相似的输出结果。我们可以这样转换实时的日志为记录：

```python
logfile = open("access-log")
loglines = follow(logfile)
log = apache_log(loglines)
```

可以这样实时输出所有 404 请求：

```python
r404 = (r for r in log if r["status"] == 404)
for r in r404:
  	print(r["host"], r["datetime"], r["request"])
```

我们仅仅将新的输入内容接到了之前的数据管道上，一切就都可以像之前正常工作。这真的很棒，我们不再需要去重复编写管道处理函数，就可以从最新的日志中很方便的查询特定的行，这就是组件化管道的魅力所在。
