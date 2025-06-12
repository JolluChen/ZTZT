'use client';

import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  message,
  Typography,
  Row,
  Col,
  Divider,
  Select,
  Space,
  Table,
  Modal,
  Tag,
  Tooltip,
} from 'antd';
import {
  SettingOutlined,
  SecurityScanOutlined,
  DatabaseOutlined,
  CloudOutlined,
  BellOutlined,
  UserOutlined,
  SaveOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

const { Title, Text } = Typography;
const { Option } = Select;

interface SystemConfig {
  app_name: string;
  app_version: string;
  max_upload_size: number;
  session_timeout: number;
  enable_registration: boolean;
  enable_email_notification: boolean;
  default_language: string;
  timezone: string;
  storage_provider: string;
  storage_config: Record<string, any>;
  email_config: Record<string, any>;
}

interface UserRole {
  id: number;
  name: string;
  description: string;
  permissions: string[];
  user_count: number;
}

const mockSystemConfig: SystemConfig = {
  app_name: 'AI中台管理系统',
  app_version: '1.0.0',
  max_upload_size: 100,
  session_timeout: 24,
  enable_registration: true,
  enable_email_notification: true,
  default_language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  storage_provider: 'local',
  storage_config: {
    path: '/uploads',
  },
  email_config: {
    smtp_server: 'smtp.example.com',
    smtp_port: 587,
    use_tls: true,
  },
};

const mockRoles: UserRole[] = [
  {
    id: 1,
    name: '超级管理员',
    description: '拥有系统所有权限',
    permissions: ['*'],
    user_count: 2,
  },
  {
    id: 2,
    name: '管理员',
    description: '管理用户和基础数据',
    permissions: ['user.manage', 'data.manage'],
    user_count: 5,
  },
  {
    id: 3,
    name: '数据分析师',
    description: '管理数据和运行实验',
    permissions: ['data.view', 'data.create', 'algorithm.run'],
    user_count: 15,
  },
  {
    id: 4,
    name: '普通用户',
    description: '查看和使用基本功能',
    permissions: ['data.view', 'model.view'],
    user_count: 50,
  },
];

export default function SettingsPage() {
  const [generalForm] = Form.useForm();
  const [securityForm] = Form.useForm();
  const [storageForm] = Form.useForm();
  const [emailForm] = Form.useForm();
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [roleForm] = Form.useForm();
  const [editingRole, setEditingRole] = useState<UserRole | null>(null);
  const queryClient = useQueryClient();

  // 模拟API调用
  const { data: systemConfig } = useQuery({
    queryKey: ['systemConfig'],
    queryFn: () => Promise.resolve(mockSystemConfig),
  });

  const { data: roles } = useQuery({
    queryKey: ['roles'],
    queryFn: () => Promise.resolve(mockRoles),
  });

  const updateConfigMutation = useMutation({
    mutationFn: (config: Partial<SystemConfig>) => {
      // 模拟API调用
      return new Promise((resolve) => {
        setTimeout(() => resolve(config), 1000);
      });
    },
    onSuccess: () => {
      message.success('配置更新成功');
      queryClient.invalidateQueries({ queryKey: ['systemConfig'] });
    },
    onError: () => {
      message.error('配置更新失败');
    },
  });

  const saveRoleMutation = useMutation({
    mutationFn: (role: Partial<UserRole>) => {
      // 模拟API调用
      return new Promise((resolve) => {
        setTimeout(() => resolve(role), 1000);
      });
    },
    onSuccess: () => {
      message.success('角色保存成功');
      setRoleModalVisible(false);
      setEditingRole(null);
      roleForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
    onError: () => {
      message.error('角色保存失败');
    },
  });

  const handleSaveGeneral = (values: any) => {
    updateConfigMutation.mutate(values);
  };

  const handleSaveSecurity = (values: any) => {
    updateConfigMutation.mutate(values);
  };

  const handleSaveStorage = (values: any) => {
    updateConfigMutation.mutate({
      storage_provider: values.provider,
      storage_config: values.config,
    });
  };

  const handleSaveEmail = (values: any) => {
    updateConfigMutation.mutate({
      email_config: values,
    });
  };

  const handleSaveRole = (values: any) => {
    saveRoleMutation.mutate(values);
  };

  const showRoleModal = (role?: UserRole) => {
    setEditingRole(role || null);
    setRoleModalVisible(true);
    if (role) {
      roleForm.setFieldsValue(role);
    } else {
      roleForm.resetFields();
    }
  };

  const roleColumns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: UserRole) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.description}
          </Text>
        </div>
      ),
    },
    {
      title: '权限',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => (
        <div>
          {permissions.slice(0, 3).map((perm) => (
            <Tag key={perm} style={{ marginBottom: '4px' }}>
              {perm}
            </Tag>
          ))}
          {permissions.length > 3 && (
            <Tag>+{permissions.length - 3}</Tag>
          )}
        </div>
      ),
    },
    {
      title: '用户数量',
      dataIndex: 'user_count',
      key: 'user_count',
      width: 100,
      render: (count: number) => (
        <span style={{ fontWeight: 'bold' }}>{count}</span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: UserRole) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              size="small"
              onClick={() => showRoleModal(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              icon={<DeleteOutlined />}
              size="small"
              danger
              disabled={record.user_count > 0}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>系统设置</Title>
        <Text type="secondary">管理系统配置和权限设置</Text>
      </div>

      <Row gutter={24}>
        {/* 常规设置 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <SettingOutlined />
                常规设置
              </Space>
            }
            extra={
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={() => generalForm.submit()}
                loading={updateConfigMutation.isPending}
              >
                保存
              </Button>
            }
            style={{ marginBottom: '24px' }}
          >
            <Form
              form={generalForm}
              layout="vertical"
              initialValues={systemConfig}
              onFinish={handleSaveGeneral}
            >
              <Form.Item
                label="应用名称"
                name="app_name"
                rules={[{ required: true, message: '请输入应用名称' }]}
              >
                <Input />
              </Form.Item>

              <Form.Item
                label="应用版本"
                name="app_version"
                rules={[{ required: true, message: '请输入应用版本' }]}
              >
                <Input />
              </Form.Item>

              <Form.Item
                label="默认语言"
                name="default_language"
              >
                <Select>
                  <Option value="zh-CN">简体中文</Option>
                  <Option value="en-US">English</Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="时区"
                name="timezone"
              >
                <Select>
                  <Option value="Asia/Shanghai">Asia/Shanghai</Option>
                  <Option value="UTC">UTC</Option>
                  <Option value="America/New_York">America/New_York</Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="允许用户注册"
                name="enable_registration"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="启用邮件通知"
                name="enable_email_notification"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* 安全设置 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <SecurityScanOutlined />
                安全设置
              </Space>
            }
            extra={
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={() => securityForm.submit()}
                loading={updateConfigMutation.isPending}
              >
                保存
              </Button>
            }
            style={{ marginBottom: '24px' }}
          >
            <Form
              form={securityForm}
              layout="vertical"
              initialValues={systemConfig}
              onFinish={handleSaveSecurity}
            >
              <Form.Item
                label="最大上传文件大小 (MB)"
                name="max_upload_size"
                rules={[{ required: true, message: '请输入最大上传文件大小' }]}
              >
                <InputNumber min={1} max={1000} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="会话超时时间 (小时)"
                name="session_timeout"
                rules={[{ required: true, message: '请输入会话超时时间' }]}
              >
                <InputNumber min={1} max={72} style={{ width: '100%' }} />
              </Form.Item>

              <Divider orientation="left" orientationMargin="0">
                <Text type="secondary">密码策略</Text>
              </Divider>

              <Form.Item
                label="最小密码长度"
                name="min_password_length"
                initialValue={8}
              >
                <InputNumber min={6} max={32} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="要求包含数字"
                name="require_numbers"
                valuePropName="checked"
                initialValue={true}
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="要求包含特殊字符"
                name="require_special_chars"
                valuePropName="checked"
                initialValue={false}
              >
                <Switch />
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>

      {/* 存储设置 */}
      <Card
        title={
          <Space>
            <DatabaseOutlined />
            存储设置
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={() => storageForm.submit()}
            loading={updateConfigMutation.isPending}
          >
            保存
          </Button>
        }
        style={{ marginBottom: '24px' }}
      >
        <Form
          form={storageForm}
          layout="vertical"
          initialValues={{
            provider: systemConfig?.storage_provider,
            config: systemConfig?.storage_config,
          }}
          onFinish={handleSaveStorage}
        >
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="存储提供商"
                name="provider"
                rules={[{ required: true, message: '请选择存储提供商' }]}
              >
                <Select>
                  <Option value="local">本地存储</Option>
                  <Option value="s3">Amazon S3</Option>
                  <Option value="oss">阿里云OSS</Option>
                  <Option value="minio">MinIO</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item
                label="存储路径"
                name={['config', 'path']}
                rules={[{ required: true, message: '请输入存储路径' }]}
              >
                <Input placeholder="/uploads" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {/* 角色权限管理 */}
      <Card
        title={
          <Space>
            <UserOutlined />
            角色权限管理
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => showRoleModal()}
          >
            新建角色
          </Button>
        }
      >
        <Table
          columns={roleColumns}
          dataSource={roles}
          rowKey="id"
          pagination={false}
        />
      </Card>

      {/* 角色编辑对话框 */}
      <Modal
        title={editingRole ? '编辑角色' : '新建角色'}
        open={roleModalVisible}
        onCancel={() => setRoleModalVisible(false)}
        onOk={() => roleForm.submit()}
        confirmLoading={saveRoleMutation.isPending}
        width={600}
      >
        <Form
          form={roleForm}
          layout="vertical"
          onFinish={handleSaveRole}
        >
          <Form.Item
            label="角色名称"
            name="name"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="角色描述"
            name="description"
            rules={[{ required: true, message: '请输入角色描述' }]}
          >
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item
            label="权限"
            name="permissions"
            rules={[{ required: true, message: '请选择权限' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择权限"
              options={[
                { label: '用户管理', value: 'user.manage' },
                { label: '数据查看', value: 'data.view' },
                { label: '数据创建', value: 'data.create' },
                { label: '数据管理', value: 'data.manage' },
                { label: '算法运行', value: 'algorithm.run' },
                { label: '模型查看', value: 'model.view' },
                { label: '模型部署', value: 'model.deploy' },
                { label: '服务管理', value: 'service.manage' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
