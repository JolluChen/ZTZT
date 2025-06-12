'use client';

import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  message,
  Typography,
  Row,
  Col,
  Avatar,
  Upload,
  Select,
  Divider,
  Space,
  Modal,
  Descriptions,
} from 'antd';
import {
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  TeamOutlined,
  EditOutlined,
  CameraOutlined,
  LockOutlined,
  SaveOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService } from '@/services';
import { User, UserProfile } from '@/types';
import { formatDate } from '@/utils';

const { Title, Text } = Typography;
const { Option } = Select;

export default function ProfilePage() {
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [editMode, setEditMode] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const queryClient = useQueryClient();

  // 获取用户信息
  const {
    data: user,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['profile'],
    queryFn: () => authService.getProfile(),
  });

  // 更新个人信息
  const updateProfileMutation = useMutation({
    mutationFn: (data: Partial<UserProfile>) => authService.updateProfile(data),
    onSuccess: () => {
      message.success('个人信息更新成功');
      setEditMode(false);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '更新失败');
    },
  });

  // 修改密码
  const changePasswordMutation = useMutation({
    mutationFn: (data: { old_password: string; new_password: string }) =>
      authService.changePassword(data),
    onSuccess: () => {
      message.success('密码修改成功');
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '密码修改失败');
    },
  });

  const handleUpdateProfile = async (values: any) => {
    updateProfileMutation.mutate(values);
  };

  const handleChangePassword = async (values: any) => {
    changePasswordMutation.mutate(values);
  };

  const handleEdit = () => {
    setEditMode(true);
    if (user?.profile) {
      form.setFieldsValue({
        phone: user.profile.phone,
        department: user.profile.department,
        position: user.profile.position,
      });
    }
  };

  const handleCancel = () => {
    setEditMode(false);
    form.resetFields();
  };

  const uploadProps = {
    name: 'avatar',
    action: '/api/upload/avatar',
    headers: {
      authorization: `Bearer ${typeof window !== 'undefined' ? localStorage.getItem('token') : ''}`,
    },
    beforeUpload: (file: File) => {
      const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
      if (!isJpgOrPng) {
        message.error('只能上传 JPG/PNG 格式的图片');
      }
      const isLt2M = file.size / 1024 / 1024 < 2;
      if (!isLt2M) {
        message.error('图片大小不能超过 2MB');
      }
      return isJpgOrPng && isLt2M;
    },
    onChange: (info: any) => {
      if (info.file.status === 'done') {
        message.success('头像上传成功');
        queryClient.invalidateQueries({ queryKey: ['profile'] });
      } else if (info.file.status === 'error') {
        message.error('头像上传失败');
      }
    },
  };

  if (isLoading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Text>加载中...</Text>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Text type="danger">加载用户信息失败</Text>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>个人信息</Title>
        <Text type="secondary">管理您的个人资料和账户设置</Text>
      </div>

      <Row gutter={24}>
        {/* 左侧：基本信息卡片 */}
        <Col xs={24} lg={8}>
          <Card>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <Upload {...uploadProps} showUploadList={false}>
                <Avatar
                  size={100}
                  icon={<UserOutlined />}
                  style={{ cursor: 'pointer', marginBottom: '16px' }}
                />
                <div>
                  <Button
                    type="link"
                    icon={<CameraOutlined />}
                    size="small"
                  >
                    更换头像
                  </Button>
                </div>
              </Upload>
            </div>

            <Descriptions column={1} size="small">
              <Descriptions.Item label="用户名">
                {user.username}
              </Descriptions.Item>
              <Descriptions.Item label="邮箱">
                {user.email}
              </Descriptions.Item>
              <Descriptions.Item label="姓名">
                {user.last_name}{user.first_name}
              </Descriptions.Item>
              <Descriptions.Item label="注册时间">
                {formatDate(user.date_joined)}
              </Descriptions.Item>
              <Descriptions.Item label="账户类型">
                {user.is_superuser ? '超级管理员' : user.is_staff ? '管理员' : '普通用户'}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                type="primary"
                icon={<LockOutlined />}
                block
                onClick={() => setPasswordModalVisible(true)}
              >
                修改密码
              </Button>
            </Space>
          </Card>
        </Col>

        {/* 右侧：详细信息 */}
        <Col xs={24} lg={16}>
          <Card
            title="详细信息"
            extra={
              !editMode ? (
                <Button
                  type="primary"
                  icon={<EditOutlined />}
                  onClick={handleEdit}
                >
                  编辑
                </Button>
              ) : (
                <Space>
                  <Button onClick={handleCancel}>取消</Button>
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    onClick={() => form.submit()}
                    loading={updateProfileMutation.isPending}
                  >
                    保存
                  </Button>
                </Space>
              )
            }
          >
            {editMode ? (
              <Form
                form={form}
                layout="vertical"
                onFinish={handleUpdateProfile}
              >
                <Row gutter={16}>
                  <Col span={12}>
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
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label="部门"
                      name="department"
                      rules={[{ required: true, message: '请选择部门' }]}
                    >
                      <Select placeholder="请选择部门">
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
                  </Col>
                </Row>

                <Form.Item
                  label="职位"
                  name="position"
                  rules={[{ required: true, message: '请输入职位' }]}
                >
                  <Input
                    prefix={<TeamOutlined />}
                    placeholder="请输入职位"
                  />
                </Form.Item>
              </Form>
            ) : (
              <Descriptions column={2} bordered>
                <Descriptions.Item label="手机号码" span={1}>
                  {user.profile?.phone || '未设置'}
                </Descriptions.Item>
                <Descriptions.Item label="部门" span={1}>
                  {user.profile?.department || '未设置'}
                </Descriptions.Item>
                <Descriptions.Item label="职位" span={2}>
                  {user.profile?.position || '未设置'}
                </Descriptions.Item>
                <Descriptions.Item label="资料创建时间" span={1}>
                  {user.profile?.created_at ? formatDate(user.profile.created_at) : '未设置'}
                </Descriptions.Item>
                <Descriptions.Item label="最后更新时间" span={1}>
                  {user.profile?.updated_at ? formatDate(user.profile.updated_at) : '未设置'}
                </Descriptions.Item>
              </Descriptions>
            )}
          </Card>
        </Col>
      </Row>

      {/* 修改密码对话框 */}
      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onCancel={() => setPasswordModalVisible(false)}
        onOk={() => passwordForm.submit()}
        confirmLoading={changePasswordMutation.isPending}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item
            label="当前密码"
            name="old_password"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入当前密码"
            />
          </Form.Item>

          <Form.Item
            label="新密码"
            name="new_password"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 8, message: '密码至少8个字符' },
              { 
                pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/,
                message: '密码必须包含大小写字母和数字'
              },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入新密码"
            />
          </Form.Item>

          <Form.Item
            label="确认新密码"
            name="confirm_password"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请再次输入新密码"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
