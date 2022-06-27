# xxsoar

## xxsoar 介绍

**xxsoar** 安全编排 是一种通过整合`安全工具`，`安全团队`和`安全基础设施`，而使安全运营和事件响应更为流畅的方法

#### 企业面临的实际问题（为什么我们需要它？）：

1. 大量的安全事件，都需要安全分析师的介入，运营成本高，企业需要用更少的钱，来做更多的事。
2. 安全分析师的分析时间，经常被浪费在一些低级别或无关紧要的事件分析上。
3. 传统的安全响应执行过程，响应时间长，人工介入多，相关处理过程难以定量评估。
4. 人员流动，带来运营过程的变化和运营质量的变化，比如老人离职，新人进来需要培训，需要时间和经验的积累。


上述问题又可以归结为两个核心问题： 

1. 非标准化（能力和流程） 
2. 耗功夫。

为了解决这俩问题SOAR方案提出了两个核心能力：

1. Orchestration，编排（集成能力）
2. Automation (Response)，自动化(响应)

这使得人工的重复工作部分->`不同工具系统之间的交互流转`，变得可复用且易自动化。

> 当不同系统之间的交互成本让人难以负担，`合`成为了节省各方面成本的选择之一。


## 安装部署

### 环境要求

1. redis
2. mongodb
3. python3.6+

### serverless 服务

```
docker run -p 8070:8070 -v /tmp:/tmp --name nuclio-dashboard quay.io/nuclio/dashboard:stable-amd64
```
- [Getting Started with Nuclio on Kubernetes](/docs/setup/k8s/getting-started-k8s.md)
- [Getting Started with Nuclio on Google Kubernetes Engine (GKE)](/docs/setup/gke/getting-started-gke.md)
- [Getting started with Nuclio on Azure Container Services (AKS)](/docs/setup/aks/getting-started-aks.md)
- [Hands-on live Kubernetes sandbox and guiding instructions for Nuclio, free on Katacoda](https://katacoda.com/javajon/courses/kubernetes-serverless/nuclio)

### xxsoar 服务配置(settings.py)

```
DEBUG = True

# MongoDB 配置
MongoDB_URL = 'mongodb://soar:password@127.0.0.1:27017'

# Redis 配置
Redis_URL = 'redis://:password@127.0.0.1:6379/0'

# serverless 配置
FAAS_HOST = "http://127.0.0.1:8070"
```

### 服务启动
```
docker-compose -f xxsoar.yml up -d
```

### 访问地址
```
http://localhost:8000
```
