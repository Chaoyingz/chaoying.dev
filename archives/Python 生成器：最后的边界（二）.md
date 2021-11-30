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

或者你可以注册一个回调函数，让 future 对象在完成后触发该函数：

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

仔细观察这俩个函数，我们可以发现这与上下文管理器的结构非常相似。`run()`函数类似于`entry()`，`result_handler()`函数类似于`exit()`。

受`@contextmanager`的启发或许我们可以把函数写成这样：

```python
@inlined_future
def do_func(x, y):
    result = yield pool.submit(func, x, y)
    print("Got:", result)

run_inline_future(do_func)
```

这样的话我们就可以把回调函数去除了。

这里有俩个独立的部分，第一部分是用任务包装生成器类似`t = Task(gen)`，第二部分是实现运行时代码的`run_inline_future(gen)`。

我将继续使用线程做为例子，主要原因是因为它们很容易使用，关键是要有一些后台处理。

现在我们的问题是怎么将生成器像之前一样分成俩块，可以这样定义一个任务类：

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

整件事都很奇怪，inlined future 完全在独立执行。

## yield from yield from yield from yield from future
