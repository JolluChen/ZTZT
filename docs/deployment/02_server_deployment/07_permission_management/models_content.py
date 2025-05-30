# AI 中台 - Django 认证系统部署

[![Django 4.2](https://img.shields.io/badge/Django-4.2-092E20?style=flat-square&logo=django)](https://www.djangoproject.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/) [![安全认证](https://img.shields.io/badge/安全认证-企业级-green?style=flat-square)](https://github.com)

**文档类型**: 部署实施文档  
**预计部署时间**: 30-45分钟  
**难度级别**: ⭐⭐⭐  
**前置要求**: PostgreSQL 16 已部署并运行

## 概述

本文档详细说明如何部署和配置 AI 中台的 Django 认证系统，包括扩展用户模型、组织管理、角色系统以及认证管理器的实现。

## 1. 扩展用户模型部署

### 1.1 创建认证应用扩展

首先创建认证系统的扩展模块：

```bash
# 创建权限管理应用扩展目录
sudo mkdir -p /opt/ai-platform/backend/config/auth_extensions
sudo chown -R ai-platform:ai-platform /opt/ai-platform/backend/config/auth_extensions
```

### 1.2 部署扩展用户模型

创建增强的用户模型，支持组织关系、API用户和安全控制：

<function_calls>
<invoke name="create_file">
<parameter name="content">"""
AI 中台用户认证模型扩展
基于 Django 4.2 + PostgreSQL 16
"""

from django.contrib.auth.models import AbstractUser, Group
from django.db import models
import uuid
from django.core.validators import RegexValidator
import json

class ExtendedUser(AbstractUser):
    """扩展的用户模型"""
    
    # 添加 UUID 字段用于外部引用
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # 扩展用户信息
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    
    # 业务相关字段
    organization = models.ForeignKey(
        'Organization', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    is_api_user = models.BooleanField(default=False, help_text="是否为API专用用户")
    api_rate_limit = models.IntegerField(default=1000, help_text="API调用频率限制/小时")
    
    # 安全字段
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(auto_now_add=True)
    must_change_password = models.BooleanField(default=False)
    
    # 元数据
    profile_data = models.JSONField(default=dict, blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_users'
        verbose_name = 'AI 平台用户'
        verbose_name_plural = 'AI 平台用户'
    
    def get_permissions_list(self):
        """获取用户所有权限列表"""
        perms = set()
        
        # 用户直接权限
        perms.update(self.user_permissions.values_list('codename', flat=True))
        
        # 组权限
        for group in self.groups.all():
            perms.update(group.permissions.values_list('codename', flat=True))
        
        # 角色权限
        for role in self.roles.all():
            perms.update(role.permissions.values_list('codename', flat=True))
            
        return list(perms)
    
    def has_platform_permission(self, permission, obj=None):
        """检查平台特定权限"""
        if self.is_superuser:
            return True
            
        # 检查对象级权限（使用 django-guardian）
        if obj:
            from guardian.shortcuts import get_perms
            return permission in get_perms(self, obj)
            
        # 检查模型级权限
        return self.has_perm(permission)

class Organization(models.Model):
    """组织机构模型"""
    
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # 层级结构
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='children'
    )
    level = models.IntegerField(default=0)
    
    # 配置信息
    settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_organizations'
        verbose_name = '组织机构'
        verbose_name_plural = '组织机构'
        
    def __str__(self):
        return self.name

class Role(models.Model):
    """角色模型"""
    
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # 权限配置
    permissions = models.ManyToManyField(
        'auth.Permission', 
        blank=True,
        related_name='roles'
    )
    
    # 业务范围
    platform_scope = models.JSONField(
        default=list, 
        help_text="适用的平台模块: ['data', 'algo', 'model', 'service']"
    )
    
    # 层级和优先级
    level = models.IntegerField(default=0, help_text="角色层级，数字越大权限越高")
    priority = models.IntegerField(default=100, help_text="角色优先级")
    
    # 状态
    is_active = models.BooleanField(default=True)
    is_system_role = models.BooleanField(default=False, help_text="是否为系统内置角色")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_roles'
        verbose_name = '角色'
        verbose_name_plural = '角色'
        ordering = ['-level', '-priority']
        
    def __str__(self):
        return f"{self.name} (Level {self.level})"

class UserRole(models.Model):
    """用户角色关联模型"""
    
    user = models.ForeignKey(
        ExtendedUser, 
        on_delete=models.CASCADE,
        related_name='roles'
    )
    role = models.ForeignKey(
        Role, 
        on_delete=models.CASCADE,
        related_name='users'
    )
    
    # 授权范围
    scope_restriction = models.JSONField(
        default=dict,
        blank=True,
        help_text="角色权限的范围限制"
    )
    
    # 有效期
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # 授权信息
    granted_by = models.ForeignKey(
        ExtendedUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_roles'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_user_roles'
        unique_together = ['user', 'role']
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色'

class PermissionLog(models.Model):
    """权限操作日志"""
    
    ACTION_CHOICES = [
        ('grant', '授权'),
        ('revoke', '撤销'),
        ('check', '检查'),
        ('deny', '拒绝'),
        ('login', '登录'),
        ('login_failed', '登录失败'),
        ('logout', '登出'),
        ('token_refresh', '令牌刷新'),
    ]
    
    user = models.ForeignKey(ExtendedUser, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    permission = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=100, blank=True)
    
    # 操作结果
    success = models.BooleanField()
    reason = models.TextField(blank=True)
    
    # 上下文信息
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    
    # 时间戳
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_permission_logs'
        verbose_name = '权限日志'
        verbose_name_plural = '权限日志'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]
