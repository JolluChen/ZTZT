import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import PermissionGuard from '@/components/common/PermissionGuard';

// Mock useAuthStore
jest.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    user: {
      permissions: ['dataset_read', 'model_read'],
    },
  }),
}));

describe('PermissionGuard', () => {
  it('renders children when user has required permission', () => {
    render(
      <PermissionGuard permissions={['dataset_read']}>
        <button>Test Button</button>
      </PermissionGuard>
    );

    expect(screen.getByText('Test Button')).toBeInTheDocument();
  });

  it('does not render children when user lacks permission', () => {
    render(
      <PermissionGuard permissions={['admin_super']}>
        <button>Admin Button</button>
      </PermissionGuard>
    );

    expect(screen.queryByText('Admin Button')).not.toBeInTheDocument();
  });

  it('renders children when user has all required permissions (requireAll=true)', () => {
    render(
      <PermissionGuard permissions={['dataset_read', 'model_read']} requireAll={true}>
        <button>Multi Permission Button</button>
      </PermissionGuard>
    );

    expect(screen.getByText('Multi Permission Button')).toBeInTheDocument();
  });

  it('does not render children when user lacks some permissions (requireAll=true)', () => {
    render(
      <PermissionGuard permissions={['dataset_read', 'admin_super']} requireAll={true}>
        <button>Missing Permission Button</button>
      </PermissionGuard>
    );

    expect(screen.queryByText('Missing Permission Button')).not.toBeInTheDocument();
  });

  it('renders fallback when provided and user lacks permission', () => {
    render(
      <PermissionGuard 
        permissions={['admin_super']} 
        fallback={<div>Access Denied</div>}
      >
        <button>Protected Button</button>
      </PermissionGuard>
    );

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.queryByText('Protected Button')).not.toBeInTheDocument();
  });
});
