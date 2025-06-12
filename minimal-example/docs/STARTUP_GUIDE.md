# 🚀 AI中台启动指南

提供多种启动方式，满足不同的开发和部署需求。

## 📋 启动脚本说明

### 1. `quick-start.sh` - 快速启动（推荐）⚡
适合日常开发使用，环境已配置的快速启动。

```bash
./quick-start.sh    # 启动服务
./stop.sh          # 停止服务
```

**适用场景**：
- ✅ 环境已完全配置
- ✅ 日常开发调试
- ✅ 快速演示展示

### 2. `start.sh` - 完整功能启动🛠️
功能完整的启动管理脚本，支持自动环境配置。

```bash
./start.sh --install   # 首次安装并启动
./start.sh backend     # 仅启动后端
./start.sh frontend    # 仅启动前端
./start.sh --help     # 查看帮助
```

**适用场景**：
- ✅ 首次安装配置
- ✅ 完整的服务管理
- ✅ 生产环境部署

## 🌐 服务访问地址

启动成功后访问：
- **前端**: http://192.168.110.88:3000
- **后端API**: http://192.168.110.88:8000/api/
- **API文档**: http://192.168.110.88:8000/swagger/
- **管理后台**: http://192.168.110.88:8000/admin/

## 🔧 故障排除

### 端口被占用
```bash
# 检查端口占用
netstat -tlnp | grep :8000
netstat -tlnp | grep :3000

# 终止占用进程
kill -9 <PID>
```

### 环境问题
```bash
# 检查Python版本
python3 --version

# 检查虚拟环境
ls backend/venv/

# 重新创建虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 数据库问题
```bash
cd backend
python manage.py check
python manage.py migrate
```

## ⚠️ 重要提醒

1. 首次使用请运行 `./start.sh --install`
2. 确保端口8000和3000未被占用
