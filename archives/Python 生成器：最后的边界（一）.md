本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'14 发表的[《Generators: The Final Frontier》](https://dabeaz.com/finalgenerator/index.html)一文。
{: #source }

这是一篇进阶教程，你需要了解以下几点：

-   Python 的核心特性
-   迭代器 / 生成器
-   装饰器
-   常见的编程模式

## 前情提要：生成器和协程

你可以通过`yield`语句来定义生成器函数：

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1
```
