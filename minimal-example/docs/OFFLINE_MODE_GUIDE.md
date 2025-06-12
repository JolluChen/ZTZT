# 🌐 离线模式使用指南

适用于网络受限或无法访问Docker镜像源的环境。

## 🚀 启动方式对比

| 启动方式 | 命令 | 适用场景 | 功能完整度 |
|---------|------|----------|-----------|
| **完整模式** | `./start.sh` | 网络正常 | 100% |
| **快速模式** | `./quick-start.sh` | 环境已配置 | 80% |
| **离线模式** | 手动启动 | 网络受限 | 60% |

## 📦 离线启动步骤

### 1. 后端启动
```bash
cd backend
source venv/bin/activate  # 激活虚拟环境
python manage.py runserver 0.0.0.0:8000
```

### 2. 前端启动（可选）
```bash
cd frontend
npm run dev
```

### 3. 访问服务
- **后端API**: http://192.168.110.88:8000
- **前端**: http://192.168.110.88:3000
- **管理后台**: http://192.168.110.88:8000/admin/

## 🔧 离线环境配置

### 环境检查
```bash
# 检查Python版本
python3 --version

# 检查Node.js版本
node --version

# 检查虚拟环境
ls backend/venv/
```

### 依赖安装
```bash
# 后端依赖（离线包）
cd backend
pip install -r requirements_local.txt

# 前端依赖
cd frontend
npm install --offline
```

## ⚠️ 离线模式限制

### 不可用功能
- ❌ Docker服务（PostgreSQL、Redis等）
- ❌ GPU推理服务
- ❌ 外部API调用
- ❌ 实时监控

### 可用功能
- ✅ Django后端API
- ✅ SQLite数据库
- ✅ 基本CRUD操作
- ✅ 用户认证
- ✅ 管理后台

## 🛠️ 故障排除

### 常见问题
1. **模块导入错误**: 检查虚拟环境是否激活
2. **端口被占用**: 使用不同端口或终止占用进程
3. **数据库错误**: 运行 `python manage.py migrate`
4. **静态文件**: 运行 `python manage.py collectstatic`

