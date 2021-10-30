本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'08 发表的[《Generator Tricks for Systems Programmers》](https://dabeaz.com/generators/index.html)一文。
{: #source }

Python 生成器很酷，但是它是什么？它可以做什么？这就是本文章要探讨的内容。我们的目标是从**[系统程序设计](https://en.wikipedia.org/wiki/Systems_programming)**的角度来探索生成器的实际应用，其中包括文件、文件系统、网络和线程等。

## 向管道提供数据

为了向生成器管道提供数据，你需要一个输入源。到目前为止我们已经有了 2 个基于文件的输入源，但是管道并没有规定输入数据必须要来自文件，并且也没有规定它必须是字符串或者要转换为字典。需要注意的是：**Python 所有对象都是[“一等公民”](https://en.wikipedia.org/wiki/First-class_citizen)，这意味着所有对象都可以公平的使用生成器管道**。

### 提供连接

生成 TCP 连接序列：

```python
import socket

# 生成连接
def receive_connections(addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSERDDR, 1)
    s.bind(addr)
    s.listen(5)
    while True:
        client = s.accept()
        yield client

# 使用连接
for c, a in receive_connections(("", 9000)):
    c.send(b"Hello World\n")
    c.close()

```

### 提供消息

接收 UDP 消息序列：

```python
import socket

# 生成消息
def receive_messages(addr, maxsize):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(addr)
    while True:
      	msg = s.recvfrom(maxsize)
        yield msg

# 使用消息
for msg, addr in receive_messages(("", 10000), 1024):
    print(msg, "from", addr)
```

## 扩展管道

很多时候我们需要同时在多个线程或是多台机器上使用管道，有办法跨进程或机器来扩展管道吗？下面我们将解决该问题。

### 跨机器扩展管道

可以像这样把生成的序列转换为**pickle**对象：

```python
def gen_pickle(source):
    for item in source:
        yield pickle.dumps(item, protocal)

def gen_unpickle(infile):
    while True:
        try:
            item = pickle.load(infile)
            yield item
        except EOFError:
            return

```

这样就可以将其方便地连接到管道或 socket 了：

```python
# 发送pickle对象
def sendto(source, addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    for pitem in gen_pickle(source):
        s.sendall(pitem)
    s.close()

# 接收pickle对象
def receivefrom(addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsocktopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    c, a = s.accept()
    for item in gen_unpickle(c.makefile("rb")):
        yield item
    c.close()

# 读取日志行并转换为记录
lines = follow(open("access-log"))
log = apache_log(lines)
sendto(log, ("", 15000))

# 从其他机器读取日志
for r in receivefrom(("", 15000)):
    print(r)
```

### 跨进程扩展管道

可以像这样使用**Queue**对象来传输管道数据：

```python
# 将生成的序列传入队列
def sendto_queue(source, thequeue):
    for item in source:
        thequeue.put(item)
    thequeue.put(StopIteration)

# 生成从队列中接收到的项
def genfrom_queue(thequeue):
    while True:
        item = thequeue.get()
        if item is StopIteration:
            break
        yield item
```

这是消费者函数，它将在自己的线程中运行：

```python
# 打印404日志
def print_404(loq_q):
    log = genfrom_queue(loq_q)
    r404 = (r for r in log if r["status"] == 404)
    for r in r404:
         print(r["host"], r["datetime"], r["request"])

# 运行消费者函数
import threading, queue
log_q = queue.Queue()
r404_thr = threading.Thread(target=print_r404, args=(log_q,))
r404_thr.start()

# 向消费者函数提供数据
lines = follow(open("access-log"))
log = apache_log(lines)
sendto_queue(log, loq_q)
```

## 数据路由

到目前为止你可以使用生成器来创建管道，并且可以跨机器和网络扩展管道。但是我们的管道只支持单个输入和单个输出，有办法能让管道输入或输出多个数据吗？

### 多数据源输入

要想让多个数据同时输入到一个管道，我们可以先把这些数据源的数据汇总到一块，就像我们之前写的这个函数一样：

```python
def gen_cat(sources):
    for src in sources:
        yield from src
```

但这样写会导致只有当某个生成器中止后下个生成器才会运行，这意味着它无法用于实时数据流。

#### 并行迭代

我们可以通过这样将多个生成器压缩到一块：

```python
z = zip(s1, s2, s3)
```

不过以这种方式写的话需要生成器是静止的，它无法再接受新的数据。

#### 多路复用

你可以使用我们之前写的多线程函数来实现[多路复用](https://en.wikipedia.org/wiki/Multiplexing)，在多个生成器数据到达的时候实时的传输数据到管道。

```python
import threading, queue
from genqueue import genfrom_queue
from gencat import gen_cat

def multiplex(sources):
    in_q = queue.Queue()
    consumers = []
    for src in sources:
        thr = threading.Thread(target=sendto_queue, args=(src, in_q))
        thr.start()
        consumers.append(genfrom_queue(in_q))
    return gen_cat(consumers)
```

这是我们到目前为止最棘手的例子。在代码中，每一个输入源都由一个线程包装并打包数据传入到共享的队列中，之后我们又为它创建了一个独立的队列数据消费者，然后把它们连接到一块就可以了。

### 广播

可以像这样消耗生成器来将数据发送到多个消费者：

```python
def broadcast(source, consumers):
    for item in source:
        for c in consumers:
            c.send(item)
```

定义消费者的 send 方法：

```python
class Consumer(object):
    def send(self, item):
        print(self, "got", item)

# 使用方式
c1, c2, c3 = Consumer(), Consumer(), Consumer()

lines = follow(open("access-log"))
broadcast(lines, [c1, c2, c3])
```

#### 网络消费者

```python
import socket, pickle

# 通过网络路由数据
class NetConsumer(object):
    def __init__(self, addr):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(addr)

    def send(self, item):
        pitem = pickle.dumps(item)
        self.s.sendall(pitem)

    def close(self):
        self.s.close()

# 使用方式
class Stat404(NetConsumer):
    def send(self, item):
        if item["status"] == 404:
            NetConsumer.send(self, item)
lines = follow(open("access-log"))
log = apache_log(lines)

stat404 = Stat404(("somehost", 15000))

broadcast(log, [stat404])
```

#### 线程消费者

```python
import queue, threading
from genqueue import genfrom_queue

class ConsumerThread(threading.Thread):
    def __init__(self, target):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.in_q = queue.Queue()
        self.target = target

    def send(self, item):
        self.in_q.put(item)

    def run(self):
        self.target(genfrom_queue(self.in_q))

# 使用方式
def find_404(log):
    for r in (r for r in log if r["status"] == 404):
        print(r["status"], r["datetime"], r["request"])

def bytes_transferred(log):
    total = 0
    for r in log:
        total += r["bytes"]
        print("Total bytes", total)

c1 = ConsumerThread(find_404)
c1.start()
c2 = ConsumerThread(bytes_transferred)
c2.start()

lines = follow(open("access-log"))
log = apache_log(lines)
broadcast(log, [c1, c2])
```

## 各种编程和调试技巧

这种数据处理管道的想法非常强大，但是当你要面对几十条广播和多路复用管道的时候阅读和调试代码就会变的异常艰难，我们下面要谈的就是这类技巧。

### 创建生成器

任何单个参数的函数都可以通过以下方式简单的变为生成器函数：

```python
def generate(func):
    def gen_func(s):
        for item in s:
          	yield func(item)
    return gen_func

# 用法
gen_sqrt = generate(math.sqrt)
for x in gen_sqrt(range(100)):
    print(x)
```

### 调试跟踪生成器

可以用创建这样一个调试函数来打印通过生成器的项：

```python
def trace(source):
    for item in source:
        print(item)
        yield item

# 用法
lines = follow(open("access-log"))

log = trace(apache_log(lines))
r404 = trace(r for r in log if r["status"] == 404)
```

### 记录生成器的最后一项

可以通过这样的方式来存储生成器的最后一项：

```python
class storelast(object):
    def __init__(self, source):
        self.source = source

   	def __next__(self):
      	item = self.source.__next__()
        self.last = item
        return item

    def __iter__(self):
      	return self

# 用法
lines = storelast(follow(open("access-log")))
log = apache_log(lines)

for r in log:
    print(r)
    print(lines.last)
```

### 关闭生成器

通过调用`.close()`方法来关闭生成器：

```python
import time

def follow(thefile):
    # 文件末尾
    thefile.seek(0, os.SEEK_END)
    while True:
      	line = thefile.readline()
        if not line:
          	time.sleep(0.1)
            continue
        yield line

# 停止方式
lines = follow(open("access-log"))
for i, line in enumerate(lines):
    print(line, end=" ")
    if i == 10:
        lines.close()
```

通过抛出`GeneratorExit`异常来关闭生成器：

```python
import time

# 允许生成器通过异常退出
def follow(thefile):
    thefile.seek(0, os.SEEK_END)
    try:
        while True:
          	line = thefile.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line
    except GeneratorExit:
      	print("Follow: Shutting down")
```

### 关闭不同线程中的生成器

你可以通过设置一个检查点来让生成器停止：

```python
def follow(thefile, shutdown=None):
    thefile.seek(0, os.SEEK_END)
    while True:
        if shutdown and shutdown.is_set():
            break
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

# 用法
import threading, signal

shutdown = threading.Event()
def sigusr1(signo, frame):
    print("Closing it down")
    shutdown.set()

lines = follow(open("access-log"), shutdown)
for line in lines:
    print(line, end=" ")
```

## 解析和打印

### 增量数据解析

生成器是一种能解析几乎所有类型增量数据的有用方法：

```python
import struct

def gen_records(record_format, thefile):
    record_size = struct.calcsize(record_format)
    while True:
        raw_record = thefile.read(record_size)
        if not raw_record:
            break
        yield struct.unpack(record_format, raw_record)

# 用法
f = open("stockdata.bin", "rb")
for name, shares, price in gen_records("<8sif", f):
    ...
```

### 像`print`一样使用`yield`

你可以用这样的方式来动态生成 I/O 输出：

```python
def print_count(n):
    yield "Hello World\n"
    yield "\n"
    yield "Look at me count to %d\n" % n
    for i in range(n):
        yield "    %d\n" % i
    yield "I'm done!\n"

# 用法
# 生成输出
out = print_count(10)

# 将它变成一个大的字符串
out_str = "".join(out)

# 写入到文件
f = open("out.txt", "w")
for chunk in out:
    f.write(chunk)

# 通过socket网络发送
for chunk in out:
    s.sendall(chunk)
```

## 协程

生成器可以通过`.send()`方法来接收值：

```python
def recv_count():
    try:
        while True:
            n = yield
            print("T-minus", n)
    except GeneratorExit:
        print("Kaboom!")

# 用法
>>>r = recv_count()
>>>r.send(None)  # 你必须先在这里调用.send(None)方法
>>>for i in range(5, 0, -1):
...    r.send(i)
...
T-minus 5
T-minus 4
T-minus 3
T-minus 2
T-minus 1
>>>r.close()
Kaboom!
>>>
```

这种类型的生成器就是[**协程**](https://en.wikipedia.org/wiki/Coroutine)，Python 书中对它的解释很少，我喜欢把它想成“接收器”或“消费者”，它会接收发送给它的值。要想让协程函数运行你必须先调用`.send(None)`方法，它会告诉函数在哪里接收第一个值。我们可以通过写一个装饰器来代替手动调用来初始化协程函数：

```python
def consumer(func):
    def start(*args, **kwargs):
        c = func(*args, **kwargs)
        c.send(None)
        return c
    return start

# 用法
@consumer
def recv_count():
    try:
        while True:
            n = yield
            print("T-minus", n)
    except GeneratorExit:
        print("Kaboom!")
```

协程通常会建立一个处理管道，与普通管道不同的是它会通过使用`.send()`方法推进来的值而不是迭代来定义。其实我们在[**广播**](/posts/python-xi-tong-cheng-xu-she-ji-zhi-sheng-cheng-qi-ji-qiao-san#yan-bo)上见过了协程，注意其中的`.send()`方法，只要消费者是协程就可以进行广播：

```python
@consumer
def find_404():
    while True:
        r = yield
        if r["status"] == 404:
            print(r["status"], r["datetime"], r["request"])

@consumer
def bytes_transferred():
    total = 0
    while True:
        r = yield
        total += r["bytes"]
        print("Total bytes", total)

lines = follow(open("access-log"))
log = apache_log(lines)
broadcast(log, [find_404(), bytes_transferred()])
```

在最后一个例子中有多个消费者但是并不包含多线程，沿着这条思路进行探索就会看到多任务协同处理的身影，但这完全又是一个不同的教程！

## 总结

**生成器**是解决各种系统相关问题的一个非常有用的工具，你可以通过它来建立处理**管道**并创建可插入式的管道组件，甚至你还可以在不同的方向（网络、线程、协程）来对它进行扩展。但在用生成器时需要格外小心，大量的生成器组合到一起会让异常捕获变得十分艰难，因此在使用生成器的时候你需要特别关注代码调试、代码可靠性和其他问题。
