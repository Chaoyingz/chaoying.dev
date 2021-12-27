本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'14 发表的[《Generators: The Final Frontier》](https://dabeaz.com/finalgenerator/index.html)一文。
{: #source }

## A Terrifying Visitor

### 让我们来编写一个编译器

我们从一个简单的计算开始：

```python
2 + 3 * 4 - 5
```

这个算式的解析树为：
![解析树](https://chaoying-1258336136.file.myqcloud.com/parse-tree.png/compress "解析树"){: alt="解析树"}

#### 分词

```python
import re
from collections import namedtuple

tokens = [
    r"(?P<NUM>\d+)",
    r"(?P<PLUS>\+)",
    r"(?P<MINUS>-)",
    r"(?P<TIMES>\*)",
    r"(?P<DIVIDE>/)",
    r"(?P<WS>\s+)",
]

master_re = re.compile("|".join(tokens))
Token = namedtuple("Token", ["type", "value"])

def tokenize(text):
    scan = master_re.scanner(text)
    return (Token(m.lastgroup, m.group()) for m in iter(scan.match, None) if m.lastgroup != "WS")

# 用法
text = '2 + 3 * 4 - 5'
for tok in tokenize(text):
    print(tok)

Token(type='NUM', value='2')
Token(type='PLUS', value='+')
Token(type='NUM', value='3')
Token(type='TIMES', value='*')
Token(type='NUM', value='4')
Token(type='MINUS', value='-')
Token(type='NUM', value='5')
```

#### 递归解析

```python
class Node:
    _fields = []
    def __init__(self, *args):
        for name, value in zip(self._fields, args):
            setattr(self, name, value)

class BinOp(Node):
    _fields = ["left", "op", "right"]


class Number(Node):
    _fields = ["value"]


def parse(toks):
    lookahead, current = next(toks, None), None
    def accept(*toktypes)
        nonlocal lookahead, current
        if lookahead and lookahead.type in toktypes:
            current, lookahead = lookahead, next(toks, None)
            return True

    def expr():
        term()
        while accept("PLUS", "MINUS"):
            left = BinOp(current.value, left)
            left.right = term()
        return left

    def term():
        left = factor()
        while accept("TIMES", "DIVIDE"):
            left = BinOp(current.value, left)
            left.right = factor()
        return left

    def factor():
        if accept("NUM"):
            return Number(current.value)
        else:
            raise SyntaxError("Expected NUM")
    return expr()
```
