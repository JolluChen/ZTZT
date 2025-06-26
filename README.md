# 🏢 ZTZT 企业级 AI 中台解决方案

> 一个完整的企业级 AI 中台架构，提供从开发到生产的全栈解决方案，支持微服务、容器化部署、GPU 加速推理和完整的监控体系。集成 Dify AI 平台，提供强大的 AI 应用构建能力。

## ⚠️ 重要声明

**本项目采用专有软件许可证，仅供学习和研究使用，严禁商业使用、分发或修改。使用前请仔细阅读 [LICENSE](LICENSE) 文件。**

## 🎯 项目概述

ZTZT 是一个企业级的 AI 中台项目，旨在为企业提供完整的人工智能基础设施和服务平台。项目采用现代化的微服务架构，支持多种部署方式，集成了 Dify AI 平台，提供从开发、测试到生产的完整解决方案。

### 🌟 最新特性 (v2025.6)

- 🤖 **Dify AI 平台集成**: 内置 Dify AI 应用构建平台，支持对话、工作流、智能体
- 🔧 **端口冲突解决**: 智能端口管理，AI中台(80) + Dify(8080) 完美协同
- 🎯 **环境管理系统**: 开发/生产环境一键切换，自动配置IP地址
- 🚀 **统一访问入口**: 通过端口80提供AI中台统一访问入口
- 📊 **增强监控**: 完整的服务监控和日志管理

### 🏗️ 架构特点

- **🔧 微服务架构**: 基于 Docker 和 Kubernetes 的容器化部署
- **🤖 AI 平台集成**: 内置 Dify AI 平台，支持 AI 应用快速构建
- **🚀 快速部署**: 提供多种环境的一键部署方案
- **🎯 智能环境管理**: 开发/生产环境零配置切换
- **📊 完整监控**: Prometheus + Grafana 监控体系
- **🔥 GPU 支持**: NVIDIA GPU 加速推理服务
- **📦 模块化设计**: 可按需选择和部署不同模块
- **🌐 生产就绪**: 支持高可用、负载均衡和自动扩缩容
- **🔀 端口智能管理**: 解决服务间端口冲突，提供统一访问入口

## 🚪 系统界面截图

> 以下为中台主要界面示例截图：

- 登录页：
  
  ![中台登录页](figs/ZT_Launcher.png)

- 首页：
  
  ![中台主页](figs/ZT_Home.png)

- Django 后台管理：
  
  ![Django Admin](figs/ZT_Admin_Django.png)

## 📁 项目结构

