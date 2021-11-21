本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'09 发表的[《A Curious Course on Coroutines and Concurrency》](https://dabeaz.com/coroutines/index.html)一文。
{: #source }

## 协程与事件调度

### 事件处理

可以用协程来编写各种处理事件流的组件，让我们来看一个解析 XML 例子。

这是一段芝加哥交通局提供的公交车实时位置数据：

```xml
<?xml version="1.0"?>
<buses>
  <bus>
    <id>7574</id>
    <route>147</route>
    <color>#3300ff</color>
    <revenue>true</revenue>
    <direction>North Bound</direction>
    <latitude>41.925682067871094</latitude>
    <longitude>-87.63092803955078</longitude>
    <pattern>2499</pattern>
    <patternDirection>North Bound</patternDirection>
    <run>P675</run>
    <finalStop><![CDATA[Paulina & Howard Terminal]]></finalStop>
    <operator>42493</operator>
  </bus>
  <bus>
    ...
  </bus>
</buses>

```

通常来说有许多种方式来解析 XML，其中一种老派的做法是使用**SAX**。SAX 是一个事件驱动的接口，你可以这样使用它：

```python
import xml.sax

class MyHandler(xml.sax.ContentHandler):
    def startElement(self, name, attrs)
        print("startElement", name)
    def endElement(self, name):
      	print("endElement", name)
    def characters(self, text):
      	print("characters", repr(text))[:40]

xml.sax.parse("bus.xml", MyHandler())
```

人们使用它的原因是它可以处理巨大的 XML 文件而无需占用过多内存，但是事件驱动的特性让它变得非常笨拙。我们可以这样将 SAX 事件分发到协程中，尝试用协程来处理事件：

```python
import xmlsax

# handler将start、text、end发送到协程中
class EventHandler(xml.sax.ContentHandler):
    def __init__(self, target):
      	self.target = target
    def startElement(self, name, attrs):
      	self.target.send(("start", (name, attrs._attrs)))
    def characters(self, text):
      	self.target.send(("text", text))
    def endElement(self, name):
      	self.target.send(("end", name))

@coroutine
def buses_to_dicts(target):
    while True:
      	event, value = yield
        # 查找用bus开头的元素
        if event == "start" and value[0] == "bus":
          	busdict = {}
            fragments = []
            while True:
              	event, value = (yield)
                if event == "start": fragments = []
                if event == "text": fragments.append(value)
                if event == "end":
                  	if value != "bus":
                      	busdict[value] = "".join(fragments)
                    else:
                      	target.send(busdict)
                        break
```

你可以这样过滤字典字段：

```python
@coroutine
def filter_on_field(fieldname, value, target):
    while True:
      	d = yield
        if d.get(fieldname) == value:
          	target.send(d)

# 用法
filter_on_field("route", "22", target)
filter_on_field("direction", "North Bound", target)
```

你可以这样处理元素：

```python
@coroutine
def bus_locations():
    while True:
        bus = yield
        print("{route}, {id}, {direction}, {latitude}, {longitude}".format(**bus))
```

将它们组织到一起，例如你可以通过这样找到所有向北的 22 路公交车：

```python
xml.sax.parse(
    "bus.xml",
    EventHandler(
        filter_on_field("route", "22",
        filter_on_field("direction", "North Bound",
        bus_locations()))
    ))
```

我之所以选 XML 做例子的原因是协程可以将数据源推到任何地方而不需要重写处理阶段的代码。假设 SAX 的速度还不够快，我们还可以用 expat 来代替它：

```python
import xml.parsers.expat

def expat_parse(f, target):
    parse = xml.parsers.expat.ParserCreate(),
    parser.buffer_size = 65536
    parser.buffer_text = True
    parser.returns_unicode = False
    parser.StartElementHandler = lambda name, attrs: target.send(("start", (name, attrs)))
    parser.EndElementHandler = lambda name: target.send(("end", name))
    parser.CharacterDataHandler = lambda data: target.send(("text", data))
    parser.ParseFile(f)

# 用法
expat_parse(open("bus.xml"),
    buses_to_dicts(
        filter_on_field("route", "22",
        filter_on_field("direction", "North Bound",
        bus_locations()
    ))
)
```

在没有改变处理阶段代码的情况下，处理速度足足快了 80%。

## 从数据处理到并行编程

到目前为止我们介绍了这些知识点：

-   协程相似于生成器
-   你可以创建一系列处理组件并把它们连接到一起
-   你可以通过建立管道、数据流来处理数据
-   你可以使用协程来处理棘手的问题（事件驱动系统）

它们都有一些共同的主题：

-   发送数据到协程
-   发送数据到线程（通过队列）
-   发送数据到处理器（通过消息）

你可以通过将协程打包进线程或分发到额外的子进程来实现并行。对于协程来说你可以将任务的实现与执行环境区分开来，协程就是实现，线程或子进程就是执行环境。

创建大量的协程、线程、进程可能是建立不可维护应用的好办法（或许它可以提升你工作的安全感 🐶），并且它有可能会让你的程序变的更慢，你需要仔细研究这个问题来确定这些是否是解决问题的好方案。

## 像任务一样使用协程

在并发编程中通常将问题细分为任务，任务通常包含以下特征：

-   独立的控制流
-   存在内部状态
-   可以被暂停或恢复
-   可以与其他任务进行沟通

协程可以作为任务吗？让我们从这几个特征出发来分别看一下：

```python
@coroutine
def grep(pattern):
  	# pattern和line是局部变量可以视为内部状态
    print("Looking for {}".format(pattern))
    while True:
        line = yield  # 可以通过yield语句来与其他协程交互
        if pattern in line:  # 控制流
            print(line)
# 协程可以暂停或恢复，yield语句会暂停函数，send方法可以恢复函数，close方法可以退出函数
```

从这些方面我们可以清楚的认识到：协程可以被看作是任务。你能在不使用线程或子进程的情况下来实现多任务处理吗？我们会在后边的章节介绍该方法。

## 操作系统速成课

对于 CPU 来说程序就是一系列指令，它会逐个运行每条指令。CPU 对多任务处理一无所知，应用程序也是如此。**操作系统**会处理一切。

正如你所知道的一样，操作系统负责在计算机上运行程序。但是我们知道：操作系统允许在同一时间运行多个程序。它会在多个任务间快速切换来做到这一点，但具体是怎么实现的呢？

### Interrupts 和 Traps

操作系统通常会用俩种方式来获得控制权：

-   **Interrupts** - 硬件相关的信号（数据接收、计时器、按键等）
-   **Traps** - 软件生成的信号

在这俩种情况下 CPU 都会暂时挂起并运行操作系统的一部分代码，这时操作系统可能会切换任务。

底层系统调用实际上就是 traps，它是一个特殊的 CPU 指令，当 trap 指令执行时，程序就会在该点暂停执行，操作系统就接管了这一切。

操作系统将应用程序放到 CPU 上运行直到遇到了 trap，此时程序会暂停执行，操作系统开始运行。

![多任务切换](https://chaoying-1258336136.file.myqcloud.com/mutitask.png/compress "操作系统多任务切换")

yield 语句其实就是一种 trap，当生成器函数遇到 yield 语句时，它就会立即暂停执行。如果你把 yield 看作是 trap 我们就可以用它来建立多任务操作系统。
