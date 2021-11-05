本文翻译自[**David Beazley**](https://dabeaz.com/about.html)在 PyCon'09 发表的[《A Curious Course on Coroutines and Concurrency》](https://dabeaz.com/coroutines/index.html)一文。
{: #source }

## 协程与事件调度

### 事件处理

协程可以编写各种处理事件流的组件，让我们来看一个解析 XML 例子。

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
        # 查找使用<bus>开头的元素
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
