本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'09 发表的[《A Curious Course on Coroutines and Concurrency》](https://dabeaz.com/coroutines/index.html)一文。
{: #source }

## 构建操作系统

### 第六步：I/O 等待

```python
class Scheduler(object):
    def __init__(self):
        ...
        self.read_waiting = {}
        self.write_waiting = {}
        ...

    def waitforread(self, task, fd):
        self.read_waiting[fd] = task

    def waitforwrite(self, task, fd):
        self.write_waiting[fd] = task

    def iopoll(self, timeout):
        if self.read_waiting or self.write_waiting:
            r, w, e = select.select(self.read_waiting, self.write_waiting, [], timeout)
            for fd in r:
                self.schedule(self.read_waiting.pop(fd))
            for fd in w:
                self.schedule(self.write_waiting.pop(fd))
    ...
```

轮询实际上有些棘手，你可以把它放到主循环中，但是这样可能会导致过度轮询，尤其是队列中已经有其他已就绪任务的时候。

另一种选择是将 I/O 轮训封装成单独的任务：

```python
class Scheduler(object):
    ...
    def iotask(self):
        while True:
            if self.ready.empty():
                self.iopoll(None)
            else:
                self.iopoll(0)
            yield

    def mainloop(self):
        self.new(self.iotask())
        while self.taskmap:
            task = self.ready.get()
            ...
```

#### 读/写 系统调用

```python
class ReadWait(SystemCall):
    def __init__(self, f):
        self.f = f

    def handle(self):
        fd = self.f.fileno()
        self.sched.waitforread(self.task, fd)


class WriteWait(SystemCall):
    def __init__(self, f):
        self.f = f

    def handle(self):
        fd = self.f.fileno()
        self.sched.waitforwrite(self.task, fd)
```

#### 新版本的 echo server

```python
def handle_client(client, addr):
    print("Connection from", addr)
    while True:
        yield ReadWait(client)
        data = client.recv(65536)
        if not data:
            break
        yield WriteWait(client)
        client.send(data)
    client.close()
    print("Client closed")

def server(port):
    print("Server starting")
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(("", port))
    sock.listen(5)
    while True:
        yield ReadWait(sock)
        client, addr = sock.accept()
        yield NewTask(handle_client(client, addr))


# 执行
def alive():
    while True:
        print("I'm alive!")
        yield

>>>sched = Scheduler()
>>>sched.new(alive())
>>>sched.new(server(45000))
>>>sched.mainloop()
```

你讲会发现它现在可以工作了。

## 堆栈的问题

在使用协程时你无法在某个函数的子函数内使用 yield 语句，这样会让 yield 语句失去效果。例如：

```python
def Accept(sock):
    yield ReadWait(sock)
    return sock.accept()

def server(port):
    ...
    while True:
        client, addr = Accept(sock)
        yield NewTask(handle_client(client, addr))
```

此时 server 函数中的控制流无法正常工作。

yield 语句只能用于顶层的协程函数，要解决该问题一个可用的方式是创建可挂起的子程序或函数。但是这只能在调度器的帮助下才能完成，你必须严格遵循 yield 语句和运用一个称作“蹦床”的技巧。

### 协程蹦床

一个非常简单的例子：

```python
# 子程序
def add(x, y):
    yield x + y

# 调用子程序
def main():
    r = yield add(2, 2)
    print(r)
    yield

def run():
    m = main()
    sub = m.send(None)
    result = sub.send(None)
    m.send(result)

>>>run()
4
```

在任务中的实现：

```python
class Task(object):
    def __init__(self, target):
        ...
        self.stack = []

    def run(self):
        while True:
            try:
                # 如果返回SystemCall则直接返回结果
                result = self.target.send(self.sendval)
                if isinstance(result, SystemCall): return result
                # 如果返回生成器则将当前协程放入栈中并再次循环调用子程序
                if isinstance(result, typing.Generator):
                    self.stack.append(self.target)
                    self.sendval = None
                    self.target = result
                else:
                    # 如果是从子程序中返回其他值则删除栈中最后一个元素，并设置返回值
                    if not self.stack: return
                    self.sendval = result
                    self.target = self.stack.pop()
            # 处理子程序中断
            except StopIteration:
                if not self.stack: raise
                self.sendval = None
                self.target = self.stack.pop()


# 现在阻塞的I/O就可以放入到内部函数中了
def Accept(sock):
    yield ReadWait(sock)
    yield sock.accept()

def Send(sock, buffer):
    while buffer:
        yield WriteWait(sock)
        len = sock.send(buffer)
        buffer = buffer[len:]

def Recv(sock, maxbytes):
    yield ReadWait(sock)
    yield sock.recv(maxbytes)
```

### 更好的 Echo Server

```python
def handle_client(client, addr):
    print("Connection from", addr)
    while True:
        data = yield Recv(client, 65536)
        if not data:
            break
        yield Send(client, data)
    print("Client closed")
    client.close()

def server(port):
    print("Server starting")
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(("", port))
    sock.listen(5)
    while True:
        client, addr = yield Accept(sock)
        yield NewTask(handle_client(client, addr))
```

现在你有了俩类可调用项，分别是普通 Python 函数或方法和子协程。对于后者调用和返回值必须使用 yield 语句。代码乍一看有些奇怪，你可以进一步使用非阻塞的 I/O 来封装对象：

```python
class Socket(object):
    def __init__(self, sock):
        self.sock = sock

    def accept(self):
        yield ReadWait(self.sock)
        client, addr = self.sock.accept()
        yield Socket(client), addr

    def send(self, buffer):
        while buffer:
            yield WriteWait(self.sock)
            len = self.sock.send(buffer)
            buffer = buffer[len:]

    def recv(self, maxbytes):
        yield ReadWait(self.sock)
        yield self.sock.recv(maxbytes)

    def close(self):
        yield self.sock.close()
```

### 最终的 Echo Server

```python
def handle_client(client, addr):
    print("Connection from", addr)
    while True:
        data = yield.client.recv(65536)
        if not data:
            break
        yield client.send(data)
    print("Client closed")
    yield client.close()

def server(port):
    print("Server starting")
    rawsock = socket(AF_INET, SOCK_STREAM)
    rawsock.bind(("", port))
    rawsock.listen(5)
    sock = Socket(rawsock)
    while True:
        client, addr = yield sock.accept()
        yield NewTask(handle_client(client, addr))
```

## 最后一些话

还有许多其他主题可以通过我们的调度器来进行探索：

-   任务间通信
-   阻塞操作处理（例如：查询数据库）
-   协程多任务和线程
-   错误处理

但是时间有限就不在这里说了。

Python 生成器要比普通人想象的更为强大：

-   可定制的迭代模式
-   处理管道和数据流
-   事件处理
-   协同式多任务

遗憾的是这相关的文章太少了。

### 性能

协同程序拥有良好的性能，我们在处理数据的部分看到了这一点。

### 协程 vs 多线程

我不任务在普通多任务系统中使用协程是值得的，多线程已经是一个成熟的方案了，但 Python 线程经常受到不好的评价（因为[GIL](https://en.wikipedia.org/wiki/Global_interpreter_lock)）。

### 风险

协程起源于上世纪 60 年代，然后悄然的消亡了。我认为一个可能的原因是在编程中使用协程实在太难了。

### 总结

如果你打算使用协程那么不要将编程范式混合在一起是至关重要的，yield 语句有 3 个主要用途：

-   迭代（生成数据）
-   接收数据（消费者）
-   Trap（协同式多任务处理系统）

不要试图编写包含其中一个以上操作的生成器函数。

我觉得协程就像烈性炸药，要尽量小心的存放它们。创建一个由协程、线程、子进程共同组成的程序通常会以失败告终。例如在我们的操作系统中，协程无法访问调度器的内部和任务，这就很好。
