'use client';

import React, { useState } from 'react';
import { Form, Input, Button, Card, Divider, Space, App } from 'antd';
import { UserOutlined, LockOutlined, EyeInvisibleOutlined, EyeTwoTone } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/authStore';
import { ROUTES } from '@/constants';

const LoginPage: React.FC = () => {
  const router = useRouter();
  const { login } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  // 获取当前API地址
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  const isLocalhost = apiUrl.includes('localhost') || apiUrl.includes('127.0.0.1');

  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      if (process.env.NODE_ENV === 'development') {
        console.log('尝试登录:', values.username);
      }
      await login(values.username, values.password);
      message.success('登录成功！');
      router.push(ROUTES.DASHBOARD);
    } catch (error: any) {
      console.error('登录错误:', error.message || '未知错误');
      
      // 处理网络错误
      if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        message.error({
          content: (
            <div>
              <div>无法连接到后端服务</div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                请检查：1) 后端服务是否运行 2) 网络连接是否正常 3) API地址是否正确
              </div>
            </div>
          ),
          duration: 6,
        });
      } else {
        message.error(error?.response?.data?.detail || error?.response?.data?.message || '登录失败，请检查用户名和密码');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
      }}
    >
      <Card
        style={{
          width: 400,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        }}
        styles={{ body: { padding: 40 } }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, fontWeight: 'bold', color: '#1890ff', margin: 0 }}>
            AI中台管理系统
          </h1>
          <p style={{ color: '#666', marginTop: 8 }}>
            智能化企业级AI平台解决方案
          </p>
        </div>

        <Form
          form={form}
          name="login"
          onFinish={handleLogin}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              autoComplete="current-password"
              iconRender={(visible) => 
                visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />
              }
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 40 }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <Divider>或</Divider>

        <div style={{ textAlign: 'center' }}>
          <Space direction="vertical" size="small">
            <Link href={ROUTES.REGISTER}>
              <Button type="link" style={{ padding: 0 }}>
                还没有账号？立即注册
              </Button>
            </Link>
            <Button type="link" style={{ padding: 0 }}>
              忘记密码？
            </Button>
          </Space>
        </div>

        <div 
          style={{ 
            marginTop: 32, 
            padding: 16, 
            background: '#f6f8fa', 
            borderRadius: 8,
            fontSize: 12,
            color: '#666',
          }}
        >
          <div style={{ fontWeight: 'bold', marginBottom: 8 }}>测试账号:</div>
          <div>管理员: admin / admin123</div>
          <div>普通用户: user / user123</div>
          
          {/* 网络配置信息 */}
          <div style={{ marginTop: 12, paddingTop: 8, borderTop: '1px solid #ddd' }}>
            <div style={{ fontWeight: 'bold', marginBottom: 4 }}>当前配置:</div>
            <div style={{ fontSize: '11px', color: '#888' }}>
              API地址: {apiUrl}
            </div>
            {isLocalhost && (
              <div style={{ 
                marginTop: 4, 
                padding: '4px 8px', 
                background: '#fff3cd', 
                border: '1px solid #ffeaa7',
                borderRadius: 4,
                color: '#856404'
              }}>
                ⚠️ 使用本地地址，跨机器访问请修改 .env.local 中的 NEXT_PUBLIC_API_URL
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;
