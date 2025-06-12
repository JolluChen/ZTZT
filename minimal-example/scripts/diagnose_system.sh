#!/bin/bash

# AI中台系统诊断脚本
# Author: AI Assistant
# Date: 2025-06-11

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 AI中台系统诊断工具${NC}"
echo "================================"

# 系统信息
echo -e "\n${PURPLE}📋 系统信息${NC}"
echo "----------------------------------------"
echo -e "${CYAN}操作系统:${NC} $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo -e "${CYAN}内核版本:${NC} $(uname -r)"
echo -e "${CYAN}架构:${NC} $(uname -m)"
echo -e "${CYAN}当前用户:${NC} $(whoami)"
echo -e "${CYAN}当前时间:${NC} $(date)"

# 网络诊断
echo -e "\n${PURPLE}🌐 网络连接诊断${NC}"
echo "----------------------------------------"

# 检查基本网络连接
echo -e "${BLUE}测试网络连接...${NC}"
if ping -c 1 8.8.8.8 &> /dev/null; then
    echo -e "${GREEN}✅ 基础网络连接正常${NC}"
else
    echo -e "${RED}❌ 基础网络连接异常${NC}"
fi

# 检查DNS解析
echo -e "${BLUE}测试DNS解析...${NC}"
if nslookup docker.io &> /dev/null; then
    echo -e "${GREEN}✅ DNS解析正常${NC}"
else
    echo -e "${RED}❌ DNS解析异常${NC}"
fi

# 检查Docker Hub连接
echo -e "${BLUE}测试Docker Hub连接...${NC}"
if curl -s --connect-timeout 10 https://index.docker.io/v1/ &> /dev/null; then
    echo -e "${GREEN}✅ Docker Hub连接正常${NC}"
else
    echo -e "${YELLOW}⚠️ Docker Hub连接超时，将使用本地离线方式${NC}"
fi

# 检查本地Docker镜像
echo -e "${BLUE}检查本地Docker镜像...${NC}"
if docker images | grep -q "postgres\|redis\|minio"; then
    echo -e "${GREEN}✅ 发现本地Docker镜像${NC}"
    echo -e "${CYAN}本地可用镜像:${NC}"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | head -10 | sed 's/^/    /'
else
    echo -e "${YELLOW}⚠️ 本地Docker镜像较少，建议预先准备镜像${NC}"
fi

# Docker诊断
echo -e "\n${PURPLE}🐳 Docker环境诊断${NC}"
echo "----------------------------------------"

# 检查Docker安装
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker已安装${NC}"
    echo -e "${CYAN}版本:${NC} $(docker --version)"
else
    echo -e "${RED}❌ Docker未安装${NC}"
    echo -e "${YELLOW}安装建议: curl -fsSL https://get.docker.com | sh${NC}"
fi

# 检查Docker服务状态
if systemctl is-active --quiet docker 2>/dev/null; then
    echo -e "${GREEN}✅ Docker服务运行中${NC}"
else
    echo -e "${RED}❌ Docker服务未运行${NC}"
    echo -e "${YELLOW}启动建议: sudo systemctl start docker${NC}"
fi

# 检查Docker权限
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ Docker权限正常${NC}"
else
    echo -e "${YELLOW}⚠️ Docker权限异常，可能需要sudo或加入docker组${NC}"
    echo -e "${YELLOW}解决建议: sudo usermod -aG docker \$USER${NC}"
fi

# 检查Docker Compose
if docker compose version &> /dev/null; then
    echo -e "${GREEN}✅ Docker Compose可用${NC}"
    echo -e "${CYAN}版本:${NC} $(docker compose version --short)"
else
    echo -e "${RED}❌ Docker Compose不可用${NC}"
fi

# 检查Docker镜像源配置
echo -e "\n${BLUE}Docker镜像源配置:${NC}"
if [ -f /etc/docker/daemon.json ]; then
    echo -e "${GREEN}✅ 发现Docker配置文件${NC}"
    if grep -q "registry-mirrors" /etc/docker/daemon.json 2>/dev/null; then
        echo -e "${GREEN}✅ 已配置镜像源${NC}"
        echo -e "${CYAN}配置的镜像源:${NC}"
        grep -A 5 "registry-mirrors" /etc/docker/daemon.json | grep "https" | sed 's/.*"https/    https/' | sed 's/",//'
    else
        echo -e "${YELLOW}⚠️ 未配置镜像源${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ 未找到Docker配置文件${NC}"
fi

# GPU环境诊断
echo -e "\n${PURPLE}🎮 GPU环境诊断${NC}"
echo "----------------------------------------"

