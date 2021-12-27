本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'14 发表的[《Generators: The Final Frontier》](https://dabeaz.com/finalgenerator/index.html)一文。
{: #source }

## GIL

Python 线程适合 I/O 类任务。但对于计算类任务会有计算能力较弱、全局解释器锁只允许使用单个 CPU、多个 CPU 绑定任务会相互干扰等问题。
标准解决方案是用 multiprocessing 或 concurrent.futures 将任务分发给多进程池。

我们之前写的 inlined futures 就用到进程池：

```python
def fib(n):
    return 1 if n <= 2 else (fib(n-1) + fib(n-2))

pool = multiprocessing.Pool()

@inlined_future
def compute_fib(n):
    result = []
    for i in range(n):
        # 输出当前的线程
        print(threading.current_thread())
        val = yield from pool.submit(fib, i)
        result.append(val)
    return result

>>>result = run_inline_future(compute_fib(35))
<_MainThread ...>
<_MainThread ...>
<Thread(Thread-1, started daemon) ...>
<Thread(Thread-1, started daemon) ...>
...
```

进程池会涉及到一个隐藏的结果线程，获取 Future 结果时发生了阻塞：
![多进程-结果线程](https://chaoying-1258336136.file.myqcloud.com/multiprocessing-thread.png/compress "多进程-结果线程"){: alt="多进程-结果线程"}

结果线程将会读取返回值并设置相关的 Future 对象的结果然后再触发回调函数。

实际上它会在我们的 inlined_future 函数内的 yield 处把主线程和结果线程分离。所有 future 的执行都在结果线程中，这看起来有些奇怪。

### 重要的一课

如果你想使用好控制流那么你必须完全掌握它背后隐藏的细节（例如在 yield 语句部分切换线程）。

我们可以在单个线程中执行生成器：

```python
def run_inline_thread(gen):
    value = None
    exc = None
    while True:
        try:
            if exc is not None:
                value = gen.throw(exc)
            else:
                value = gen.send(value)
            try:
                value = yield value
                exc = None
            except Exception as e:
                exc = e
        except StopIteration:
            return exc.value

@inlined_future
def compute_fibs(n):
    result = []
    for i in range(n):
        print(threading.current_thread())
        val = yield from pool.submit(fib, i)
        result.append(val)
    return result

tpool = ThreadPoolExecutor(max_workers=2)
t1 = tpool.submit(run_inline_thread(compute_fibs(35)))
t2 = tpool.submit(run_inline_thread(compute_fibs(35)))
result1 = t1.result()
result2 = t2.result()
```

进程、线程和 Futures 完美的组织到了一起。

## Fake it until you make it

### Actors

协程和 Actors 之间有着惊人的相似之处。Actors 有以下特征：

-   接收消息
-   发送消息到其他 actors
-   创建新 actors
-   不共享状态（只发送消息）

那协程可以作为 actors 吗？例子：

```python
@actor
def printer():
    while True:
        msg = yield
        print("printer:", msg)

printer()
n = 10
while n > 0:
    send('printer', "Hello!")
    n -= 1
```

### 尝试 1

创建一个协程的注册表和装饰器：

```python
_registry = {}
def send(name, msg):
    _registry[name].send(msg)

def actor(func):
    def wrapper(*args, **kwargs):
        gen = func(*args, **kwargs)
        gen.__next__()
        _registry[gen.__name__] = gen
        return gen
    return wrapper

# 简单用法
@actor
def printer():
    while True:
        msg = yield
        print("printer:", msg)

printer()
n = 10
while n > 0:
    send('printer', n)
    n -= 1

# 输出
printer: 10
printer: 9
printer: 8
...
printer: 1
```

我们可以写一个循环 ping-pong 的高级用法：

```python
@actor
def ping():
    while True:
        n = yield
        print("ping:", n)
        send('pong', n + 1)

@actor
def pong():
    while True:
        n = yield
        print("pong:", n)
        send('ping', n + 1)

ping()
pong()
send('ping', 0)

# 输出
ping: 0
pong: 1
Traceback (most recent call last):
    ...
ValueError: generator already executing
```

但是这样写会报错，actors 和协程最大的区别在于：

-   并行执行
-   异步消息传递

虽然协程有一个`send()`方法但是它只是一个普通方法：

-   同步
-   涉及到调用堆栈
-   不允许递归和重入

方案一：使用线程包装生成器：

```python
class Actor(threading.Thread):
    def __init__(self, gen):
        super().__init__()
        self.daemon = True
        self.gen = gen
        self.mailbox = Queue()
        self.start()

    def send(self, msg):
        self.mailbox.send(msg)

    def run(self):
        while True:
            msg = self.mailbox.get()
            self.gen.send(msg)
```

方案二：写一个小的消息调度器

```python
_registry = {}
_msg_queue = deque()

# 将消息放入队列
def send(name, msg):
    _msg_queue.append((name, msg))

# 一有消息就执行
def run():
    while _msg_queue:
        name, msg = _msg_queue.popleft()
        _registry[name].send(msg)

# 用法
@actor
def ping():
    while True:
        n = yield
        print("ping:", n)
        send('pong', n + 1)

@actor
def pong():
    while True:
        n = yield
        print("pong:", n)
        send('ping', n + 1)

ping()
pong()
send('ping', 0)
run()

# 输出
ping: 0
pong: 1
ping: 2
pong: 3
...
```

但目前这个假的 actor 还存在俩个问题：

-   不是真正并发
-   很容易阻塞

让我们在下一节中解决该问题。
