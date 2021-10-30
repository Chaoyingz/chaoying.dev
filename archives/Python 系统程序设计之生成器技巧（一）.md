本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'08 发表的[《Generator Tricks for Systems Programmers》](https://dabeaz.com/generators/index.html)一文。
{: #source }

Python 生成器很酷，但是它是什么？它可以做什么？这就是本文章要探讨的内容。我们的目标是从**[系统程序设计](https://en.wikipedia.org/wiki/Systems_programming)**的角度来探索生成器的实际应用，其中包括文件、文件系统、网络和线程等。

## 迭代器和生成器简介

### 迭代器（Iterator）

正如你所知道的，python 有一个 for 语句，你可以使用它来遍历一个集合，并且你可能已经注意到了，它不仅可以遍历列表而且还可以遍历许多不同的对象。

```python
# 遍历字典
# 如果遍历字典，你会获取到该字典的键
>>>prices = {
...    "GOOG": 490.10,
...    "AAPL": 145.23,
...    "YHOO": 21.71
...}
>>>for key in prices:
...    print(key)
...
YHOO
AAPL
YHOO
>>>

# 遍历字符串
# 如果遍历字符串，你会获取到字符
>>>s = "Yow!"
>>>for c in s:
...    print(c)
...
Y
o
w
!
>>>

# 遍历文件
# 如果遍历文件，你会获取到行
>>>for line in open("real.txt"):
...    print(line, end='')
...
 			Real Programmers write in FORTRAN
    Maybe they do now,
    in this decadent era of
    Lite beer, hand calculators, and "user-friendly" software
    but back in the Good Old Days,
    when the term "software" sounded funny
    and Real Computers were made out of drums and vacuum tubes,
    Real Programmers wrote in machine code.
    Not FORTRAN. Not RATFOR. Not, even, assembly language.
    Machine Code.
    Raw, unadorned, inscrutable hexadecimal numbers.
    Directly.

```

许多操作都会消费一个**可迭代（iterable）**对象，如：sum(s)、min(s)、max(s)、list(s)、tuple(s)、set(s)、dict(s)或是 item in s。之所以你可以在这些不同的对象上进行迭代，是因为存在一个特定的协议。

```python
>>>items = [1, 4, 5]
>>>it = iter(items)
>>>it.__next__()
1
>>>it.__next__()
4
>>>it.__next__()
5
>>>it.__next__()
Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
StopIteration
>>>
```

for 语句的内部实现是这样的：

```python
_iter = iter(obj)  # 获取迭代器对象
while 1:
    try:
        x = _iter.__next__()  # 获取下一项
    except StopIteration:  # 没有更多项时停止
        break
    ...
```

所以任何支持 iter()方法的对象都是可迭代的，我们也可以通过自己定义对象来支持迭代操作。

```python
>>>for x in countdown(10):
...    print(x, end=" ")
...
10 9 8 7 6 5 4 3 2 1
>>>
```

如果想做到像上面这样，则需要 countdown 对象实现\_\_iter\_\_()和\_\_next\_\_()方法。

简单实现：

```python
class countdown(object):
    def __init__(self, start):
        self.start = start
    def __iter__(self):
        return countdown_iter(self.start)

class countdown_iter(object):
    def __init__(self, count):
        self.count = count
    def __next__(self):
        if self.count <= 0:
            raise StopIteration
        r = self.count
        self.count -= 1
        return r

```

在不同对象的迭代器设计中有许多不同的微妙细节，然而我们不打算讨论这些，这篇文章主要谈论的是生成器而不是迭代器。

### 生成器（Generator）

生成器是生成一个结果队列而不是单个值的函数：

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1

>>>for i in countdown(5):
...    print(i, end=" ")
...
5 4 3 2 1
>>>
```

它和普通函数有着很大的区别，调用生成器函数会创建一个生成器对象，但是它不会开始运行这个函数。

```python
def countdown(n):
    print("Counting down from", n)
    while n > 0:
      yield n
      n -= 1
    print("Counting down end")

>>>x = countdown(10)
>>>x
<generator object at 0x58490>
>>>
```

这个函数只会在调用\_\_next\_\_()方法的时候才会执行，**yield**关键字生成了一个值，但会暂停函数，直到再次调用\_\_next\_\_()方法的时候函数才会恢复。当函数运行完时迭代就会停止。

```python
>>>x.__next__()
9
>>>x.__next__()
8
...

>>>x.__next__()
1
>>>x.__next__()
Counting down end
Traceback (most recent call last):
    File "<stdin>", line 1, in ?
StopIteration
>>>
```

生成器函数可以作为编写迭代器的一种更简便的方式，你不用再关心迭代器协议（\_\_next\_\_()，\_\_iter\_\_()），它就会按预期的那样完成迭代工作。

### 生成器和迭代器的区别

生成器函数和支持迭代的对象略有不同，**生成器是一次性操作（one-time operation），你只能对生成器的数据遍历一次，如果你再想遍历它必须得再次调用生成器函数来重新创建生成器**，这和列表有着很大的不同。

### 生成器表达式

你可以像下方代码这样用类似列表推导式的方式来创建一个生成器表达式，它会遍历列表，并对列表的每一项乘以 2，但是结果只能产生一次。

```python
>>>a = [1, 2, 3, 4]
>>>b = (2 * x for x in a)
>>>b
<generator object at 0x58760>
>>>for i in b: print(b, end=" ")
...
2 4 6 8
>>>

# 小技巧：如果被用做单个函数参数则可以删除括弧
>>>sum(2 * x for x in a)
```

它和列表推导式的区别是它不会构造一个列表，它唯一的作用就是被用做迭代，一旦被消耗就无法再次使用。

在这节中我们学会了使用生成器函数和生成器表达式这两种方式来创建生成器。下面我们来探讨一下生成器的实际应用。

## 如何处理数据文件？

#### 编程问题

如何对 Apache web 服务器日志中的最后一列数据进行求和，计算出总共传输了多少字节的数据？日志文件可能会非常大（Gbytes），文件的格式如下：

```shell
81.107.39.38 - ... "GET /ply/ HTTP/1.1" 200 7587
81.107.39.38 - ... "GET /favicon.ico HTTP/1.1" 404 133
81.107.39.38 - ... "GET /ply/bookplug.gif HTTP/1.1" 200 23903
81.107.39.38 - ... "GET /ply/ply.html HTTP/1.1" 200 97238
81.107.39.38 - ... "GET /ply/example.html HTTP/1.1" 200 2359
66.249.72.134 - ... "GET /index.html HTTP/1.1" 200 4447
```

通过观察我们可以看到字节数在最后一列，可能的值为数字或缺省值（-）。

#### 迭代器方案

我们可以简单的使用 for 循环来解决该问题：

```python
with open("access-log") as wwwlog:
    total = 0
    for line in wwwlog:
        bytes_sent = line.rsplit(None, 1)[1]
        if bytes_sent != "-":
            total += int(bytes_sent)
    print("Total", total)
```

我们通过逐行遍历日志并更新求和结果，但这种方案看起来也太有年代感了，让我们试着用生成器来解决一下。

#### 生成器方案

```python
with open("access-log") as wwwlog:
    bytecolumn = (line.rsplit(None, 1)[1] for line in wwwlog)
    bytes_sent = (int(x) for x in bytecolum if x != "-")
    print("Total", sum(bytes_sent))
```

这和 for 循环版本有些不一样，生成器版本有着更少的代码和完全不同的编程风格。要理解这个方案，需要把它想成一个处理数据的管道，管道中依次排列着 access-log -> wwwlog -> bytecolumn -> bytes_sent -> sum() -> total，在代码中的每一步我们都声明了将应用于整个数据流的操作。与 for 循环聚焦于每行上的问题不同，我们把问题分解成了对整个文件的大操作（big operations）。这种编程风格叫作 **[声明式编程（Declarative Programming）](https://en.wikipedia.org/wiki/Declarative_programming)**，解决问题的关键在于要有远大的眼光。

将管道黏在一起的是发生在每一步中的迭代。计算过程在最后一步中，sum()函数消耗了从管道里拉取到的值（通过调用\_\_next\_\_()方法），最终生成了结果。

当然，生成器还有着各自各样的奇特魔力。让我们试着处理个 1.3Gb 的日志文件。传统的[awk]([AWK - 维基百科，自由的百科全书 (wikipedia.org)](https://zh.wikipedia.org/wiki/AWK))命令处理该文件需要整整 70 秒，for 循环版本需要运行 18.6 秒，而生成器版本只需要 16.7 秒。生成器不仅不慢甚至还比 for 循环快了 10%，并且它还有只需要更少代码和更容易阅读的优点。关键是我们不再需要创建庞大的临时列表，因此该解决方案不仅更快而且还可以应用于更加庞大的数据文件。

生成器解决方案借用了在不同组件之间通过管道来传输数据的概念。甚至你也可以通过将不同类型的管道组件插入到一起来共同处理数据流。这听起来有些耳熟？没错，这就是[Unix 哲学](https://en.wikipedia.org/wiki/Unix_philosophy)，Unix 哲学指通过收集有用的系统组件做为管道，并将各个管道连接到文件或相互连接，这样我们就可以用它来执行复杂的计算机任务。
