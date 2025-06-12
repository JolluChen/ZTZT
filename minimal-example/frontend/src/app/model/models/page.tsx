'use client';

import React, { useState, useEffect } from 'react';
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
  Tooltip,
  Typography,
  Row,
  Col,
  Statistic,
  Badge,
  Popconfirm,
} from 'antd';
import {
  PlusOutlined,
  EyeOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import MainLayout from '@/components/layout/MainLayout';
import ModelDeploy from '@/components/model/ModelDeploy';
import { modelService } from '@/services';
import { Model, ModelCreateRequest } from '@/types';
import { STATUS_LABELS, TABLE_CONFIG } from '@/constants';
import { formatDate, formatFileSize } from '@/utils';

const { Title, Text } = Typography;
const { Option } = Select;

export default function ModelsPage() {
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [deployModalVisible, setDeployModalVisible] = useState(false);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [form] = Form.useForm();
  const [deployForm] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取模型列表
  const {
    data: modelsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['models'],
    queryFn: () => modelService.getModels(),
  });

  // 获取实验列表（用于创建模型时选择）
  const { data: experimentsData } = useQuery({
    queryKey: ['experiments'],
    queryFn: () => modelService.getExperiments(),
  });

  // 创建模型
  const createModelMutation = useMutation({
    mutationFn: (data: ModelCreateRequest) => modelService.createModel(data),
    onSuccess: () => {
      message.success('模型创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '创建失败');
    },
  });

  // 部署模型
  const deployModelMutation = useMutation({
    mutationFn: ({ id, config }: { id: number; config: any }) =>
      modelService.deployModel(id, config),
    onSuccess: () => {
      message.success('模型部署启动成功');
      setDeployModalVisible(false);
      deployForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '部署失败');
    },
  });

  // 删除模型
  const deleteModelMutation = useMutation({
    mutationFn: (id: number) => modelService.deleteModel(id),
    onSuccess: () => {
      message.success('模型删除成功');
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '删除失败');
    },
  });

  const handleCreateModel = async (values: ModelCreateRequest) => {
    createModelMutation.mutate(values);
  };

  const handleDeployModel = async (values: any) => {
    if (selectedModel) {
      deployModelMutation.mutate({
        id: selectedModel.id,
        config: values,
      });
    }
  };

  const handleDeleteModel = (id: number) => {
    deleteModelMutation.mutate(id);
  };

  const showDeployModal = (model: Model) => {
    setSelectedModel(model);
    setDeployModalVisible(true);
    deployForm.setFieldsValue({
      environment: 'production',
      replicas: 1,
      memory: '512Mi',
      cpu: '500m',
    });
  };

  const columns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: Model) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            v{record.version}
          </Text>
        </div>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      width: 250,
    },
    {
      title: '算法',
      dataIndex: 'algorithm',
      key: 'algorithm',
      width: 120,
      render: (algorithm: string) => (
        <Tag color="blue">{algorithm}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = STATUS_LABELS[status] || { text: status, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '准确率',
      dataIndex: 'metrics',
      key: 'accuracy',
      width: 100,
      render: (metrics: Record<string, any>) => {
        const accuracy = metrics?.accuracy;
        if (accuracy !== undefined) {
          return (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 'bold', color: accuracy > 0.8 ? '#52c41a' : accuracy > 0.6 ? '#faad14' : '#ff4d4f' }}>
                {(accuracy * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '10px', color: '#999' }}>准确率</div>
            </div>
          );
        }
        return '-';
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time: string) => formatDate(time),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: Model) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
            />
          </Tooltip>
          <Tooltip title="查看指标">
            <Button
              type="text"
              icon={<BarChartOutlined />}
              size="small"
            />
          </Tooltip>
          {record.status === 'ready' && (
            <Tooltip title="部署模型">
              <Button
                type="text"
                icon={<CloudUploadOutlined />}
                size="small"
                onClick={() => showDeployModal(record)}
              />
            </Tooltip>
          )}
          <Popconfirm
            title="确定要删除这个模型吗？"
            onConfirm={() => handleDeleteModel(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                icon={<DeleteOutlined />}
                size="small"
                danger
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 统计数据
  const stats = {
    total: modelsData?.results?.length || 0,
    ready: modelsData?.results?.filter((m: Model) => m.status === 'ready').length || 0,
    deployed: modelsData?.results?.filter((m: Model) => m.status === 'deployed').length || 0,
    training: modelsData?.results?.filter((m: Model) => m.status === 'training').length || 0,
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>模型管理</Title>
        <Text type="secondary">管理和部署机器学习模型</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总模型数"
              value={stats.total}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="就绪模型"
              value={stats.ready}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已部署"
              value={stats.deployed}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="训练中"
              value={stats.training}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容 */}
      <Card>
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              创建模型
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              loading={isLoading}
            >
              刷新
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={modelsData?.results || []}
          rowKey="id"
          loading={isLoading}
          {...TABLE_CONFIG}
        />
      </Card>

      {/* 创建模型对话框 */}
      <Modal
        title="创建模型"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={createModelMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateModel}
        >
          <Form.Item
            label="模型名称"
            name="name"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="请输入模型名称" />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
            rules={[{ required: true, message: '请输入模型描述' }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="请输入模型描述"
            />
          </Form.Item>

          <Form.Item
            label="实验"
            name="experiment"
            rules={[{ required: true, message: '请选择实验' }]}
          >
            <Select placeholder="请选择实验">
              {experimentsData?.results?.map((exp: any) => (
                <Option key={exp.id} value={exp.id}>
                  {exp.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="版本号"
            name="version"
          >
            <Input placeholder="如：1.0.0，留空自动生成" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 部署模型对话框 */}
      {selectedModel && (
        <ModelDeploy 
          modelId={selectedModel.id}
          visible={deployModalVisible}
          onClose={() => {
            setDeployModalVisible(false);
            setSelectedModel(null);
          }}
          onSuccess={() => {
            setDeployModalVisible(false);
            setSelectedModel(null);
            queryClient.invalidateQueries({ queryKey: ['models'] });
          }}
        />
      )}
    </div>
  );
}
