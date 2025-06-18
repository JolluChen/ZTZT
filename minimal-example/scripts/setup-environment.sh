#!/bin/bash

# =============================================================================
# AI中台 + Dify 环境配置脚本
# 一次性完成所有环境配置：镜像构建、数据库初始化、网络创建等
# 只需要运行一次，后续使用 quick-start.sh 启动服务即可
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 开始配置 AI中台 + Dify AI平台 环境${NC}"
echo -e "${YELLOW}⚠️  这是一次性环境配置，可能需要较长时间完成${NC}"
echo

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 设置国内镜像源环境变量
echo -e "${BLUE}🌐 配置国内镜像源...${NC}"
source "${SCRIPT_DIR}/setup-mirrors.sh"

echo -e "${BLUE}🌐 使用国内镜像源加速下载${NC}"
echo -e "   PyPI: ${PIP_INDEX_URL}"
echo -e "   NPM: ${NPM_CONFIG_REGISTRY}"
echo

# 配置选项
SETUP_DIFY=true
FORCE_REBUILD=false

for arg in "$@"; do
    case $arg in
        --no-dify)
            SETUP_DIFY=false
            shift
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --no-dify         跳过 Dify 环境配置"
            echo "  --force-rebuild   强制重新构建所有镜像"
            echo "  --help, -h        显示此帮助信息"
            exit 0
            ;;
    esac
done

# 获取项目根目录
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}📍 项目根目录: $PROJECT_ROOT${NC}"

# 本地镜像加载函数
load_local_image() {
    local image_name=$1
    local image_tag=${2:-"latest"}
    local packages_dir="/home/lsyzt/ZTZT/packages/docker-images"
    
    echo -e "${BLUE}检查镜像: ${image_name}:${image_tag}${NC}"
    
    # 检查镜像是否已存在
    if docker images | grep -q "${image_name}.*${image_tag}"; then
        echo -e "${GREEN}✅ 镜像 ${image_name}:${image_tag} 已存在${NC}"
        return 0
    fi
    
    # 尝试从本地加载镜像
    echo -e "${YELLOW}⚠️ 镜像不存在，尝试从本地包加载...${NC}"
    
    # 尝试多种可能的文件名
    local possible_files=(
        "${packages_dir}/${image_name}-${image_tag}.tar"
        "${packages_dir}/${image_name}.tar"
        "${packages_dir}/${image_name//\//-}-${image_tag}.tar"
        "${packages_dir}/${image_name//\//-}.tar"
    )
    
    for file in "${possible_files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${BLUE}从本地加载镜像: $file${NC}"
            docker load -i "$file"
            echo -e "${GREEN}✅ 镜像加载成功: ${image_name}${NC}"
            return 0
        fi
    done
    
    echo -e "${RED}❌ 本地镜像文件未找到: ${image_name}${NC}"
    return 1
}

# 1. 检查必要的工具
echo -e "${YELLOW}🔍 步骤1: 检查必要工具${NC}"
echo -e "${BLUE}检查 Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

echo -e "${BLUE}检查 Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    exit 1
fi

echo -e "${BLUE}检查 Python 虚拟环境...${NC}"
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠️  后端虚拟环境不存在，正在创建...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    # 使用中国 PyPI 镜像源
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
    pip install -r requirements.txt
    cd ..
fi

echo -e "${BLUE}检查 Node.js 依赖...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  前端依赖不存在，正在安装...${NC}"
    cd frontend
    # 设置 npm 中国镜像源
    npm config set registry https://registry.npmmirror.com/
    npm install
    cd ..
fi

echo -e "${GREEN}✅ 工具检查完成${NC}"

# 2. 创建 Docker 网络
echo -e "${YELLOW}🌐 步骤2: 创建 Docker 网络${NC}"
docker network create ai_platform_network 2>/dev/null || echo -e "${YELLOW}⚠️  网络已存在${NC}"
echo -e "${GREEN}✅ Docker 网络就绪${NC}"

# 3. 检查基础镜像（跳过构建，使用本地开发模式）
echo -e "${YELLOW}📦 步骤3: 检查基础镜像${NC}"

# 加载基础服务所需的 Docker 镜像
echo -e "${BLUE}加载基础服务镜像...${NC}"
load_local_image "postgres" "16"
load_local_image "redis" "7.2"
load_local_image "bitnami/minio" "2024.6.4-debian-12-r0"

