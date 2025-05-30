# ⭐ AI中台 - Django REST API完整部署指南 (Ubuntu 24.04 LTS)

本文档指导如何在AI中台项目中配置Django和Django REST Framework (DRF)以支持中台管理系统的后端服务和RESTful API。

> **⚠️ 重要提示**: 本文档基于成功优化的最小化AI平台示例，确保所有配置与实际项目兼容。

## ⏱️ 预计部署时间
- **Django环境配置**: 45-60分钟
- **API框架设置**: 30-45分钟  
- **认证系统集成**: 45-60分钟
- **测试和验证**: 30分钟
- **总计**: 2.5-3小时

## 🎯 部署目标
✅ Django 4.2.16 + DRF 3.15.2 环境  
✅ JWT认证系统  
✅ 四大平台API (算法、数据、模型、服务)  
✅ Swagger API文档  
✅ 权限管理系统

## 📋 前提条件

在开始之前，请确保已完成：
- ✅ [Ubuntu 24.04 基础系统安装](../01_environment_deployment/00_os_installation_ubuntu.md)
- ✅ [Python 3.10 开发环境配置](./09_python_environment_setup.md)
- ✅ [数据库系统安装](./05_database_setup.md)

## 1. 概述

Django 将用于构建中台的管理后台界面，而 Django REST Framework 将用于提供中台内部以及与外部应用交互的 RESTful API。这种组合为快速开发、身份认证和权限管理提供了强大的支持。

### 技术栈
- **后端框架**: Python 3.10 + Django 4.2
- **API 框架**: Django REST Framework 3.15
- **身份认证**: JWT (JSON Web Tokens)
- **数据库**: PostgreSQL 16 (生产) / SQLite (开发)
- **缓存**: Redis 7.0
- **文档**: Swagger (drf-yasg)

## 2. 环境准备

### 2.1 激活Python虚拟环境

```bash
# 激活AI平台环境 (按照09_python_environment_setup.md配置的环境)
source /opt/ai-platform/ai-platform-env/bin/activate

# 或使用快捷命令
ai-platform

# 验证Python环境
python --version  # 应该显示Python 3.10.x
which python      # 应该指向虚拟环境中的Python
```

### 2.2 创建项目目录结构

```bash
# 创建AI平台后端项目目录
cd /opt/ai-platform
mkdir -p backend/{config,apps,static,media,logs}
cd backend

# 设置目录权限
sudo chown -R $USER:$USER /opt/ai-platform/backend
```

### 2.3 安装Django相关依赖

```bash
# 确保在虚拟环境中
source /opt/ai-platform/ai-platform-env/bin/activate

# 安装Django核心组件
pip install \
    Django==4.2.16 \
    djangorestframework==3.15.2 \
    djangorestframework-simplejwt==5.3.0 \
    django-cors-headers==4.3.1 \
    drf-yasg==1.21.7

# 安装数据库驱动
pip install \
    psycopg2-binary==2.9.9 \
    redis==5.0.1

# 安装其他必要组件
pip install \
    python-dotenv==1.0.0 \
    celery==5.3.4 \
    gunicorn==21.2.0 \
    whitenoise==6.6.0

# 验证安装
python -c "import django; print(f'Django: {django.get_version()}')"
python -c "import rest_framework; print('DRF installed successfully')"
```

## 3. Django 项目初始化

### 3.1 创建Django项目

```bash
# 确保在正确的目录中
cd /opt/ai-platform/backend

# 创建Django项目
django-admin startproject config .

# 创建应用目录结构
mkdir -p apps
cd apps

# 创建各个应用模块
python ../manage.py startapp authentication
python ../manage.py startapp algorithm_platform
python ../manage.py startapp data_platform
python ../manage.py startapp model_platform
python ../manage.py startapp service_platform

# 返回后端目录
cd ..

# 验证项目结构
tree -L 3 .
```

### 3.2 配置应用模块

为每个应用创建 `__init__.py` 文件：

```bash
# 创建apps包的__init__.py
touch apps/__init__.py

# 为每个应用配置模块
for app in authentication algorithm_platform data_platform model_platform service_platform; do
    echo "default_app_config = 'apps.$app.apps.${app^}Config'" > apps/$app/__init__.py
done
```

### 3.2. 配置文件 (`ai_platform/settings.py`)

1.  **注册应用**:

    ```python
    # ...
    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'rest_framework_simplejwt',
        'guardian', # 如果使用 django-guardian
        'admin_panel',
        'api_service',
        # 其他应用...
    ]
    # ...
    ```

