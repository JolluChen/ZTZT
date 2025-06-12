#!/bin/bash

# =============================================================================
# AI中台停止脚本
# 用于停止由启动脚本启动的服务
# =============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 停止 AI中台 服务${NC}"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 停止后端服务
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        rm -f logs/backend.pid
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    else
        echo -e "${RED}❌ 后端服务进程不存在${NC}"
        rm -f logs/backend.pid
    fi
else
    echo -e "${YELLOW}⚠️  未找到后端PID文件${NC}"
fi

# 停止前端服务
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        rm -f logs/frontend.pid
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    else
        echo -e "${RED}❌ 前端服务进程不存在${NC}"
        rm -f logs/frontend.pid
    fi
else
    echo -e "${YELLOW}⚠️  未找到前端PID文件${NC}"
fi

# 强制杀死可能占用端口的进程
echo -e "${YELLOW}检查端口占用...${NC}"

# 检查8000端口
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}强制停止端口8000上的进程...${NC}"
    lsof -ti:8000 | xargs -r kill -9
fi

# 检查3000端口
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}强制停止端口3000上的进程...${NC}"
    lsof -ti:3000 | xargs -r kill -9
fi

echo -e "${GREEN}🛑 所有服务已停止！${NC}"