# 跳过 Django 镜像构建（使用本地 Python 虚拟环境）
echo -e "${BLUE}Django 后端使用本地虚拟环境运行，跳过镜像构建${NC}"

# 跳过 Next.js 镜像构建（使用本地 npm 运行）
echo -e "${BLUE}Next.js 前端使用本地 npm 运行，跳过镜像构建${NC}"

echo -e "${GREEN}✅ 镜像检查完成（使用本地开发模式）${NC}"

# 4. 启动基础服务并配置
echo -e "${YELLOW}🗄️  步骤4: 启动和配置基础服务${NC}"
cd docker

echo -e "${BLUE}启动 PostgreSQL...${NC}"
docker compose -f docker-compose.yml up -d postgres
sleep 5

echo -e "${BLUE}启动 MinIO...${NC}"
docker compose -f docker-compose.yml up -d minio
sleep 3

echo -e "${GREEN}✅ 基础服务已启动${NC}"

# 等待数据库就绪
echo -e "${BLUE}等待 PostgreSQL 就绪...${NC}"
until docker exec ai_platform_postgres pg_isready -U ai_user; do
    echo -e "${YELLOW}⏳ 等待数据库启动...${NC}"
    sleep 2
done
echo -e "${GREEN}✅ PostgreSQL 就绪${NC}"

# 初始化数据库
echo -e "${BLUE}初始化 AI 中台数据库...${NC}"
cd ..
cd backend
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}✅ AI 中台数据库初始化完成${NC}"
deactivate
cd ..

# 5. Dify 环境配置
if [ "$SETUP_DIFY" = true ]; then
    echo -e "${YELLOW}🤖 步骤5: 配置 Dify 环境${NC}"
    
    # 加载必要的 Docker 镜像
    echo -e "${BLUE}加载 Dify 所需的基础镜像...${NC}"
    
    # 加载 weaviate 镜像
    if ! load_local_image "semitechnologies/weaviate" "1.24.4"; then
        # 尝试加载其他版本的 weaviate
        if load_local_image "weaviate" "1.22.4"; then
            # 创建标签别名以保证兼容性
            docker tag semitechnologies/weaviate:1.22.4 semitechnologies/weaviate:1.24.4 2>/dev/null || true
        else
            echo -e "${RED}❌ 无法加载 weaviate 镜像${NC}"
            SETUP_DIFY=false
        fi
    fi
    
    # 如果基础镜像加载失败，跳过 Dify 配置
    if [ "$SETUP_DIFY" = false ]; then
        echo -e "${YELLOW}⚠️ 由于缺少必要镜像，跳过 Dify 环境配置${NC}"
    else
        # 检查 Dify 源码
        DIFY_REPO_PATH="/home/lsyzt/ZTZT/dify-repo"
        if [ ! -d "$DIFY_REPO_PATH" ]; then
            echo -e "${YELLOW}⚠️  Dify 源码目录不存在: $DIFY_REPO_PATH${NC}"
            echo -e "${BLUE}尝试从预构建镜像获取 Dify 服务...${NC}"
            
            # 检查是否有预构建的 Dify 镜像
            if docker images | grep -q "langgenius/dify-api" && docker images | grep -q "langgenius/dify-web"; then
                echo -e "${GREEN}✅ 发现预构建的 Dify 镜像${NC}"
                # 为预构建镜像创建别名
                docker tag langgenius/dify-api:latest ai-platform-dify-api:latest 2>/dev/null || true
                docker tag langgenius/dify-web:latest ai-platform-dify-web:latest 2>/dev/null || true
            else
                echo -e "${YELLOW}⚠️  未发现 Dify 镜像，将跳过 Dify 环境配置${NC}"
                echo -e "${BLUE}如需启用 Dify，请：${NC}"
                echo -e "   1. 下载 Dify 源码到 $DIFY_REPO_PATH，或"
                echo -e "   2. 将 Dify 镜像文件放入 /home/lsyzt/ZTZT/packages/docker-images/ 目录"
                SETUP_DIFY=false
            fi
        else
            # 构建 Dify 镜像
            echo -e "${BLUE}从源码构建 Dify API 镜像...${NC}"
            if [ "$FORCE_REBUILD" = true ] || ! docker images | grep -q "ai-platform-dify-api"; then
                if [ -f "$DIFY_REPO_PATH/api/Dockerfile" ]; then
                    # 使用国内镜像源构建
                    docker build -t ai-platform-dify-api "$DIFY_REPO_PATH/api" ${DOCKER_BUILD_ARGS}
                    echo -e "${GREEN}✅ Dify API 镜像构建完成${NC}"
                else
                    echo -e "${RED}❌ Dify API Dockerfile 不存在${NC}"
                    SETUP_DIFY=false
                fi
            else
                echo -e "${YELLOW}⚠️  Dify API 镜像已存在，跳过构建${NC}"
            fi
            
            echo -e "${BLUE}从源码构建 Dify Web 镜像...${NC}"
            if [ "$FORCE_REBUILD" = true ] || ! docker images | grep -q "ai-platform-dify-web"; then
                if [ -f "$DIFY_REPO_PATH/web/Dockerfile" ]; then
                    # 使用国内镜像源构建
                    docker build -t ai-platform-dify-web "$DIFY_REPO_PATH/web" ${DOCKER_BUILD_ARGS}
                    echo -e "${GREEN}✅ Dify Web 镜像构建完成${NC}"
                else
                    echo -e "${RED}❌ Dify Web Dockerfile 不存在${NC}"
                    SETUP_DIFY=false
                fi
            else
                echo -e "${YELLOW}⚠️  Dify Web 镜像已存在，跳过构建${NC}"
            fi
        fi
        
        # 只有在镜像存在的情况下才初始化数据库
        if [ "$SETUP_DIFY" = true ] && (docker images | grep -q "ai-platform-dify-api"); then
            # 初始化 Dify 数据库
            echo -e "${BLUE}初始化 Dify 数据库...${NC}"
            if [ -f "scripts/init-dify.sh" ]; then
                chmod +x scripts/init-dify.sh
                ./scripts/init-dify.sh
                echo -e "${GREEN}✅ Dify 数据库初始化完成${NC}"
            else
                echo -e "${RED}❌ Dify 初始化脚本不存在${NC}"
                SETUP_DIFY=false
            fi
        fi
    fi
    
    if [ "$SETUP_DIFY" = true ]; then
        echo -e "${GREEN}✅ Dify 环境配置完成${NC}"
    else
        echo -e "${YELLOW}⚠️  Dify 环境配置失败或跳过${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  跳过 Dify 环境配置${NC}"