```
ZTZT/
├── 📄 README.md                    # 项目主文档（本文件）
├── 🐍 main.py                      # 主应用入口
├── 📂 minimal-example/             # 🎯 最小化示例项目
│   ├── 🚀 quick-start.sh          # 快速启动脚本
│   ├── 🛑 stop.sh                 # 停止脚本
│   ├── 🖥️ backend/                # Django 后端服务
│   ├── 🎨 frontend/               # Next.js 前端应用
│   ├── 🐳 docker/                 # Docker 配置文件
│   │   ├── docker-compose.yml     # 基础服务配置
│   │   ├── dify-docker-compose.yml # Dify AI平台配置
│   │   ├── ai-platform-nginx.conf # AI中台统一入口配置
│   │   └── dify-nginx.conf        # Dify nginx配置
│   ├── 📊 monitoring/             # 监控配置
│   ├── 📝 scripts/                # 核心脚本目录
│   │   ├── setup-environment.sh   # 环境配置脚本（一次性）
│   │   ├── env-config.sh          # 环境管理脚本（开发/生产切换）
│   │   └── stop.sh                # 停止服务脚本
│   ├── 📖 docs/                   # 详细文档
│   │   ├── PORT_CONFLICT_RESOLUTION.md  # 端口冲突解决方案
│   │   └── environment-config.md  # 环境配置详细说明
│   ├── .env.development           # 开发环境配置模板
│   ├── .env.production            # 生产环境配置模板
│   └── .env-status/               # 环境状态标记目录
├── 🤖 dify/                       # Dify AI 平台源码
│   ├── api/                       # Dify API 服务
│   ├── web/                       # Dify Web 界面
│   ├── docker/                    # Dify Docker 配置
│   └── ...                       # 其他 Dify 组件
│   └── 📖 docs/                   # 详细文档
├── 📂 configs/                     # ⚙️ 配置文件目录
│   ├── 🐳 docker-compose/         # Docker Compose 配置
│   ├── ⛵ helm-values/            # Helm Charts 配置
│   ├── ☸️ kubernetes/             # Kubernetes 资源文件
│   └── 🔧 scripts/                # 配置脚本
├── 📂 docs/                        # 📚 项目文档
│   ├── 📋 Outline.md              # 项目文档大纲
│   ├── 🚀 deployment/             # 部署文档
│   │   ├── deployment_overview.md # 部署方案对比和选择
│   │   ├── deployment_steps.md    # 详细部署指南
│   │   ├── 01_environment_deployment/ # 基础环境配置
│   │   │   ├── 00_os_installation_ubuntu.md     # Ubuntu系统安装
│   │   │   ├── 01_container_platform_setup.md   # 容器平台配置
│   │   │   ├── 02_kubernetes_networking.md      # K8s网络配置
│   │   │   ├── 03_storage_systems_kubernetes.md # K8s存储系统
│   │   │   ├── 04_resource_management_kubernetes.md # K8s资源管理
│   │   │   └── 05_accounts_passwords_reference.md # 账号密码参考
│   │   ├── 02_server_deployment/   # 服务部署指南
│   │   │   ├── 05_database_deployment/ # 数据库部署
│   │   │   ├── 05_database_setup.md    # 数据库配置
│   │   │   ├── 06_django_rest_setup.md # Django REST配置
│   │   │   ├── 07_permission_management/ # 权限管理
│   │   │   ├── 07_permission_setup.md   # 权限配置
│   │   │   ├── 08_nodejs_setup.md       # Node.js配置
│   │   │   └── 09_python_environment_setup.md # Python环境配置
│   │   └── 03_application_deployment/ # 应用部署指南
│   │       ├── 00_application_overview.md  # 应用部署概览
│   │       ├── 01_backend_deployment.md    # 后端部署
│   │       ├── 02_frontend_deployment.md   # 前端部署
│   │       ├── 03_api_integration.md       # API集成
│   │       ├── 04_system_validation.md     # 系统验证
│   │       └── 05_deployment_checklist.md  # 部署检查清单
│   ├── 💻 development/            # 开发文档
│   │   ├── development_Plan.md    # 项目开发路线图
│   │   ├── product_development_document_enhanced.md # 详细产品设计
│   │   ├── database_design.md     # 数据库架构设计
│   │   ├── project_structure.md   # 项目组织结构
│   │   ├── implementation_steps.md # 实现步骤
│   │   └── implementation_gpu_inference_openwebui.md # GPU功能实现
│   ├── 🌐 ip/                     # 网络配置文档
│   │   ├── ip_address_ranges.md   # IP地址范围规划
│   │   ├── service_ip_port_mapping.md # 服务端口映射
│   │   └── common_ports_reference.md  # 常用端口参考
│   └── 📋 info/                   # 参考信息
│       └── accounts_passwords_ports_reference.md # 账号密码端口参考
├── 📂 monitoring/                  # 📊 监控系统
│   ├── 🔍 prometheus/             # Prometheus 配置
│   └── 📈 alertmanager/           # 告警管理
└── 📂 packages/                    # 📦 打包和分发
    ├── ⚙️ configs/                # 打包配置
    ├── 🐳 docker-images/          # Docker 镜像
    ├── ⛵ helm-charts/            # Helm 图表
    └── 💾 installers/             # 安装程序
```

## 🚀 快速开始

### 🎯 最小化示例（推荐入门）

如果你是第一次接触本项目，建议从最小化示例开始：

