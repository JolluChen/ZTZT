# Dify AI Platform 集成文档

## 概述

本文档描述了如何将 Dify AI 平台集成到现有的 AI 中台系统中。集成后，用户可以在"服务中台 / 创建应用"界面中选择创建 Dify AI 应用。

## 架构概述

```
AI 中台架构 + Dify 集成
├── 前端 (Next.js)
│   ├── 应用创建界面 (支持传统应用 + Dify 应用)
│   └── 应用管理界面
├── 后端 (Django)
│   ├── Dify 应用管理 API
│   ├── Dify 对话管理 API
│   └── Dify 知识库管理 API
├── 基础服务
│   ├── PostgreSQL (共享数据库)
│   ├── Redis (共享缓存)
│   └── MinIO (共享存储)
└── Dify 服务
    ├── Dify API (端口 8001)
    ├── Dify Web Console
    ├── Dify Worker
    └── Nginx 反向代理
```

## 集成功能

### 1. 应用创建
- **应用类型选择**: 传统应用 vs Dify AI 应用
- **Dify 应用配置**: 
  - 应用类型（对话、文本生成、工作流、智能体）
  - 模式（简单、高级）
  - API 配置（密钥、地址）

### 2. 数据模型
- **DifyApplication**: Dify 应用管理
- **DifyConversation**: 对话记录管理
- **DifyDataset**: 知识库管理

### 3. API 端点
- `GET/POST /api/service/dify/applications/` - 应用管理
- `GET/POST /api/service/dify/conversations/` - 对话管理
- `GET/POST /api/service/dify/datasets/` - 知识库管理

## 部署指南

### 前置要求
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+

### 1. 快速部署
```bash
# 克隆项目
cd /home/lsyzt/ZTZT/minimal-example

# 运行集成脚本
chmod +x scripts/deploy-dify.sh
./scripts/deploy-dify.sh
```

### 2. 手动部署

#### 步骤 1: 准备环境配置
```bash
# 复制环境配置
cp configs/dify.env.example configs/dify.env
# 编辑配置文件
vim configs/dify.env
```

#### 步骤 2: 启动基础服务
```bash
docker-compose -f docker/docker-compose.yml up -d postgres redis minio
```

#### 步骤 3: 初始化 Dify 数据库
```bash
chmod +x scripts/init-dify.sh
./scripts/init-dify.sh
```

#### 步骤 4: 启动 Dify 服务
```bash
docker-compose -f docker/dify-docker-compose.yml --profile dify up -d
```

#### 步骤 5: 启动 AI 平台服务
```bash
# 后端服务
cd backend
source venv/bin/activate
python manage.py runserver

# 前端服务
cd frontend
npm install
npm run dev
```

## 配置说明

### 环境变量配置 (configs/dify.env)
```bash
# 基础配置
DIFY_SECRET_KEY=sk-ai-platform-dify-integration-2024
DIFY_CONSOLE_WEB_URL=http://localhost:8001
DIFY_SERVICE_API_URL=http://localhost:8001

# 数据库配置 (共享 AI 中台数据库)
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=ai_password
POSTGRES_DB=dify

# 存储配置 (共享 MinIO)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### Nginx 配置 (docker/dify-nginx.conf)
- API 路由代理到 Dify API (端口 5001)
- Web Console 代理到 Dify Web (端口 3000)
- 文件上传/下载优化
- WebSocket 支持

## 使用说明

### 1. 创建 Dify 应用

1. 访问 AI 中台: `http://localhost:3000`
2. 导航到"服务中台" → "应用管理"
3. 点击"创建应用"
4. 选择"Dify AI 应用"
5. 配置应用参数：
   - 应用名称和描述
   - Dify 应用类型
   - API 配置

### 2. 管理 Dify 应用

- **查看应用**: 应用列表显示状态、配置等信息
- **启动/停止**: 控制应用运行状态
- **监控**: 查看应用运行指标
- **配置**: 更新应用配置

