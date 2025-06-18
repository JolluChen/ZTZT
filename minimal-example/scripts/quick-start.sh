#!/bin/bash

# =============================================================================
# AI中台服务启动脚本 (纯服务启动，不包含环境配置)
# 使用前请先运行 scripts/setup-environment.sh 完成环境配置
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 启动 AI中台服务${NC}"

# 默认启用 Dify 集成
ENABLE_DIFY=true
DAEMON_MODE=false
for arg in "$@"; do
    case $arg in
        --no-dify)
            ENABLE_DIFY=false
            shift
            ;;
        --daemon)
            DAEMON_MODE=true
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --no-dify      禁用 Dify AI 平台集成（默认启用）"
            echo "  --daemon       后台运行模式，启动完成后脚本退出"
            echo "  --help, -h     显示此帮助信息"
            echo
            echo "注意："
            echo "  启动前请确保已运行 scripts/setup-environment.sh 完成环境配置"
            echo "  使用 --daemon 模式时，服务将完全在后台运行，可安全关闭终端"
            exit 0
            ;;
    esac
done

# 获取脚本目录并设置项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 如果脚本在 scripts 目录中，项目根目录是上一级；如果在根目录中，项目根目录就是当前目录
if [[ "$SCRIPT_DIR" == */scripts ]]; then
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    PROJECT_ROOT="$SCRIPT_DIR"
fi
cd "$PROJECT_ROOT"

# 检查环境配置状态
echo -e "${BLUE}🔍 检查环境配置状态...${NC}"
if [ ! -f ".env-status/last-setup" ]; then
    echo -e "${RED}❌ 环境未配置！${NC}"
    echo -e "${YELLOW}请先运行以下命令配置环境：${NC}"
    echo -e "   ${GREEN}./scripts/setup-environment.sh${NC}"
    echo
    exit 1
fi

# 检查 Dify 配置
if [ "$ENABLE_DIFY" = true ] && [ ! -f ".env-status/dify-configured" ]; then
    echo -e "${YELLOW}⚠️  Dify 环境未配置，将自动禁用 Dify 集成${NC}"
    ENABLE_DIFY=false
fi

if [ "$ENABLE_DIFY" = true ]; then
    echo -e "${GREEN}🤖 Dify AI 平台集成已启用${NC}"
else
    echo -e "${YELLOW}⚠️  Dify AI 平台集成已禁用${NC}"
fi

# 确保必要的目录存在
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
    
    # 停止后端服务
    if [ -f "logs/backend.pid" ]; then
        kill $(cat logs/backend.pid) 2>/dev/null || true
        rm -f logs/backend.pid
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    fi
    
    # 停止前端服务
    if [ -f "logs/frontend.pid" ]; then
        kill $(cat logs/frontend.pid) 2>/dev/null || true
        rm -f logs/frontend.pid
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    fi
    
    # 停止 Docker 服务
    echo -e "${BLUE}停止 Docker 服务...${NC}"
    cd docker
    
    # 停止 Grafana
    docker compose -f docker-compose.offline.yml down grafana >/dev/null 2>&1
    
    # 如果启用了 Dify，停止 Dify 服务
    if [ "$ENABLE_DIFY" = true ]; then
        docker compose -f dify-docker-compose.yml --profile dify down >/dev/null 2>&1
    fi
    
    # 停止基础服务
    docker compose -f docker-compose.yml down >/dev/null 2>&1
    
    cd ..
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 启动前的状态检查
echo -e "${BLUE}🔍 检查服务状态...${NC}"

# 检查 Docker 网络是否存在
if ! docker network ls | grep -q "ai_platform_network"; then
    echo -e "${RED}❌ Docker 网络不存在，请运行环境配置脚本${NC}"
    exit 1
fi

# 如果启用 Dify，检查必要的镜像是否存在
if [ "$ENABLE_DIFY" = true ]; then
    if ! docker images | grep -q "ai-platform-dify-api" || ! docker images | grep -q "ai-platform-dify-web"; then
        echo -e "${RED}❌ Dify 镜像不存在，请运行环境配置脚本${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"

# 清理可能占用的端口
echo -e "${BLUE}🔍 检查端口占用情况...${NC}"
check_and_cleanup_port 8000 "Django后端"
check_and_cleanup_port 3000 "Next.js前端"

# 如果启用 Dify，检查 Dify 端口
if [ "$ENABLE_DIFY" = true ]; then
    check_and_cleanup_port 8001 "Dify服务"
fi

# 启动 Docker 服务
echo -e "${YELLOW}🐳 步骤1: 启动 Docker 服务${NC}"
cd docker

# 启动基础服务
echo -e "${BLUE}启动基础服务 (PostgreSQL, MinIO)...${NC}"
docker compose -f docker-compose.yml up -d postgres minio >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 基础服务已启动${NC}"
else
    echo -e "${RED}❌ 基础服务启动失败${NC}"
    exit 1
fi