```bash
# 进入最小化示例目录
cd minimal-example

# 第一步：环境配置（仅首次使用）
./scripts/setup-environment.sh

# 第二步：环境切换（自动配置IP地址）
./scripts/env-config.sh dev    # 开发环境 (localhost)
# 或
./scripts/env-config.sh prod   # 生产环境 (192.168.110.88)

# 第三步：启动服务（包含 Dify AI 平台）
./quick-start.sh

# 🌐 访问服务
# AI中台统一入口: http://localhost/        (推荐)
# AI中台前端: http://localhost:3000        (直接访问)
# AI中台后端: http://localhost:8000        (直接访问)
# Dify AI平台: http://localhost:8080       (AI应用构建)
# API文档: http://localhost/swagger/
# 监控面板: http://localhost:3002
```

详细说明请查看：[minimal-example/README.md](minimal-example/README.md)

### 🔧 核心特性说明

#### 🤖 Dify AI 平台集成
- **统一管理**: 在AI中台界面中创建和管理Dify应用
- **AI应用构建**: 支持对话机器人、文本生成、工作流、智能体
- **API集成**: 完整的RESTful API支持
- **端口分离**: Dify运行在8080端口，与AI中台完美协同

#### 🎯 智能端口管理
- **端口80**: AI中台统一访问入口（nginx反向代理）
- **端口3000**: Next.js前端直接访问
- **端口8000**: Django后端直接访问  
- **端口8080**: Dify AI平台独立访问
- **无冲突**: 解决了传统端口冲突问题

#### 🔄 环境管理系统
- **一键切换**: `./scripts/env-config.sh dev/prod`
- **自动配置**: IP地址、API端点自动更新
- **配置同步**: 前端、后端、Docker配置同步
- **安全备份**: 切换前自动备份配置

### 🏗️ 完整环境部署

#### 前置要求

- **Docker** 20.10+ 和 **Docker Compose** 2.0+
- **Kubernetes** 1.24+ （可选，用于生产环境）
- **NVIDIA GPU** + **NVIDIA Container Toolkit**（可选，用于 GPU 加速）
- **Python** 3.8+ （用于工具脚本）

#### 部署方式选择

| 部署方式 | 适用场景 | 复杂度 | 功能完整度 |
|---------|----------|--------|-----------|
| **最小化示例** | 快速体验、开发测试 | ⭐ | 80% |
| **Docker Compose** | 单机部署、演示环境 | ⭐⭐ | 95% |
| **Kubernetes** | 生产环境、集群部署 | ⭐⭐⭐ | 100% |

### 📊 Docker Compose 部署

```bash
# 启动基础服务
docker compose -f configs/docker-compose/docker-compose-mongodb.yml up -d
docker compose -f configs/docker-compose/docker-compose-kafka.yml up -d

# 启动完整监控栈
cd monitoring
docker compose up -d
```

### ☸️ Kubernetes 部署

```bash
# 应用存储配置
kubectl apply -f configs/kubernetes/

# 使用 Helm 部署服务
helm install postgresql -f configs/helm-values/postgresql-values.yaml bitnami/postgresql
helm install redis -f configs/helm-values/redis-values.yaml bitnami/redis
helm install minio -f configs/helm-values/minio-values.yaml bitnami/minio

# 部署 Prometheus 监控
helm install prometheus -f configs/helm-values/prometheus-values.yaml prometheus-community/kube-prometheus-stack
```

## 🔧 核心功能

### 🎯 AI 中台核心

- **🔐 用户管理中台**: JWT 认证、RBAC 权限控制、用户生命周期管理
- **📊 数据中台**: 数据集管理、ETL 流水线、数据质量监控
- **🧠 算法中台**: 实验管理、模型训练、超参数优化
- **🤖 模型中台**: 模型注册、版本管理、A/B 测试
- **⚡ 服务中台**: API 网关、服务治理、负载均衡

### 🏗️ 基础设施

- **🐳 容器化**: Docker + Kubernetes 容器编排
- **📊 监控告警**: Prometheus + Grafana + AlertManager
- **💾 数据存储**: PostgreSQL + MongoDB + Redis + MinIO
- **🔍 日志收集**: ELK Stack（可选）
- **🌐 服务网格**: Istio（可选）

### 🔥 GPU 加速

- **⚡ 推理服务**: NVIDIA Triton Inference Server
- **🤖 LLM 支持**: Ollama + OpenWebUI
- **📊 GPU 监控**: DCGM Exporter + GPU 仪表板
- **🔧 模型管理**: 多格式模型支持（ONNX、TensorRT、PyTorch）