2.  **配置 REST Framework**:

    ```python
    # ...
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework_simplejwt.authentication.JWTAuthentication',
            # 可以添加其他认证方式，如 SessionAuthentication 用于浏览器访问
            'rest_framework.authentication.SessionAuthentication',
        ),
        'DEFAULT_PERMISSION_CLASSES': (
            'rest_framework.permissions.IsAuthenticated', # 默认需要认证
        ),
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 10 # 默认分页大小
    }
    # ...
    ```

3.  **配置 JWT (Simple JWT)**:

    ```python
    # ...
    from datetime import timedelta

    SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), # 访问令牌有效期
        'REFRESH_TOKEN_LIFETIME': timedelta(days=1),    # 刷新令牌有效期
        'ROTATE_REFRESH_TOKENS': False,
        'BLACKLIST_AFTER_ROTATION': True,
        'UPDATE_LAST_LOGIN': False,

        'ALGORITHM': 'HS256',
        'SIGNING_KEY': SECRET_KEY, # 使用 Django 的 SECRET_KEY
        'VERIFYING_KEY': None,
        'AUDIENCE': None,
        'ISSUER': None,

        'AUTH_HEADER_TYPES': ('Bearer',),
        'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
        'USER_ID_FIELD': 'id',
        'USER_ID_CLAIM': 'user_id',
        'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

        'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
        'TOKEN_TYPE_CLAIM': 'token_type',

        'JTI_CLAIM': 'jti',

        'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
        'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5), # 滑动窗口访问令牌有效期
        'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1), # 滑动窗口刷新令牌有效期
    }
    # ...
    ```

4.  **配置 `django-guardian` (如果使用)**:

    ```python
    # ...
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend', # Django 原生认证
        'guardian.backends.ObjectPermissionBackend', # django-guardian 对象权限认证
    )
    # ...
    ```

### 3.3. 配置 URL (`ai_platform/urls.py`)

```python
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # API 认证端点
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 其他 API 应用的 URL
    # path('api/v1/', include('api_service.urls')),
    # 其他管理后台应用的 URL
    # path('management/', include('admin_panel.urls')),
]
```

### 3.4. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

## 4. 构建 RESTful API

以 `api_service` 应用为例。

### 4.1. 定义模型 (`api_service/models.py`)

```python
from django.db import models

class ExampleModel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
```

### 4.2. 定义序列化器 (`api_service/serializers.py`)

```python
from rest_framework import serializers
from .models import ExampleModel

class ExampleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleModel
        fields = ['id', 'name', 'description', 'created_at']
```

### 4.3. 定义视图 (`api_service/views.py`)

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import ExampleModel
from .serializers import ExampleModelSerializer

class ExampleModelViewSet(viewsets.ModelViewSet):
    queryset = ExampleModel.objects.all()
    serializer_class = ExampleModelSerializer
    permission_classes = [IsAuthenticated] # 示例：需要认证才能访问
```

### 4.4. 配置应用 URL (`api_service/urls.py`)

创建 `api_service/urls.py` 文件：

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExampleModelViewSet

router = DefaultRouter()
router.register(r'examples', ExampleModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

然后在项目 `ai_platform/urls.py` 中包含这些 URL：

```python
# ai_platform/urls.py
# ...
urlpatterns = [
    # ...
    path('api/v1/', include('api_service.urls')), # 添加此行
    # ...
]
```

## 5. 运行开发服务器

```bash
python manage.py runserver
```

现在可以通过 `http://127.0.0.1:8000/api/v1/examples/` 访问示例 API (需要认证)。
可以通过 `http://127.0.0.1:8000/api/token/` 获取 JWT 令牌。

## 6. 部署注意事项

-   **生产环境**: 使用 Gunicorn 或 uWSGI 作为应用服务器，并配合 Nginx 作为反向代理。
-   **静态文件和媒体文件**: 正确配置静态文件和媒体文件的服务。
-   **数据库**: 连接到在 `05_database_setup.md` 中配置的 PostgreSQL 数据库。
-   **环境变量**: 使用环境变量管理敏感配置 (如 `SECRET_KEY`, 数据库凭证)。
-   **安全性**:
    -   启用 HTTPS。
    -   配置 CORS (Cross-Origin Resource Sharing) 如果前端和后端部署在不同域。
    -   定期更新依赖。
    -   遵循 Django 和 DRF 的安全最佳实践。

## 7. 中台管理系统前端集成

中台管理系统的网页前端 (如 React/Vue) 将通过调用此处定义的 RESTful API 来获取数据、执行操作并展示信息。身份认证将通过 JWT 实现，前端在请求时携带 JWT 令牌。

---

**后续步骤**:
根据具体需求，继续开发各个模块的 API 接口和管理后台功能。参考 Django 和 Django REST Framework 的官方文档获取更详细的信息。
