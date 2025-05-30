# AI 中台 - Django 用户认证部署

[![Django 4.2](https://img.shields.io/badge/Django-4.2-092E20?style=flat-square&logo=django)](https://www.djangoproject.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)

**部署时间**: 30-45分钟  
**难度级别**: ⭐⭐⭐  
**前置要求**: PostgreSQL 数据库已部署并运行

## 📋 部署概览

基于现有的 `apps/authentication` 应用，完善和配置 Django 用户认证系统，包括用户模型、组织管理和用户配置功能。

## 🔧 现有模型分析

### 当前实现状态

```python
# apps/authentication/models.py - 现有实现
class User(AbstractUser):
    """扩展用户模型 - ✅ 已实现"""
    email = models.EmailField(unique=True, verbose_name='邮箱')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name='头像')
    bio = models.TextField(blank=True, verbose_name='个人简介')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

class Organization(models.Model):
    """组织机构 - ✅ 已实现"""
    name = models.CharField(max_length=200, unique=True, verbose_name='组织名称')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

class UserProfile(models.Model):
    """用户配置文件 - ✅ 已实现"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    department = models.CharField(max_length=100, blank=True, verbose_name='部门')
    position = models.CharField(max_length=100, blank=True, verbose_name='职位')
    preferences = models.JSONField(default=dict, verbose_name='用户偏好')
```

## 🚀 部署步骤

### 步骤 1: 验证现有配置

```bash
# 进入项目目录
cd /opt/ai-platform/backend

# 激活虚拟环境
source /opt/ai-platform/venv/bin/activate

# 检查现有模型
python manage.py showmigrations authentication
```

### 步骤 2: 完善认证应用配置

创建或更新 `apps/authentication/admin.py`：

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Organization, UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {
            'fields': ('phone', 'avatar', 'bio', 'created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """组织管理"""
    list_display = ('name', 'is_active', 'created_at', 'user_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_count(self, obj):
        return obj.userprofile_set.count()
    user_count.short_description = '用户数量'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户配置管理"""
    list_display = ('user', 'organization', 'department', 'position')
    list_filter = ('organization', 'department')
    search_fields = ('user__username', 'user__email', 'department', 'position')
    autocomplete_fields = ('user', 'organization')
```

### 步骤 3: 创建认证视图

创建 `apps/authentication/views.py`：

```python
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import User, UserProfile, Organization
from .serializers import (
    UserSerializer, UserRegistrationSerializer, 
    UserProfileSerializer, OrganizationSerializer
)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """用户注册"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # 自动创建用户配置
        UserProfile.objects.get_or_create(user=user)
        return Response({
            'message': '用户注册成功',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """用户配置管理"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrganizationListView(generics.ListAPIView):
    """组织列表"""
    queryset = Organization.objects.filter(is_active=True)
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
```

### 步骤 4: 创建序列化器

创建 `apps/authentication/serializers.py`：

```python
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, Organization

class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'phone', 'avatar', 'bio', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')

class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 
                 'first_name', 'last_name', 'phone')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密码确认不匹配")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class OrganizationSerializer(serializers.ModelSerializer):
    """组织序列化器"""
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = ('id', 'name', 'description', 'is_active', 'user_count')
    
    def get_user_count(self, obj):
        return obj.userprofile_set.count()

class UserProfileSerializer(serializers.ModelSerializer):
    """用户配置序列化器"""
    user = UserSerializer(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('user', 'organization', 'organization_name', 
                 'department', 'position', 'preferences')
```

### 步骤 5: 配置 URL 路由

创建 `apps/authentication/urls.py`：

```python
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('profile/', views.user_profile, name='profile'),
    path('organizations/', views.OrganizationListView.as_view(), name='organizations'),
]
```

### 步骤 6: 更新主 URL 配置

在 `config/urls.py` 中添加认证路由：

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    # 其他应用路由...
]
```

### 步骤 7: 数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations authentication

# 应用迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

## 🔧 高级配置

### 用户模型信号处理

创建 `apps/authentication/signals.py`：

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """用户创建时自动创建配置文件"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """保存用户时同步保存配置文件"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
```

在 `apps/authentication/apps.py` 中注册信号：

```python
from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = '认证系统'
    
    def ready(self):
        import apps.authentication.signals
```

### 自定义用户验证

创建 `apps/authentication/backends.py`：

```python
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """支持邮箱或用户名登录"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
        except User.DoesNotExist:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
```

## 🧪 部署验证

### 测试用户注册

```bash
# 测试用户注册 API
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 测试管理后台

```bash
# 启动开发服务器
python manage.py runserver 0.0.0.0:8000

# 访问管理后台
# http://localhost:8000/admin/
```

### 验证数据库数据

```sql
-- 连接数据库检查用户数据
\c ai_platform_db

-- 检查用户表
SELECT id, username, email, is_active, created_at FROM auth_users LIMIT 5;

-- 检查组织表
SELECT id, name, is_active, created_at FROM auth_organizations LIMIT 5;

-- 检查用户配置表
SELECT up.id, u.username, o.name as org_name, up.department 
FROM auth_userprofile up 
LEFT JOIN auth_users u ON up.user_id = u.id 
LEFT JOIN auth_organizations o ON up.organization_id = o.id 
LIMIT 5;
```

## 📊 性能优化

### 数据库索引优化

```sql
-- 添加常用查询索引
CREATE INDEX IF NOT EXISTS idx_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON auth_users(phone);
CREATE INDEX IF NOT EXISTS idx_users_active ON auth_users(is_active);
CREATE INDEX IF NOT EXISTS idx_org_active ON auth_organizations(is_active);
CREATE INDEX IF NOT EXISTS idx_profile_org ON auth_userprofile(organization_id);
```

### 查询优化

```python
# 优化的用户查询示例
users_with_profiles = User.objects.select_related('profile', 'profile__organization')

# 批量预取组织信息
organizations_with_users = Organization.objects.prefetch_related(
    'userprofile_set__user'
).filter(is_active=True)
```

## 🔒 安全配置

### 密码策略

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 用户会话配置
SESSION_COOKIE_AGE = 86400  # 24小时
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True
```

## 🔗 下一步

- [JWT 令牌认证配置](./03_jwt_authentication.md) - 配置 API 认证
- [Django 权限系统](./04_django_permissions.md) - 设置权限控制
- [API 安全配置](./06_api_security.md) - 加强 API 安全

## ⚠️ 注意事项

1. **数据迁移**: 如果已有用户数据，谨慎进行模型变更
2. **权限设计**: 提前规划好组织架构和权限分配
3. **安全考虑**: 确保敏感信息的加密存储
4. **备份策略**: 部署前备份现有数据
5. **测试覆盖**: 充分测试所有认证流程
