本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'14 发表的[《Generators: The Final Frontier》](https://dabeaz.com/finalgenerator/index.html)一文。
{: #source }

这是一篇进阶教程，阅读之前你需要了解以下几点：

-   Python 的核心特性
-   迭代器 / 生成器
-   装饰器
-   常见的编程模式

## 前情提要：生成器和协程

### 迭代

你可以通过`yield`语句来定义生成器函数：

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1
```

生成器函数可以被当做可迭代对象：

```python
for x in countdown(5):
    print("T-minus", x)
```

可以通过`next()`方法来运行生成器对象：

```python
>>>c = countdown(3)
>>>c
<generator object countdown at 0x7f8b8b8b8d10>
>>>next(c)
T-minus 3
>>>next(c)
T-minus 2
>>>next(c)
T-minus 1
>>>next(c)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
StopIteration
>>>
```

当函数返回的时候会抛出`StopIteration`异常。

用作迭代器只是生成器的一个小功能，我们可以用`yield`语句来做更多事情。

### 管道

类似于 Unix 中的 shell 管道，将几个生成器连接起来可以组成处理管道：

```python
def process(sequence):
    for s in sequence:
        ... do something with s ...
        yield item
```

这非常有用，你还可以通过`yield`语句来接收值：

```python
def receiver():
    while True:
        item = yield
        print("Got:", item)

# 你可以向这个生成器来发送值：
recv = receiver()
next(recv)  # 跳过第一个yield
recv.send("Hello")
recv.send("World")
```

### 协程和数据流

协程支持数据流风格的处理器、发布/订阅、事件仿真。

无论在什么地方只需要插入一个`yield`语句就可以定义生成器函数。通过调用生成器函数可以创建一个生成器实例：

```python
def generator():
    ...
    ... yield ...
    ...

>>>g = generator()
>>>g
<generator object generator at 0x7f8b8b8b8d10>
>>>
```

可以通过`next()`方法来返回生成器生成的值，这是在新创建的生成器上唯一被允许的操作，类似于`gen.__next__()`。

你可以用`send()`方法来向生成器发送值，然后再获取它：

```python
def generator():
    ...
    item = yield
    ...
    ...
    yield value

>>>g = generator()
>>>next(g)
>>>value = g.send(10)
10
```

### 异常处理

`gen.close()`方法可以中断生成器，它会抛出`StopIteration`异常，如果未对异常进行处理生成器会静默退出：

```python
def generator():
    try:
        yield
    except GeneratorExit:
        ...
```

如果在 yield 处产生异常，生成器将会返回下一个 yield 值：

```python
def generator():
    try:
        yield
    except RuntimeError as e:
        ...
    yield 10

>>>g = generator()
>>>next(g)
>>>val = g.throw(RuntimeError, "Broken")
10
```

生成器退出时会触发`StopIteration`异常，可以通过这个特性来获取返回值：

```python
def generator():
    yield
    return "Done"

>>>g = generator()
>>>try:
>>>   next(g)
>>>except StopIteration as e:
>>>   print(e.value)
Done
```

### 生成器委托

可以通过`yield from`语句来委托生成器：

```python
def generator():
    yield value
    return result

def func():
    result = yield from generator()
```

它允许生成器来调用另一个生成器，通过这种特性可以将多个可迭代对象组织到一块：

```python
def chain(x, y):
    yield from x
    yield from y

>>>a = [1, 2, 3]
>>>b = [4, 5, 6]
>>>for x in chain(a, b):
...     print(x)
...
1 2 3 4 5 6
>>>c = [7, 8, 9]
>>>for x in chain(a, chain(b, c)):
...     print(x)
...
1 2 3 4 5 6 7 8 9
>>>
```

### 最小示例

```python
def generator():
    ...
    yield
    ...
    return result

# 生成器实例的操作
gen = generator()
# 跳到下一个yield
next(gen)
# 向生成器发送值
gen.send(item)
# 关闭生成器
gen.close()
# 触发异常
gen.throw(exc, val, tb)
# 委托
result = yeild from gen
```

使用这些特性你可以做许多有趣的事情。

## 现在来看看完全不同的东西

### 一个共同的主题

考虑以下结构：

```python
f = open()
...
f.close()
.......................
lock.acquire()
...
lock.release()
.......................
db.start_transaction()
...
db.commit()
.......................
start = time.time()
...
end = time.time()
```

这些结构很常见，你可以在任何地方看到它们。

### 上下文管理器

`with`语句允许控制代码段的进出：

```python
with open(filename) as f:
    statement
    statement
    ...

with lock:
    statement
    statement
    ...
```

可以通过`@contextmanager`简单的来实现你自己的上下文管理器：

```python
import time
from contextlib import contextmanager

# 计算代码块多执行时间
@contextmanager
def timethis(label):
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        print('{}: {}'.format(label, end - start))

# 用法
with timethis('counting'):
    n = 1000000
    while n > 0:
        n -= 1

# 输出
counting: 0.023


# 建立临时目录
import tempfile, shutil
from contextlib import contextmanager

@contextmanager
def tempdir():
    path = tempfile.mkdtemp()
    try:
        yield path
    finally:
        shutil.rmtree(path)

# 用法
with tempdir() as path:
    ...
```

如果一个类实现了`__enter__()`和`__exit__()`方法，那么它就可以监听代码块的进入和退出:

```python
# 实现上下文管理器
class Manager(object):
    def __enter__(self):
        print('Entering')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            print('Exiting')
        else:
            print('Exiting due to exception')
            return False

# 用法
with Manager() as m:
    print('Inner block')

# 输出
Entering
Inner block
Exiting

# 自动删除零时目录
import tempfile, shutil

class TempDir(object):
    def __enter__(self):
        self.path = tempfile.mkdtemp()
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.path)

# 用法
with TempDir() as path:
    ...
```

看起来`@contextmanager`用了和上下文管理器类相似的代码，那它具体是怎么工作的呢？我们可以把`yield`语句想象成一把剪刀，它把代码块分成两部分，上半部分对应了上下文管理器的`__enter__()`方法，下半部分对应了`__exit__()`方法，`yield`是其成为可能的魔法。

这是上下文管理器的包装类：

```python
class GeneratorCM(object):
    def __init__(self, gen):
        self.gen = gen

    def __enter__(self):
        # 运行生成器至yield
        return next(self.gen)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # 运行生成器至下一yield
                next(self.gen)
            else:
                # 如果有异常，则抛出异常
                self.gen.throw(exc_type, exc_val, exc_tb)
            raise RuntimeError('generator ignored exception')
        except StopIteration:
            # 如果生成器结束，则忽略
            pass
        else:
            # 如果生成器没有结束，则抛出异常
            raise RuntimeError('generator didn\'t stop'

# 把它写成装饰器
def contextmanager(func):
    def helper(*args, **kwds):
        return GeneratorCM(func(*args, **kwds))
    return helper
```

实际的实现要比这更加复杂，会有一些令人讨厌的极端情况：

-   没有相关值的异常
-   在 with 代码块中触发`StopIteration`
-   在上下文管理器中触发异常

可以阅读 [PEP-343](https://www.python.org/dev/peps/pep-0343/) 来查看更多相关内容。

为什么我会选这个例子来开头？这是一个完全不同的`yield`语句用法，它重制了控制流，并让其他人用起来更加方便。
