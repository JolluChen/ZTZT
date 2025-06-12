# ✅ AI中台 - 部署检查清单 (Ubuntu 24.04 LTS)

## 📋 文档概述

本检查清单提供AI中台完整部署过程的验证要点，确保系统的每个组件都正确安装、配置和运行。

> **⏱️ 预计检查时间**: 1-2小时  
> **🎯 检查目标**: 全面验证部署成功

## 🎯 部署阶段检查

### 第一阶段：环境部署检查 ✅

#### 1.1 操作系统安装
- [ ] Ubuntu 24.04 LTS 已正确安装
- [ ] 系统已更新到最新版本
- [ ] 网络连接正常
- [ ] 用户权限配置正确
- [ ] SSH访问已配置（如需要）

**验证命令:**
```bash
# 检查系统版本
lsb_release -a

# 检查系统更新状态
apt list --upgradable
```

#### 1.2 基础软件包
- [ ] Git 已安装并配置
- [ ] Curl 和 Wget 已安装
- [ ] 文本编辑器已安装
- [ ] 系统监控工具已配置

**验证命令:**
```bash
# 检查必需软件包
which git curl wget nano htop
```

### 第二阶段：服务器部署检查 ✅

#### 2.1 PostgreSQL 数据库
- [ ] PostgreSQL 16 已安装
- [ ] 数据库服务正在运行
- [ ] ai_platform 数据库已创建
- [ ] 数据库用户已配置
- [ ] 连接权限已设置

**验证命令:**
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 测试数据库连接
sudo -u postgres psql -c "\l" | grep ai_platform
```

#### 2.2 Redis 缓存服务
- [ ] Redis 服务器已安装
- [ ] Redis 服务正在运行
- [ ] 缓存配置已优化
- [ ] 内存使用正常

**验证命令:**
```bash
# 检查Redis状态
sudo systemctl status redis-server

# 测试Redis连接
redis-cli ping
```

#### 2.3 Nginx Web 服务器
- [ ] Nginx 已安装并配置
- [ ] 虚拟主机配置正确
- [ ] SSL证书已配置（如需要）
- [ ] 静态文件服务正常
- [ ] 反向代理配置正确

**验证命令:**
```bash
# 检查Nginx状态
sudo systemctl status nginx

# 测试配置文件
sudo nginx -t
```

#### 2.4 Python 环境
- [ ] Python 3.10 已安装
- [ ] pip 包管理器最新版本
- [ ] 虚拟环境已创建
- [ ] 所需Python包已安装
- [ ] 环境变量已配置

**验证命令:**
```bash
# 检查Python版本
python3 --version

# 检查虚拟环境
source /opt/ai_platform/venv/bin/activate
pip list | grep -E "(django|djangorestframework|psycopg2)"
```

#### 2.5 Node.js 环境
- [ ] Node.js 20 LTS 已安装
- [ ] npm 包管理器可用
- [ ] 全局包已安装
- [ ] 项目依赖已安装

**验证命令:**
```bash
# 检查Node.js版本
node --version
npm --version
```

### 第三阶段：应用部署检查 ✅

#### 3.1 Django 后端应用
- [ ] 项目代码已部署到 `/opt/ai_platform`
- [ ] 虚拟环境已激活
- [ ] 依赖包已安装完成
- [ ] 环境变量已配置
- [ ] 数据库迁移已完成
- [ ] 静态文件已收集
- [ ] 超级用户已创建

**验证命令:**
```bash
# 检查Django项目
cd /opt/ai_platform
source venv/bin/activate
python manage.py check

# 检查数据库迁移
python manage.py showmigrations

# 检查静态文件
ls -la static/
```

#### 3.2 系统服务配置
- [ ] systemd 服务文件已创建
- [ ] 服务自动启动已启用
- [ ] 服务运行状态正常
- [ ] 日志记录正常

**验证命令:**
```bash
# 检查AI中台服务状态
sudo systemctl status ai_platform
sudo systemctl is-enabled ai_platform

