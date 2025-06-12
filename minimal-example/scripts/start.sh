#!/bin/bash

# =============================================================================
# AI中台一键启动脚本
# 作者: ZTZT AI Platform Team
# 版本: 1.0.0
# 描述: 一键启动后端Django服务和前端Next.js服务
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"
FRONTEND_DIR="${SCRIPT_DIR}/frontend"
VENV_DIR="${SCRIPT_DIR}/venv"
LOGS_DIR="${SCRIPT_DIR}/logs"
PID_DIR="${LOGS_DIR}/pids"

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=3000

# PID文件
BACKEND_PID_FILE="${PID_DIR}/backend.pid"
FRONTEND_PID_FILE="${PID_DIR}/frontend.pid"

# 日志文件
BACKEND_LOG_FILE="${LOGS_DIR}/backend.log"
FRONTEND_LOG_FILE="${LOGS_DIR}/frontend.log"

# =============================================================================
# 工具函数
# =============================================================================

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🤖 AI中台启动脚本                        ║"
    echo "║               ZTZT AI Platform Startup Script                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${CYAN}🔄 $1${NC}"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "命令 '$1' 未找到，请先安装"
        return 1
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 等待端口可用
wait_for_port() {
    local port=$1
    local timeout=${2:-30}
    local count=0
    
    print_step "等待端口 $port 可用..."
    while ! nc -z localhost $port 2>/dev/null; do
        if [ $count -ge $timeout ]; then
            print_error "等待端口 $port 超时"
            return 1
        fi
        sleep 1
        count=$((count + 1))
    done
    print_success "端口 $port 已可用"
}

# 创建必要的目录
create_directories() {
    print_step "创建必要的目录..."
    mkdir -p "$LOGS_DIR"
    mkdir -p "$PID_DIR"
    print_success "目录创建完成"
}

# 检查依赖环境
check_dependencies() {
    print_step "检查系统依赖..."
    
    # 检查Python
    if ! check_command python3; then
        print_error "请先安装 Python 3.10+"
        exit 1
    fi
    
    # 检查Node.js
    if ! check_command node; then
        print_error "请先安装 Node.js 18+"
        exit 1
    fi
    
    # 检查npm
    if ! check_command npm; then
        print_error "请先安装 npm"
        exit 1
    fi
    
    print_success "系统依赖检查完成"
}

# 设置Python虚拟环境
setup_venv() {
    print_step "设置Python虚拟环境..."
    
    if [ ! -d "$VENV_DIR" ]; then
        print_info "创建新的虚拟环境..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 升级pip
    pip install --upgrade pip
    
    print_success "虚拟环境设置完成"
}

# 安装后端依赖
install_backend_deps() {
    print_step "安装后端依赖..."
    
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "后端依赖安装完成"
    else
        print_error "未找到 requirements.txt 文件"
        exit 1
    fi
}

# 安装前端依赖
install_frontend_deps() {
    print_step "安装前端依赖..."
    
    cd "$FRONTEND_DIR"
    
    if [ -f "package.json" ]; then
        if [ ! -d "node_modules" ]; then
            npm install
        else
            print_info "前端依赖已存在，跳过安装"
        fi
        print_success "前端依赖安装完成"
    else
        print_error "未找到 package.json 文件"
        exit 1
    fi
}

# 初始化数据库
init_database() {
    print_step "初始化数据库..."
    
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    
    # 检查是否需要迁移
    if [ ! -f "db.sqlite3" ]; then
        print_info "执行数据库迁移..."
        python manage.py migrate
        print_success "数据库迁移完成"
    else
        print_info "数据库已存在，跳过迁移"
    fi
}

# 启动后端服务
start_backend() {
    print_step "启动后端服务..."
    
    # 检查端口是否被占用
    if check_port $BACKEND_PORT; then
        print_warning "端口 $BACKEND_PORT 已被占用，尝试停止现有服务..."
        stop_backend
        sleep 2
    fi
    
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    
    # 启动后端服务（后台运行）
    nohup python manage.py runserver 0.0.0.0:$BACKEND_PORT > "$BACKEND_LOG_FILE" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
    
    # 等待服务启动
    wait_for_port $BACKEND_PORT
    print_success "后端服务已启动 (PID: $(cat $BACKEND_PID_FILE))"
    print_info "后端访问地址: http://localhost:$BACKEND_PORT"
    print_info "后端日志文件: $BACKEND_LOG_FILE"
}

