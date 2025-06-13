# 🏢 ZTZT 企业级 AI 中台解决方案

> 一个完整的企业级 AI 中台架构，提供从开发到生产的全栈解决方案，支持微服务、容器化部署、GPU 加速推理和完整的监控体系。

## ⚠️ 重要声明

**本项目采用专有软件许可证，仅供学习和研究使用，严禁商业使用、分发或修改。使用前请仔细阅读 [LICENSE](LICENSE) 文件。**

## 🎯 项目概述

ZTZT 是一个企业级的 AI 中台项目，旨在为企业提供完整的人工智能基础设施和服务平台。项目采用现代化的微服务架构，支持多种部署方式，并提供了从开发、测试到生产的完整解决方案。

### 🏗️ 架构特点

- **🔧 微服务架构**: 基于 Docker 和 Kubernetes 的容器化部署
- **🚀 快速部署**: 提供多种环境的一键部署方案
- **📊 完整监控**: Prometheus + Grafana 监控体系
- **🔥 GPU 支持**: NVIDIA GPU 加速推理服务
- **📦 模块化设计**: 可按需选择和部署不同模块
- **🌐 生产就绪**: 支持高可用、负载均衡和自动扩缩容

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
│   ├── ⚙️ start.sh                # 完整启动脚本
│   ├── 🛑 stop.sh                 # 停止脚本
│   ├── 🖥️ backend/                # Django 后端服务
│   ├── 🎨 frontend/               # Next.js 前端应用
│   ├── 🐳 docker/                 # Docker 配置文件
│   ├── 📊 monitoring/             # 监控配置
│   └── 📖 docs/                   # 详细文档
├── 📂 configs/                     # ⚙️ 配置文件目录
│   ├── 🐳 docker-compose/         # Docker Compose 配置
│   ├── ⛵ helm-values/            # Helm Charts 配置
│   ├── ☸️ kubernetes/             # Kubernetes 资源文件
│   └── 🔧 scripts/                # 配置脚本
├── 📂 docs/                        # 📚 项目文档
│   ├── 🚀 deployment/             # 部署文档
│   ├── 💻 development/            # 开发文档
│   └── 🌐 ip/                     # 网络配置文档
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

# 一键启动所有服务
./quick-start.sh

# 访问服务
# 前端: http://localhost:3000
# 后端: http://localhost:8000
# API文档: http://localhost:8000/swagger/
```

详细说明请查看：[minimal-example/README.md](minimal-example/README.md)

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

### 最小化示例服务

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端应用** | http://localhost:3000 | AI 中台管理界面 |
| **后端 API** | http://localhost:8000 | REST API 服务 |
| **API 文档** | http://localhost:8000/swagger/ | Swagger 接口文档 |
| **管理后台** | http://localhost:8000/admin/ | Django 管理后台 |

### 完整环境服务

| 服务 | 地址 | 账号/密码 | 说明 |
|------|------|-----------|------|
| **前端界面** | http://192.168.110.88:3000 | admin / admin123 | 主要的 Web 界面 |
| **后端 API** | http://192.168.110.88:8000 | - | Django REST API |
| **API文档** | http://192.168.110.88:8000/swagger/ | - | Swagger API 文档 |
| **管理后台** | http://192.168.110.88:8000/admin/ | admin / admin123 | Django 管理后台 |
| **Grafana监控** | http://192.168.110.88:3002 | admin / admin123 | 监控仪表板 |
| **Prometheus** | http://192.168.110.88:9090 | - | 监控数据收集 |
| **PostgreSQL** | localhost:5432 | postgres / postgres | 数据库服务 |
| **Redis** | localhost:6379 | - | 缓存服务 |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin | 对象存储管理界面 |
| **MinIO API** | http://localhost:9000 | minioadmin / minioadmin | 对象存储 API |
| **Prometheus** | http://localhost:9090 | - | 监控数据收集 |
| **Grafana** | http://localhost:3002 | admin / admin123 | 监控仪表板 |
| **Triton Server HTTP** | http://localhost:8100 | - | GPU 推理服务 HTTP API* |
| **Triton Server gRPC** | localhost:8001 | - | GPU 推理服务 gRPC API* |
| **Triton Metrics** | http://localhost:8002 | - | Triton 监控指标* |
| **OpenWebUI** | http://localhost:8080 | admin / admin123 | LLM 交互界面* |
| **Ollama API** | http://localhost:11434 | - | LLM API 服务* |
| **DCGM Exporter** | http://localhost:9400 | - | GPU 监控指标* |

*仅在检测到 GPU 或启用相应 profile 时启动

## 📚 文档导航

### 🚀 部署文档
- [部署概览](docs/deployment/deployment_overview.md) - 部署方案对比和选择
- [部署步骤](docs/deployment/deployment_steps.md) - 详细部署指南
- [环境部署](docs/deployment/01_environment_deployment/) - 基础环境配置
- [服务部署](docs/deployment/02_server_deployment/) - 服务部署指南
- [应用部署](docs/deployment/03_application_deployment/) - 应用部署指南

### 💻 开发文档
- [开发计划](docs/development/development_Plan.md) - 项目开发路线图
- [产品文档](docs/development/product_development_document_enhanced.md) - 详细产品设计
- [数据库设计](docs/development/database_design.md) - 数据库架构设计
- [项目结构](docs/development/project_structure.md) - 项目组织结构
- [GPU 推理实现](docs/development/implementation_gpu_inference_openwebui.md) - GPU 功能实现

### 🌐 网络配置
- [IP 地址范围](docs/ip/ip_address_ranges.md) - 网络规划
- [服务端口映射](docs/ip/service_ip_port_mapping.md) - 端口分配规则
- [常用端口参考](docs/ip/common_ports_reference.md) - 端口使用规范

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