# 查看服务日志
sudo journalctl -u ai_platform --lines=20
```

#### 3.3 四大平台API
- [ ] 算法平台API正常
- [ ] 数据平台API正常
- [ ] 模型平台API正常
- [ ] 服务平台API正常
- [ ] API文档可访问

**验证命令:**
```bash
# 测试API端点
curl -f http://localhost:8000/api/algorithm/
curl -f http://localhost:8000/api/data/
curl -f http://localhost:8000/api/model/
curl -f http://localhost:8000/api/service/
```

#### 3.4 用户认证系统
- [ ] JWT认证已配置
- [ ] 用户注册功能正常
- [ ] 登录功能正常
- [ ] 权限控制有效
- [ ] 会话管理正常

**验证命令:**
```bash
# 测试认证API
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

#### 3.5 前端界面
- [ ] 管理后台可访问
- [ ] 用户门户正常显示
- [ ] 前端资源加载正常
- [ ] 响应式设计工作
- [ ] 浏览器兼容性良好

**验证命令:**
```bash
# 测试前端页面
curl -f http://localhost/admin/
curl -f http://localhost/portal/
curl -f http://localhost/swagger/
curl -f http://localhost/redoc/
```

## 🔍 功能测试检查清单

### 4.1 基础功能测试
- [ ] 用户可以成功注册
- [ ] 用户可以正常登录
- [ ] 管理员可以访问后台
- [ ] API文档页面正常显示
- [ ] 数据持久化正常

### 4.2 API功能测试
- [ ] GET请求正常返回数据
- [ ] POST请求可以创建数据
- [ ] PUT请求可以更新数据
- [ ] DELETE请求可以删除数据
- [ ] 认证机制正常工作

### 4.3 性能测试
- [ ] 页面加载时间 < 3秒
- [ ] API响应时间 < 200ms
- [ ] 并发10用户测试通过
- [ ] 内存使用在合理范围
- [ ] CPU使用率正常

### 4.4 安全测试
- [ ] 未认证请求被拒绝
- [ ] SQL注入防护有效
- [ ] XSS防护启用
- [ ] CSRF保护启用
- [ ] 敏感信息不泄露

## 📊 监控和维护检查

### 5.1 日志配置
- [ ] 应用日志正常记录
- [ ] 错误日志有意义
- [ ] 访问日志已启用
- [ ] 日志轮转已配置
- [ ] 日志级别合适

**验证命令:**
```bash
# 检查日志文件
sudo ls -la /var/log/ai_platform/
tail -f /var/log/ai_platform/application.log
```

### 5.2 系统监控
- [ ] 系统资源监控正常
- [ ] 服务健康检查通过
- [ ] 磁盘使用监控
- [ ] 网络连接监控
- [ ] 备份策略已实施

### 5.3 安全配置
- [ ] 防火墙规则已配置
- [ ] 不必要端口已关闭
- [ ] 文件权限设置正确
- [ ] 定期安全更新计划
- [ ] 密码策略已实施

## 🚀 生产就绪检查

### 6.1 性能优化
- [ ] 数据库查询已优化
- [ ] 静态文件压缩启用
- [ ] 缓存策略已实施
- [ ] CDN配置（如需要）
- [ ] 负载均衡配置（如需要）

### 6.2 高可用性
- [ ] 服务自动重启配置
- [ ] 数据库备份策略
- [ ] 故障恢复计划
- [ ] 监控告警设置
- [ ] 灾难恢复方案

### 6.3 扩展性
- [ ] 水平扩展方案
- [ ] 垂直扩展方案
- [ ] 数据库分片计划
- [ ] 微服务架构考虑
- [ ] 容器化准备

## 📝 部署验证脚本

### 快速验证脚本

