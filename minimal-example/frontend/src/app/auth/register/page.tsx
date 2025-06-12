'use client';

import React, { useState } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  Typography,
  message,
  Row,
  Col,
  Steps,
  Select,
  Checkbox,
} from 'antd';
import {
  UserOutlined,
  MailOutlined,
  LockOutlined,
  PhoneOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authService } from '@/services';

const { Title, Text } = Typography;
const { Option } = Select;

interface RegisterFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  first_name: string;
  last_name: string;
  phone: string;
  department: string;
  position: string;
  agreement: boolean;
}

export default function RegisterPage() {
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const router = useRouter();

  const registerMutation = useMutation({
    mutationFn: (data: RegisterFormData) => {
      const { confirmPassword, agreement, ...registerData } = data;
      return authService.register(registerData);
    },
    onSuccess: () => {
      message.success('注册成功！请登录');
      router.push('/auth/login');
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.message || '注册失败，请重试';
      message.error(errorMessage);
    },
  });

  const handleSubmit = async (values: RegisterFormData) => {
    registerMutation.mutate(values);
  };

  const nextStep = async () => {
    try {
      if (currentStep === 0) {
        await form.validateFields(['username', 'email', 'password', 'confirmPassword']);
      } else if (currentStep === 1) {
        await form.validateFields(['first_name', 'last_name', 'phone']);
      }
      setCurrentStep(currentStep + 1);
    } catch (error) {
      // 验证失败，不进入下一步
    }
  };

  const prevStep = () => {
    setCurrentStep(currentStep - 1);
  };

  const steps = [
    {
      title: '账户信息',
      description: '设置登录账户',
    },
    {
      title: '个人信息',
      description: '完善个人资料',
    },
    {
      title: '工作信息',
      description: '填写工作信息',
    },
  ];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <>
            <Form.Item
              label="用户名"
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
                { max: 20, message: '用户名最多20个字符' },
                { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="请输入用户名"
                size="large"
              />
            </Form.Item>

            <Form.Item
              label="邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入邮箱地址' },
                { type: 'email', message: '请输入有效的邮箱地址' },
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="请输入邮箱地址"
                size="large"
              />
            </Form.Item>

            <Form.Item
              label="密码"
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 8, message: '密码至少8个字符' },
                { 
                  pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/,
                  message: '密码必须包含大小写字母和数字'
                },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请输入密码"
                size="large"
              />
            </Form.Item>

            <Form.Item
              label="确认密码"
              name="confirmPassword"
              dependencies={['password']}
              rules={[
                { required: true, message: '请确认密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('两次输入的密码不一致'));
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请再次输入密码"
                size="large"
              />
            </Form.Item>
          </>
        );

      case 1:
        return (
          <>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="姓氏"
                  name="last_name"
                  rules={[{ required: true, message: '请输入姓氏' }]}
                >
                  <Input placeholder="请输入姓氏" size="large" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="名字"
                  name="first_name"
                  rules={[{ required: true, message: '请输入名字' }]}
                >
                  <Input placeholder="请输入名字" size="large" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              label="手机号码"
              name="phone"
              rules={[
                { required: true, message: '请输入手机号码' },
                { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' },
              ]}
            >
              <Input
                prefix={<PhoneOutlined />}
                placeholder="请输入手机号码"
                size="large"
              />
            </Form.Item>
          </>
        );

      case 2:
        return (
          <>
            <Form.Item
              label="部门"
              name="department"
              rules={[{ required: true, message: '请选择部门' }]}
            >
              <Select placeholder="请选择部门" size="large">
                <Option value="技术部">技术部</Option>
                <Option value="产品部">产品部</Option>
                <Option value="运营部">运营部</Option>
                <Option value="市场部">市场部</Option>
                <Option value="销售部">销售部</Option>
                <Option value="人事部">人事部</Option>
                <Option value="财务部">财务部</Option>
                <Option value="其他">其他</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="职位"
              name="position"
              rules={[{ required: true, message: '请输入职位' }]}
            >
              <Input
                prefix={<TeamOutlined />}
                placeholder="请输入职位"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="agreement"
              valuePropName="checked"
              rules={[
                {
                  validator: (_, value) =>
                    value ? Promise.resolve() : Promise.reject(new Error('请阅读并同意用户协议')),
                },
              ]}
            >
              <Checkbox>
                我已阅读并同意{' '}
                <Link href="/terms" target="_blank" style={{ color: '#1890ff' }}>
                  《用户协议》
                </Link>{' '}
                和{' '}
                <Link href="/privacy" target="_blank" style={{ color: '#1890ff' }}>
                  《隐私政策》
                </Link>
              </Checkbox>
            </Form.Item>
          </>
        );

      default:
        return null;
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
        padding: '20px',
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: '600px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          borderRadius: '16px',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <Title level={2} style={{ marginBottom: '8px' }}>
            注册账户
          </Title>
          <Text type="secondary">
            加入AI中台管理系统
          </Text>
        </div>

        <Steps current={currentStep} style={{ marginBottom: '32px' }}>
          {steps.map((step, index) => (
            <Steps.Step
              key={index}
              title={step.title}
              description={step.description}
            />
          ))}
        </Steps>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          size="large"
        >
          {renderStepContent()}

          <div style={{ marginTop: '32px' }}>
            <Row gutter={16}>
              {currentStep > 0 && (
                <Col span={12}>
                  <Button
                    size="large"
                    block
                    onClick={prevStep}
                  >
                    上一步
                  </Button>
                </Col>
              )}
              <Col span={currentStep > 0 ? 12 : 24}>
                {currentStep < steps.length - 1 ? (
                  <Button
                    type="primary"
                    size="large"
                    block
                    onClick={nextStep}
                  >
                    下一步
                  </Button>
                ) : (
                  <Button
                    type="primary"
                    size="large"
                    block
                    htmlType="submit"
                    loading={registerMutation.isPending}
                  >
                    完成注册
                  </Button>
                )}
              </Col>
            </Row>
          </div>
        </Form>

        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <Text type="secondary">
            已有账户？{' '}
            <Link href="/auth/login" style={{ color: '#1890ff' }}>
              立即登录
            </Link>
          </Text>
        </div>
      </Card>
    </div>
  );
}
