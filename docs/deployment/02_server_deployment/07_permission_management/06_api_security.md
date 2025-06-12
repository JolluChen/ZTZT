# AI 中台 - API 安全配置

[![Security](https://img.shields.io/badge/Security-API%20Protection-red?style=flat-square&logo=shield)](https://www.owasp.org/) [![Django](https://img.shields.io/badge/Django-Security-092e20?style=flat-square&logo=django)](https://docs.djangoproject.com/en/stable/topics/security/)

**部署时间**: 30-40分钟  
**难度级别**: ⭐⭐⭐⭐  
**前置要求**: JWT认证系统已部署

## 📋 API 安全概览

API 安全是 AI 中台系统的关键组成部分，涵盖认证授权、输入验证、速率限制、安全头配置等多个层面。本文档提供全面的 API 安全配置指南。

## 🔐 基础安全配置

### 步骤 1: 安装安全依赖

```bash
# 进入项目目录
cd /opt/ai-platform/backend

# 激活虚拟环境
source /opt/ai-platform/venv/bin/activate

# 安装安全相关包
pip install django-cors-headers
pip install django-ratelimit
pip install django-security
pip install cryptography
pip install django-encrypted-model-fields

# 更新 requirements.txt
pip freeze > requirements.txt
```

### 步骤 2: CORS 安全配置

在 `config/settings.py` 中配置 CORS：

```python
# 添加到 INSTALLED_APPS
INSTALLED_APPS = [
    # ...existing apps...
    'corsheaders',
    'django_ratelimit',
]

# CORS 中间件配置
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # ...existing middleware...
]

# CORS 配置
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ai-platform.example.com",  # 生产环境域名
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',
]

CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# 生产环境严格配置
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "https://ai-platform.example.com",
    ]
    CORS_ALLOW_ALL_ORIGINS = False
```

### 步骤 3: 安全头配置

```python
# 安全头配置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000
X_FRAME_OPTIONS = 'DENY'

# HTTPS 配置（生产环境）
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

## 🛡️ API 访问控制

### 自定义权限类

创建 `apps/authentication/permissions.py`：

```python
from rest_framework import permissions
from rest_framework.request import Request
from django.utils import timezone
from .models import User
import logging

logger = logging.getLogger(__name__)

class IsOwnerOrAdmin(permissions.BasePermission):
    """只有资源所有者或管理员可以访问"""
    
    def has_object_permission(self, request, view, obj):
        # 管理员拥有所有权限
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # 检查是否为资源所有者
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False

class IsOrganizationMember(permissions.BasePermission):
    """只有同组织成员可以访问"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            user_org = request.user.profile.organization
            return user_org is not None
        except:
            return False
    
    def has_object_permission(self, request, view, obj):
        try:
            user_org = request.user.profile.organization
            if hasattr(obj, 'organization'):
                return obj.organization == user_org
            if hasattr(obj, 'user') and hasattr(obj.user, 'profile'):
                return obj.user.profile.organization == user_org
        except:
            pass
        
        return False

class APIKeyPermission(permissions.BasePermission):
    """API 密钥认证"""
    
    def has_permission(self, request, view):
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            return False
        
        # 验证 API 密钥
        try:
            from .models import APIKey
            key_obj = APIKey.objects.get(key=api_key, is_active=True)
            
            # 检查过期时间
            if key_obj.expires_at and key_obj.expires_at < timezone.now():
                return False
            
            # 记录使用
            key_obj.last_used = timezone.now()
            key_obj.usage_count += 1
            key_obj.save()
            
            # 将 API 密钥用户设置到请求中
            request.api_key_user = key_obj.user
            return True
        except:
            return False

class RateLimitPermission(permissions.BasePermission):
    """速率限制权限"""
    
    def has_permission(self, request, view):
        from django_ratelimit.decorators import ratelimit
        from django_ratelimit.exceptions import Ratelimited
        
        # 根据用户类型设置不同的速率限制
        if request.user.is_superuser:
            rate = '1000/h'
        elif request.user.is_staff:
            rate = '500/h'
        else:
            rate = '100/h'
        
        try:
            ratelimit(key='user', rate=rate, method='ALL')(lambda r: None)(request)
            return True
        except Ratelimited:
            return False
```

### API 密钥模型

在 `apps/authentication/models.py` 中添加：

```python
import secrets
from django.db import models
from django.utils import timezone

class APIKey(models.Model):
    """API 密钥模型"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100, help_text='API 密钥名称')
    key = models.CharField(max_length=64, unique=True, help_text='API 密钥')
    is_active = models.BooleanField(default=True, help_text='是否激活')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text='过期时间')
    last_used = models.DateTimeField(null=True, blank=True, help_text='最后使用时间')
    usage_count = models.IntegerField(default=0, help_text='使用次数')
    
    # 权限配置
    permissions = models.JSONField(default=list, help_text='允许的权限列表')
    ip_whitelist = models.JSONField(default=list, help_text='IP 白名单')
    
    class Meta:
        db_table = 'auth_api_key'
        verbose_name = 'API 密钥'
        verbose_name_plural = 'API 密钥'
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_key():
        """生成 API 密钥"""
        return secrets.token_urlsafe(48)
    
    def is_expired(self):
        """检查是否过期"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def has_permission(self, permission):
        """检查是否有特定权限"""
        return permission in self.permissions or 'all' in self.permissions
```

## 🔒 输入验证与过滤

### 自定义验证器

创建 `apps/authentication/validators.py`：

```python
import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class StrongPasswordValidator:
    """强密码验证器"""
    
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(_('密码至少需要8个字符'))
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('密码必须包含至少一个大写字母'))
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('密码必须包含至少一个小写字母'))
        
        if not re.search(r'\d', password):
            raise ValidationError(_('密码必须包含至少一个数字'))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_('密码必须包含至少一个特殊字符'))
    
    def get_help_text(self):
        return _('密码必须至少8个字符，包含大小写字母、数字和特殊字符')

class UsernameValidator(RegexValidator):
    """用户名验证器"""
    regex = r'^[a-zA-Z0-9_-]+$'
    message = _('用户名只能包含字母、数字、下划线和连字符')

def validate_file_extension(value):
    """文件扩展名验证"""
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.docx', '.xlsx']
    ext = value.name.lower().split('.')[-1]
    if f'.{ext}' not in allowed_extensions:
        raise ValidationError(f'不支持的文件类型: {ext}')

def validate_ip_address(value):
    """IP 地址验证"""
    import ipaddress
    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise ValidationError('无效的 IP 地址格式')
```

### 输入清理中间件

创建 `apps/authentication/security_middleware.py`：

```python
import json
import html
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

class InputSanitizationMiddleware(MiddlewareMixin):
    """输入清理中间件"""
    
    def process_request(self, request):
        # 清理 GET 参数
        for key, value in request.GET.items():
            if isinstance(value, str):
                request.GET = request.GET.copy()
                request.GET[key] = html.escape(value.strip())
        
        # 清理 POST 数据
        if request.content_type == 'application/json':
            try:
                if hasattr(request, 'body') and request.body:
                    data = json.loads(request.body)
                    cleaned_data = self._clean_json_data(data)
                    request._body = json.dumps(cleaned_data).encode('utf-8')
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.warning(f"Invalid JSON data in request from {request.META.get('REMOTE_ADDR')}")
        
        return None
    
    def _clean_json_data(self, data):
        """递归清理 JSON 数据"""
        if isinstance(data, dict):
            return {key: self._clean_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._clean_json_data(item) for item in data]
        elif isinstance(data, str):
            # 去除潜在的 XSS 攻击代码
            cleaned = html.escape(data.strip())
            # 移除 SQL 注入关键字
            sql_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'SELECT', 'UNION', 'EXEC']
            for keyword in sql_keywords:
                cleaned = cleaned.replace(keyword.lower(), '').replace(keyword.upper(), '')
            return cleaned
        else:
            return data

class SecurityLoggingMiddleware(MiddlewareMixin):
    """安全日志中间件"""
    
    def process_request(self, request):
        # 记录可疑请求
        suspicious_patterns = [
            'script', 'javascript', 'vbscript', 'onload', 'onerror',
            'union', 'select', 'drop', 'delete', 'insert', 'update',
            '../', '..\\', '/etc/passwd', 'cmd.exe'
        ]
        
        request_data = str(request.GET) + str(getattr(request, 'body', ''))
        
        for pattern in suspicious_patterns:
            if pattern.lower() in request_data.lower():
                logger.warning(
                    f"Suspicious request detected from {request.META.get('REMOTE_ADDR')}: "
                    f"Pattern '{pattern}' found in {request.method} {request.path}"
                )
                break
        
        return None

class RateLimitMiddleware(MiddlewareMixin):
    """速率限制中间件"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.request_counts = {}
    
    def process_request(self, request):
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # 清理过期记录
        self.cleanup_old_records(current_time)
        
        # 检查速率限制
        if client_ip in self.request_counts:
            requests_in_window = [
                timestamp for timestamp in self.request_counts[client_ip]
                if current_time - timestamp < 60  # 1分钟窗口
            ]
            
            if len(requests_in_window) >= 100:  # 每分钟最多100请求
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JsonResponse({
                    'error': '请求频率过高，请稍后再试'
                }, status=429)
            
            self.request_counts[client_ip] = requests_in_window + [current_time]
        else:
            self.request_counts[client_ip] = [current_time]
        
        return None
    
    def get_client_ip(self, request):
        """获取客户端 IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def cleanup_old_records(self, current_time):
        """清理过期记录"""
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = [
                timestamp for timestamp in self.request_counts[ip]
                if current_time - timestamp < 60
            ]
            if not self.request_counts[ip]:
                del self.request_counts[ip]
```

## 🔍 安全监控

### 安全事件记录

创建 `apps/authentication/security_models.py`：

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class SecurityEvent(models.Model):
    """安全事件记录"""
    
    EVENT_TYPES = [
        ('login_success', '登录成功'),
        ('login_failed', '登录失败'),
        ('logout', '用户登出'),
        ('password_change', '密码修改'),
        ('permission_denied', '权限拒绝'),
        ('suspicious_activity', '可疑活动'),
        ('api_key_used', 'API密钥使用'),
        ('rate_limit_exceeded', '超出速率限制'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '严重'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='low')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'security_event'
        verbose_name = '安全事件'
        verbose_name_plural = '安全事件'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.timestamp}"

class LoginAttempt(models.Model):
    """登录尝试记录"""
    
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'login_attempt'
        verbose_name = '登录尝试'
        verbose_name_plural = '登录尝试'
        ordering = ['-timestamp']
    
    @classmethod
    def record_attempt(cls, username, ip_address, success, user_agent=''):
        """记录登录尝试"""
        return cls.objects.create(
            username=username,
            ip_address=ip_address,
            success=success,
            user_agent=user_agent
        )
    
    @classmethod
    def get_failed_attempts(cls, username=None, ip_address=None, minutes=30):
        """获取失败尝试次数"""
        since = timezone.now() - timezone.timedelta(minutes=minutes)
        query = cls.objects.filter(success=False, timestamp__gte=since)
        
        if username:
            query = query.filter(username=username)
        if ip_address:
            query = query.filter(ip_address=ip_address)
        
        return query.count()
```

### 监控信号

创建 `apps/authentication/signals.py`：

```python
from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .security_models import SecurityEvent, LoginAttempt
from .models import User
import logging

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """记录用户登录"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # 记录安全事件
    SecurityEvent.objects.create(
        event_type='login_success',
        severity='low',
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        description=f'用户 {user.username} 成功登录',
        metadata={
            'login_method': 'web' if 'Mozilla' in user_agent else 'api',
            'timestamp': timezone.now().isoformat()
        }
    )
    
    # 记录登录尝试
    LoginAttempt.record_attempt(user.username, ip_address, True, user_agent)
    
    logger.info(f"User {user.username} logged in from {ip_address}")

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """记录登录失败"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    username = credentials.get('username', 'unknown')
    
    # 记录安全事件
    SecurityEvent.objects.create(
        event_type='login_failed',
        severity='medium',
        ip_address=ip_address,
        user_agent=user_agent,
        description=f'用户名 {username} 登录失败',
        metadata={
            'username': username,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    # 记录登录尝试
    LoginAttempt.record_attempt(username, ip_address, False, user_agent)
    
    # 检查是否需要锁定
    failed_count = LoginAttempt.get_failed_attempts(username=username, minutes=30)
    if failed_count >= 5:
        SecurityEvent.objects.create(
            event_type='suspicious_activity',
            severity='high',
            ip_address=ip_address,
            description=f'用户名 {username} 30分钟内登录失败{failed_count}次',
            metadata={'failed_attempts': failed_count}
        )
    
    logger.warning(f"Failed login attempt for {username} from {ip_address}")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """记录用户登出"""
    if user and request:
        ip_address = get_client_ip(request)
        
        SecurityEvent.objects.create(
            event_type='logout',
            severity='low',
            user=user,
            ip_address=ip_address,
            description=f'用户 {user.username} 登出',
        )
        
        logger.info(f"User {user.username} logged out from {ip_address}")

def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip
```

## 🧪 安全测试

### 安全测试脚本

创建 `test_api_security.py`：

```python
#!/usr/bin/env python3
import requests
import json
import time
import threading

BASE_URL = 'http://localhost:8000/api'

def test_cors_headers():
    """测试 CORS 配置"""
    print("1. 测试 CORS 配置...")
    
    headers = {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Authorization, Content-Type'
    }
    
    response = requests.options(f'{BASE_URL}/auth/token/', headers=headers)
    print(f"CORS 预检请求: {response.status_code}")
    print(f"CORS 头: {response.headers.get('Access-Control-Allow-Origin')}")

def test_security_headers():
    """测试安全头"""
    print("\n2. 测试安全头...")
    
    response = requests.get(f'{BASE_URL}/auth/profile/')
    security_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Referrer-Policy'
    ]
    
    for header in security_headers:
        value = response.headers.get(header)
        print(f"{header}: {value}")

def test_rate_limiting():
    """测试速率限制"""
    print("\n3. 测试速率限制...")
    
    # 快速发送多个请求
    for i in range(10):
        response = requests.get(f'{BASE_URL}/auth/profile/')
        print(f"请求 {i+1}: {response.status_code}")
        if response.status_code == 429:
            print("速率限制生效!")
            break

def test_input_validation():
    """测试输入验证"""
    print("\n4. 测试输入验证...")
    
    # XSS 测试
    xss_payload = '<script>alert("xss")</script>'
    response = requests.post(f'{BASE_URL}/auth/register/', json={
        'username': xss_payload,
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    print(f"XSS 测试: {response.status_code}")
    
    # SQL 注入测试
    sql_payload = "admin'; DROP TABLE users; --"
    response = requests.post(f'{BASE_URL}/auth/token/', json={
        'username': sql_payload,
        'password': 'password'
    })
    print(f"SQL 注入测试: {response.status_code}")

def test_authentication_bypass():
    """测试认证绕过"""
    print("\n5. 测试认证绕过...")
    
    # 尝试无令牌访问保护端点
    response = requests.get(f'{BASE_URL}/auth/profile/')
    print(f"无令牌访问: {response.status_code}")
    
    # 尝试无效令牌
    headers = {'Authorization': 'Bearer invalid_token'}
    response = requests.get(f'{BASE_URL}/auth/profile/', headers=headers)
    print(f"无效令牌: {response.status_code}")

if __name__ == '__main__':
    print("API 安全测试开始...")
    test_cors_headers()
    test_security_headers()
    test_rate_limiting()
    test_input_validation()
    test_authentication_bypass()
    print("\nAPI 安全测试完成!")
```

## 📊 部署清单

### 安全配置检查表

```bash
#!/bin/bash
# 创建安全检查脚本 security_checklist.sh

echo "AI 中台 API 安全配置检查"
echo "========================="

# 1. 检查 HTTPS 配置
echo "1. 检查 HTTPS 配置..."
if curl -s -I https://localhost | grep -q "HTTP/1.1 200\|HTTP/2 200"; then
    echo "✅ HTTPS 配置正常"
else
    echo "❌ HTTPS 配置异常"
fi

# 2. 检查安全头
echo "2. 检查安全头..."
HEADERS=("X-Content-Type-Options" "X-Frame-Options" "X-XSS-Protection")
for header in "${HEADERS[@]}"; do
    if curl -s -I http://localhost:8000 | grep -q "$header"; then
        echo "✅ $header 已配置"
    else
        echo "❌ $header 未配置"
    fi
done

# 3. 检查数据库连接安全
echo "3. 检查数据库连接..."
python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT version()')
print('✅ 数据库连接正常')
"

# 4. 检查日志配置
echo "4. 检查日志配置..."
if [ -f "/opt/ai-platform/backend/logs/security.log" ]; then
    echo "✅ 安全日志配置正常"
else
    echo "❌ 安全日志未配置"
fi

echo "安全检查完成!"
```

### 更新 settings.py

在 `config/settings.py` 中添加完整安全配置：

```python
# 添加中间件
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.authentication.middleware.JWTAuthenticationMiddleware',
    'apps.authentication.security_middleware.InputSanitizationMiddleware',
    'apps.authentication.security_middleware.SecurityLoggingMiddleware',
    'apps.authentication.security_middleware.RateLimitMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 密码验证器
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'apps.authentication.validators.StrongPasswordValidator',
    },
]
```

## 🔗 下一步

- [审计监控配置](./07_audit_monitoring.md) - 设置审计和监控
- [部署测试验证](./08_deployment_testing.md) - 完整部署测试

## ⚠️ 安全提醒

1. **定期更新**: 保持所有依赖包的最新版本
2. **密钥轮换**: 定期轮换 API 密钥和 JWT 密钥
3. **监控告警**: 设置安全事件的实时监控和告警
4. **备份策略**: 确保安全配置和密钥的安全备份
5. **渗透测试**: 定期进行安全渗透测试
