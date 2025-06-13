# 🤖 AI 中台最小化示例

> 企业级AI中台的最小化示例项目，基于Django + Next.js构建，包含完整的四大中台功能。

一个完整的 AI 中台解决方案，支持 GPU 加速推理、模型管理、监控和可视化界面。

## 🔧 功能特性

### 核心功能
- ✅ **完整的 AI 中台界面**：React + TypeScript 前端
- ✅ **REST API 后端**：Django + PostgreSQL
- ✅ **模型管理**：支持多种模型格式
- ✅ **数据管理**：PostgreSQL + Redis + MinIO
- ✅ **监控系统**：Prometheus + Grafana
- ✅ **快速部署**：优化的启动脚本，支持后台运行
- ✅ **实时监控**：自动启动Grafana监控面板

### GPU 功能（可选）
- ✅ **GPU 加速推理**：NVIDIA Triton Inference Server
- ✅ **大语言模型**：Ollama + OpenWebUI
- ✅ **GPU 监控**：DCGM Exporter + GPU 仪表板
- ✅ **多 GPU 支持**：自动检测和管理多张 GPU

### 监控功能
- ✅ **系统监控**：CPU、内存、磁盘使用率
- ✅ **GPU 监控**：GPU 使用率、显存、温度、功耗
- ✅ **服务监控**：各服务健康状态和性能指标
- ✅ **自动化监控**：一键启动 Grafana + Prometheus 监控栈
- ✅ **可视化界面**：预配置的 Grafana 仪表板
- ✅ **智能告警**：基于阈值的自动告警系统

## 🚪 系统界面截图

> 以下为中台主要界面示例截图：

- 登录页：
  
  ![中台登录页](../figs/ZT_Launcher.png)

- 首页：
  
  ![中台主页](../figs/ZT_Home.png)

- Django 后台管理：
  
  ![Django Admin](../figs/ZT_Admin_Django.png)

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose
- 可选：NVIDIA GPU + NVIDIA Container Toolkit（用于 GPU 加速）
- Python 3.8+（用于工具脚本）

### 快速启动

#### 🚀 一键启动 (推荐)
```bash
./start.sh
```
自动检测环境并选择最适合的启动模式。

#### ⚡ 快速启动（环境已配置）
```bash
# 快速启动所有服务（适合日常开发）
# 现已支持自动启动Grafana监控
./quick-start.sh

# 停止服务
./stop.sh
```

> **🎉 新特性**: `quick-start.sh` 现在支持后台运行！服务启动后脚本会自动退出，关闭终端不会影响服务运行。

#### 启动模式选择

```bash
# 自动模式（推荐）
./start.sh

# 完整模式 - Docker容器化，包含所有服务
./start.sh --full

# 离线模式 - 使用本地Docker镜像，无需网络
./start.sh --offline

# 本地模式 - 本地Python环境，无需Docker
./start.sh --local

# 停止所有服务
./stop.sh

# 重置环境
./reset.sh
```

#### 环境要求对比

| 启动模式 | Docker | 网络 | Python | 功能完整度 | 推荐场景 |
|---------|--------|------|--------|-----------|----------|
| 完整模式 | ✅ | ✅ | - | 100% | 生产部署、完整测试 |
| 离线模式 | ✅ | ❌ | - | 70-90% | 网络受限、演示 |
| 本地模式 | ❌ | ❌ | ✅ | 60% | 开发调试、快速验证 |

## 📁 项目结构

```
minimal-example/
├── start.sh                    # 统一启动脚本（支持多种模式）
├── stop.sh                     # 统一停止脚本
├── reset.sh                    # 统一重置脚本
├── docker-compose.yml          # 主要服务配置
├── backend/                    # Django 后端
├── frontend/                   # Next.js 前端
├── monitoring/                 # 监控配置
├── model-repository/           # 模型仓库
├── scripts/                    # 核心工具脚本
│   ├── generate_sample_models.py   # 生成示例模型
│   ├── manage_triton_models.py     # Triton模型管理
│   └── diagnose_system.sh          # 系统诊断工具
├── tests/                      # 测试脚本
├── utilities/                  # 工具脚本
├── docs/                       # 文档
└── archived/                   # 归档文件
```