fi

# 6. 创建启动标记文件
echo -e "${YELLOW}📝 步骤6: 创建环境标记${NC}"
mkdir -p .env-status
echo "$(date)" > .env-status/last-setup
if [ "$SETUP_DIFY" = true ]; then
    touch .env-status/dify-configured
fi
echo -e "${GREEN}✅ 环境标记已创建${NC}"

# 7. 创建必要目录
echo -e "${YELLOW}📁 步骤7: 创建运行时目录${NC}"
mkdir -p logs
mkdir -p data/uploads
mkdir -p data/media
echo -e "${GREEN}✅ 运行时目录已创建${NC}"

# 完成
echo
echo -e "${GREEN}🎉 ===== 环境配置完成！ =====${NC}"
echo -e "${GREEN}✅ Docker 网络已创建${NC}"
echo -e "${GREEN}✅ 基础服务已配置${NC}"
echo -e "${GREEN}✅ 数据库已初始化${NC}"
if [ "$SETUP_DIFY" = true ]; then
    echo -e "${GREEN}✅ Dify 环境已配置${NC}"
fi
echo
echo -e "${BLUE}📋 镜像列表：${NC}"
docker images | grep -E "(ai-platform|postgres|redis|minio|nginx)" | head -10

echo
echo -e "${YELLOW}💡 下一步：${NC}"
echo -e "   使用 ${GREEN}./quick-start.sh${NC} 启动所有服务"
echo -e "   使用 ${GREEN}./stop.sh${NC} 停止所有服务"
echo
echo -e "${BLUE}🔧 如需重新配置环境：${NC}"
echo -e "   ${YELLOW}./scripts/setup-environment.sh --force-rebuild${NC}"
