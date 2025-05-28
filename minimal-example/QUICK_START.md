# 🚀 快速启动指南

## 系统概述
最小化AI平台已完全优化完成，所有功能正常运行，可立即使用！

## 🎯 快速启动步骤

### 1. 启动后端服务器
```powershell
cd "d:\Study\StudyFiles\PyFiles\LSY\ZTZT\minimal-example\backend"
python manage.py runserver
```

### 2. 立即可访问的地址
- **🏠 API主页**: http://127.0.0.1:8000/
- **📚 Swagger文档**: http://127.0.0.1:8000/swagger/
- **📖 ReDoc文档**: http://127.0.0.1:8000/redoc/
- **⚙️ 管理后台**: http://127.0.0.1:8000/admin/

## 🔑 管理员账户信息

### 超级管理员
- **用户名**: `admin`
- **密码**: `admin`
- **权限**: 全部权限（可访问Django Admin界面）
- **登录地址**: http://127.0.0.1:8000/admin/

## 🧪 API测试示例

### 用户注册
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "testpass123",
    "password_confirm": "testpass123"
  }'
```

### 用户登录
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### 获取用户资料（需要Token）
```bash
curl -X GET http://127.0.0.1:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🏗️ 系统架构

### 可用的API端点
```
/api/auth/          # 用户认证模块
├── register/       # 用户注册
├── login/          # 用户登录
└── profile/        # 用户资料

/api/algorithm/     # 算法平台API
/api/data/          # 数据平台API  
/api/model/         # 模型平台API
/api/service/       # 服务平台API
```

### 技术栈
- **后端框架**: Django 4.2.7 + Django REST Framework 3.15.2
- **认证系统**: JWT (djangorestframework-simplejwt 5.3.0)
- **数据库**: SQLite (开发环境)
- **API文档**: drf-yasg 1.21.7 (Swagger + ReDoc)
- **Python版本**: 3.10

## ✅ 系统状态检查

### 验证系统运行状态
1. **服务器启动**: `python manage.py runserver` 成功无错误
2. **数据库连接**: SQLite数据库文件存在且可访问
3. **API响应**: 访问 http://127.0.0.1:8000/ 返回JSON格式信息
4. **管理界面**: 使用admin/admin可成功登录管理后台
5. **文档系统**: Swagger和ReDoc页面正常显示

### 故障排除
如果遇到问题，可以运行以下检查：

```powershell
# 检查Python版本
python --version

# 检查Django安装
python -c "import django; print(django.get_version())"

# 检查数据库状态
cd "d:\Study\StudyFiles\PyFiles\LSY\ZTZT\minimal-example\backend"
python manage.py check

# 重新应用迁移（如需要）
python manage.py migrate
```

## 🚀 下一步开发

### 立即可做
1. **测试API功能** - 使用Swagger或Postman测试所有端点
2. **开发前端** - 基于这些API开发前端应用
3. **添加业务逻辑** - 在现有ViewSet基础上扩展功能
4. **创建示例数据** - 通过API或Admin界面添加测试数据

### 进阶配置
1. **切换数据库** - 配置PostgreSQL替换SQLite
2. **添加缓存** - 集成Redis提升性能
3. **文件存储** - 配置媒体文件上传功能
4. **部署配置** - 准备生产环境配置

---

**🎉 恭喜！您的最小化AI平台已经完全就绪，可以开始开发了！**

*文档更新时间: 2025年5月28日*
