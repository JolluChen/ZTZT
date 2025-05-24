# AI 中台 - Django 与 RESTful API 环境配置

本文档指导如何在 AI 中台项目中配置 Django 和 Django REST Framework (DRF) 以支持中台管理系统的后端服务和 RESTful API。

## 1. 概述

Django 将用于构建中台的管理后台界面，而 Django REST Framework 将用于提供中台内部以及与外部应用交互的 RESTful API。这种组合为快速开发、身份认证和权限管理提供了强大的支持。

参考 `docs/Outline.md`，相关技术栈包括：

-   **后端框架**: Python 3.10, Django
-   **API 框架**: Django REST Framework
-   **身份认证**: Django REST Framework + JWT (JSON Web Tokens)
-   **权限管理 (应用层)**: Django + Django-Guardian, OPA (Open Policy Agent) - 本文档主要关注 Django 原生和 DRF 的配置。

## 2. 环境准备

### 2.1. Python 环境

确保已安装 Python 3.10 或更高版本。建议使用虚拟环境管理项目依赖。

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
```

### 2.2. 安装核心依赖

```bash
pip install django djangorestframework djangorestframework-simplejwt django-guardian
```

-   `django`: 核心 Web 框架。
-   `djangorestframework`: 用于构建 RESTful API。
-   `djangorestframework-simplejwt`: 用于 JWT 认证。
-   `django-guardian`: 用于对象级权限管理 (如果需要)。

## 3. Django 项目配置

### 3.1. 创建 Django 项目和应用

```bash
django-admin startproject ai_platform .  # 在当前目录创建项目
python manage.py startapp admin_panel     # 创建一个名为 admin_panel 的应用
python manage.py startapp api_service     # 创建一个名为 api_service 的应用 (用于API)
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
