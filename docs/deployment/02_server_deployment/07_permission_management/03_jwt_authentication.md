# AI 中台 - JWT 令牌认证配置

[![JWT](https://img.shields.io/badge/JWT-Authentication-000000?style=flat-square&logo=jsonwebtokens)](https://jwt.io/) [![DRF](https://img.shields.io/badge/DRF-SimpleJWT-ff1709?style=flat-square)](https://django-rest-framework-simplejwt.readthedocs.io/)

**部署时间**: 20-30分钟  
**难度级别**: ⭐⭐⭐  
**前置要求**: Django 用户认证系统已部署

## 📋 JWT 认证概览

JSON Web Token (JWT) 是一种无状态的认证机制，特别适合 API 服务和微服务架构。本文档将配置基于 Django REST Framework SimpleJWT 的令牌认证系统。

## 🔧 安装配置

### 步骤 1: 安装依赖包

```bash
# 进入项目目录
cd /opt/ai-platform/backend

# 激活虚拟环境
source /opt/ai-platform/venv/bin/activate

# 安装 JWT 认证包
pip install djangorestframework-simplejwt

# 更新 requirements.txt
pip freeze > requirements.txt
```

### 步骤 2: Django 配置

在 `config/settings.py` 中添加 JWT 配置：

```python
from datetime import timedelta

# 添加到 INSTALLED_APPS
INSTALLED_APPS = [
    # ...existing apps...
    'rest_framework',
    'rest_framework_simplejwt',
    'apps.authentication',
]

# REST Framework 配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT 配置
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'ai-platform',
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(hours=1),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# 自定义用户模型
AUTH_USER_MODEL = 'authentication.User'
```

### 步骤 3: URL 路由配置

更新 `config/urls.py`：

```python
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    
    # JWT 认证端点
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
```

## 🔐 自定义 JWT 视图

### 自定义令牌序列化器

创建 `apps/authentication/jwt_serializers.py`：

```python
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import User, UserProfile

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义 JWT 令牌获取序列化器"""
    
    username_field = 'username'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 支持邮箱登录
        self.fields['username'] = serializers.CharField()
        self.fields['username'].help_text = '用户名或邮箱地址'
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # 添加自定义声明
        token['user_id'] = user.id
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        
        # 添加用户配置信息
        try:
            profile = user.profile
            token['organization_id'] = profile.organization.id if profile.organization else None
            token['organization_name'] = profile.organization.name if profile.organization else None
            token['department'] = profile.department
            token['position'] = profile.position
        except UserProfile.DoesNotExist:
            token['organization_id'] = None
            token['organization_name'] = None
            token['department'] = ''
            token['position'] = ''
        
        return token
    
    def validate(self, attrs):
        # 支持邮箱或用户名登录
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # 尝试通过用户名或邮箱查找用户
            try:
                if '@' in username:
                    user = User.objects.get(email=username)
                    attrs['username'] = user.username
                else:
                    user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise serializers.ValidationError('无效的用户名或密码')
        
        return super().validate(attrs)

class TokenRefreshSerializer(serializers.Serializer):
    """令牌刷新序列化器"""
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        try:
            refresh = RefreshToken(attrs['refresh'])
            data = {'access': str(refresh.access_token)}
            
            if refresh.blacklisted():
                raise TokenError('Token is blacklisted')
            
            return data
        except TokenError:
            raise serializers.ValidationError('无效的刷新令牌')
```

### 自定义 JWT 视图

创建 `apps/authentication/jwt_views.py`：

```python
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import logout
from .jwt_serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """自定义令牌获取视图"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # 记录登录日志
            user = self.get_user_from_token(response.data.get('access'))
            if user:
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
        
        return response
    
    def get_user_from_token(self, access_token):
        """从令牌中获取用户"""
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            token = AccessToken(access_token)
            user_id = token.get('user_id')
            return User.objects.get(id=user_id)
        except:
            return None

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """用户登出"""
    try:
        # 将当前刷新令牌加入黑名单
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Django 会话登出
        logout(request)
        
        return Response({
            'message': '成功登出'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': '登出失败',
            'detail': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def token_info(request):
    """获取当前令牌信息"""
    try:
        # 从请求头获取令牌
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            access_token = auth_header[7:]
            from rest_framework_simplejwt.tokens import AccessToken
            token = AccessToken(access_token)
            
            return Response({
                'user_id': token.get('user_id'),
                'username': token.get('username'),
                'email': token.get('email'),
                'organization_name': token.get('organization_name'),
                'department': token.get('department'),
                'position': token.get('position'),
                'expires_at': token.get('exp'),
                'token_type': token.get('token_type'),
            })
        else:
            return Response({
                'error': '无效的认证头'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': '令牌解析失败',
            'detail': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
```

### 更新 URL 配置

更新 `apps/authentication/urls.py`：

```python
from django.urls import path
from . import views, jwt_views

app_name = 'authentication'

urlpatterns = [
    # 用户管理
    path('register/', views.register_user, name='register'),
    path('profile/', views.user_profile, name='profile'),
    path('organizations/', views.OrganizationListView.as_view(), name='organizations'),
    
    # JWT 认证
    path('token/', jwt_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('token/info/', jwt_views.token_info, name='token_info'),
    path('logout/', jwt_views.logout_view, name='logout'),
]
```

## 🔒 安全增强

### 令牌黑名单配置

添加到 `config/settings.py`：

```python
# 添加黑名单应用
INSTALLED_APPS = [
    # ...existing apps...
    'rest_framework_simplejwt.token_blacklist',
]

# JWT 黑名单配置
SIMPLE_JWT = {
    # ...existing config...
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}
```

执行迁移：

```bash
python manage.py migrate token_blacklist
```

### 自定义中间件

创建 `apps/authentication/middleware.py`：

```python
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """JWT 认证中间件"""
    
    def process_request(self, request):
        # 跳过不需要认证的端点
        exempt_paths = [
            '/api/auth/token/',
            '/api/auth/register/',
            '/admin/',
            '/api/docs/',
        ]
        
        if any(request.path.startswith(path) for path in exempt_paths):
            return None
        
        # 检查 JWT 令牌
        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(
                jwt_auth.get_raw_token(jwt_auth.get_header(request))
            )
            user = jwt_auth.get_user(validated_token)
            request.user = user
            
            # 记录访问日志
            logger.info(f"JWT authentication successful for user: {user.username}")
            
        except (InvalidToken, TokenError) as e:
            # 记录认证失败
            logger.warning(f"JWT authentication failed: {str(e)}")
            
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': '认证失败',
                    'detail': '无效或过期的令牌'
                }, status=401)
        
        return None

class SecurityHeadersMiddleware(MiddlewareMixin):
    """安全头中间件"""
    
    def process_response(self, request, response):
        # 添加安全头
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CORS 配置
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'  # 生产环境应限制具体域名
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
```

在 `config/settings.py` 中注册中间件：

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.authentication.middleware.JWTAuthenticationMiddleware',
    'apps.authentication.middleware.SecurityHeadersMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

## 🧪 测试验证

### JWT 功能测试脚本

创建 `test_jwt_auth.py`：

```python
#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = 'http://localhost:8000/api/auth'

def test_jwt_authentication():
    """测试 JWT 认证流程"""
    
    # 1. 用户注册
    print("1. 测试用户注册...")
    register_data = {
        'username': 'jwttest',
        'email': 'jwttest@example.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123',
        'first_name': 'JWT',
        'last_name': 'Test'
    }
    
    response = requests.post(f'{BASE_URL}/register/', json=register_data)
    print(f"注册响应: {response.status_code} - {response.text}")
    
    # 2. 获取 JWT 令牌
    print("\n2. 测试 JWT 令牌获取...")
    login_data = {
        'username': 'jwttest',
        'password': 'testpass123'
    }
    
    response = requests.post(f'{BASE_URL}/token/', json=login_data)
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        print(f"令牌获取成功")
        print(f"Access Token: {access_token[:50]}...")
        print(f"Refresh Token: {refresh_token[:50]}...")
    else:
        print(f"令牌获取失败: {response.status_code} - {response.text}")
        return
    
    # 3. 使用令牌访问保护端点
    print("\n3. 测试令牌访问...")
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(f'{BASE_URL}/profile/', headers=headers)
    print(f"访问用户配置: {response.status_code}")
    if response.status_code == 200:
        print(f"用户信息: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 4. 测试令牌信息
    print("\n4. 测试令牌信息...")
    response = requests.get(f'{BASE_URL}/token/info/', headers=headers)
    print(f"令牌信息: {response.status_code}")
    if response.status_code == 200:
        print(f"令牌详情: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 5. 测试令牌刷新
    print("\n5. 测试令牌刷新...")
    refresh_data = {'refresh': refresh_token}
    response = requests.post(f'{BASE_URL}/token/refresh/', json=refresh_data)
    print(f"令牌刷新: {response.status_code}")
    if response.status_code == 200:
        new_access = response.json()['access']
        print(f"新 Access Token: {new_access[:50]}...")
    
    # 6. 测试登出
    print("\n6. 测试用户登出...")
    logout_data = {'refresh_token': refresh_token}
    response = requests.post(f'{BASE_URL}/logout/', json=logout_data, headers=headers)
    print(f"登出响应: {response.status_code} - {response.text}")

if __name__ == '__main__':
    test_jwt_authentication()
```

运行测试：

```bash
python test_jwt_auth.py
```

### 性能测试

```bash
# 使用 Apache Bench 测试令牌端点性能
# 首先获取有效令牌
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

# 测试认证端点性能
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/auth/profile/
```

## 📊 监控配置

### 日志配置

在 `config/settings.py` 中添加：

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'jwt_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/opt/ai-platform/backend/logs/jwt_auth.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.authentication': {
            'handlers': ['jwt_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🔗 下一步

- [Django 权限系统](./04_django_permissions.md) - 配置权限控制
- [角色权限管理](./05_role_based_access.md) - 实现 RBAC
- [API 安全配置](./06_api_security.md) - 加强 API 安全

## ⚠️ 安全提醒

1. **密钥管理**: 确保 SECRET_KEY 的安全性，生产环境使用环境变量
2. **令牌生命周期**: 根据安全需求调整令牌过期时间
3. **HTTPS 强制**: 生产环境必须使用 HTTPS 传输令牌
4. **刷新策略**: 实施适当的令牌刷新和撤销策略
5. **监控告警**: 设置异常令牌使用的监控和告警