# 启动前端服务
start_frontend() {
    print_step "启动前端服务..."
    
    # 检查端口是否被占用
    if check_port $FRONTEND_PORT; then
        print_warning "端口 $FRONTEND_PORT 已被占用，尝试停止现有服务..."
        stop_frontend
        sleep 2
    fi
    
    cd "$FRONTEND_DIR"
    
    # 启动前端服务（后台运行）
    nohup npm run dev > "$FRONTEND_LOG_FILE" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
    
    # 等待服务启动
    wait_for_port $FRONTEND_PORT
    print_success "前端服务已启动 (PID: $(cat $FRONTEND_PID_FILE))"
    print_info "前端访问地址: http://localhost:$FRONTEND_PORT"
    print_info "前端日志文件: $FRONTEND_LOG_FILE"
}

# 停止后端服务
stop_backend() {
    if [ -f "$BACKEND_PID_FILE" ]; then
        local pid=$(cat "$BACKEND_PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            print_success "后端服务已停止 (PID: $pid)"
        else
            print_warning "后端服务进程不存在 (PID: $pid)"
        fi
        rm -f "$BACKEND_PID_FILE"
    else
        print_warning "未找到后端PID文件"
    fi
    
    # 强制杀死占用端口的进程
    if check_port $BACKEND_PORT; then
        local port_pid=$(lsof -ti:$BACKEND_PORT)
        if [ -n "$port_pid" ]; then
            kill -9 $port_pid 2>/dev/null || true
            print_info "强制停止端口 $BACKEND_PORT 上的进程"
        fi
    fi
}

# 停止前端服务
stop_frontend() {
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            print_success "前端服务已停止 (PID: $pid)"
        else
            print_warning "前端服务进程不存在 (PID: $pid)"
        fi
        rm -f "$FRONTEND_PID_FILE"
    else
        print_warning "未找到前端PID文件"
    fi
    
    # 强制杀死占用端口的进程
    if check_port $FRONTEND_PORT; then
        local port_pid=$(lsof -ti:$FRONTEND_PORT)
        if [ -n "$port_pid" ]; then
            kill -9 $port_pid 2>/dev/null || true
            print_info "强制停止端口 $FRONTEND_PORT 上的进程"
        fi
    fi
}

# 检查服务状态
check_status() {
    echo
    print_info "=== 服务状态检查 ==="
    
    # 检查后端状态
    if [ -f "$BACKEND_PID_FILE" ]; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        if ps -p $backend_pid > /dev/null 2>&1; then
            print_success "后端服务运行中 (PID: $backend_pid, 端口: $BACKEND_PORT)"
        else
            print_error "后端服务未运行 (PID文件存在但进程不存在)"
        fi
    else
        print_error "后端服务未运行 (无PID文件)"
    fi
    
    # 检查前端状态
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        if ps -p $frontend_pid > /dev/null 2>&1; then
            print_success "前端服务运行中 (PID: $frontend_pid, 端口: $FRONTEND_PORT)"
        else
            print_error "前端服务未运行 (PID文件存在但进程不存在)"
        fi
    else
        print_error "前端服务未运行 (无PID文件)"
    fi
    
    echo
    print_info "=== 端口占用情况 ==="
    if check_port $BACKEND_PORT; then
        print_info "端口 $BACKEND_PORT (后端): 已占用"
    else
        print_warning "端口 $BACKEND_PORT (后端): 空闲"
    fi
    
    if check_port $FRONTEND_PORT; then
        print_info "端口 $FRONTEND_PORT (前端): 已占用"
    else
        print_warning "端口 $FRONTEND_PORT (前端): 空闲"
    fi
}

# 显示访问地址
show_urls() {
    echo
    print_info "=== 🌟 访问地址 ==="
    echo -e "${GREEN}🏠 后端API主页:    ${CYAN}http://localhost:$BACKEND_PORT/${NC}"
    echo -e "${GREEN}📚 Swagger文档:    ${CYAN}http://localhost:$BACKEND_PORT/swagger/${NC}"
    echo -e "${GREEN}📖 ReDoc文档:      ${CYAN}http://localhost:$BACKEND_PORT/redoc/${NC}"
    echo -e "${GREEN}⚙️  管理后台:       ${CYAN}http://localhost:$BACKEND_PORT/admin/${NC}"
    echo -e "${GREEN}🎨 前端界面:       ${CYAN}http://localhost:$FRONTEND_PORT/${NC}"
    echo
    print_info "🔑 管理员账户: admin / admin123"
}

# 显示日志
show_logs() {
    local service=$1
    case $service in
        "backend")
            if [ -f "$BACKEND_LOG_FILE" ]; then
                echo -e "${BLUE}=== 后端日志 ===${NC}"
                tail -f "$BACKEND_LOG_FILE"
            else
                print_error "后端日志文件不存在"
            fi
            ;;
        "frontend")
            if [ -f "$FRONTEND_LOG_FILE" ]; then
                echo -e "${BLUE}=== 前端日志 ===${NC}"
                tail -f "$FRONTEND_LOG_FILE"
            else
                print_error "前端日志文件不存在"
            fi
            ;;
        *)
            print_error "无效的服务名称。使用: backend 或 frontend"
            ;;
    esac
}

