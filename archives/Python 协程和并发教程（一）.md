本文翻译自**[David Beazley](https://dabeaz.com/about.html)**在 PyCon'09 发表的[《A Curious Course on Coroutines and Concurrency》](https://dabeaz.com/coroutines/index.html)一文。
{: #source }

## 生成器和协程介绍

### 生成器

生成器是生成结果序列而不是单个值的函数，通过使用`yield`关键字你可以生成一系列值。生成器与普通函数有着很大的差异，调用生成器函数会创建一个生成器对象，但是该过程并不会让函数开始运行，只有调用生成器的`__next__()`方法时它才开始运行。`yield`关键字会生成一个值并挂起函数，函数会在下一次调用`__next__()`方法时才恢复运行。

```python
# 生成器函数
def countdown(n):
    print("Counting down from", n)
    while n > 0:
        yield n
        n -= 1

# 注意调用该函数时的输出
>>>x = countdown(10)
>>>x
<generator object countdown at 0x10c58db50>
>>>

# 调用__next__()方法，函数开始执行
>>>x.__next__()
Counting down from 10
10

# 此时函数将停止运行，再次调用才会恢复
>>>x.__next__()
9
```

### 协程

你也可以这样通过使用`yield`关键字来让函数来消费值：

```python
def countdown():
    print("Counting down")
    while True:
        n = yield
        print(n)


# 还是生成器对象
>>>y = countdown()
>>>y
<generator object countdown at 0x10c58dbd0>

# 必须先使用send(None)方法来激活该语句
>>>y.send(None)
>>>y.send(10)
Counting down
10

# 依旧可以使用__next__()方法
>>>y.__next__()
None

# 可以调用close()方法来让函数退出运行
>>>y.close()
```

我们把这样的生成器称为协程函数，运行任何协程函数都必须先调用`__next__()`方法或`send(None)`方法，它会让函数执行到第一个`yield`语句来准备接收值。

尽管生成器和协程有些相似的地方，但是它们两个完全不同的概念。**生成器生产值，而协程则消费值**。

## 协程、管道和数据流

协程可以用来建立管道，你只需要将协程组织到一块，然后通过调用`send()`方法就可以向管道传入数据。协程管道需要有一个初始数据源（生产者）和一个末端，数据源通常来说不是一个协程，它用于驱动整个管道；末端负责接收发送给它的所有数据并处理它们。

下面我们来写一个简单的例子，它会模仿类型 Unix 系统`tail -f`命令的行为：

```python
import time

# 数据源
def follow(thefile, target):
    thefile.seek(0, 2)
    while True:
      	line = thefile.readline()
       	if not line:
        		time.sleep(0.1)
            continue
        target.send(line)

# 用于激活协程函数
def coroutine(func):
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        cr.__next__()
        return cr
   	return start

# 末端
@coroutine
def printer():
    while True:
      	line = yield
        print(line)

# 把他们组织到一块
f = open("access-log")
follow(f, printer())

# 你可以再加一个协程函数
@coroutine
def grep(pattern, target):
    while True:
      	line = yield
        if pattern in line:
          	target.send(line)

f = open("access-log")
follow(f, grep("python", printer()))

# 可以将迭代器和协程结合到一块来做一个广播管道
@coroutine
def broadcast(targets):
    while True:
      	item = yield
        for target in targets:
          	target.send(item)

f = open("access-log")
follow(f, broadcast([grep("python", printer()), grep("ply", printer()), grep("swig", printer())]))

# 甚至我们可以直接这样写
p = printer()
follow(f, broadcast([grep("python", p), grep("ply", p), grep("swig", p)]))
```

协程提供了比简单迭代器更强大的数据路由的可能性，你可以建立一系列简单的数据处理组件，并将它们组合到一块来形成更复杂的管道和分支。

我们可以用[面向对象设计模式](https://en.wikipedia.org/wiki/Design_Patterns)来写一个与`grep`协程函数同样功能的类：

```python
class GrepHandler:
    def __init__(self, pattern, target):
    		self.pattern = pattern
        self.target = target

    def send(self, line):
      	if self.pattern in line:
          	self.target.send(line)
```

与协程版本相比类的版本存在一些明显的缺点：

-   协程通过一个函数就可以定义

-   类版本需要定义一个类、俩个方法、可能还需要格外的基类或库导入

-   运行速度比协程更慢（因为它需要通过类的`self`方法读取变量）
