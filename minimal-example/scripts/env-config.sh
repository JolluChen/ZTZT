#!/bin/bash

# =============================================================================
# 环境配置管理脚本
# 用于在开发和生产环境之间切换配置文件
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo -e "${BLUE}🔧 环境配置管理工具${NC}"

# 显示帮助信息
show_help() {
    echo "用法: $0 [环境类型]"
    echo
    echo "环境类型:"
    echo "  dev         切换到开发环境配置"
    echo "  prod        切换到生产环境配置"
    echo "  status      查看当前环境配置状态"
    echo "  backup      备份当前配置文件"
    echo "  restore     恢复配置文件"
    echo "  --help, -h  显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 dev      # 切换到开发环境"
    echo "  $0 prod     # 切换到生产环境"
    echo "  $0 status   # 查看当前状态"
}

# 备份配置文件
backup_configs() {
    echo -e "${YELLOW}📦 备份当前配置文件...${NC}"
    
    mkdir -p "$PROJECT_ROOT/.env-backup"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_dir="$PROJECT_ROOT/.env-backup/backup_$timestamp"
    mkdir -p "$backup_dir"
    
    # 备份根目录配置文件
    if [ -f "$PROJECT_ROOT/.env" ]; then
        cp "$PROJECT_ROOT/.env" "$backup_dir/.env"
        echo -e "${GREEN}✅ 已备份 .env${NC}"
    fi
    
    # 备份前端配置文件
    if [ -f "$PROJECT_ROOT/frontend/.env.local" ]; then
        cp "$PROJECT_ROOT/frontend/.env.local" "$backup_dir/.env.local"
        echo -e "${GREEN}✅ 已备份 frontend/.env.local${NC}"
    fi
    
    # 备份后端配置文件
    if [ -f "$PROJECT_ROOT/backend/.env" ]; then
        cp "$PROJECT_ROOT/backend/.env" "$backup_dir/backend.env"
        echo -e "${GREEN}✅ 已备份 backend/.env${NC}"
    fi
    
    echo -e "${GREEN}✅ 配置文件已备份到: $backup_dir${NC}"
}

# 切换到开发环境
switch_to_development() {
    echo -e "${YELLOW}🔄 切换到开发环境配置...${NC}"
    
    # 复制主配置文件
    if [ -f "$PROJECT_ROOT/.env.development" ]; then
        cp "$PROJECT_ROOT/.env.development" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✅ 已设置主配置文件 (.env)${NC}"
    else
        echo -e "${RED}❌ 开发环境配置文件 (.env.development) 不存在${NC}"
        exit 1
    fi
    
    # 复制前端配置文件
    if [ -f "$PROJECT_ROOT/frontend/.env.local.development" ]; then
        cp "$PROJECT_ROOT/frontend/.env.local.development" "$PROJECT_ROOT/frontend/.env.local"
        echo -e "${GREEN}✅ 已设置前端配置文件 (.env.local)${NC}"
    else
        echo -e "${RED}❌ 前端开发环境配置文件 (.env.local.development) 不存在${NC}"
    fi
    
    # 复制后端配置文件
    if [ -f "$PROJECT_ROOT/.env.development" ]; then
        cp "$PROJECT_ROOT/.env.development" "$PROJECT_ROOT/backend/.env"
        echo -e "${GREEN}✅ 已设置后端配置文件 (backend/.env)${NC}"
    fi
    
    # 创建环境标识文件
    echo "development" > "$PROJECT_ROOT/.env-status/current-env"
    echo "$(date)" > "$PROJECT_ROOT/.env-status/last-switch"
    
    echo -e "${GREEN}🎉 已成功切换到开发环境！${NC}"
    echo -e "${BLUE}💡 提示：重启服务以应用新配置${NC}"
}

# 切换到生产环境
switch_to_production() {
    echo -e "${YELLOW}🔄 切换到生产环境配置...${NC}"
    
    # 检查生产环境配置文件是否存在
    if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
        echo -e "${RED}❌ 生产环境配置文件 (.env.production) 不存在${NC}"
        echo -e "${YELLOW}请先创建生产环境配置文件，或使用模板：${NC}"
        echo -e "   cp .env.example .env.production"
        exit 1
    fi
    
    # 警告提示
    echo -e "${RED}⚠️  注意：您即将切换到生产环境配置！${NC}"
    echo -e "${YELLOW}这将覆盖当前的配置文件。确认继续？ (y/N)${NC}"
    read -r confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}已取消切换${NC}"
        exit 0
    fi
    
    # 复制主配置文件
    cp "$PROJECT_ROOT/.env.production" "$PROJECT_ROOT/.env"
    echo -e "${GREEN}✅ 已设置主配置文件 (.env)${NC}"
    
    # 复制前端配置文件
    if [ -f "$PROJECT_ROOT/frontend/.env.local.production" ]; then
        cp "$PROJECT_ROOT/frontend/.env.local.production" "$PROJECT_ROOT/frontend/.env.local"
        echo -e "${GREEN}✅ 已设置前端配置文件 (.env.local)${NC}"
    else
        echo -e "${YELLOW}⚠️  前端生产环境配置文件 (.env.local.production) 不存在${NC}"
    fi
    
    # 复制后端配置文件
    cp "$PROJECT_ROOT/.env.production" "$PROJECT_ROOT/backend/.env"
    echo -e "${GREEN}✅ 已设置后端配置文件 (backend/.env)${NC}"
    
    # 创建环境标识文件
    mkdir -p "$PROJECT_ROOT/.env-status"
    echo "production" > "$PROJECT_ROOT/.env-status/current-env"
    echo "$(date)" > "$PROJECT_ROOT/.env-status/last-switch"
    
    echo -e "${GREEN}🎉 已成功切换到生产环境！${NC}"
    echo -e "${RED}⚠️  重要提示：${NC}"
    echo -e "   • 请检查生产环境配置中的敏感信息（密码、密钥等）"
    echo -e "   • 确保服务器IP地址和端口配置正确"
    echo -e "   • 重启所有服务以应用新配置"
}

