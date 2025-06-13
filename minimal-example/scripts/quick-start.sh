#!/bin/bash

# =============================================================================
# AI中台快速启动脚本 (环境已配置版)
# 按照用户提供的原始步骤执行
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 启动 AI中台 (快速模式)${NC}"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 创建必要的目录
mkdir -p logs

# 端口检查和清理函数
check_and_cleanup_port() {
    local port=$1
    local service_name=$2
    
    # 检查端口是否被占用
    if netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
        echo -e "${YELLOW}⚠️  检测到${service_name}端口${port}被占用，正在清理...${NC}"
        # 找到占用端口的进程并终止
        local pid=$(netstat -tlnp 2>/dev/null | grep ":${port} " | awk '{print $7}' | cut -d'/' -f1)
        if [ ! -z "$pid" ] && [ "$pid" != "-" ]; then
            kill $pid 2>/dev/null || true
            sleep 2
            echo -e "${GREEN}✅ ${service_name}端口${port}已清理${NC}"
        fi
    fi
}

# 清理函数
cleanup() {
    echo -e "${YELLOW}🛑 正在停止服务...${NC}"
    if [ -f "logs/backend.pid" ]; then
        kill $(cat logs/backend.pid) 2>/dev/null || true
        rm -f logs/backend.pid
    fi
    if [ -f "logs/frontend.pid" ]; then
        kill $(cat logs/frontend.pid) 2>/dev/null || true
        rm -f logs/frontend.pid
    fi
    # 停止Grafana容器
    echo -e "${BLUE}正在停止Grafana...${NC}"
    cd docker && docker compose -f docker-compose.offline.yml down grafana >/dev/null 2>&1 && cd ..
    echo -e "${GREEN}✅ 服务已停止${NC}"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 清理可能占用的端口
echo -e "${BLUE}🔍 检查端口占用情况...${NC}"
check_and_cleanup_port 8000 "Django后端"
check_and_cleanup_port 3000 "Next.js前端"

# 启动Grafana监控服务
echo -e "${YELLOW}📊 步骤0: 启动Grafana监控服务${NC}"
cd docker
echo -e "${BLUE}正在启动Grafana...${NC}"
docker compose -f docker-compose.offline.yml up -d grafana >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Grafana服务已启动${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana启动失败或已在运行${NC}"
fi
cd ..

# 1. 进入后端目录
echo -e "${YELLOW}📡 步骤1: 进入后端目录${NC}"
cd backend

# 2. 激活虚拟环境
echo -e "${YELLOW}🐍 步骤2: 激活虚拟环境${NC}"
source venv/bin/activate

# 3. 启动服务 (数据库已预配置)
echo -e "${YELLOW}🚀 步骤3: 启动Django服务${NC}"
nohup python manage.py runserver 0.0.0.0:8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"

# 4. 返回上级目录
echo -e "${YELLOW}📂 步骤4: 返回上级目录${NC}"
cd ..

# 等待后端启动
echo -e "${YELLOW}⏳ 等待后端服务启动...${NC}"
sleep 3

# 5. 进入前端目录
echo -e "${YELLOW}🎨 步骤5: 进入前端目录${NC}"
cd frontend

# 6. 启动开发服务器
echo -e "${YELLOW}🚀 步骤6: 启动前端开发服务器${NC}"
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"

# 等待前端启动
echo -e "${YELLOW}⏳ 等待前端服务启动...${NC}"
sleep 5

cd ..

echo
echo -e "${GREEN}🎉 ===== 启动完成！ =====${NC}"
echo -e "${GREEN}🏠 后端地址: http://192.168.110.88:8000${NC}"
echo -e "${GREEN}🎨 前端地址: http://192.168.110.88:3000${NC}"
echo -e "${GREEN}📚 API文档: http://192.168.110.88:8000/swagger/${NC}"
echo -e "${GREEN}⚙️  管理后台: http://192.168.110.88:8000/admin/ (admin/admin123)${NC}"
echo -e "${GREEN}📊 Grafana监控: http://192.168.110.88:3002${NC}"

echo
echo -e "${YELLOW}💡 提示：${NC}"
echo -e "   • 使用 ${RED}./stop.sh${NC} 停止所有服务"
echo -e "   • 服务已在后台运行，关闭终端不影响服务"
echo -e "   • 日志见 logs/ 目录，PID已保存到 logs/ 目录"

echo -e "${GREEN}✅ 所有服务已在后台启动，脚本即将退出${NC}"
# 脚本直接退出，不再阻塞终端
exit 0
