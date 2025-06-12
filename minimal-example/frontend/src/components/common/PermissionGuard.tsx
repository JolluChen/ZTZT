'use client';

import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { PERMISSIONS } from '@/constants';

interface PermissionGuardProps {
  permissions: string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
  requireAll?: boolean; // 是否需要所有权限都满足
}

const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permissions,
  children,
  fallback = null,
  requireAll = false,
}) => {
  const { user, hasPermission } = useAuthStore();

  // 如果用户未登录，不显示内容
  if (!user) {
    return <>{fallback}</>;
  }

  // 检查权限
  const hasRequiredPermissions = requireAll
    ? permissions.every(permission => hasPermission(permission))
    : permissions.some(permission => hasPermission(permission));

  // 如果没有权限，显示fallback或返回null
  if (!hasRequiredPermissions) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// 权限检查Hook
export const usePermission = () => {
  const { hasPermission } = useAuthStore();

  return {
    canView: (resource: string) => hasPermission(`${resource}.view`),
    canCreate: (resource: string) => hasPermission(`${resource}.create`),
    canEdit: (resource: string) => hasPermission(`${resource}.edit`),
    canDelete: (resource: string) => hasPermission(`${resource}.delete`),
    canManage: (resource: string) => hasPermission(`${resource}.manage`),
    hasPermission,
  };
};

// 权限按钮组件
interface PermissionButtonProps {
  permission: string;
  children: React.ReactNode;
  [key: string]: unknown;
}

export const PermissionButton: React.FC<PermissionButtonProps> = ({
  permission,
  children,
  ...props
}) => {
  const { hasPermission } = useAuthStore();

  if (!hasPermission(permission)) {
    return null;
  }

  return React.cloneElement(children as React.ReactElement, props);
};

export default PermissionGuard;
