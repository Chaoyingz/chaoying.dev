本文翻译自[**cbeams**](https://cbea.ms/author/cbeams/)编写的[《How to Write a Git Commit Message》](https://cbea.ms/git-commit/)一文。
{: #source }

## 为什么好的提交信息很重要？

如果你浏览任意一个 Git 仓库的日志，你可能会发现它的提交信息或多或少是一团糟。来看看我早期在 Spring 的提交记录：

```bash
$ git log --oneline -5 --author cbeams --before "Fri Mar 26 2009"

e5f4b49 Re-adding ConfigurationPostProcessorTests after its brief removal in r814...
2db0f12 fixed two build-breaking issues: + reverted ClassMetadataReadingVisitor...
147709f Tweaks to package-info.java files
22b25e0 Consolidated Util and MutableAnnotationUtils ...
7f96f57 polishing
```

将其与来自同一个仓库最近的提交进行比较：

```bash
$ git log --oneline -5 --author pwebb --before "Sat Aug 30 2014"

5ba3db6 Fix failing CompositePropertySourceTests
84564a0 Rework @PropertySource early parsing logic
e142fd1 Add tests for ImportSelector meta-data
887815f Update docbook dependency and generate epub
ac8326d Polish mockito usage
```

你更想读哪个？
前者长度和样式各不相同，后者简洁而一致；前者是默认情况下发生的，后者是有意为之的。

虽然许多 Git 仓库的日志看起来像前者，但也有例外，Linux 内核和 Git 自己就是很好的例子。看看 Spring Boot 任何 Tim Pope 管理的仓库。

这些 Git 仓库的贡献者知道，一个精心制作的提交信息是向其他开发人员传递如何更新内容的最佳方式（对他们未来的自己也如此）。diff 会告诉你更改了什么，但是只有提交信息才能正确的告诉你为什么更改。Peter Hutterer 很好的阐述了这一点：

> 重新建立一段代码的上下文是一种浪费。我们不能完全避免它，所以应该努力地减少它。提交信息可以完成做到这一点，因此可以从提交消息看出开发人员是否是一个好的协作者。

如果你还没有仔细考虑过什么是一个好的 Git 提交信息，那么可能是因为你没有花太多时间和 Git 日志打交道。这是一个恶性循环：因为历史提交记录是非结构化且不一致的，所以人们不会花太多时间使用或关注它。因为它没有被使用所以它依旧会是无结构或不一致的。

但精心维护的 git 日志是一种非常美妙的东西。`git blame`、`reveert`、`rebase`、`log`、`shortlog`和其他命令都会因此变的有意义起来。审查别人的提交和拉请求变成了一件值得做的事情，并且这些工作突然之间可以独立完成了。了解为什么一些事情发生在几个月前或几年前是可能的，而且是有效的。

项目的长期成功依赖于其可维护性，而维护者很少有比项目日志更强大的工具。
花时间去学习如何好好使用它是值得的。一开始可能很麻烦的事情很快就会变成习惯，最终成为了所有参与者的骄傲和生产力的源泉。

大多数编程语言对于什么是惯用风格都有明确的约定，例如命名和格式等。当然，这些惯例有很多变化，但是大多数开发者都同意选择一个规则并坚持它远比每个人都做自己的事情所带来的混乱要好的多。

团队处理提交日志的方法也应该如此。为了创建一个有用的修订历史，团队应该首先就提交消息约定达成一致，该约定至少定义了以下三件事：

-   **风格**：标记语法、换行边距、语法、大写、标点符号。把这些事情讲清楚，去掉猜测，让一切尽可能的简单。最终的结果将是一个非常一致的日志，而不是一个看起来有但没人真正读的东西。

-   **内容**：提交信息的主体（如果有的话）应该包含什么类型的信息？或者不应该包含什么？

-   **元数据**：应该如何发布问题跟踪 ID，拉取请求号？

幸运的是，对于 Git 提交消息的惯例已经有一些成熟的约定。实际上其中许多都是以某些 Git 命令的方式运行的，你不需要再发明什么。只要遵循下面的 7 条规则，你就可以轻松地创建一个有用的日志。

## 好提交信息的 7 条规则（以下句子将动词提前来对应英文祈使句）

1. 分割标题和正文用标题
2. 限制标题行的长度为 50 个字符
3. 大写标题行首字母
4. 不要以句号结束标题行
5. 使用祈使句在标题行
6. 限制正文每行在 72 个字符内
7. 用正文解释*什么*、*为什么*和*怎样*

例如：

```
Summarize changes in around 50 characters or less

More detailed explanatory text, if necessary. Wrap it to about 72
characters or so. In some contexts, the first line is treated as the
subject of the commit and the rest of the text as the body. The
blank line separating the summary from the body is critical (unless
you omit the body entirely); various tools like `log`, `shortlog`
and `rebase` can get confused if you run the two together.

Explain the problem that this commit is solving. Focus on why you
are making this change as opposed to how (the code explains that).
Are there side effects or other unintuitive consequences of this
change? Here's the place to explain them.

Further paragraphs come after blank lines.

 - Bullet points are okay, too

 - Typically a hyphen or asterisk is used for the bullet, preceded
   by a single space, with blank lines in between, but conventions
   vary here

If you use an issue tracker, put references to them at the bottom,
like this:

Resolves: #123
See also: #456, #789
```

## 1. 分割标题和正文用标题

`git commit`的 manpage 可以看到：

> 虽然不是必需的，但是最好在提交信息的开头用一个简单的（少于 50 个字符）行总结更改，然后是一个空行，然后是一个更全面的描述。提交信息中的第一个空行之前的文本被视为提交标题，该标题会在整个 Git 中使用。例如 Git-format-patch 将可以将提交转换为 email，他在邮件的 subject 中使用这个标题，在正文中使用提交的其他部分。

首先不是每个 commit 都需要一个 subject 和一个 body。有时一行代码就可以了，特别是当更改非常简单，不需影响上下文。例如：

```bash
Fix typo in introduction to user guide
```

没必须再多写什么，如果读者想知道更改了什么错别字，他可以简单地查看 commit 本身，即使用`git show`、`git diff`或`git log -p`。

如果你要再命令行提交类似的东西，使用`-m`选项来`git commit`是很方便的：

```bash
$git commit -m "Fix typo in introduction to user guide"
```

然而，当提交需要一些解释和上下文时，你需要编写正文。例如：

```bash
Derezz the master control program

MCP turned out to be evil and had become intent on world domination.
This commit throws Tron's disc into MCP (causing its deresolution)
and turns it back into a chess game.
```

用`-m`选项写带有正文的提交信息并不容易。你最好在合适的编辑器中编写消息。如果你还没有在命令行设置一个用于 Git 的编辑器，请阅读[Git Pro 的这一部分](https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration)。

在任何情况下将标题和正文分开都是很好的。这是完整的日志：

```bash
$git log
commit 42e769bdf4894310333942ffc5a15151222a87be
Author: Kevin Flynn <kevin@flynnsarcade.com>
Date:   Fri Jan 01 00:00:00 1982 -0200

 Derezz the master control program

 MCP turned out to be evil and had become intent on world domination.
 This commit throws Tron's disc into MCP (causing its deresolution)
 and turns it back into a chess game.
```

现在`git log --oneline`命令只会显示标题行了：

```bash
$git log --oneline
42e769 Derezz the master control program
```

或者使用`git shortlog`命令会将用户的提交分组，为了简洁，它只显示标题：

```bash
$git shortlog
Kevin Flynn (1):
      Derezz the master control program

Alan Bradley (1):
      Introduce security program "Tron"

Ed Dillinger (3):
      Rename chess program to "MCP"
      Modify chess program
      Upgrade chess program

Walter Gibbs (1):
      Introduce protoype chess program
```

在 Git 中还有许多其他地方需要区分标题行和正文，但如果没有中间的空行他们都不能正常工作。

## 2. 限制标题行的长度为 50 个字符

50 个字符并不是一个硬性限制，只是一个经验法制。将标题行保持在这样的长度内可以确保它们的可读性，并迫使作者思考一下如何用最简洁的方式来解释内容。

> 提示：如果你觉得很难总结那么意味着你一次提交了太多变更内容。要争取[原子提交](https://www.freshconsulting.com/atomic-commits/)。

GitHub 的界面完全体现了这一点。如果超过了 50 个字符它会警告你，并将用省略号截断超出 72 个字符的标题行。所以你可以用 50 个字符，但 72 个字符是硬性限制。

## 3. 大写标题行首字母

这听起来很简单，标题行以大写字母开始。
例如：

-   Accelerate to 88 miles per hour

替代：

-   ~~accelerate to 88 miles per hour~~

## 4. 不要以句号结束标题行

没有必要在标题行末尾加标点。此外，当你试图将它们保持在 50 个字符或更少的时候空间是很宝贵的。
例如：

-   Open the pod bay doors

替代：

-   ~~Open the pod bay doors.~~

## 5. 使用祈使句在标题行

祈使句是指：“口语或书面用语，好像在发出命令或指示”。例如：

-   打扫你的房间
-   关上门
-   倒出去垃圾

你现在看到的这 7 条规则都是祈使句（例如“限制正文每行在 72 个字符内”）。

祈使句听起来有些粗鲁，这就是我们为什么不经常使用它的原因。但是祈使句非常适合做 Git 提交信息的标题行。这样做的原因是：每当 Git 代表你去创建一个提交时它本身就相当于创建了一个命令。

例如当你使用`git merge`时会默认创建一条信息：

```bash
Merge branch 'myfeature'
```

或者在使用`git revert`时：

```bash
Revert "Add the thing with the stuff"

This reverts commit cc87791524aedd593cff5a74532befe7ab69ce9d.
```

或者在 GitHub 的 pull request 点击“合并”时：

```bash
Merge pull request #123 from someuser/somebranch
```

因此，当你使用祈使句来编写提交信息时你要遵循 Git 自己的内置约定。例如：

-   重构 X 子系统
-   更新入门文档
-   去除过时的方法
-   发布版本 1.0.0

一开始这样写可能会有些尴尬。我们更习惯于使用陈述句，也就是报告事实。这就是为什么提交信息总是这样的原因：

-   ~~修复了 Y 的 bug~~
-   ~~改变了 X 的行为~~

有时提交信息也会被写为对其内容的描述：

-   ~~修复了其他错误的东西~~
-   ~~很棒的新 API 方法~~

为了消除所有疑惑，这里有一个简单的规则：

**一个正确的 Git 提交应该完成以下功能：**

-   如果应用该提交将会[标题行]

例如：

-   如果应用该提交将会*重构 X 子系统*
-   如果应用该提交将会*更新入门文档*
-   如果应用该提交将会*去除过时的方法*
-   如果应用该提交将会*发布版本 1.0.0*
-   如果应用该提交将会*合并#123 pull request*

需要注意的是如果你使用非祈使句的话是行不通的：

-   如果应用了该提交将会 ~~修复了 Y 的 bug~~
-   如果应用了该提交将会 ~~改变了 X 的行为~~
-   如果应用了该提交将会 ~~修复了其他错误的东西~~
-   如果应用了该提交将会 ~~很棒的新 API 方法~~

> 提示：祈使句的使用在标题行很重要，但当你写正文的时候可以放松这个限制。

## 6. 限制正文每行在 72 个字符内

Git 不会自动将文本换行，在编写提交信息正文时必须注意它的右边距并手动将文本换行。

建议 72 个字符的宽度，这样 Git 就有足够的空间来缩进文本，同时保持所有内容在 80 个字符以内。

一个好的文本编辑器可以在这里提供帮助。可以很方便的将 Vim 配置成这样，例如在编写提交信息的时候将文本换行限制为 72 个字符。然而传统的 IDE 在提交信息这方面的支持一直很糟糕。

## 7. 用正文解释*什么*、*为什么*和*怎样*

这个来自比特币的核心提交是一个很好的例子，它解释了什么发生了变化以及为什么发生变化：

```bash
commit eb0b56b19017ab5c16c745e6da39c53126924ed6
Author: Pieter Wuille <pieter.wuille@gmail.com>
Date:   Fri Aug 1 22:57:55 2014 +0200

   Simplify serialize.h's exception handling

   Remove the 'state' and 'exceptmask' from serialize.h's stream
   implementations, as well as related methods.

   As exceptmask always included 'failbit', and setstate was always
   called with bits = failbit, all it did was immediately raise an
   exception. Get rid of those variables, and replace the setstate
   with direct exception throwing (which also removes some dead
   code).

   As a result, good() is never reached after a failure (there are
   only 2 calls, one of which is in tests), and can just be replaced
   by !eof().

   fail(), clear(n) and exceptions() are just never called. Delete
   them.
```

看看完全不同的地方，想想作者花时间在这里提供上下文为同行和未来的提交者节省了多少时间。如果他不这样做，这些时间将会永远消失。

在大多数情况下，你可以忽略关于如何进行更改的细节。在这方面代码通常是可以自我解释的。（如果代码非常复杂，需要大量的解释，那么注释就是用来干这个的）。只要把重点放在弄清楚你最初做出这些改变的原因、现在的工作方式以及你当初决定用这种解决方式的原因就可以了。

未来感谢你的人可能就会是你自己！

## Tips

### 学会使用命令行，不要用 IDE。

由于 Git 子命令的一些原因。使用命令行是一种明智的行为。Git 非常强大，IDE 也一样但是它们的工作方式不同。我每天都在使用一个 IDE，也用过其他 IDE，但是我从没见过 IDE 的 Git 集成能比得上 Git 命令行。

IDE 和执行命令行在某些行为上是等价的，但是当你尝试通过 IDE 提交、合并、变基或进行复杂的历史分析时，一切都会崩溃。

如果你要使用 Git 的全部功能那么命令行一定是必不可少的。

请记住，无论是使用 Bash、Zsh 还是 Powershell 它们都会提供自动补全功能，它们减轻了记忆子命令和开关的痛苦。

### 阅读 Pro Git

[Pro Git](https://git-scm.com/book/en/v2)这本书可以在网上免费获取，它非常棒。
