AWS Batch 让开发人员、科学家和工程师能够轻松高效地在 AWS 上运行成千上万个批处理计算作业。AWS Batch 可以根据提交的批处理作业的容量和特定资源需求动态提供计算资源（如 CPU 或内存优化实例）最佳的数量和类型。借助 AWS Batch，你无需安装和管理运行作业所使用的批处理计算软件或服务器集群，从而使你能够专注于分析结果和解决问题。

目录
{: .h2}

[TOC]

## AWS Batch 简介

批量计算（Batch computing）是指在多个计算实例上异步地、自动地运行作业。运行单个作业可能很简单，但当需要大规模运行多个作业，特别是有多个依赖关系的作业是很具挑战性的。这就是 AWS Batch 所解决的问题。

AWS Batch 将作业分为四个部分：

1. 作业（Jobs）：提交到 AWS Batch 的作业单元，可以是 shell 脚本、可执行文件或 Docker 镜像
2. 作业定义（Job Definition）：描述作业是如何执行的
3. 作业队列（Job Queues）：所有已提交的作业都在作业队列中
4. 计算环境（Compute Environment）：运行作业的计算资源

![AWS Batch运作流程](https://chaoying-1258336136.file.myqcloud.com/0_LhyLjfye1TUn341e.png/compress "AWS Batch运作流程")

## 创建 Batch 资源步骤

### 创建计算环境

可以选择将计算环境配置为由 AWS 管理或是你自己直接管理。如果是 AWS 管理，那么你要提供以下信息:

1. 实例类别
2. 最小和最大的 vCPUs 数量
3. 访问所需服务的 IAM 角色
4. 你所需要计算环境的 VPC、子网信息

### 创建作业队列

选择已创建的计算环境，设置作业队列的优先级，Batch 将优先为优先级整数值较大的作业队列提供计算环境。

### 创建作业定义

定义容器镜像、作业的 CPU 和内存。

### 创建作业

以作业定义为蓝本，提交新作业，其中作业分为 3 种类型：

1. 单个作业（Individual Jobs）
2. 数组作业（Array Job）：一组并行运行的作业
3. 多节点并行作业（Multi-node parallel Jobs）：可以让你将作业部署到多个集群。目前支持基于 IP 或使用节点通信的框架，如 Apache MXNet、TensorFlow、Caffe2 和 Message Passing Interface（MPI）

## 创建一个简单的 “fetch & run” AWS Batch 作业

理论讲的够多了，让我们看看实际情况吧。首先**你需要自行创建计算环境和作业队列**，并且**安装 Docker 和 AWS CLI**。

### 构建 fetch & run 的 Docker 镜像

fetch & run 的 Docker 镜像基于 Amazon Linux。它包含一个简单的脚本，该脚本读取一些环境变量，然后使用 AWS CLI 下载要执行的作业脚本（或压缩文件）。

首先，从 aws-batch-helpers 的 Github 仓库[下载](https://github.com/awslabs/aws-batch-helpers/archive/master.zip)源代码。解压下载的文件，打开“fetch-and-run”目录，这个目录保护俩个文件：

-   Dockerfile
-   Fetch_and_run.sh

Dockerfile 使用 Docker 来构建镜像。让我们看下 Dockerfile 的内容：

```Dockerfile
FROM amazonlinux:latest

RUN yum -y install unzip aws-cli
ADD fetch_and_run.sh /usr/local/bin/fetch_and_run.sh
WORKDIR /tmp
USER nobody

ENTRYPOINT ["/usr/local/bin/fetch_and_run.sh"]
```

-   FROM 行让 Docker 从[amazonlinux](https://hub.docker.com/r/_/amazonlinux/)仓库拉取基本镜像，使用 latest 标签
-   RUN 行执行一个 shell 命令，安装所需要的依赖
-   ADD 行复制 fetch_and_run.sh 脚本到容器中的/usr/local/bin 目录
-   WORKDIR 行设置/tmp 目录为使用容器的默认目录
-   USER 行设置容器的默认用户
-   最后，ENTRYPOINT 行命令 Docker 容器启动后执行/usr/local/bin/fetch_and_run.sh 脚本。当作为 AWS Batch 作业运行时可以将命令参数传递给它

现在，让我们构建 Docker 镜像！如果你已经安装了 Docker，你可以通过以下命令构建镜像（注意命令末尾的点）：

```bash
docker build -t awsbatch/fetch_and_run .
```

这个命令应该产生类似如下的输出：

```shell
Sending build context to Docker daemon 373.8 kB

Step 1/6 : FROM amazonlinux:latest
latest: Pulling from library/amazonlinux
c9141092a50d: Pull complete
Digest: sha256:2010c88ac1e7c118d61793eec71dcfe0e276d72b38dd86bd3e49da1f8c48bf54
Status: Downloaded newer image for amazonlinux:latest
 ---> 8ae6f52035b5
Step 2/6 : RUN yum -y install unzip aws-cli
 ---> Running in e49cba995ea6
Loaded plugins: ovl, priorities
Resolving Dependencies
--> Running transaction check
---> Package aws-cli.noarch 0:1.11.29-1.45.amzn1 will be installed

  << removed for brevity >>

Complete!
 ---> b30dfc9b1b0e
Removing intermediate container e49cba995ea6
Step 3/6 : ADD fetch_and_run.sh /usr/local/bin/fetch_and_run.sh
 ---> 256343139922
Removing intermediate container 326092094ede
Step 4/6 : WORKDIR /tmp
 ---> 5a8660e40d85
Removing intermediate container b48a7b9c7b74
Step 5/6 : USER nobody
 ---> Running in 72c2be3af547
 ---> fb17633a64fe
Removing intermediate container 72c2be3af547
Step 6/6 : ENTRYPOINT /usr/local/bin/fetch_and_run.sh
 ---> Running in aa454b301d37
 ---> fe753d94c372

Removing intermediate container aa454b301d37
Successfully built 9aa226c28efc
```

当你运行以下命令时，你应该会看到一个叫 fetch_and_run 的新本地镜像。

```bash
docker images
```

```shell
REPOSITORY               TAG              IMAGE ID            CREATED             SIZE
awsbatch/fetch_and_run   latest           9aa226c28efc        19 seconds ago      374 MB
amazonlinux              latest           8ae6f52035b5        5 weeks ago         292 MB
```

要添加更多包到镜像，你可以更新 RUN 行或者在它的后面再添加一行。

### 创建 ECR 储存库

下一步是创建一个 ECR 储存库来存储 Docker 镜像，这样 AWS Batch 就可以在运行作业时检索它。

1. 在[ECR 控制台](https://console.aws.amazon.com/ecs/home?region=us-east-1)，选择**开始**或**创建存储库**
2. 输入储存库的名称，例如：awsbatch/fetch_and_run
3. 选择**下一步**

你可以保持控制台打开，它的提示可能会有帮助。

### 把构建好的镜像推到 ECR

现在你已经有了一个 Docker 镜像和一个 ECR 存储库，是时候将镜像推到存储库了。如果你使用了前面的示例名称，请使用以下的 AWS CLI 命令。将**ACCOUNT**替换为你自己的账户。

```bash
aws ecr get-login --region us-east-1

docker tag awsbatch/fetch_and_run:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/awsbatch/fetch_and_run:latest

docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/awsbatch/fetch_and_run:latest
```

### 在 S3 创建一个简单的作业脚本

接下来，创建并上传一个简单的作业脚本，该脚本将在你刚刚在 ECR 中构建并注册的 fetch_and_run 镜像中执行。首先创建一个名为 myjob.sh 的文件，内容如下：

```sh
#!/bin/bash
date
echo "Args: $@"
env
echo "This is my simple test job!."
echo "jobId: $AWS_BATCH_JOB_ID"
echo "jobQueue: $AWS_BATCH_JQ_NAME"
echo "computeEnvironment: $AWS_BATCH_CE_NAME"
sleep $1
date
echo "bye bye!!"
```

上传脚本到 S3 存储桶。

```she
aws s3 cp myjob.sh s3://<bucket>/myjob.sh
```

### 创建 IAM 角色

当 fetch_and_run 镜像作为 AWS Batch 作业运行时，它需要从 Amazon S3 获取脚本。你需要一个 IAM 角色，AWS Batch 作业可以使用该角色访问 S3。

1. 在[IAM 控制台](https://console.aws.amazon.com/iam/home?region=us-east-1)，选择**角色**，**创建新角色**
2. 在可信实体项选择**AWS 服务**，然后选择**弹性容器服务**。案例中选择**弹性容器服务任务**，然后选择**下一步：权限**
3. 在**附加策略**页，Filter 框中输入“AmazonS3ReadOnlyAccess”，然后选择该策略复选框。然后选择**下一步：确认**
4. 输入新角色名称，例如：batchJobRole 并选择**创建角色**，你可以看到新角色的详情。

### 创建作业定义

现在我们已经创建了所有必要的资源，将所有内容放在一起并构建一个作业定义，你就可以使用该作业定义来运行一个或多个 AWS Batch 作业。

1. 在[AWS Batch 控制台](https://console.aws.amazon.com/batch/home?region=us-east-1)，选择**作业定义**，点**创建**
2. **作业定义名称**行，输入一个定义名称，例如：fetch_and_run
3. **IAM 角色**行，选择你之前创建好的角色，batchJobRole
4. **ECR 存储库地址**行，输入 fetch_and_run 镜像推送到的地址，例如 012345678901.dkr.ecr.us-east-1.amazonaws.com/awsbatch/fetch_and_run
5. 将**Command**字段留空
6. **vCPUs**行输入 1，**内存**行输入 500
7. **用户**行输入“nobody”
8. 选择**创建作业定义**

### 提交并运行作业

现在，提交并运行一个使用 fetch_and_run 镜像的作业来下载脚本并执行。

1. 在[AWS Batch 控制台](https://console.aws.amazon.com/batch/home?region=us-east-1)，选择**作业**，**提交作业**
2. 输入作业的名称，例如：script_test
3. 选择 fetch_and_run 作业定义
4. **作业队列**行选择已创建的作业队列
5. **命令**行输入“myjob.sh 60”
6. 输入以下环境变量然后**提交作业**
    - Key=BATCH_FILE_TYPE, Value=script
    - Key=BATCH_FILE_S3_URL, Value=s3:///myjob.sh（不要忘了替换为正确的文件 URL）
7. 作业完成后，检查控制台中作业的最终状态
8. 在作业详细信息页面中，你还可以选择在**CloudWatch**控制台查看该作业的日志

### fetch and run 镜像是如何工作的

fetch_and_run 镜像利用了 Docker 的 ENTRYPOINT 和提交作业时命令行中输入的内容，shell 脚本会读取环境变量并提供给 AWS Batch 作业。在构建 Docker 镜像时，他会以 Amazon Linux 为基础镜像并从 yum 仓库安装一些软件包。这就组成了作业的执行环境。

如果你要运行的脚本需要更多的包，你可以在 Dockerfile 中使用 RUN 参数添加他们。你甚至可以通过更新 FROM 参数将其更改为不同的基础镜像，例如 Ubuntu。

接下来，将 fetch_and_run.sh 脚本添加到镜像并设置为容器的 ENTRYPOINT。该脚本只读取一些环境变量，然后从 S3 下载并运行 script/zip 文件。脚本会查找 BATCH_FILE_TYPE 和 BATCH_FILE_S3_URL 环境变量。如果没找到会提示如下信息：

-   BATCH_FILE_TYPE not set, unable to determine type (zip/script) of

正确用法：

```shell
export BATCH_FILE_TYPE="script"

export BATCH_FILE_S3_URL="s3://my-bucket/my-script"

fetch_and_run.sh script-from-s3 [ <script arguments> ]
```

或

```shell
export BATCH_FILE_TYPE="zip"

export BATCH_FILE_S3_URL="s3://my-bucket/my-zip"

fetch_and_run.sh script-from-zip [ <script arguments> ]
```

这表明 BATCH_FILE_TYPE 可以为 script 或 zip 俩个值。当设置为“script”时，它会让 fetch_and_run.sh 脚本下载一个文件并执行它。如果将其设置为“zip”，它会让 fetch_and_run.sh 脚本下载一个 zip 文件，然后解压文件并根据传递的参数来执行它。

最后，ENTRYPOINT 参数告诉 Docker 在创建容器时执行/usr/local/bin/fetch_and_run.sh 脚本，此外，它会将**命令**参数的内容传递给脚本。这让你能够通过提交作业时填入的**命令**字段来控制 fetch_and_run 镜像中脚本的参数。

## 参考链接

1. [Getting started with AWS Batch. AWS Batch allow developers to build… | by Sunit Mehta | Servian](https://servian.dev/getting-started-with-aws-batch-3442446fc62)

2. [Creating a Simple “Fetch & Run” AWS Batch Job | AWS Compute Blog (amazon.com)](https://aws.amazon.com/cn/blogs/compute/creating-a-simple-fetch-and-run-aws-batch-job/)
