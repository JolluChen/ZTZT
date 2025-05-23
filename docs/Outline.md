# 一、中台框架

## 1. 系统层
### 1.1. 系统
- **操作系统**
  - Ubuntu 22.04 LTS

### 1.2. 容器化
- **Kubernetes**
  - 1.28.8
- **Docker**
  - 25.0.6+（启用 BuildKit 和 Containerd）
- **CRI-Dockerd**
  - 0.2.x

### 1.3. 网络
- **SDN 网络**
  - Calico
  - Cilium
  - OVN
- **Nginx 反向代理**

### 1.4. 存储
- **内容**
  - 容器数据
    - Docker、k8s 配置文件
  - 日志数据
    - 系统日志
    - Docker 日志
    - k8s 日志
    - 监控数据
  - 容器持久化数据
    - 数据库元数据
    - ……
  - 网络数据
    - 网络配置规则

- **技术**
    - **容器数据**
        - Harbor
    - **日志数据**
        - ELK Stack
        - Prometheus
    - **容器持久化数据**
        - MinIO
        - PostgreSQL
    - **网络数据**
        - Calico/Cilium 自带存储机制

### 1.5. 资源管理
#### 1.5.1. 资源可视化
- Prometheus
- Grafana

#### 1.5.2. 资源管理
##### 1.5.2.1. GPU 资源池化
- **开源**
  - NVIDIA Device Plugin
    - k8s 中动态分配 GPU 资源（适配 Docker/k8s）
  - k8s + CRI-O
- **商业**
  - 青云
  - NVIDIA Bitfusion

##### 1.5.2.2. 分层管理存储
- SSD
- HDD

#### 1.5.3. 资源权限管理

#### 1.5.4. 资源日志

### 1.6. 权限管理
#### 1.6.1. 身份认证
- 前端：Keycloak / Auth0
- 后端：Django REST Framework + JWT
- K8s：ServiceAccount 分配 Pod 访问身份，同步 Keycloak

#### 1.6.2. 权限
- **应用层**
  - Django + Django-Guardian
  - OPA (Open Policy Agent)
- **系统层**
  - K8s RBAC
  - Calico / Cilium 网络策略
- **存储层**
  - PostgreSQL 16
  - MinIO
  - Kafka
#### 1.6.3. 资源、操作权限
  - Harbor
  - MLflow + Kubeflow
  - Redis ACL
#### 1.6.4. 统一管理
  - Hashicorp Vault
  - Apache Ranger
  - UI 界面
#### 1.6.5. 权限监控
    - ELK Stack
    - Prometheus + Grafana
    - OpenTelemetry

## 2. 核心服务层
### 2.1. 后端
- Python 3.10
    - Django
        - 管理、后台界面
    - RESTful API + Django REST Framework
        - 中台之间的交互
- Node.js 18.x LTS
    - Express.js
        - 前端开发API
    - npm / yarn / pnpm
        - 包管理器
### 2.2. 数据库
- **RDBMS**
    - PostgreSQL 16（模型元数据、用户权限、系统配置、任务调度记录）
- **NoSQL**
    - MongoDB 6.0（日志数据、配置文件、临时缓存）
- **向量数据库**
    - Weaviate 1.22（Embedding、RAG）
### 2.3. 缓存
Redis 7.0
### 2.4. 消息队列
Kafka 3.6

## 3. 应用层
### 3.1. 容器编排
- Docker Compose
- Kubernetes (k8s)
### 3.2. 资源监控
Grafana
### 3.3. 中台部署

#### 3.3.1. 数据中台

1. **数据采集**
    - 数据库采集
    - 文件采集：Flume
    - 网络采集：Kafka
2. **数据存储**
    - 非结构化数据：MinIO / HDFS
    - 结构化数据：PostgreSQL 16 + pgvector
    - 向量数据：Weaviate
3. **数据处理**
    - 数据标注：
        - 文本标注：Label Studio
        - 图像标注：CVAT
        - 视频标注：VATIC
4. **数据分析**
    - 数据清洗：Pandas / OpenRefine
    - 批处理：Apache Spark
    - 流处理：Apache Flink
    - ML：Scikit-learn / XGBoost / LightGBM
    - DL：Pytorch / Tensorflow
    - 特征工程：Featuretools
5. **数据分析**
    - 统计、可视化
        - CLAP：ClickHouse
        - 日志分析：Elasticsearch + Kibana
        - 交互式分析：Apache Superset
    - 数据服务
        - FastAPI -> API
        - Apache Airflow -> 任务调度

#### 3.3.2. 算法中台
- **算法仓库**
    - Git
    - 数据/模型 版本控制：DVC
    - 实验追踪：MLflow
- **算法模型管理**
    - PyTorch
    - TensorFlow
    - Horovod
- **算法调优**
    - 超参优化：Optuna
    - 分布式超参优化(集成PyTorch、TensorFlow)：Ray Tune
    - ML流水线：Kubeflow

#### 3.3.3. 模型中台
- **内容**
    - 模型仓库
    - 模型管理
    - 模型训练
    - 模型微调
    - 模型转换
    - 模型监控
- **技术**
    - 跨平台加速推理：ONNX Runtime
    - 模型压缩(量化、蒸馏)：PyTorch Lighting
    - 模型加速：OpenVINO
    - PyTorch模型服务化：TorchServe
    - Triton Inference Serve

#### 3.3.4. 服务中台 / 应用工作台
- **内容**
    - 服务(应用)封装
    - 服务(应用)发布
    - 服务(应用)监控
- **技术**
    - 前端集成：Next.js（基于React）
    - API网关：Kong
    - 监控集成：Grafana

## 4. 用户交互层
- **React 18.x**
    - 主系统模块
    - 数据模块
    - 工作流
    - 构建工具：Webpack 5
    - UI组件库：Ant Design
- **OpenWebUI**
    - LLM 交互
    - LLM 应用
    - 本地知识库