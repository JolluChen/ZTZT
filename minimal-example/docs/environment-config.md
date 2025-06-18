# =============================================================================
# 环境配置说明文档
# =============================================================================

## 📁 配置文件结构

本项目采用环境分离的配置管理方式，包含以下配置文件：

### 🔧 主配置文件
- `.env.development` - 开发环境配置模板
- `.env.production` - 生产环境配置模板  
- `.env` - 当前激活的配置文件（由脚本自动生成）

### 🎨 前端配置文件
- `frontend/.env.local.development` - 前端开发环境配置
- `frontend/.env.local.production` - 前端生产环境配置
- `frontend/.env.local` - 前端当前激活配置（由脚本自动生成）

### 📡 后端配置文件
- `backend/.env` - 后端当前激活配置（由脚本自动生成）

## 🚀 快速开始

### 1. 环境切换

```bash
# 切换到开发环境
./scripts/env-config.sh dev

# 切换到生产环境  
./scripts/env-config.sh prod

# 查看当前环境状态
./scripts/env-config.sh status
```

### 2. 配置文件管理

```bash
# 备份当前配置
./scripts/env-config.sh backup

# 恢复配置文件
./scripts/env-config.sh restore
```

## 🔧 配置说明

### 开发环境特点
- **API地址**: `http://localhost:8000`
- **前端地址**: `http://localhost:3000`  
- **调试模式**: 启用
- **日志级别**: DEBUG
- **数据库**: 开发数据库 (`ai_platform_dev`)
- **安全性**: 较低（适合开发）

### 生产环境特点
- **API地址**: `http://192.168.110.88:8000`
- **前端地址**: `http://192.168.110.88:3000`
- **调试模式**: 禁用
- **日志级别**: INFO/WARNING
- **数据库**: 生产数据库 (`ai_platform_prod`)
- **安全性**: 高（适合生产部署）

## 🔐 安全注意事项

### 1. 敏感信息处理
- **密码**: 生产环境中必须修改所有默认密码
- **密钥**: JWT密钥、WebUI密钥等必须使用强密码
- **API密钥**: 第三方服务的API密钥需要妥善保管

### 2. 文件权限
```bash
# 设置配置文件权限（推荐）
chmod 600 .env.production
chmod 600 frontend/.env.local.production
```

### 3. 版本控制
以下文件已在 `.gitignore` 中排除：
- `.env`
- `.env.production`
- `frontend/.env.local`
- `frontend/.env.local.production`
- `backend/.env`

## 📋 配置检查清单

### 开发环境配置检查
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] MinIO存储正常
- [ ] 前端API地址正确
- [ ] 调试工具可用

### 生产环境配置检查
- [ ] 更新所有默认密码
- [ ] 修改服务器IP地址
- [ ] 禁用调试模式
- [ ] 配置HTTPS（如需要）
- [ ] 设置邮件服务
- [ ] 配置监控告警
- [ ] 测试备份功能

## 🛠️ 常见问题

### Q: 如何修改服务器IP地址？
A: 编辑 `.env.production` 文件，将所有 `192.168.110.88` 替换为实际IP地址。

### Q: 如何添加新的环境变量？
A: 在对应的配置模板文件中添加，然后重新切换环境。

### Q: 配置文件丢失怎么办？
A: 使用 `./scripts/env-config.sh restore` 恢复备份，或从模板重新配置。

### Q: 如何验证配置是否正确？
A: 使用 `./scripts/env-config.sh status` 查看当前配置状态。

## 🔄 部署工作流

### 本地开发
1. `./scripts/env-config.sh dev` - 切换开发环境
2. `./quick-start.sh` - 启动服务
3. 开发和测试

### 生产部署
1. 编辑 `.env.production` 中的生产配置
2. `./scripts/env-config.sh prod` - 切换生产环境
3. `./quick-start.sh` - 启动生产服务
4. 验证服务运行正常

## 📞 技术支持

如有问题，请检查：
1. 环境配置是否正确
2. 网络连接是否正常
3. 服务是否正常启动
4. 日志文件中的错误信息

---
*最后更新: 2024年12月18日*
