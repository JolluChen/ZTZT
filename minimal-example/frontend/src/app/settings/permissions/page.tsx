'use client';

import React, { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Typography,
  Row,
  Col,
  Divider,
  Switch,
  Tree,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  TeamOutlined,
  SecurityScanOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import MainLayout from '@/components/layout/MainLayout';
import PermissionGuard from '@/components/common/PermissionGuard';
import { formatDateTime } from '@/utils';

const { Title, Text } = Typography;
const { Option } = Select;

// 模拟权限数据
const mockPermissions = [
  {
    key: 'dataset_read',
    title: '数据集查看',
    description: '查看数据集列表和详情',
    category: 'data',
  },
  {
    key: 'dataset_write',
    title: '数据集管理',
    description: '创建、编辑、删除数据集',
    category: 'data',
  },
  {
    key: 'model_read',
    title: '模型查看',
    description: '查看模型列表和详情',
    category: 'model',
  },
  {
    key: 'model_deploy',
    title: '模型部署',
    description: '部署和管理模型服务',
    category: 'model',
  },
  {
    key: 'user_manage',
    title: '用户管理',
    description: '管理系统用户和权限',
    category: 'admin',
  },
];

const mockRoles = [
  {
    id: 1,
    name: '数据分析师',
    description: '负责数据分析和模型训练',
    permissions: ['dataset_read', 'dataset_write', 'model_read'],
    userCount: 12,
    createdAt: '2024-01-15T10:30:00Z',
  },
  {
    id: 2,
    name: '模型工程师',
    description: '负责模型部署和运维',
    permissions: ['model_read', 'model_deploy'],
    userCount: 8,
    createdAt: '2024-01-20T14:20:00Z',
  },
  {
    id: 3,
    name: '系统管理员',
    description: '系统管理和用户权限管理',
    permissions: ['dataset_read', 'dataset_write', 'model_read', 'model_deploy', 'user_manage'],
    userCount: 3,
    createdAt: '2024-01-10T09:00:00Z',
  },
];

export default function PermissionsPage() {
  const [activeTab, setActiveTab] = useState('roles');
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [selectedRole, setSelectedRole] = useState<any>(null);
  const [form] = Form.useForm();

  const handleCreateRole = async (values: any) => {
    console.log('创建角色:', values);
    message.success('角色创建成功');
    setRoleModalVisible(false);
    form.resetFields();
  };

  const handleEditRole = (role: any) => {
    setSelectedRole(role);
    form.setFieldsValue(role);
    setRoleModalVisible(true);
  };

  const handleDeleteRole = (roleId: number) => {
    console.log('删除角色:', roleId);
    message.success('角色删除成功');
  };

  const roleColumns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '权限数量',
      dataIndex: 'permissions',
      key: 'permissionCount',
      width: 120,
      render: (permissions: string[]) => (
        <Tag color="blue">{permissions.length}个权限</Tag>
      ),
    },
    {
      title: '用户数量',
      dataIndex: 'userCount',
      key: 'userCount',
      width: 100,
      render: (count: number) => (
        <Space>
          <UserOutlined />
          {count}
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 180,
      render: (time: string) => formatDateTime(time),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: any, record: any) => (
        <Space>
          <PermissionGuard permissions={['user_manage']}>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditRole(record)}
            >
              编辑
            </Button>
          </PermissionGuard>
          
          <PermissionGuard permissions={['user_manage']}>
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteRole(record.id)}
            >
              删除
            </Button>
          </PermissionGuard>
        </Space>
      ),
    },
  ];

  const permissionTreeData = [
    {
      title: '数据管理',
      key: 'data',
      children: mockPermissions
        .filter(p => p.category === 'data')
        .map(p => ({
          title: p.title,
          key: p.key,
        })),
    },
    {
      title: '模型管理',
      key: 'model',
      children: mockPermissions
        .filter(p => p.category === 'model')
        .map(p => ({
          title: p.title,
          key: p.key,
        })),
    },
    {
      title: '系统管理',
      key: 'admin',
      children: mockPermissions
        .filter(p => p.category === 'admin')
        .map(p => ({
          title: p.title,
          key: p.key,
        })),
    },
  ];

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        <div style={{ marginBottom: '24px' }}>
          <Title level={2}>权限管理</Title>
          <Text type="secondary">管理系统角色和权限设置</Text>
        </div>

        {/* 权限示例演示 */}
        <Card title="权限控制演示" style={{ marginBottom: '24px' }}>
          <Space wrap size="middle">
            <PermissionGuard permissions={['dataset_read']}>
              <Button type="primary" icon={<UserOutlined />}>
                数据查看权限按钮
              </Button>
            </PermissionGuard>

            <PermissionGuard permissions={['dataset_write']}>
              <Button type="default" icon={<EditOutlined />}>
                数据编辑权限按钮
              </Button>
            </PermissionGuard>

            <PermissionGuard permissions={['model_deploy']}>
              <Button type="default" icon={<SettingOutlined />}>
                模型部署权限按钮
              </Button>
            </PermissionGuard>

            <PermissionGuard permissions={['user_manage']}>
              <Button danger icon={<SecurityScanOutlined />}>
                管理员权限按钮
              </Button>
            </PermissionGuard>

            <PermissionGuard 
              permissions={['dataset_read', 'model_read']}
              requireAll={true}
            >
              <Button type="dashed">
                需要多个权限的按钮
              </Button>
            </PermissionGuard>
          </Space>
          
          <Divider />
          
          <Text type="secondary">
            上述按钮会根据用户权限动态显示/隐藏。当前演示中默认拥有 dataset_read 和 model_read 权限。
          </Text>
        </Card>

        {/* 角色管理 */}
        <Card>
          <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
            <div>
              <Title level={4}>角色列表</Title>
              <Text type="secondary">管理系统角色和对应的权限</Text>
            </div>
            <PermissionGuard permissions={['user_manage']}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setSelectedRole(null);
                  form.resetFields();
                  setRoleModalVisible(true);
                }}
              >
                新建角色
              </Button>
            </PermissionGuard>
          </div>

          <Table
            columns={roleColumns}
            dataSource={mockRoles}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
          />
        </Card>

        {/* 角色编辑模态框 */}
        <Modal
          title={selectedRole ? '编辑角色' : '新建角色'}
          open={roleModalVisible}
          onCancel={() => {
            setRoleModalVisible(false);
            setSelectedRole(null);
            form.resetFields();
          }}
          onOk={() => form.submit()}
          width={600}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleCreateRole}
          >
            <Form.Item
              label="角色名称"
              name="name"
              rules={[{ required: true, message: '请输入角色名称' }]}
            >
              <Input placeholder="请输入角色名称" />
            </Form.Item>

            <Form.Item
              label="角色描述"
              name="description"
              rules={[{ required: true, message: '请输入角色描述' }]}
            >
              <Input.TextArea
                rows={3}
                placeholder="请输入角色描述"
              />
            </Form.Item>

            <Form.Item
              label="权限设置"
              name="permissions"
              rules={[{ required: true, message: '请选择权限' }]}
            >
              <Tree
                checkable
                treeData={permissionTreeData}
                defaultExpandAll
              />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </MainLayout>
  );
}
