# AI 中台 - Django 权限系统配置

[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=flat-square&logo=django)](https://www.djangoproject.com/) [![Guardian](https://img.shields.io/badge/Guardian-Object%20Permissions-green?style=flat-square)](https://django-guardian.readthedocs.io/)

**部署时间**: 30-45分钟  
**难度级别**: ⭐⭐⭐⭐  
**前置要求**: Django 用户认证和 JWT 认证已配置

## 📋 权限系统概览

Django 权限系统提供模型级和对象级的精细化权限控制。本文档将配置基于 Django 内置权限系统和 django-guardian 的对象级权限管理。

## 🔧 权限模型设计

### Django 内置权限

Django 自动为每个模型创建四个基本权限：
- `add_<model>`: 添加权限
- `change_<model>`: 修改权限  
- `delete_<model>`: 删除权限
- `view_<model>`: 查看权限

### 自定义权限配置

创建 `apps/authentication/permissions.py`：

```python
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from ..models import User, Organization, UserProfile

class PermissionManager:
    """权限管理器"""
    
    # 自定义权限定义
    CUSTOM_PERMISSIONS = {
        'authentication.user': [
            ('can_manage_users', '可以管理用户'),
            ('can_view_user_list', '可以查看用户列表'),
            ('can_reset_password', '可以重置密码'),
            ('can_activate_user', '可以激活/停用用户'),
        ],
        'authentication.organization': [
            ('can_manage_organization', '可以管理组织'),
            ('can_view_organization_users', '可以查看组织用户'),
            ('can_assign_users', '可以分配用户到组织'),
        ],
        'authentication.userprofile': [
            ('can_manage_profiles', '可以管理用户配置'),
            ('can_view_profile_details', '可以查看配置详情'),
        ]
    }
    
    @classmethod
    def create_custom_permissions(cls):
        """创建自定义权限"""
        for app_model, permissions in cls.CUSTOM_PERMISSIONS.items():
            app_label, model_name = app_model.split('.')
            content_type = ContentType.objects.get(
                app_label=app_label, 
                model=model_name
            )
            
            for codename, name in permissions:
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults={'name': name}
                )
                if created:
                    print(f"Created permission: {codename} - {name}")
    
    @classmethod
    def get_user_permissions(cls, user):
        """获取用户所有权限"""
        # 直接权限
        user_permissions = user.user_permissions.all()
        
        # 组权限
        group_permissions = Permission.objects.filter(
            group__user=user
        )
        
        # 合并权限
        all_permissions = user_permissions.union(group_permissions)
        
        return {
            'user_permissions': list(user_permissions.values_list('codename', flat=True)),
            'group_permissions': list(group_permissions.values_list('codename', flat=True)),
            'all_permissions': list(all_permissions.values_list('codename', flat=True))
        }
```

## 🎯 基于角色的权限控制 (RBAC)

### 角色模型定义

在 `apps/authentication/models.py` 中添加角色模型：

```python
from django.contrib.auth.models import Group, Permission
from django.db import models

class Role(models.Model):
    """角色模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='角色名称')
    display_name = models.CharField(max_length=100, verbose_name='显示名称')
    description = models.TextField(blank=True, verbose_name='角色描述')
    permissions = models.ManyToManyField(
        Permission, 
        blank=True, 
        verbose_name='权限'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'
        db_table = 'auth_roles'
    
    def __str__(self):
        return self.display_name
    
    def add_permission(self, permission_codename):
        """添加权限"""
        try:
            permission = Permission.objects.get(codename=permission_codename)
            self.permissions.add(permission)
        except Permission.DoesNotExist:
            raise ValueError(f"Permission {permission_codename} does not exist")
    
    def remove_permission(self, permission_codename):
        """移除权限"""
        try:
            permission = Permission.objects.get(codename=permission_codename)
            self.permissions.remove(permission)
        except Permission.DoesNotExist:
            pass
    
    def get_permissions_list(self):
        """获取权限列表"""
        return list(self.permissions.values_list('codename', flat=True))

class UserRole(models.Model):
    """用户角色关联"""
    user = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        verbose_name='用户'
    )
    role = models.ForeignKey(
        Role, 
        on_delete=models.CASCADE, 
        verbose_name='角色'
    )
    assigned_by = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='assigned_roles',
        verbose_name='分配者'
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='分配时间')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    class Meta:
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色'
        unique_together = ('user', 'role')
        db_table = 'auth_user_roles'
    
    def __str__(self):
        return f"{self.user.username} - {self.role.display_name}"

# 扩展 User 模型
class User(AbstractUser):
    # ...existing fields...
    
    def has_role(self, role_name):
        """检查用户是否拥有指定角色"""
        return self.userrole_set.filter(
            role__name=role_name, 
            is_active=True
        ).exists()
    
    def get_roles(self):
        """获取用户所有角色"""
        return Role.objects.filter(
            userrole__user=self,
            userrole__is_active=True
        )
    
    def assign_role(self, role_name, assigned_by=None):
        """分配角色给用户"""
        try:
            role = Role.objects.get(name=role_name, is_active=True)
            user_role, created = UserRole.objects.get_or_create(
                user=self,
                role=role,
                defaults={'assigned_by': assigned_by}
            )
            if not created and not user_role.is_active:
                user_role.is_active = True
                user_role.assigned_by = assigned_by
                user_role.save()
            return user_role
        except Role.DoesNotExist:
            raise ValueError(f"Role {role_name} does not exist")
    
    def remove_role(self, role_name):
        """移除用户角色"""
        UserRole.objects.filter(
            user=self,
            role__name=role_name
        ).update(is_active=False)
    
    def get_all_permissions(self):
        """获取用户所有权限（包括角色权限）"""
        # Django 内置权限
        permissions = set(super().get_all_permissions())
        
        # 角色权限
        for role in self.get_roles():
            role_permissions = role.permissions.values_list('content_type__app_label', 'codename')
            for app_label, codename in role_permissions:
                permissions.add(f"{app_label}.{codename}")
        
        return permissions
```

### 权限检查装饰器

创建 `apps/authentication/decorators.py`：

```python
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

def role_required(role_names):
    """角色权限装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if isinstance(role_names, str):
                required_roles = [role_names]
            else:
                required_roles = role_names
            
            user_roles = [role.name for role in request.user.get_roles()]
            
            if not any(role in user_roles for role in required_roles):
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': '权限不足',
                        'detail': f'需要以下角色之一: {", ".join(required_roles)}'
                    }, status=403)
                else:
                    raise PermissionDenied(f"需要角色: {', '.join(required_roles)}")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def permission_required_api(permission_codename):
    """API 权限装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': '未认证',
                    'detail': '需要登录访问'
                }, status=401)
            
            if not request.user.has_perm(permission_codename):
                return JsonResponse({
                    'error': '权限不足',
                    'detail': f'需要权限: {permission_codename}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

class OrganizationPermissionMixin:
    """组织权限混入类"""
    
    def has_organization_permission(self, user, organization, permission_type='view'):
        """检查用户对组织的权限"""
        # 超级用户拥有所有权限
        if user.is_superuser:
            return True
        
        # 检查用户是否属于该组织
        try:
            profile = user.profile
            if profile.organization_id != organization.id:
                return False
        except:
            return False
        
        # 检查具体权限
        permission_map = {
            'view': 'authentication.view_organization',
            'change': 'authentication.change_organization',
            'delete': 'authentication.delete_organization',
            'manage': 'authentication.can_manage_organization',
        }
        
        required_permission = permission_map.get(permission_type)
        if required_permission:
            return user.has_perm(required_permission)
        
        return False
```

## 🔐 权限中间件

创建 `apps/authentication/permission_middleware.py`：

```python
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
import logging

logger = logging.getLogger(__name__)

class PermissionMiddleware(MiddlewareMixin):
    """权限检查中间件"""
    
    # 需要特殊权限的 URL 配置
    PROTECTED_URLS = {
        'authentication:organizations': 'authentication.view_organization',
        'admin:*': 'auth.is_staff',  # 管理后台需要 staff 权限
    }
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """在视图执行前检查权限"""
        # 跳过不需要权限检查的路径
        exempt_paths = [
            '/api/auth/token/',
            '/api/auth/register/',
            '/api/auth/token/refresh/',
        ]
        
        if any(request.path.startswith(path) for path in exempt_paths):
            return None
        
        # 检查用户认证状态
        if not request.user.is_authenticated:
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': '未认证',
                    'detail': '需要登录访问'
                }, status=401)
            return None
        
        # 解析当前 URL
        try:
            url_name = resolve(request.path).url_name
            namespace = resolve(request.path).namespace
            
            if namespace:
                full_url_name = f"{namespace}:{url_name}"
            else:
                full_url_name = url_name
            
            # 检查是否需要特殊权限
            required_permission = None
            for pattern, permission in self.PROTECTED_URLS.items():
                if pattern.endswith('*'):
                    if full_url_name.startswith(pattern[:-1]):
                        required_permission = permission
                        break
                elif pattern == full_url_name:
                    required_permission = permission
                    break
            
            # 执行权限检查
            if required_permission:
                if required_permission == 'auth.is_staff':
                    if not request.user.is_staff:
                        return JsonResponse({
                            'error': '权限不足',
                            'detail': '需要管理员权限'
                        }, status=403)
                else:
                    if not request.user.has_perm(required_permission):
                        logger.warning(
                            f"User {request.user.username} denied access to {request.path}"
                        )
                        return JsonResponse({
                            'error': '权限不足',
                            'detail': f'需要权限: {required_permission}'
                        }, status=403)
            
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
        
        return None
```

## 🔧 权限管理视图

创建 `apps/authentication/permission_views.py`：

```python
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Role, UserRole
from .permissions import PermissionManager
from .decorators import role_required, permission_required_api
from .serializers import RoleSerializer, UserRoleSerializer, PermissionSerializer

class RoleListCreateView(generics.ListCreateAPIView):
    """角色列表和创建"""
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return super().get_permissions()

class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """角色详情、更新和删除"""
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_permissions(request):
    """获取用户权限信息"""
    user = request.user
    
    # 获取用户角色
    user_roles = user.get_roles()
    
    # 获取权限信息
    permissions_info = PermissionManager.get_user_permissions(user)
    
    return Response({
        'user_id': user.id,
        'username': user.username,
        'roles': [
            {
                'id': role.id,
                'name': role.name,
                'display_name': role.display_name,
                'permissions': role.get_permissions_list()
            }
            for role in user_roles
        ],
        'permissions': permissions_info,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
    })

@api_view(['POST'])
@role_required(['admin', 'user_manager'])
def assign_user_role(request):
    """分配用户角色"""
    user_id = request.data.get('user_id')
    role_id = request.data.get('role_id')
    
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        role = Role.objects.get(id=role_id)
        
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            assigned_by=request.user
        )
        
        return Response({
            'message': f'成功为用户 {user.username} 分配角色 {role.display_name}',
            'user_role_id': user_role.id
        })
        
    except User.DoesNotExist:
        return Response({
            'error': '用户不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Role.DoesNotExist:
        return Response({
            'error': '角色不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': '分配失败',
            'detail': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@role_required(['admin', 'user_manager'])
def remove_user_role(request, user_id, role_id):
    """移除用户角色"""
    try:
        user_role = UserRole.objects.get(
            user_id=user_id,
            role_id=role_id,
            is_active=True
        )
        user_role.is_active = False
        user_role.save()
        
        return Response({
            'message': '角色移除成功'
        })
        
    except UserRole.DoesNotExist:
        return Response({
            'error': '用户角色关系不存在'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_permission(request):
    """检查用户是否拥有指定权限"""
    permission = request.GET.get('permission')
    
    if not permission:
        return Response({
            'error': '未指定权限'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    has_permission = request.user.has_perm(permission)
    
    return Response({
        'user': request.user.username,
        'permission': permission,
        'has_permission': has_permission
    })
```

## 🧪 权限系统测试

### 测试脚本

创建 `test_permissions.py`：

```python
#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://localhost:8000/api/auth'

def test_permission_system():
    """测试权限系统"""
    
    # 1. 登录获取令牌
    print("1. 获取管理员令牌...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = requests.post(f'{BASE_URL}/token/', json=login_data)
    if response.status_code == 200:
        token = response.json()['access']
        headers = {'Authorization': f'Bearer {token}'}
        print("✅ 管理员登录成功")
    else:
        print("❌ 管理员登录失败")
        return
    
    # 2. 检查用户权限
    print("\n2. 检查用户权限...")
    response = requests.get(f'{BASE_URL}/permissions/', headers=headers)
    if response.status_code == 200:
        permissions = response.json()
        print(f"✅ 用户权限: {len(permissions['permissions']['all_permissions'])} 个")
        print(f"用户角色: {[role['display_name'] for role in permissions['roles']]}")
    else:
        print(f"❌ 权限检查失败: {response.status_code}")
    
    # 3. 测试角色列表
    print("\n3. 获取角色列表...")
    response = requests.get(f'{BASE_URL}/roles/', headers=headers)
    if response.status_code == 200:
        roles = response.json()
        print(f"✅ 系统角色: {len(roles['results'])} 个")
        for role in roles['results'][:3]:
            print(f"  - {role['display_name']}: {role['description']}")
    else:
        print(f"❌ 角色列表获取失败: {response.status_code}")
    
    # 4. 测试权限检查
    print("\n4. 测试特定权限检查...")
    test_permissions = [
        'authentication.view_user',
        'authentication.can_manage_users',
        'authentication.add_organization'
    ]
    
    for perm in test_permissions:
        response = requests.get(
            f'{BASE_URL}/check-permission/', 
            params={'permission': perm}, 
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            status_icon = "✅" if result['has_permission'] else "❌"
            print(f"  {status_icon} {perm}: {result['has_permission']}")
        else:
            print(f"  ❌ 检查失败: {perm}")

if __name__ == '__main__':
    test_permission_system()
```

### 数据库迁移

```bash
# 创建角色相关的迁移
python manage.py makemigrations authentication

# 应用迁移
python manage.py migrate

# 创建自定义权限
python manage.py shell -c "
from apps.authentication.permissions import PermissionManager
PermissionManager.create_custom_permissions()
"
```

## 📊 权限管理命令

创建 `apps/authentication/management/commands/setup_permissions.py`：

```python
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group
from apps.authentication.models import Role
from apps.authentication.permissions import PermissionManager

class Command(BaseCommand):
    help = '初始化权限系统'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-roles',
            action='store_true',
            help='创建预定义角色',
        )
    
    def handle(self, *args, **options):
        # 创建自定义权限
        self.stdout.write('创建自定义权限...')
        PermissionManager.create_custom_permissions()
        
        if options['create_roles']:
            self.create_default_roles()
        
        self.stdout.write(
            self.style.SUCCESS('权限系统初始化完成')
        )
    
    def create_default_roles(self):
        """创建默认角色"""
        default_roles = [
            {
                'name': 'admin',
                'display_name': '系统管理员',
                'description': '拥有系统所有权限',
                'permissions': ['*']  # 所有权限
            },
            {
                'name': 'user_manager',
                'display_name': '用户管理员',
                'description': '负责用户和组织管理',
                'permissions': [
                    'authentication.add_user',
                    'authentication.change_user',
                    'authentication.view_user',
                    'authentication.can_manage_users',
                    'authentication.add_organization',
                    'authentication.change_organization',
                    'authentication.view_organization',
                ]
            },
            {
                'name': 'regular_user',
                'display_name': '普通用户',
                'description': '基础用户权限',
                'permissions': [
                    'authentication.view_user',
                    'authentication.change_userprofile',
                ]
            }
        ]
        
        for role_data in default_roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'display_name': role_data['display_name'],
                    'description': role_data['description']
                }
            )
            
            if created or role_data['permissions'] == ['*']:
                # 分配权限
                if role_data['permissions'] == ['*']:
                    # 分配所有权限
                    role.permissions.set(Permission.objects.all())
                else:
                    # 分配指定权限
                    for perm_code in role_data['permissions']:
                        try:
                            permission = Permission.objects.get(codename=perm_code.split('.')[-1])
                            role.permissions.add(permission)
                        except Permission.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f'权限不存在: {perm_code}')
                            )
                
                self.stdout.write(f'✅ 创建角色: {role.display_name}')
```

执行权限初始化：

```bash
python manage.py setup_permissions --create-roles
```

## 🔗 下一步

- [角色权限管理](./05_role_based_access.md) - 深入配置 RBAC
- [API 安全配置](./06_api_security.md) - 加强 API 安全防护
- [权限审计监控](./07_audit_monitoring.md) - 设置审计和监控

## ⚠️ 注意事项

1. **权限设计**: 遵循最小权限原则，避免权限过度分配
2. **角色规划**: 提前规划好角色层次和权限分配策略  
3. **权限缓存**: 考虑权限检查的性能优化和缓存策略
4. **审计日志**: 记录所有权限变更和敏感操作
5. **安全测试**: 定期进行权限控制的安全测试
