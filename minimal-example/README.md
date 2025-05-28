# AI 中台最小化示例

这是一个AI中台的最小化示例项目，包含核心功能的简化实现。

## 项目概述

### 功能范围
- **用户管理**: 注册、登录、基础权限
- **数据中台**: 数据集上传、管理、预览
- **算法中台**: 实验创建、运行、追踪
- **模型中台**: 模型注册、版本管理
- **服务中台**: 应用创建、部署

### 技术栈
- **后端**: Django 4.2 + Django REST Framework
- **前端**: Next.js 13 + React 18 + Ant Design
- **数据库**: PostgreSQL 15 + Redis 7
- **部署**: Docker + docker-compose

## 快速开始

> 📚 **快速启动**: 查看 [QUICK_START.md](./QUICK_START.md) 获得完整的启动指南和管理员账户信息。

### 环境要求
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Git

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd ai-platform-minimal
```

2. 后端设置
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. 前端设置
```bash
cd frontend
npm install
```

4. 启动服务
```bash
# 启动数据库和缓存
docker-compose up -d postgres redis

# 运行数据库迁移
cd backend
python manage.py migrate

# 创建管理员账户（已预设置）
# 管理员账户：admin
# 管理员密码：admin
# 如需重新创建：python manage.py createsuperuser

# 启动后端
python manage.py runserver

# 启动前端 (新终端)
cd frontend
npm run dev
```

5. 访问应用
- 前端: http://localhost:3000
- 后端API: http://localhost:8000/api
- 管理后台: http://localhost:8000/admin (管理员: admin / admin)
- API文档: http://localhost:8000/swagger/ 或 http://localhost:8000/redoc/

## 项目结构

```
ai-platform-minimal/
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── apps/
│       ├── authentication/
│       ├── data_platform/
│       ├── algo_platform/
│       ├── model_platform/
│       └── service_platform/
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── store/
│   └── public/
└── docs/
    ├── api.md
    ├── deployment.md
    └── user_guide.md
```

## 核心功能

### 1. 用户管理
- 用户注册和登录
- 基于角色的权限控制
- 用户配置文件管理

### 2. 数据中台
- 数据集上传和存储
- 数据预览和基础统计
- 数据集版本管理

### 3. 算法中台
- 实验项目管理
- 实验运行和参数记录
- 简单的实验追踪

### 4. 模型中台
- 模型文件上传和注册
- 模型版本管理
- 基础模型信息展示

### 5. 服务中台
- 简单应用定义
- 基础服务发布
- 应用状态监控

## 开发指南

### 后端开发
- 使用Django REST Framework构建API
- 遵循RESTful设计原则
- 实现基础的认证和权限控制

### 前端开发
- 使用Next.js App Router
- 组件化开发方式
- 响应式设计

### 数据库设计
- 基于PostgreSQL的关系型设计
- 支持基础的向量存储
- 简化的权限模型

## 部署说明

### 开发环境
使用docker-compose进行本地开发

### 生产环境
- 支持Docker容器化部署
- 可扩展到Kubernetes环境
- 支持环境变量配置

## 扩展路径

此最小化示例为完整AI中台的基础版本，可以逐步扩展：

1. **增强数据处理**: 集成Spark、Airflow等
2. **完善算法开发**: 集成MLflow、Kubeflow等
3. **强化模型服务**: 集成TorchServe、Triton等
4. **扩展监控**: 集成Prometheus、Grafana等
5. **增加安全**: 完善认证、审计等功能

## 许可证

MIT License
