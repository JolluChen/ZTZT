#!/bin/bash

# =============================================================================
# AI中台服务停止脚本
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🛑 停止 AI中台服务${NC}"

# 获取脚本目录并设置项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 停止后端服务
echo -e "${YELLOW}📡 停止后端服务...${NC}"
if [ -f "logs/backend.pid" ]; then
    PID=$(cat logs/backend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo -e "${GREEN}✅ 后端服务已停止 (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  后端服务已经停止${NC}"
    fi
    rm -f logs/backend.pid
else
    echo -e "${YELLOW}⚠️  未找到后端服务PID文件${NC}"
fi

# 停止前端服务
echo -e "${YELLOW}🎨 停止前端服务...${NC}"
if [ -f "logs/frontend.pid" ]; then
    PID=$(cat logs/frontend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo -e "${GREEN}✅ 前端服务已停止 (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  前端服务已经停止${NC}"
    fi
    rm -f logs/frontend.pid
else
    echo -e "${YELLOW}⚠️  未找到前端服务PID文件${NC}"
fi

# 停止 Docker 服务
echo -e "${YELLOW}🐳 停止 Docker 服务...${NC}"
cd docker

# 停止 Dify 服务
echo -e "${BLUE}停止 Dify 服务...${NC}"
if docker compose -f dify-docker-compose.yml --profile dify ps -q | grep -q .; then
    docker compose -f dify-docker-compose.yml --profile dify down >/dev/null 2>&1
    echo -e "${GREEN}✅ Dify 服务已停止${NC}"
else
    echo -e "${YELLOW}⚠️  Dify 服务未运行${NC}"
fi

# 停止监控服务
echo -e "${BLUE}停止监控服务...${NC}"
if docker compose -f docker-compose.offline.yml ps -q grafana | grep -q .; then
    docker compose -f docker-compose.offline.yml down grafana >/dev/null 2>&1
    echo -e "${GREEN}✅ Grafana 已停止${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana 未运行${NC}"
fi

# 停止基础服务
echo -e "${BLUE}停止基础服务...${NC}"
if docker compose -f docker-compose.yml ps -q | grep -q .; then
    docker compose -f docker-compose.yml down >/dev/null 2>&1
    echo -e "${GREEN}✅ 基础服务已停止${NC}"
else
    echo -e "${YELLOW}⚠️  基础服务未运行${NC}"
fi

cd ..

# 清理可能残留的端口占用
echo -e "${YELLOW}🔍 检查端口占用情况...${NC}"

# 检查并清理8000端口
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}清理端口8000上的进程...${NC}"
    lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
fi

# 检查并清理3000端口
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}清理端口3000上的进程...${NC}"
    lsof -ti:3000 | xargs -r kill -9 2>/dev/null || true
fi

# 检查并清理8080端口 (Dify)
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}清理端口8080上的进程...${NC}"
    lsof -ti:8080 | xargs -r kill -9 2>/dev/null || true
fi

echo
echo -e "${GREEN}🎉 ===== 所有服务已停止！ =====${NC}"
echo
echo -e "${YELLOW}💡 重新启动服务：${NC}"
echo -e "   ${GREEN}./quick-start.sh${NC}     - 启动所有服务（包括Dify）"
echo -e "   ${GREEN}./quick-start.sh --no-dify${NC} - 启动服务（不包括Dify）"
echo
echo -e "${BLUE}🔧 重新配置环境：${NC}"
echo -e "   ${YELLOW}./scripts/setup-environment.sh${NC}"