## 🌐 服务访问地址

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

## 📚 使用指南

### 模型管理

```bash
# 生成示例模型
python3 scripts/generate_sample_models.py

# 管理 Triton 模型
python3 scripts/manage_triton_models.py
```

### 系统诊断

```bash
# 系统诊断和问题排查
bash scripts/diagnose_system.sh
```

### 测试和验证

```bash
# GPU 环境完整测试
python3 tests/test_gpu_stack_complete.py

# 基础GPU环境测试
python3 tests/test_gpu_environment.py

# 部署验证测试
python3 tests/validate_deployment.py

# API功能测试
python3 tests/test_complete_api.py

# 系统完整性验证
python3 tests/system_validation.py

# Triton客户端测试
python3 tests/test_triton_client.py
```

### 故障排查

```bash
# 系统环境诊断（推荐第一步）
bash scripts/diagnose_system.sh

# 查看服务状态
docker compose ps

# 查看服务日志
docker compose logs <service-name>

# 重启特定服务
docker compose restart <service-name>

# 完全重新启动
./stop.sh && ./start.sh
```

## 🛠️ 开发指南

### 本地开发

```bash
# 完整环境开发（需要Docker）
./start.sh

# 快速启动（后台运行，推荐）
./quick-start.sh
# 注意：quick-start.sh 现在支持后台运行
# 启动完成后脚本会自动退出，服务继续在后台运行
# 关闭终端不会影响服务

# 本地开发模式（网络受限/仅后端开发）
./start_local.sh

# 或手动启动后端
cd backend
python manage.py runserver

# 前端开发
cd frontend
npm run dev
```

### 环境说明

- **完整环境** (`./start.sh`): 包含所有服务（数据库、缓存、对象存储、GPU服务等）
- **本地开发** (`./start_local.sh`): 仅启动Django后端，使用SQLite数据库
- **混合开发**: Docker启动基础服务，本地启动开发服务

### 脚本说明

- `start.sh`: 主启动脚本，自动检测 GPU 并启动相应服务
- `quick-start.sh`: 快速启动脚本，**现已支持后台运行**，自动启动 Grafana 监控
- `stop.sh`: 停止脚本，清理容器和网络
- `scripts/`: 包含各种工具脚本
- `tests/`: 包含测试和验证脚本

#### quick-start.sh 新特性
- ✅ **后台运行**: 服务启动后脚本自动退出
- ✅ **监控集成**: 自动启动 Grafana 监控服务  
- ✅ **端口检查**: 自动检测并清理端口冲突
- ✅ **日志记录**: 后端和前端日志保存到 logs/ 目录
- ✅ **PID 管理**: 进程 ID 保存，便于管理

## 📖 文档

详细文档请查看 `docs/` 目录：

- [启动指南](docs/STARTUP_GUIDE.md) - **推荐首次使用阅读**
- [用户指南](docs/USER_GUIDE.md) - 功能使用和操作指南
- [离线模式指南](docs/OFFLINE_MODE_GUIDE.md) - 网络受限环境使用指南

## 🐛 问题解决

如果遇到问题，请按以下顺序排查：

1. **基础检查**
   - 检查 Docker 服务是否正常运行
   - 确认端口没有被占用（3000, 8000, 3002）
   - 查看容器日志排查具体错误
   
2. **监控服务问题**
   - Grafana 无法访问：检查 http://192.168.110.88:3002
   - 检查 Grafana 容器状态：`docker ps | grep grafana`
   - 查看 Grafana 日志：`docker logs ai-platform-grafana`

3. **服务状态检查**
   ```bash
   # 检查所有容器状态
   docker ps