# 检查NVIDIA驱动
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✅ NVIDIA驱动已安装${NC}"
    echo -e "${CYAN}GPU信息:${NC}"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits | while read line; do
        echo "    $line"
    done
else
    echo -e "${YELLOW}⚠️ 未检测到NVIDIA GPU或驱动${NC}"
fi

# 检查Docker GPU支持
if docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✅ Docker GPU支持正常${NC}"
else
    echo -e "${YELLOW}⚠️ Docker GPU支持异常或未配置${NC}"
fi

# 存储空间诊断
echo -e "\n${PURPLE}💾 存储空间诊断${NC}"
echo "----------------------------------------"
echo -e "${CYAN}磁盘使用情况:${NC}"
df -h | grep -E '^/dev/' | awk '{print "    " $1 ": " $3 "/" $2 " (" $5 " 已使用)"}'

echo -e "\n${CYAN}Docker存储使用:${NC}"
if command -v docker &> /dev/null && docker info &> /dev/null; then
    docker system df 2>/dev/null | tail -n +2 | while read line; do
        echo "    $line"
    done
else
    echo "    无法获取Docker存储信息"
fi

# 内存诊断
echo -e "\n${PURPLE}🧠 内存诊断${NC}"
echo "----------------------------------------"
echo -e "${CYAN}内存使用情况:${NC}"
free -h | awk 'NR==2{printf "    总内存: %s, 已使用: %s, 可用: %s (%.2f%% 已使用)\n", $2, $3, $7, $3/$2*100}'

# 端口使用诊断
echo -e "\n${PURPLE}🔌 端口使用诊断${NC}"
echo "----------------------------------------"
echo -e "${CYAN}AI中台相关端口检查:${NC}"
ports=(8000 8100 3001 3002 5432 6379 9000 9001 9090 11434)
for port in "${ports[@]}"; do
    if ss -tuln | grep -q ":$port "; then
        echo -e "${YELLOW}⚠️ 端口 $port 已被占用${NC}"
    else
        echo -e "${GREEN}✅ 端口 $port 可用${NC}"
    fi
done

# 项目文件诊断
echo -e "\n${PURPLE}📁 项目文件诊断${NC}"
echo "----------------------------------------"
required_files=(
    "docker-compose.yml"
    "start.sh"
    "stop.sh"
    "reset.sh"
    "backend/requirements.txt"
    "backend/manage.py"
    "scripts/generate_sample_models.py"
    "scripts/manage_triton_models.py"
    "scripts/diagnose_system.sh"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file 存在${NC}"
    else
        echo -e "${RED}❌ $file 缺失${NC}"
    fi
done

# 提供解决建议
echo -e "\n${PURPLE}💡 问题解决建议${NC}"
echo "----------------------------------------"

echo -e "\n${BLUE}1. 网络连接问题:${NC}"
echo "   • 如果Docker镜像拉取失败，使用本地开发模式: ./start_local.sh"
echo "   • 预先在有网络的环境下拉取所需镜像"
echo "   • 使用离线镜像包或本地镜像仓库"

echo -e "\n${BLUE}2. Docker问题:${NC}"
echo "   • 确保Docker服务运行: sudo systemctl start docker"
echo "   • 添加用户到docker组: sudo usermod -aG docker \$USER"
echo "   • 重启后重新登录: logout 然后重新登录"

echo -e "\n${BLUE}3. 权限问题:${NC}"
echo "   • 给脚本添加执行权限: chmod +x *.sh"
echo "   • 给Python脚本添加执行权限: chmod +x scripts/*.py tests/*.py"
echo "   • 某些操作可能需要sudo权限"

echo -e "\n${BLUE}4. 存储空间不足:${NC}"
echo "   • 清理Docker: docker system prune -a"
echo "   • 删除未使用的镜像: docker image prune -a"
echo "   • 清理系统临时文件"

echo -e "\n${BLUE}5. 启动建议:${NC}"
echo "   • 自动模式: ./start.sh（推荐，自动选择最佳模式）"
echo "   • 完整模式: ./start.sh --full（Docker + 网络）"
echo "   • 离线模式: ./start.sh --offline（Docker，无网络）"
echo "   • 本地模式: ./start.sh --local（Python，无Docker）"
echo "   • 停止所有服务: ./stop.sh"
echo "   • 完全重置系统: ./reset.sh"
echo "   • 系统诊断: bash scripts/diagnose_system.sh"
echo "   • 生成示例模型: python3 scripts/generate_sample_models.py"

echo ""
echo -e "${GREEN}🎯 诊断完成！根据上述建议解决问题后重新启动服务。${NC}"
echo ""