# 启动监控服务
echo -e "${BLUE}启动监控服务 (Grafana)...${NC}"
docker compose -f docker-compose.offline.yml up -d grafana >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Grafana已启动${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana启动失败或已在运行${NC}"
fi

# 如果启用 Dify，启动 Dify 服务
if [ "$ENABLE_DIFY" = true ]; then
    echo -e "${BLUE}启动 Dify 服务...${NC}"
    docker compose -f dify-docker-compose.yml --profile dify up -d >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Dify 服务已启动${NC}"
    else
        echo -e "${RED}❌ Dify 服务启动失败${NC}"
    fi
fi

cd ..

# 等待服务就绪
echo -e "${BLUE}⏳ 等待服务就绪...${NC}"
sleep 5

# 启动后端服务
echo -e "${YELLOW}📡 步骤2: 启动后端服务${NC}"
cd backend

echo -e "${BLUE}激活虚拟环境...${NC}"
source venv/bin/activate

echo -e "${BLUE}启动 Django 服务...${NC}"
# 使用 nohup 和 disown 确保进程完全脱离终端会话
nohup python manage.py runserver 0.0.0.0:8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
disown $BACKEND_PID
echo $BACKEND_PID > ../logs/backend.pid
echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"

cd ..

# 启动前端服务
echo -e "${YELLOW}🎨 步骤3: 启动前端服务${NC}"
cd frontend

echo -e "${BLUE}启动 Next.js 开发服务器...${NC}"
# 使用 nohup 和 disown 确保进程完全脱离终端会话
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
disown $FRONTEND_PID
echo $FRONTEND_PID > ../logs/frontend.pid
echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"

cd ..

# 等待服务完全启动
echo -e "${BLUE}⏳ 等待服务完全启动...${NC}"
sleep 5

echo
echo -e "${GREEN}🎉 ===== 服务启动完成！ =====${NC}"
echo -e "${GREEN}🏠 后端地址: http://192.168.110.88:8000${NC}"
echo -e "${GREEN}🎨 前端地址: http://192.168.110.88:3000${NC}"
echo -e "${GREEN}📚 API文档: http://192.168.110.88:8000/swagger/${NC}"
echo -e "${GREEN}⚙️  管理后台: http://192.168.110.88:8000/admin/ (admin/admin123)${NC}"
echo -e "${GREEN}📊 Grafana监控: http://192.168.110.88:3002${NC}"

# 如果启用了 Dify，显示 Dify 相关地址
if [ "$ENABLE_DIFY" = true ]; then
    echo -e "${GREEN}🤖 Dify 控制台: http://192.168.110.88:8001${NC}"
    echo -e "${GREEN}🔗 Dify API: http://192.168.110.88:8001/v1${NC}"
fi

echo
echo -e "${YELLOW}💡 使用提示：${NC}"
echo -e "   • 使用 ${RED}Ctrl+C${NC} 或 ${RED}./scripts/stop.sh${NC} 停止所有服务"
if [ "$ENABLE_DIFY" = true ]; then
    echo -e "   • Dify 首次使用需要访问控制台进行初始化设置"
    echo -e "   • 在 AI 中台前端可以创建 Dify AI 应用"
fi
echo -e "   • 服务日志见 ${BLUE}logs/${NC} 目录"
echo -e "   • 如需重新配置环境，运行 ${BLUE}./scripts/setup-environment.sh --force-rebuild${NC}"

echo
echo -e "${BLUE}📈 服务状态：${NC}"
echo -e "   • 后端服务: 运行中 (PID: $BACKEND_PID)"
echo -e "   • 前端服务: 运行中 (PID: $FRONTEND_PID)"
echo -e "   • Docker服务: 运行中"
if [ "$ENABLE_DIFY" = true ]; then
    echo -e "   • Dify服务: 运行中"
fi

echo -e "${GREEN}✅ 所有服务已成功启动并运行${NC}"

# 如果是 daemon 模式，脚本退出，服务继续在后台运行
if [ "$DAEMON_MODE" = true ]; then
    echo
    echo -e "${GREEN}🔄 后台运行模式：脚本退出，服务继续运行${NC}"
    echo -e "${YELLOW}💡 管理提示：${NC}"
    echo -e "   • 查看服务状态: ps aux | grep -E '(python|node).*:(8000|3000)'"
    echo -e "   • 查看服务日志: tail -f logs/{backend,frontend}.log"
    echo -e "   • 停止所有服务: ./stop.sh"
    echo -e "   • 重新启动服务: ./quick-start.sh"
    exit 0
fi

# 保持脚本运行，等待用户中断
echo
echo -e "${YELLOW}🔄 脚本将继续运行以监控服务，按 Ctrl+C 停止所有服务${NC}"
echo -e "${BLUE}💡 提示：可以关闭此终端，服务将继续在后台运行${NC}"
echo -e "${BLUE}💡 或者使用 './quick-start.sh --daemon' 启动后台模式${NC}"

# 等待用户中断或保持运行
while true; do
    sleep 10
    # 检查服务是否还在运行
    if [ -f "logs/backend.pid" ] && ! kill -0 $(cat logs/backend.pid) 2>/dev/null; then
        echo -e "${RED}❌ 后端服务意外停止${NC}"
        break
    fi
    if [ -f "logs/frontend.pid" ] && ! kill -0 $(cat logs/frontend.pid) 2>/dev/null; then
        echo -e "${RED}❌ 前端服务意外停止${NC}"
        break
    fi
done