# 显示帮助信息
show_help() {
    echo -e "${CYAN}用法: $0 [命令]${NC}"
    echo
    echo -e "${YELLOW}可用命令:${NC}"
    echo -e "  ${GREEN}start${NC}         启动所有服务 (默认)"
    echo -e "  ${GREEN}stop${NC}          停止所有服务"
    echo -e "  ${GREEN}restart${NC}       重启所有服务"
    echo -e "  ${GREEN}status${NC}        检查服务状态"
    echo -e "  ${GREEN}backend${NC}       仅启动后端服务"
    echo -e "  ${GREEN}frontend${NC}      仅启动前端服务"
    echo -e "  ${GREEN}stop-backend${NC}  仅停止后端服务"
    echo -e "  ${GREEN}stop-frontend${NC} 仅停止前端服务"
    echo -e "  ${GREEN}logs backend${NC}  查看后端日志"
    echo -e "  ${GREEN}logs frontend${NC} 查看前端日志"
    echo -e "  ${GREEN}urls${NC}          显示访问地址"
    echo -e "  ${GREEN}help${NC}          显示此帮助信息"
    echo
    echo -e "${YELLOW}示例:${NC}"
    echo -e "  $0                    # 启动所有服务"
    echo -e "  $0 start              # 启动所有服务"
    echo -e "  $0 stop               # 停止所有服务"
    echo -e "  $0 status             # 检查状态"
    echo -e "  $0 logs backend       # 查看后端日志"
}

# =============================================================================
# 主函数
# =============================================================================

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 解析命令行参数
case "${1:-start}" in
    "start")
        print_header
        create_directories
        check_dependencies
        setup_venv
        install_backend_deps
        install_frontend_deps
        init_database
        start_backend
        start_frontend
        show_urls
        print_success "🎉 所有服务启动完成！"
        ;;
    
    "stop")
        print_header
        print_step "停止所有服务..."
        stop_backend
        stop_frontend
        print_success "🛑 所有服务已停止"
        ;;
    
    "restart")
        print_header
        print_step "重启所有服务..."
        stop_backend
        stop_frontend
        sleep 2
        start_backend
        start_frontend
        show_urls
        print_success "🔄 所有服务重启完成！"
        ;;
    
    "status")
        print_header
        check_status
        ;;
    
    "backend")
        print_header
        create_directories
        check_dependencies
        setup_venv
        install_backend_deps
        init_database
        start_backend
        print_success "🎉 后端服务启动完成！"
        ;;
    
    "frontend")
        print_header
        create_directories
        check_dependencies
        install_frontend_deps
        start_frontend
        print_success "🎉 前端服务启动完成！"
        ;;
    
    "stop-backend")
        print_step "停止后端服务..."
        stop_backend
        ;;
    
    "stop-frontend")
        print_step "停止前端服务..."
        stop_frontend
        ;;
    
    "logs")
        if [ -n "$2" ]; then
            show_logs "$2"
        else
            print_error "请指定服务名称: backend 或 frontend"
            exit 1
        fi
        ;;
    
    "urls")
        show_urls
        ;;
    
    "help"|"-h"|"--help")
        print_header
        show_help
        ;;
    
    *)
        print_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac
