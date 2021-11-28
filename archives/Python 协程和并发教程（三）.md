本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'09 发表的[《A Curious Course on Coroutines and Concurrency》](https://dabeaz.com/coroutines/index.html)一文。
{: #source }

## 构建操作系统

我们的目标是：

-   建立一个多任务操作系统
-   只使用原始 Python 代码不依赖其他库
-   不使用线程
-   不使用子进程
-   使用生成器/协程

动机：

-   最近有许多人对线程的替代品感兴趣（特别是由于[GIL](https://en.wikipedia.org/wiki/Global_interpreter_lock)）
-   非阻塞和异步 I/O
-   例如：能够同时支持数千个客户端连接的服务器
-   许多聚焦于事件驱动和**[反应器模式](https://en.wikipedia.org/wiki/Reactor_pattern)**的工作

### 第一步：定义任务

定义任务类：

```python
class Task(object):
    taskid = 0
    def __init__(self, target):
        Task.taskid += 1
        self.tid = Task.taskid  # 任务ID
        self.target = target  # 目标协程
        self.sendval = None  # 要发送的值

    def run(self):
        return self.target.send(self.sendval)
```

任务类是一个协程的包装器，它只有一个操作：`run()`，包装器的使用方式是：

```python
def foo():
    print("Part 1")
    yield
    print("Part 2")
    yield

>>>t1 = Task(foo())
>>>t1.run()
Part 1
>>>t1.run()
Part 2
>>>
```

`run()`方法将执行任务到下一个 yield 语句。

### 第二步：调度器

```python
class Scheduler(object):
    def __init__(self):
        self.ready = Queue()  # 定义准备运行的任务
        self.taskmap = {}  # 跟踪所有任务的字典（每个任务都有独立的ID）

    def new(self, target):
        # 将新任务引入调度器
        newtask = Task(target)
        self.taskmap[newtask.tid] = newtask
        self.schedule(newtask)
        return newtask.tid

    def schedule(self, task):
        # 将任务放入队列，让任务准备好运行
        self.ready.put(task)

    def mainloop(self):
        # 从任务队列拉取任务，将它们运行到下一个yield语句
        while self.taskmap:
            task = self.ready.get()
            result = task.run()
            self.schedule(task)
```

#### 第一版本的多任务：

```python
# 定义俩个任务
def foo():
    while True:
        print("I'm foo")
        yield

def bar():
    while True:
        print("I'm bar")
        yield

# 在调度器里运行它们
>>>sched = Scheduler()
>>>sched.new(foo())
>>>sched.new(bar())
>>>sched.mainloop()
I'm foo
I'm bar
I'm foo
I'm bar
I'm foo
I'm bar
```

需要重复强调的一点是**yield 语句就是 trap**。每个任务都会一直运行直到遇到下一个 yield 语句，此时调度器将获得控制权并切换到下一个任务。

但目前存在的问题是如果任务停止，调度器将崩溃。

### 第三步：任务退出

```python
class Scheduler(object):
    ...
    def exit(self, task):
        # 从任务字典中移除task
        print(f"Task {task.tid} terminated")
        del self.taskmap[task.tid]
    ...
    def mainloop(self):
        while self.taskmap:
            task = self.ready.get()
            # 捕获任务退出并清理该任务
            try:
                result = task.run()
            execpt StopIteration:
                self.exit(task)
            else:
                self.schedule(task)
```

#### 第二个版本的多任务：

```python
# 定义任务
def foo():
    for i in range(10):
        print("I'm foo")
        yield

def bar():
    for i in range(5):
        print("I'm bar")
        yield

>>>sched = Scheduler()
>>>sched.new(foo())
>>>sched.new(bar())
>>>sched.mainloop()
I'm foo
I'm bar
...
Task 2 terminated
...
Task 1 terminated
```

### 第四步：系统调用

在真实的操作系统中，traps 是应用程序请求系统服务的一种方式。在我们的代码中，调度器就是操作系统，yield 语句就是 trap。任务可以使用 yield 语句来与调度器交互。

```python
class SystemCall(object):
    # 系统调用基类，所有的系统操作都将在这个类中实现
    def handle(self):
        pass

class Scheduler(object):
    ...
    def mainloop(self):
        while self.taskmap:
            task = self.ready.get()
            try:
                # 获取任务的运行结果，如果类型为SystemCall则运行一些必要步骤
                result = task.run()
                if isinstance(result, SystemCall):
                    # 设置一些有关运行环境的属性
                    result.task = task
                    result.sched = self
                    result.handle()
                    continue
            except StopIteration:
                self.exit(task)
                continue
            self.schedule(task)

class GetTid(SystemCall):
    def handle(self):
        self.task.sendval = self.task.tid
        self.sched.schedule(self.task)

def foo():
    mytid = yield GetTid()
    for i in range(5):
        print("I'm foo", mytid)
        yield

def bar():
    mytid = yield GetTid()
    for i in range(10):
        print("I'm bar", mytid)
        yield

# 实际调用
>>>sched = Scheduler()
>>>sched.new(foo())
>>>sched.new(bar())
>>>sched.mainloop()
I'm foo 1
I'm bar 2
I'm foo 1
I'm bar 2
I'm foo 1
I'm bar 2
I'm foo 1
I'm bar 2
I'm foo 1
I'm bar 2
Task 1 terminated
I'm bar 2
I'm bar 2
I'm bar 2
I'm bar 2
I'm bar 2
Task 2 terminated
```

真正的操作系统有很强大的保护机制（例如：内存保护），应用程序无法强关联至系统内核（traps 是唯一的接口），理智起见我们将模仿这一点：

-   任务无法看到调度器
-   任务无法看到其他任务
-   yield 是唯一的外部接口

### 第五步：任务管理器

让我们来创建更多种类的系统调用和任务管理函数，任务管理函数应该有创建新任务、结束已存在任务和等待任务退出的功能，这些是线程或进程常用的操作。

#### 创建新任务

```python
class NewTask(SystemCall):
    def __init__(self, target):
        self.target = target

    def handle(self):
        tid = self.sched.new(self.target)
        self.task.sendval = tid
        self.sched.schedule(self.task)

# 用法
def bar():
    while True:
        print("I'm bar")
        yield

def sometask():
    ...
    t1 = yield NewTask(bar())
```

#### 结束现有任务

```python
class KillTask(SystemCall):
    def __init__(self, tid):
        self.tid = tid

    def handle(self):
        task = self.sched.taskmap.get(self.tid, None)
        if task:
            task.target.close()
            self.task.sendval = True
        else:
            self.task.sendval = False
        self.sched.schedule(self.task)

# 简单用法
def sometask():
    t1 = yield NewTask(foo())
    ...
    yield KillTask(t1)

# 整体用法
def foo():
    mytid = yield GetTid()
    while True:
        print("I'm foo", mytid)
        yield

def main():
    child = yield NewTask(foo())
    for i in range(5):
        yield
    yield KillTask(child)
    print("main done")

>>>sched = Scheduler()
>>>sched.new(main())
>>>sched.mainloop()
I'm foo 2
I'm foo 2
I'm foo 2
I'm foo 2
I'm foo 2
Task 2 terminated
main done
Task 1 terminated
```

#### 等待任务结束

这是个更棘手的问题，等待的任务必须将自己从运行队列中移除，这需要一些调度器方面的改动。

```python
class Scheduler(object):
    def __init__(self):
        ...
        # 定义一个将任务ID映射到待退出任务的字典
        self.exit_waiting = {}
        ...

    def exit(self, task):
        print(f"Task {task.id} terminated")
        del self.taskmap[task.id]
        # 当某个任务退出时，将其子任务传入任务队列
        for task in self.exit_waiting.pop(task.tid, []):
            self.schedule(task)

    def waitforexit(self, task, waittid):
        # 将某个任务设置为另一个任务的子任务
        if waittid in self.taskmap:
            self.exit_warting.setdefault(waittid, []).append(task)
            return True
        else:
            return False

# 系统调用
class WaitTask(SystemCall):
    def __init__(self, tid):
        self.tid = tid

    def handle(self):
        result = self.sched.waitforexit(self.task, self.tid)
        self.task.sendval = result
        if not result:
            self.sched.schedule(self.task)
```

需要注意错误处理，如果任务不存在将立即把它放入调度器。下面是用法：

```python
def foo():
    for i in range(5):
        print("I'm foo")
        yield

def main():
    child = yield NewTask(foo())
    print("Waiting for child")
    yield WaitTask(child)
    print("Child done")

>>>sched = Scheduler()
>>>sched.new(main())
>>>sched.mainloop()
Waiting for child
I'm foo 2
I'm foo 2
I'm foo 2
I'm foo 2
I'm foo 2
Task 2 terminated
Child done
Task 1 terminated
```

我们可以看到：**任务引用其他任务的唯一方法是使用调度器分配好的数字 ID**，这是一种封闭和安全的策略。它将所有任务分割开来（无内部链接），所有任务管理都将由调度器实现。下面让我们来实现一个简单的 echo sever：

```python
def handle_client(client, addr):
    # 客户端请求处理器
    print(f"Connection from {addr}")
    while True:
        data = client.recv(65536)
        if not data:
            break
        client.send(data)
    client.close()
    print("Client closed")
    yield

def server(port):
    # 服务器
    print("Server starting")
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(("", port))
    sock.listen(5)
    # 主循环，等待连接并启动一个新任务来处理客户端请求
    while True:
        client, addr = sock.accept()
        yield NewTask(handle_client(client, addr))


# 测试
def alive():
    while True:
        print("I'm alive!")

>>>sched = Scheduler()
>>>sched.new(alive())
>>>sched.new(server(45000))
>>>sched.mainloop()
I'm alive!
Server starting
```

当服务器运行时，调度器将锁定不再执行任何任务，真实的操作系统会暂停 Python 解释器会等待 I/O 操作完成，但在我们的多任务操作中这样的操作显然是不可取的，它会阻塞整个调度器。
