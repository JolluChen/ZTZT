'use client';

import React, { useState, useEffect } from 'react';
import { Layout, Menu, Dropdown, Avatar, Badge, Button, Drawer, theme } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  DeploymentUnitOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useAppStore } from '@/store/appStore';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import { ROUTES } from '@/constants';

const { Header, Sider, Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const router = useRouter();
  const pathname = usePathname();
  const { token } = theme.useToken();
  
  const { user, logout } = useAuthStore();
  const { collapsed, toggleSidebar, notifications } = useAppStore();
  
  const [notificationDrawer, setNotificationDrawer] = useState(false);

  // 菜单配置
  const menuItems = [
    {
      key: ROUTES.DASHBOARD,
      icon: <DashboardOutlined />,
      label: <Link href={ROUTES.DASHBOARD}>仪表盘</Link>,
    },
    {
      key: 'data',
      icon: <DatabaseOutlined />,
      label: '数据中台',
      children: [
        {
          key: ROUTES.DATA_OVERVIEW,
          label: <Link href={ROUTES.DATA_OVERVIEW}>数据概览</Link>,
        },
        {
          key: ROUTES.DATA_DATASETS,
          label: <Link href={ROUTES.DATA_DATASETS}>数据集管理</Link>,
        },
        {
          key: ROUTES.DATA_UPLOAD,
          label: <Link href={ROUTES.DATA_UPLOAD}>数据上传</Link>,
        },
      ],
    },
    {
      key: 'algorithm',
      icon: <ExperimentOutlined />,
      label: '算法中台',
      children: [
        {
          key: ROUTES.ALGORITHM_OVERVIEW,
          label: <Link href={ROUTES.ALGORITHM_OVERVIEW}>算法概览</Link>,
        },
        {
          key: ROUTES.ALGORITHM_EXPERIMENTS,
          label: <Link href={ROUTES.ALGORITHM_EXPERIMENTS}>实验管理</Link>,
        },
        {
          key: ROUTES.ALGORITHM_CREATE,
          label: <Link href={ROUTES.ALGORITHM_CREATE}>创建实验</Link>,
        },
      ],
    },
    {
      key: 'model',
      icon: <DeploymentUnitOutlined />,
      label: '模型中台',
      children: [
        {
          key: ROUTES.MODEL_OVERVIEW,
          label: <Link href={ROUTES.MODEL_OVERVIEW}>模型概览</Link>,
        },
        {
          key: ROUTES.MODEL_MODELS,
          label: <Link href={ROUTES.MODEL_MODELS}>模型管理</Link>,
        },
        {
          key: ROUTES.MODEL_DEPLOY,
          label: <Link href={ROUTES.MODEL_DEPLOY}>模型部署</Link>,
        },
      ],
    },
    {
      key: 'service',
      icon: <AppstoreOutlined />,
      label: '服务中台',
      children: [
        {
          key: ROUTES.SERVICE_OVERVIEW,
          label: <Link href={ROUTES.SERVICE_OVERVIEW}>服务概览</Link>,
        },
        {
          key: ROUTES.SERVICE_APPLICATIONS,
          label: <Link href={ROUTES.SERVICE_APPLICATIONS}>应用管理</Link>,
        },
        {
          key: ROUTES.SERVICE_CREATE,
          label: <Link href={ROUTES.SERVICE_CREATE}>创建应用</Link>,
        },
      ],
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
      children: [
        {
          key: ROUTES.SETTINGS_PERMISSIONS,
          label: <Link href={ROUTES.SETTINGS_PERMISSIONS}>权限管理</Link>,
        },
        {
          key: ROUTES.SETTINGS,
          label: <Link href={ROUTES.SETTINGS}>系统配置</Link>,
        },
      ],
    },
    {
      key: ROUTES.DEMO,
      icon: <AppstoreOutlined />,
      label: <Link href={ROUTES.DEMO}>组件演示</Link>,
    },
  ];

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
      onClick: () => router.push('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
      onClick: () => router.push('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout();
        router.push(ROUTES.LOGIN);
      },
    },
  ];

  // 获取当前选中的菜单项
  const getSelectedKeys = () => {
    if (pathname === ROUTES.DASHBOARD) return [ROUTES.DASHBOARD];
    
    // 数据中台
    if (pathname.startsWith('/data')) {
      return [pathname];
    }
    
    // 算法中台
    if (pathname.startsWith('/algorithm')) {
      return [pathname];
    }
    
    // 模型中台
    if (pathname.startsWith('/model')) {
      return [pathname];
    }
    
    // 服务中台
    if (pathname.startsWith('/service')) {
      return [pathname];
    }
    
    return [pathname];
  };

  // 获取打开的菜单项
  const getOpenKeys = () => {
    if (pathname.startsWith('/data')) return ['data'];
    if (pathname.startsWith('/algorithm')) return ['algorithm'];
    if (pathname.startsWith('/model')) return ['model'];
    if (pathname.startsWith('/service')) return ['service'];
    return [];
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        style={{
          background: token.colorBgContainer,
          borderRight: `1px solid ${token.colorBorder}`,
        }}
        width={240}
      >
        <div 
          style={{ 
            height: 64, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            borderBottom: `1px solid ${token.colorBorder}`,
            fontSize: collapsed ? 14 : 18,
            fontWeight: 'bold',
            color: token.colorPrimary,
          }}
        >
          {collapsed ? 'AI' : 'AI中台管理系统'}
        </div>
        
        <Menu
          mode="inline"
          selectedKeys={getSelectedKeys()}
          defaultOpenKeys={getOpenKeys()}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>
      
      <Layout>
        <Header 
          style={{ 
            padding: '0 24px', 
            background: token.colorBgContainer,
            borderBottom: `1px solid ${token.colorBorder}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={toggleSidebar}
              style={{ fontSize: 16, width: 64, height: 64 }}
            />
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* 通知 */}
            <Badge count={notifications.length} size="small">
              <Button
                type="text"
                icon={<BellOutlined />}
                onClick={() => setNotificationDrawer(true)}
                style={{ fontSize: 16 }}
              />
            </Badge>
            
            {/* 用户信息 */}
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 8, 
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: 6,
                }}
              >
                <Avatar size="small" icon={<UserOutlined />} />
                <span>{user?.username || '用户'}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: token.colorBgContainer,
            borderRadius: token.borderRadius,
            minHeight: 'calc(100vh - 112px)',
          }}
        >
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </Content>
      </Layout>
      
      {/* 通知抽屉 */}
      <Drawer
        title="系统通知"
        placement="right"
        onClose={() => setNotificationDrawer(false)}
        open={notificationDrawer}
        width={400}
      >
        {notifications.length === 0 ? (
          <div style={{ textAlign: 'center', color: token.colorTextSecondary }}>
            暂无通知
          </div>
        ) : (
          <div>
            {notifications.map(notification => (
              <div 
                key={notification.id}
                style={{
                  padding: 16,
                  marginBottom: 8,
                  border: `1px solid ${token.colorBorder}`,
                  borderRadius: token.borderRadius,
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                  {notification.title}
                </div>
                {notification.message && (
                  <div style={{ color: token.colorTextSecondary, fontSize: 12 }}>
                    {notification.message}
                  </div>
                )}
                <div style={{ color: token.colorTextTertiary, fontSize: 11, marginTop: 4 }}>
                  {new Date(notification.timestamp).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </Drawer>
    </Layout>
  );
};

export default MainLayout;