# 查看当前环境状态
show_status() {
    echo -e "${BLUE}📊 当前环境配置状态${NC}"
    echo
    
    # 检查环境标识文件
    if [ -f "$PROJECT_ROOT/.env-status/current-env" ]; then
        local current_env=$(cat "$PROJECT_ROOT/.env-status/current-env")
        echo -e "${GREEN}当前环境: $current_env${NC}"
        
        if [ -f "$PROJECT_ROOT/.env-status/last-switch" ]; then
            local last_switch=$(cat "$PROJECT_ROOT/.env-status/last-switch")
            echo -e "${BLUE}上次切换: $last_switch${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  未检测到环境标识文件${NC}"
    fi
    
    echo
    echo -e "${BLUE}配置文件状态：${NC}"
    
    # 检查主配置文件
    if [ -f "$PROJECT_ROOT/.env" ]; then
        local api_url=$(grep "NEXT_PUBLIC_API_URL" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2 || echo "未找到")
        echo -e "  • 主配置文件: ${GREEN}存在${NC} (API: $api_url)"
    else
        echo -e "  • 主配置文件: ${RED}不存在${NC}"
    fi
    
    # 检查前端配置文件
    if [ -f "$PROJECT_ROOT/frontend/.env.local" ]; then
        local frontend_api=$(grep "NEXT_PUBLIC_API_URL" "$PROJECT_ROOT/frontend/.env.local" 2>/dev/null | cut -d'=' -f2 || echo "未找到")
        echo -e "  • 前端配置文件: ${GREEN}存在${NC} (API: $frontend_api)"
    else
        echo -e "  • 前端配置文件: ${RED}不存在${NC}"
    fi
    
    # 检查后端配置文件
    if [ -f "$PROJECT_ROOT/backend/.env" ]; then
        local backend_debug=$(grep "DEBUG" "$PROJECT_ROOT/backend/.env" 2>/dev/null | cut -d'=' -f2 || echo "未找到")
        echo -e "  • 后端配置文件: ${GREEN}存在${NC} (DEBUG: $backend_debug)"
    else
        echo -e "  • 后端配置文件: ${RED}不存在${NC}"
    fi
    
    echo
    echo -e "${BLUE}可用的环境配置模板：${NC}"
    [ -f "$PROJECT_ROOT/.env.development" ] && echo -e "  • ${GREEN}.env.development${NC} (开发环境)" || echo -e "  • ${RED}.env.development (不存在)${NC}"
    [ -f "$PROJECT_ROOT/.env.production" ] && echo -e "  • ${GREEN}.env.production${NC} (生产环境)" || echo -e "  • ${RED}.env.production (不存在)${NC}"
}

# 恢复配置文件
restore_configs() {
    echo -e "${YELLOW}🔄 恢复配置文件...${NC}"
    
    local backup_dir="$PROJECT_ROOT/.env-backup"
    if [ ! -d "$backup_dir" ]; then
        echo -e "${RED}❌ 备份目录不存在${NC}"
        exit 1
    fi
    
    # 列出可用的备份
    echo -e "${BLUE}可用的备份：${NC}"
    ls -la "$backup_dir" | grep "^d" | grep "backup_" | awk '{print "  • " $9}'
    
    echo -e "${YELLOW}请输入要恢复的备份目录名（如：backup_20241218_143000）：${NC}"
    read -r backup_name
    
    local restore_dir="$backup_dir/$backup_name"
    if [ ! -d "$restore_dir" ]; then
        echo -e "${RED}❌ 指定的备份目录不存在${NC}"
        exit 1
    fi
    
    # 恢复文件
    if [ -f "$restore_dir/.env" ]; then
        cp "$restore_dir/.env" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✅ 已恢复 .env${NC}"
    fi
    
    if [ -f "$restore_dir/.env.local" ]; then
        cp "$restore_dir/.env.local" "$PROJECT_ROOT/frontend/.env.local"
        echo -e "${GREEN}✅ 已恢复 frontend/.env.local${NC}"
    fi
    
    if [ -f "$restore_dir/backend.env" ]; then
        cp "$restore_dir/backend.env" "$PROJECT_ROOT/backend/.env"
        echo -e "${GREEN}✅ 已恢复 backend/.env${NC}"
    fi
    
    echo -e "${GREEN}🎉 配置文件恢复完成！${NC}"
}

# 主逻辑
case "${1:-}" in
    "dev"|"development")
        backup_configs
        switch_to_development
        ;;
    "prod"|"production")
        backup_configs
        switch_to_production
        ;;
    "status")
        show_status
        ;;
    "backup")
        backup_configs
        ;;
    "restore")
        restore_configs
        ;;
    "--help"|"-h"|"help")
        show_help
        ;;
    "")
        echo -e "${RED}❌ 请指定环境类型${NC}"
        echo
        show_help
        exit 1
        ;;
    *)
        echo -e "${RED}❌ 未知的环境类型: $1${NC}"
        echo
        show_help
        exit 1
        ;;
esac
