# Dify AI 平台集成部署指南

## 概述

本文档描述了如何在 AI 中台中集成和部署 Dify AI 平台，使其作为"服务中台"的一部分提供 AI 应用创建和管理功能。

## 架构说明

### 集成架构
```
AI 中台
├── 数据中台 (Data Platform)
├── 算法中台 (Algorithm Platform)  
├── 模型中台 (Model Platform)
└── 服务中台 (Service Platform)
    ├── 传统应用管理
    └── Dify AI 应用管理 ✨
```

### 服务组件
- **dify-api**: Dify 核心 API 服务
- **dify-web**: Dify Web 控制台
- **dify-worker**: 后台任务处理器
- **dify-nginx**: 反向代理服务

## 快速部署

### 1. 前置条件

确保以下服务已运行：
- PostgreSQL (AI 中台共享)
- Redis (AI 中台共享)  
- MinIO (AI 中台共享)

### 2. 启动基础服务

```bash
cd /home/lsyzt/ZTZT/minimal-example

# 启动基础服务
docker compose -f docker/docker-compose.yml up -d postgres redis minio
```

### 3. 初始化 Dify 数据库

```bash
# 运行初始化脚本
chmod +x scripts/init-dify.sh
./scripts/init-dify.sh
```

### 4. 启动 Dify 服务

```bash
# 启动 Dify 相关服务
docker compose -f docker/dify-docker-compose.yml --profile dify up -d
```

### 5. 验证部署

检查服务状态：
```bash
docker compose -f docker/dify-docker-compose.yml ps
```

访问服务：
- Dify Web Console: http://localhost:8001
- Dify API: http://localhost:8001/v1

## 配置说明

### 环境变量配置

主要配置在 `configs/dify.env` 文件中：

```env
# Dify 核心配置
DIFY_SECRET_KEY=sk-ai-platform-dify-integration-2024
DIFY_CONSOLE_WEB_URL=http://localhost:8001
DIFY_SERVICE_API_URL=http://localhost:8001

# 数据库配置 (使用 AI 中台的 PostgreSQL)
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=ai_password
DIFY_DB_NAME=dify

# Redis 配置 (使用 AI 中台的 Redis)
REDIS_HOST=redis
REDIS_PORT=6379
DIFY_REDIS_DB=2

# 存储配置 (使用 AI 中台的 MinIO)
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
DIFY_S3_BUCKET=dify
```

### Nginx 配置

Dify 的 Nginx 配置位于 `docker/dify-nginx.conf`，主要功能：
- API 请求代理到 dify-api:5001
- Web 界面代理到 dify-web:3000
- 文件上传和下载支持
- WebSocket 支持

## 功能集成

### 前端集成

在 AI 中台的前端界面中，Dify 集成体现在：

1. **应用创建**: 服务中台 -> 创建应用 -> 选择"Dify AI 应用"
2. **应用类型**: 支持对话应用、文本生成、工作流、智能体
3. **配置选项**: API 密钥、API 地址、模式选择

### 后端集成

Django 后端的集成包括：

1. **模型扩展**: `DifyApplication`, `DifyConversation`, `DifyDataset`
2. **API 端点**: `/api/service/dify/` 下的 RESTful API
3. **数据库**: 使用 AI 中台的 PostgreSQL 实例

## API 接口

### Dify 应用管理

```http
# 获取 Dify 应用列表
GET /api/service/dify/applications/

# 创建 Dify 应用
POST /api/service/dify/applications/
{
    "name": "我的 AI 助手",
    "description": "智能客服应用",
    "app_type": "chat",
    "mode": "simple",
    "api_key": "app-xxx",
    "api_url": "http://localhost:8001"
}

# 更新 Dify 应用
PATCH /api/service/dify/applications/{id}/

# 删除 Dify 应用
DELETE /api/service/dify/applications/{id}/
```

### 对话管理

```http
# 获取应用的对话列表
GET /api/service/dify/applications/{app_id}/conversations/

# 创建新对话
POST /api/service/dify/applications/{app_id}/conversations/
{
    "user_id": 1,
    "inputs": {}
}

# 发送消息
POST /api/service/dify/applications/{app_id}/conversations/{conversation_id}/messages/
{
    "query": "你好",
    "inputs": {},
    "response_mode": "blocking"
}
```

## 故障排除

### 常见问题

1. **Dify API 无法访问**
   - 检查 docker 容器状态
   - 验证网络连接
   - 查看 nginx 日志

2. **数据库连接失败**
   - 确认 PostgreSQL 已启动
   - 检查数据库凭据
   - 验证 dify 数据库是否已创建

3. **Redis 连接问题**
   - 确认 Redis 容器运行
   - 检查 Redis 配置
   - 验证网络连通性

### 日志查看

```bash
# 查看 Dify API 日志
docker logs ai_platform_dify_api

# 查看 Dify Worker 日志
docker logs ai_platform_dify_worker

# 查看 Nginx 日志
docker logs ai_platform_dify_nginx
```

## 安全考虑

1. **API 密钥管理**: 生产环境中应使用强密钥
2. **网络隔离**: 考虑使用内部网络通信
3. **访问控制**: 配置适当的防火墙规则
4. **数据备份**: 定期备份 Dify 相关数据

## 扩展和维护

### 升级 Dify

```bash
# 停止当前服务
docker compose -f docker/dify-docker-compose.yml --profile dify down

# 拉取新镜像
docker compose -f docker/dify-docker-compose.yml pull

# 重新启动
docker compose -f docker/dify-docker-compose.yml --profile dify up -d
```

### 监控和指标

建议集成以下监控：
- 容器健康检查
- API 响应时间监控
- 数据库连接监控
- 存储使用情况

## 总结

通过以上步骤，您已成功将 Dify AI 平台集成到 AI 中台中，用户现在可以：

1. 在统一界面中创建和管理 AI 应用
2. 选择传统模型部署或 Dify AI 应用
3. 利用 Dify 的丰富功能构建智能应用
4. 通过 AI 中台的统一认证和权限管理

集成完成后，AI 中台将具备更强大的 AI 应用构建和部署能力。