## 🌐 服务访问

### 最小化示例服务 (新架构)

| 服务 | 地址 | 说明 |
|------|------|------|
| **🌐 AI中台统一入口** | **http://localhost:80** | **🆕 统一访问入口 (推荐)** |
| 🎨 前端应用 (直接) | http://localhost:3000 | Next.js AI 中台管理界面 |
| 🖥️ 后端 API (直接) | http://localhost:8000 | Django REST API 服务 |
| **🤖 Dify AI平台** | **http://localhost:8080** | **🆕 AI应用构建平台** |
| 📚 API 文档 | http://localhost:80/swagger/ | Swagger 接口文档 |
| ⚙️ 管理后台 | http://localhost:80/admin/ | Django 管理后台 |
| 📊 监控面板 | http://localhost:3002 | Grafana 监控仪表板 |

> **🎯 架构优势**: 
> - **统一入口**: 端口80提供AI中台完整功能访问
> - **AI平台**: 端口8080独立运行Dify AI应用构建平台  
> - **无冲突**: 智能端口管理，各服务协同工作
> - **灵活访问**: 既可统一访问，也可直接访问各服务

### 生产环境服务

| 服务 | 地址 | 账号/密码 | 说明 |
|------|------|-----------|------|
| **🌐 AI中台统一入口** | **http://192.168.110.88:80** | admin / admin123 | **统一访问入口** |
| 🎨 前端界面 (直接) | http://192.168.110.88:3000 | admin / admin123 | Next.js Web 界面 |
| 🖥️ 后端 API (直接) | http://192.168.110.88:8000 | - | Django REST API |
| **🤖 Dify AI平台** | **http://192.168.110.88:8080** | 需初次设置 | **AI应用构建平台** |
| 📚 API文档 | http://192.168.110.88:80/swagger/ | - | Swagger API 文档 |
| ⚙️ 管理后台 | http://192.168.110.88:80/admin/ | admin / admin123 | Django 管理后台 |
| 📊 Grafana监控 | http://192.168.110.88:3002 | admin / admin123 | 监控仪表板 |
| 🔍 Prometheus | http://192.168.110.88:9090 | - | 监控数据收集 |
### 数据存储和基础服务

| 服务 | 地址 | 账号/密码 | 说明 |
|------|------|-----------|------|
| 🗄️ PostgreSQL (AI中台) | localhost:5432 | ai_user / ai_password | 主数据库 |
| 🗄️ PostgreSQL (Dify) | localhost:5433 | dify_user / dify_password | Dify专用数据库 |
| 💾 Redis (AI中台) | localhost:6379 | - | 缓存服务 |
| 💾 Redis (Dify) | localhost:6380 | - | Dify缓存 |
| 📦 MinIO Console | http://localhost:9001 | minioadmin / minioadmin | 对象存储管理界面 |
| 📦 MinIO API | http://localhost:9000 | minioadmin / minioadmin | 对象存储 API |
| 🔍 Weaviate (Dify) | http://localhost:8081 | - | 向量数据库 |

### GPU 加速服务 (可选)*

| 服务 | 地址 | 账号/密码 | 说明 |
|------|------|-----------|------|
| ⚡ Triton Server HTTP | http://localhost:8100 | - | GPU 推理服务 HTTP API |
| ⚡ Triton Server gRPC | localhost:8101 | - | GPU 推理服务 gRPC API |
| 📊 Triton Metrics | http://localhost:8102 | - | Triton 监控指标 |
| 🤖 OpenWebUI | http://localhost:3001 | admin / admin123 | LLM 交互界面 |
| 🦙 Ollama API | http://localhost:11434 | - | LLM API 服务 |
| 📊 DCGM Exporter | http://localhost:9400 | - | GPU 监控指标 |

*仅在检测到 GPU 或启用相应 profile 时启动

> **💡 端口说明**: 
> - **统一访问**: 建议使用端口80的统一入口访问AI中台功能
> - **独立平台**: Dify AI平台在端口8080独立运行，专注AI应用构建
> - **直接访问**: 各服务仍支持通过原端口直接访问
> - **端口管理**: 智能端口分配避免冲突，详见 [端口冲突解决方案](minimal-example/docs/PORT_CONFLICT_RESOLUTION.md)