### 3. 访问 Dify Console

直接访问 Dify Web Console: `http://localhost:8001`

## API 文档

### Dify 应用管理

#### 创建应用
```http
POST /api/service/dify/applications/
Content-Type: application/json

{
  "name": "智能客服",
  "description": "基于 Dify 的智能客服应用",
  "app_type": "chat",
  "mode": "simple",
  "api_key": "app-xxx",
  "api_url": "http://localhost:8001"
}
```

#### 获取应用列表
```http
GET /api/service/dify/applications/
```

#### 启动应用对话
```http
POST /api/service/dify/applications/{id}/chat/
Content-Type: application/json

{
  "message": "你好",
  "conversation_id": "optional-conversation-id"
}
```

### 对话管理

#### 获取对话历史
```http
GET /api/service/dify/conversations/{conversation_id}/messages/
```

#### 创建对话
```http
POST /api/service/dify/conversations/
Content-Type: application/json

{
  "application": 1,
  "title": "客户咨询"
}
```

## 故障排除

### 常见问题

1. **Dify 服务无法启动**
   ```bash
   # 检查日志
   docker-compose -f docker/dify-docker-compose.yml logs dify-api
   
   # 检查数据库连接
   docker exec -it ai_platform_postgres psql -U ai_user -d dify -c "\\dt"
   ```

2. **API 请求失败**
   ```bash
   # 检查网络连接
   docker network ls
   docker network inspect ai_platform_network
   
   # 检查服务状态
   docker ps --filter "name=dify"
   ```

3. **前端无法连接后端**
   ```bash
   # 检查 CORS 配置
   curl -I http://localhost:8000/api/service/dify/applications/
   ```

### 日志查看

```bash
# Dify API 日志
docker logs ai_platform_dify_api

# Dify Worker 日志
docker logs ai_platform_dify_worker

# Nginx 日志
docker logs ai_platform_dify_nginx

# Django 后端日志
cd backend && source venv/bin/activate && python manage.py runserver --verbosity=2
```

### 性能监控

访问 Grafana 监控面板: `http://localhost:3001`

- Dify 服务指标
- 数据库性能
- API 响应时间
- 资源使用情况

## 扩展和定制

### 添加新的 Dify 应用类型

1. 更新后端模型 (`backend/apps/service_platform/models.py`)
2. 更新前端表单 (`frontend/src/app/service/applications/page.tsx`)
3. 添加相应的 API 处理逻辑

### 集成其他 AI 服务

参考 Dify 集成模式，可以类似地集成其他 AI 服务：
- LangChain
- Flowise
- n8n

### 自定义 Nginx 配置

编辑 `docker/dify-nginx.conf` 添加：
- 自定义路由规则
- 缓存策略
- 安全配置
- 负载均衡

## 安全考虑

1. **API 密钥管理**: 使用环境变量存储敏感信息
2. **网络隔离**: 使用 Docker 网络隔离服务
3. **访问控制**: 配置适当的 CORS 和认证策略
4. **数据加密**: 生产环境启用 HTTPS/TLS

## 生产部署建议

1. **资源配置**:
   - Dify API: 2 CPU, 4GB RAM
   - Dify Worker: 1 CPU, 2GB RAM
   - PostgreSQL: 2 CPU, 4GB RAM

2. **高可用性**:
   - 多实例部署
   - 负载均衡
   - 数据库主从复制

3. **监控告警**:
   - 服务健康检查
   - 资源使用监控
   - 错误日志告警

4. **备份策略**:
   - 数据库定期备份
   - 应用配置备份
   - 容器镜像版本管理

## 更新日志

- **v1.0.0** (2024-01-20): 初始版本，基础 Dify 集成
- **v1.0.1** (2024-01-21): 添加对话管理功能
- **v1.0.2** (2024-01-22): 优化 Nginx 配置，添加监控支持
