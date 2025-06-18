#!/bin/bash

# =============================================================================
# Dify 数据库初始化脚本
# 用于在 setup-environment.sh 中初始化 Dify 数据库
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 开始配置 Dify 环境...${NC}"
echo -e "${YELLOW}⚠️  跳过数据库初始化，将通过Web界面完成${NC}"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查 Dify API 容器是否存在
if ! docker images | grep -q "ai-platform-dify-api"; then
    echo -e "${RED}❌ Dify API 镜像不存在，无法启动 Dify 服务${NC}"
    exit 1
fi

# 启动 Dify 所需的数据库服务
echo -e "${BLUE}启动 Dify 数据库服务...${NC}"

# 检查并加载本地 weaviate 镜像
if ! docker images | grep -q "semitechnologies/weaviate"; then
    echo -e "${YELLOW}⚠️ 未找到 weaviate 镜像，尝试从本地包加载...${NC}"
    
    if [ -f "/home/lsyzt/ZTZT/packages/docker-images/weaviate.tar" ]; then
        echo -e "${BLUE}从本地加载 weaviate 镜像...${NC}"
        docker load -i /home/lsyzt/ZTZT/packages/docker-images/weaviate.tar
        echo -e "${GREEN}✅ weaviate 镜像加载成功${NC}"
    elif [ -f "/home/lsyzt/ZTZT/packages/docker-images/weaviate-1.22.4.tar" ]; then
        echo -e "${BLUE}从本地加载 weaviate-1.22.4 镜像...${NC}"
        docker load -i /home/lsyzt/ZTZT/packages/docker-images/weaviate-1.22.4.tar
        # 为确保兼容性，创建标签别名
        docker tag semitechnologies/weaviate:1.22.4 semitechnologies/weaviate:1.24.4 2>/dev/null || true
        echo -e "${GREEN}✅ weaviate 镜像加载成功${NC}"
    else
        echo -e "${RED}❌ 本地 weaviate 镜像未找到，请检查 packages/docker-images 目录${NC}"
        exit 1
    fi
fi

cd docker
docker compose -f docker-compose.yml up -d dify-postgres >/dev/null 2>&1
docker compose -f docker-compose.yml up -d dify-redis >/dev/null 2>&1
docker compose -f docker-compose.yml up -d dify-weaviate >/dev/null 2>&1
cd ..

# 等待 Dify Postgres 数据库就绪
echo -e "${BLUE}等待 Dify PostgreSQL 就绪...${NC}"
until docker exec dify_postgres pg_isready -U dify_user 2>/dev/null; do
    echo -e "${YELLOW}⏳ 等待 Dify 数据库启动...${NC}"
    sleep 2
done
echo -e "${GREEN}✅ Dify PostgreSQL 就绪${NC}"

echo -e "${GREEN}✅ Dify 基础服务已启动！${NC}"
echo -e "${YELLOW}💡 Dify 数据库初始化将通过Web界面完成${NC}"
echo -e "   访问地址: http://192.168.110.88:8001/install"
echo -e "${YELLOW}⚠️  首次访问时需要创建管理员账户并完成初始化${NC}"