## 📚 文档导航

### 📋 文档概览
- [项目文档大纲](docs/Outline.md) - 完整文档索引和概览

### 🚀 部署文档
- [部署概览](docs/deployment/deployment_overview.md) - 部署方案对比和选择指南
- [部署步骤](docs/deployment/deployment_steps.md) - 详细部署流程指南

#### 🏗️ 环境部署 (`docs/deployment/01_environment_deployment/`)
- [Ubuntu系统安装](docs/deployment/01_environment_deployment/00_os_installation_ubuntu.md) - 操作系统安装配置
- [容器平台配置](docs/deployment/01_environment_deployment/01_container_platform_setup.md) - Docker/K8s平台搭建
- [Kubernetes网络配置](docs/deployment/01_environment_deployment/02_kubernetes_networking.md) - K8s网络规划与配置
- [存储系统配置](docs/deployment/01_environment_deployment/03_storage_systems_kubernetes.md) - K8s存储解决方案
- [资源管理配置](docs/deployment/01_environment_deployment/04_resource_management_kubernetes.md) - K8s资源调度与管理
- [账号密码参考](docs/deployment/01_environment_deployment/05_accounts_passwords_reference.md) - 系统账号配置参考

#### 🖥️ 服务部署 (`docs/deployment/02_server_deployment/`)
- [数据库部署](docs/deployment/02_server_deployment/05_database_setup.md) - PostgreSQL/MongoDB/Redis部署
- [Django REST配置](docs/deployment/02_server_deployment/06_django_rest_setup.md) - 后端API服务配置
- [权限管理配置](docs/deployment/02_server_deployment/07_permission_setup.md) - RBAC权限系统配置
- [Node.js环境配置](docs/deployment/02_server_deployment/08_nodejs_setup.md) - 前端运行环境配置
- [Python环境配置](docs/deployment/02_server_deployment/09_python_environment_setup.md) - 后端Python环境配置

#### 🚀 应用部署 (`docs/deployment/03_application_deployment/`)
- [应用部署概览](docs/deployment/03_application_deployment/00_application_overview.md) - 应用架构与部署策略
- [后端应用部署](docs/deployment/03_application_deployment/01_backend_deployment.md) - Django后端部署指南
- [前端应用部署](docs/deployment/03_application_deployment/02_frontend_deployment.md) - Next.js前端部署指南
- [API集成配置](docs/deployment/03_application_deployment/03_api_integration.md) - 前后端API集成
- [系统验证测试](docs/deployment/03_application_deployment/04_system_validation.md) - 部署验证与测试
- [部署检查清单](docs/deployment/03_application_deployment/05_deployment_checklist.md) - 生产部署检查项

### 💻 开发文档
- [项目开发路线图](docs/development/development_Plan.md) - 项目规划与里程碑
- [产品设计文档](docs/development/product_development_document_enhanced.md) - 详细产品设计规范
- [数据库架构设计](docs/development/database_design.md) - 数据模型与关系设计
- [项目组织结构](docs/development/project_structure.md) - 代码组织与模块划分
- [功能实现步骤](docs/development/implementation_steps.md) - 开发实施指南
- [GPU推理功能实现](docs/development/implementation_gpu_inference_openwebui.md) - GPU加速与LLM集成

### 🌐 网络配置文档
- [IP地址范围规划](docs/ip/ip_address_ranges.md) - 网络地址分配策略
- [服务端口映射规范](docs/ip/service_ip_port_mapping.md) - 端口分配与管理规则
- [常用端口参考手册](docs/ip/common_ports_reference.md) - 标准端口使用规范

### 📋 参考信息
- [账号密码端口参考](docs/info/accounts_passwords_ports_reference.md) - 系统账号与端口快速参考

## 🛠️ 开发指南

### 本地开发环境

```bash
# 1. 克隆项目
git clone <repository-url>
cd ZTZT

# 2. 启动最小化开发环境
cd minimal-example
./quick-start.sh

# 3. 开发后端（可选）
cd backend
python manage.py runserver

# 4. 开发前端（可选）
cd frontend
npm run dev
```

