'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Spin } from 'antd';
import { useAuthStore } from '@/store/authStore';
import { ROUTES } from '@/constants';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    // 检查是否已登录
    const localToken = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    
    if (localToken && isAuthenticated) {
      // 已登录，跳转到仪表盘
      router.push(ROUTES.DASHBOARD);
    } else {
      // 未登录，跳转到登录页
      router.push(ROUTES.LOGIN);
    }
  }, [router, isAuthenticated]);

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh' 
    }}>
      <Spin size="large" tip="正在跳转..." />
    </div>
  );
}