```bash
#!/bin/bash
# AI中台部署快速验证脚本

echo "🔍 开始AI中台部署验证..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数器
PASSED=0
FAILED=0

# 检查函数
check_command() {
    local desc="$1"
    local cmd="$2"
    
    echo -n "检查 $desc... "
    
    if eval "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAILED++))
    fi
}

check_service() {
    local service="$1"
    local desc="$2"
    
    echo -n "检查 $desc 服务... "
    
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✅ 运行中${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ 未运行${NC}"
        ((FAILED++))
    fi
}

check_url() {
    local url="$1"
    local desc="$2"
    
    echo -n "检查 $desc... "
    
    if curl -f -s "$url" >/dev/null; then
        echo -e "${GREEN}✅ 可访问${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ 不可访问${NC}"
        ((FAILED++))
    fi
}

echo "=" * 50

# 系统基础检查
echo "📋 系统基础检查"
check_command "Python 3.10" "python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'"
check_command "pip 可用" "pip3 --version"
check_command "Git 可用" "git --version"

echo

# 服务状态检查
echo "🔧 服务状态检查"
check_service "postgresql" "PostgreSQL"
check_service "redis-server" "Redis"
check_service "nginx" "Nginx"
check_service "ai_platform" "AI中台"

echo

# 网络连接检查
echo "🌐 网络连接检查"
check_url "http://localhost:8000/health/" "Django应用"
check_url "http://localhost/admin/" "管理后台"
check_url "http://localhost/swagger/" "API文档"
check_url "http://localhost/redoc/" "ReDoc文档"

echo

# API功能检查
echo "🔗 API功能检查"
check_url "http://localhost:8000/api/algorithm/" "算法平台API"
check_url "http://localhost:8000/api/data/" "数据平台API"
check_url "http://localhost:8000/api/model/" "模型平台API"
check_url "http://localhost:8000/api/service/" "服务平台API"

echo

# 文件和目录检查
echo "📁 文件和目录检查"
check_command "应用目录存在" "[ -d /opt/ai_platform ]"
check_command "虚拟环境存在" "[ -d /opt/ai_platform/venv ]"
check_command "静态文件存在" "[ -d /opt/ai_platform/static ]"
check_command "日志目录存在" "[ -d /var/log/ai_platform ]"

echo
echo "=" * 50

# 结果统计
TOTAL=$((PASSED + FAILED))
SUCCESS_RATE=$((PASSED * 100 / TOTAL))

echo "📊 验证结果统计:"
echo -e "总检查项: $TOTAL"
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo -e "成功率: ${GREEN}$SUCCESS_RATE%${NC}"

echo

if [ $SUCCESS_RATE -ge 95 ]; then
    echo -e "${GREEN}🎉 恭喜！AI中台部署验证优秀，系统已准备好投入使用。${NC}"
elif [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "${YELLOW}👍 AI中台部署验证良好，建议检查失败的项目。${NC}"
else
    echo -e "${RED}⚠️ AI中台部署验证存在问题，请检查并修复失败项目后重新验证。${NC}"
fi

echo
echo "📚 相关文档:"
echo "- 系统验证: docs/deployment/03_application_deployment/04_system_validation.md"
echo "- 故障排除: docs/deployment/troubleshooting.md"

exit $([ $SUCCESS_RATE -ge 80 ] && echo 0 || echo 1)
```

### 保存并运行验证脚本

```bash
# 创建验证脚本
cat > ~/ai_platform_check.sh << 'EOF'
[上面的验证脚本内容]
EOF

# 添加执行权限
chmod +x ~/ai_platform_check.sh

# 运行验证
~/ai_platform_check.sh
```

## 📚 相关文档链接

- [部署概览](../deployment_overview.md)
- [环境部署](../01_environment_deployment/)
- [服务器部署](../02_server_deployment/)
- [应用部署概览](00_application_overview.md)
- [后端部署](01_backend_deployment.md)
- [前端部署](02_frontend_deployment.md)
- [API集成测试](03_api_integration.md)
- [系统验证](04_system_validation.md)

## 📞 技术支持

如果在验证过程中遇到问题，请参考：

1. **日志分析**: 查看应用和系统日志定位问题
2. **服务重启**: 重启相关服务解决临时问题
3. **配置检查**: 验证配置文件语法和内容
4. **权限检查**: 确认文件和目录权限正确
5. **网络诊断**: 检查端口占用和防火墙设置

---

> **📝 注意**: 本检查清单基于Ubuntu 24.04 LTS环境编写，请根据实际环境调整相应检查项目。
> 
> **⭐ 提示**: 建议将此检查清单保存为checklist文件，在每次部署时逐项验证。