## 🧪 测试和验证

### 快速验证

```bash
# 验证最小化示例
cd minimal-example
python tests/system_validation.py

# 验证 GPU 功能（如果有 GPU）
python tests/test_gpu_environment.py

# 验证 API 功能
python tests/test_complete_api.py
```

### 完整测试

```bash
# 运行所有测试
cd minimal-example
find tests/ -name "*.py" -exec python {} \;

# 系统诊断
bash scripts/diagnose_system.sh
```

## 🔧 配置管理

### 环境变量

主要配置通过环境变量管理，参考配置文件：

- `configs/docker-compose/` - Docker Compose 环境配置
- `configs/helm-values/` - Kubernetes Helm 配置
- `minimal-example/configs/` - 应用配置

### 自定义配置

```bash
# 复制配置模板
cp configs/docker-compose/docker-compose-mongodb.yml.example \
   configs/docker-compose/docker-compose-mongodb.yml

# 编辑配置
vim configs/docker-compose/docker-compose-mongodb.yml
```

## 📊 监控和运维

### 监控仪表板

- **Grafana**: http://localhost:3002 (admin/admin123)
  - 系统监控仪表板
  - GPU 监控仪表板
  - 服务监控仪表板
  - 业务监控仪表板

### 日志查看

```bash
# Docker Compose 日志
docker compose logs -f

# Kubernetes 日志
kubectl logs -f deployment/backend

# 应用日志
tail -f minimal-example/logs/*.log
```

### 健康检查

```bash
# 服务状态检查
docker compose ps

# 系统资源检查
cd minimal-example
bash scripts/diagnose_system.sh
```

## 🔥 生产部署

### 高可用配置

- **数据库集群**: PostgreSQL 主从复制 + Redis 集群
- **应用集群**: Kubernetes 多副本部署
- **负载均衡**: Nginx Ingress Controller
- **存储**: 分布式存储 + 备份策略

### 安全配置

- **网络安全**: VPC + 安全组 + 防火墙
- **数据加密**: TLS/SSL + 数据库加密
- **访问控制**: RBAC + OAuth2 + JWT
- **镜像安全**: 镜像扫描 + 签名验证

### 性能优化

- **缓存策略**: Redis 缓存 + CDN
- **数据库优化**: 索引优化 + 连接池
- **GPU 优化**: 模型量化 + 批处理
- **监控调优**: 基于监控数据的性能调优

## 🐛 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep :8000
   
   # 检查 Docker 状态
   docker system df
   docker system prune
   ```

2. **GPU 服务无法启动**
   ```bash
   # 检查 GPU 驱动
   nvidia-smi
   
   # 检查 Docker GPU 支持
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

3. **监控数据缺失**
   ```bash
   # 检查 Prometheus 目标
   curl http://localhost:9090/api/v1/targets
   
   # 重启监控服务
   docker compose restart prometheus grafana
   ```

### 获取帮助

- **Issue 提交**: [GitHub Issues](https://github.com/your-repo/ZTZT/issues)
- **文档搜索**: 查看 `docs/` 目录下的详细文档
- **社区支持**: [Discussions](https://github.com/your-repo/ZTZT/discussions)

## 📄 许可证

本项目采用 **专有软件许可证**，仅供查看和学习使用，不允许商业使用、分发或修改。

### 📋 使用限制

- ✅ **允许**: 个人学习和研究
- ✅ **允许**: 查看源代码
- ❌ **禁止**: 商业使用
- ❌ **禁止**: 二次分发
- ❌ **禁止**: 修改后发布
- ❌ **禁止**: 用于生产环境

详细许可条款请查看 [LICENSE](LICENSE) 文件。

---

## 🔗 相关链接

- [最小化示例文档](minimal-example/README.md) - 快速开始指南
- [部署文档](docs/deployment/) - 详细部署指南  
- [开发文档](docs/development/) - 开发者指南
- [监控配置](monitoring/) - 监控系统配置
- [许可证文件](LICENSE) - 使用条款和限制

**📚 如果本项目对您的学习有帮助，欢迎 star 支持！但请注意遵守许可证条款。**