本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'14 发表的[《Generators: The Final Frontier》](https://dabeaz.com/finalgenerator/index.html)一文。
{: #source }

## Call me, maybe

首先我们来看下面这个例子：

```python
from concurrent.futures import ThreadPoolExecutor

def func(x, y):
    import time
    time.sleep(5)
    return x + y

pool = ThreadPoolExecutor(max_workers=2)
fut = pool.submit(func, 1, 2)
r = fut.result()
print("Got:", r)
```

将函数运行在独立的线程中等待结果。

### Future

future 对象是一个即将计算完成的结果，你可以等待结果返回，但是这样会阻塞调用者：

```python
>>>fut = pool.submit(func, 2, 3)
>>>fut
<concurrent.futures.Future at 0x7f8b8b8b9d60>
>>>fut.result()  # 阻塞
5
>>>
```

或者可以选择注册一个回调函数，让 future 对象在完成后触发该函数：

```python
def run():
    fut = pool.submit(func, 2, 3)
    fut.add_done_callback(result_handler)

def result_handler(fut):
    print("Got:", fut.result())
```

### futures 异常处理

当函数返回一个异常时，future 对象会自动抛出异常：

```python
>>>fut = pool.submit(func, 2, "Hello")
>>>fut.result()
...
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

我们可以在回调函数内通过`fut.result()`捕获异常：

```python
def run():
    fut = pool.submit(func, 2, 3)
    fut.add_done_callback(result_handler)

def result_handler(fut):
    try:
        print("Got:", fut.result())
    except Exception as e:
        print("Exception:", e)
```

### 回调处理

仔细观察这俩个函数，可以发现这与上下文管理器的结构非常相似。`run()`函数类似于`entry()`，`result_handler()`函数类似于`exit()`。

受`@contextmanager`的启发或许我们可以把函数写成这样：

```python
@inlined_future
def do_func(x, y):
    result = yield pool.submit(func, x, y)
    print("Got:", result)

run_inline_future(do_func)
```

这样的话就可以把回调函数去除了。

这里有俩个独立的部分，第一部分是用任务包装生成器类似`t = Task(gen)`，第二部分是实现运行时代码的`run_inline_future(gen)`。

我将继续使用线程做为例子，主要原因是因为它们很容易使用。

现在我们的问题是怎么将生成器像之前一样分成俩部分，可以这样定义一个任务类：

```python
class Task:
    def __init__(self, gen):
        self._gen = gen

    def step(self, value=None):
        # 将生成器推进到下一个yield并发送一个值
        try:
            fut = self._gen.send(value)
            # 将回调附加到future上
            fut.add_done_callback(self._wakeup)
        except StopIteration as exc:
            pass

    def _wakeup(self, fut):
        result = fut.result()
        self.step(result)

# 用法
pool = ThreadPoolExecutor(max_workers=2)
def func(x, y):
    import time
    time.sleep(5)
    return x + y

def do_func(x, y):
    result = yield pool.submit(func, x, y)
    print("Got:", result)

t = Task(do_func(2, 3))
t.step()

# 输出
Got: 5

# 多个yield
pool = ThreadPoolExecutor(max_workers=2)

def func(x, y):
    import time
    time.sleep(1)
    return x + y

def do_many(n):
    while n > 0:
        result = yield pool.submit(func, 2, 3)
        print("Got:", result)
        n -= 1

t = Task(do_many(10))
t.step()
```

异常处理：

```python
class Task:
    def __init__(self, gen):
        self._gen = gen

    def step(self, value=None, exc=None):
        try:
            # 根据exc是否为None来决定是否抛出异常
            if exc:
                fut = self._gen.throw(exc)
            else:
                fut = self._gen.send(value)
            fut.add_done_callback(self._wakeup)
        except StopIteration as exc:
            pass

    def _wakeup(self, fut):
        # 捕获异常，然后进行下一步
        try:
            result = fut.result()
            self.step(result)
        except Exception as exc:
            self.step(exc=exc)

# 用法
def do_func(x, y):
    try:
        result = yield pool.submit(func, x, y)
        print("Got:", result)
    except Exception as e:
        print("Exception:", e)

t = Task(do_func(2, "Hello"))
t.step()
```

整体看起来会有些奇怪，inlined future 完全在独立执行。

## yield from yield from yield from yield from future

### 聚焦 Future

通过观察我们可以看到任务中的生成器（`self._gen`）必须生成一个 Future 来添加回调函数。可以尝试写一个支持在几秒后执行内联 Future 的库函数：

```python
def after(delay, gen):
    yield pool.submit(time.sleep, delay)
    yield gen

# 但是这样写会报错
>>>Task(after(5, do_func(2, 3))).step()
Traceback (most recent call last):
...
AttributeError: 'generator' object has no attribute
'add_done_callback'
```

报错原因是`gen`是生成器而不是 Future，那可以手动迭代生成器就可以让它来生成需要的 Future：

```python
def after(delay, gen):
    yield pool.submit(time.sleep, delay)
    for f in gen:
        yield f

>>>Task(after(5, do_func(2, 3))).step()
Got: None
```

不幸的是结果在某个地方丢失了，当然你可以显而易见的把它改成这样：

```python
def after(delay, gen):
    yield pool.submit(time.sleep, delay)
    result = None
    try:
        while True:
            f = gen.send(result)
            result = yield f
    except StopIteration:
        pass

>>>Task(after(5, do_func(2, 3))).step()
Got: 5
```

这样我们的库函数就可以正常工作了，更好的方案是用 `yield from` 来替代 `yield`：

```python
def after(delay, gen):
    yield pool.submit(time.sleep, delay)
    yield from gen

>>>Task(after(5, do_func(2, 3))).step()
Got: 5
```

### yield from

`yield from`可以用于委托子生成器：

```python
def generator():
    ...
    yield value
    ...
    return result

def func():
    result = yield from generator()
```

`yield from`比你想象的强的多，它可以移交控制流到其他生成器，操作发生在当前 yield。

我们可以在任何地方都直接使用`yield from`吗？来看下面这个例子：

```python
def after(delay, gen):
    yield from pool.submit(time.sleep, delay)
    yield from gen

>>>Task(after(5, do_func(2, 3))).step()
Traceback (most recent call last):
...
TypeError: 'Future' object is not iterable
```

看来`yield`和`yield from`是无法相互替换的。

### 迭代 Future

但是可以通过以下方式来办到这一点：

```python
def patch_future(cls):
    def __iter__(self):
        if not self.done():
            yield self
        return self.result()
    cls.__iter__ = __iter__

from concurrent.futures import Future
patch_future(Future)
```

通过简单的生成自己并获取结果让`Future`实例可以被迭代。

事实上 Future 只做了一件事那就是 yields。

你可以写一个装饰器来对`after`函数做前置验证：

```python
import inspect
def inlined_future(func):
    assert inspect.isgeneratorfunction(func)
    return func
```

### 将 Tasks 转换为 Futures

Task 实例目前除了`step()`方法外不能做任何事情，我们可以尝试将它转换为`Future`：

```python
class Task(Future):
    def __init__(self, gen):
        self._gen = gen
        self._step()

    def step(self, value=None, exc=None):
        try:
            if exc:
                fut = self._gen.throw(exc)
            else:
                fut = self._gen.send(value)
            fut.add_done_callback(self._wakeup)
        except StopIteration as exc:
            self.set_result(exc.value)

# 获取结果
@inlined_future
def do_func(x, y):
    result = yield pool.submit(pow, x, y)
    return result

t = Task(do_func(2, 3))
t.step()
...
print("Got:", t.result())
```

你创建了一个任务来运行生成器生成 Future，任务本身也是一个 Future。

### 任务运行器

可以创建公共函数来隐藏细节：

```python
def start_inline_future(fut):
    t = Task(fut)
    t.step()
    return t

def run_inline_future(fut):
    t = start_inline_future(fut)
    return t.result()

# 用法：运行一个行内的 Future
result = run_inline_future(do_func(2, 3))
print("Got:", result)

# 用法：并行运行行内的 futures
t1 = start_inline_future(do_func(2, 3))
t2 = start_inline_future(do_func(3, 2))
result1, result2 = t1.result(), t2.result()
```

我们在线程上建立了一个基于生成器的任务系统，它会在隐藏的后台来执行 future。

### asyncio

事实上 asyncio 就是采用类似的方式来实现的，当然它还有一些事件循环的细节。下面是一些例子：

```python
# 简单实用
import asyncio

def func(x, y):
    return x + y

async def do_func(x, y):
    await async.sleep(0.1)
    return func(x, y)

loop = asyncio.get_event_loop()
result = loop.run_until_complete(do_func(2, 3))
print("Got:", result)

# echo server
import asyncio

async def echo_client(reader, writer):
    while True:
        line = await reader.readline()
        if not line:
            break
        resp = b"Got: " + line
        writer.write(resp)
    writer.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.start_server(echo_client, host="", port=8080))
loop.run_forever()
```
