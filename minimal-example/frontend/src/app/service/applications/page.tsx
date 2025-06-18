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
  Progress,
  Alert,
} from 'antd';
import {
  PlusOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  StopOutlined,
  DeleteOutlined,
  ReloadOutlined,
  MonitorOutlined,
  LinkOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import MainLayout from '@/components/layout/MainLayout';
import ApplicationMonitor from '@/components/service/ApplicationMonitor';
import { serviceService } from '@/services';
import { Application, ApplicationCreateRequest } from '@/types';
import { STATUS_LABELS, TABLE_CONFIG } from '@/constants';
import { formatDate } from '@/utils';

const { Title, Text } = Typography;
const { Option } = Select;

export default function ApplicationsPage() {
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [monitorModalVisible, setMonitorModalVisible] = useState(false);
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [form] = Form.useForm();
  const [configForm] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取应用列表
  const {
    data: appsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['applications'],
    queryFn: () => serviceService.getApplications(),
  });

  // 获取模型列表（用于创建应用时选择）
  const { data: modelsData } = useQuery({
    queryKey: ['models'],
    queryFn: () => serviceService.getModels(),
  });

  // 创建应用
  const createAppMutation = useMutation({
    mutationFn: (data: ApplicationCreateRequest) => serviceService.createApplication(data),
    onSuccess: () => {
      message.success('应用创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '创建失败');
    },
  });

  // 启动应用
  const startAppMutation = useMutation({
    mutationFn: (id: number) => serviceService.startApplication(id),
    onSuccess: () => {
      message.success('应用启动成功');
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '启动失败');
    },
  });

  // 停止应用
  const stopAppMutation = useMutation({
    mutationFn: (id: number) => serviceService.stopApplication(id),
    onSuccess: () => {
      message.success('应用停止成功');
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '停止失败');
    },
  });

  // 删除应用
  const deleteAppMutation = useMutation({
    mutationFn: (id: number) => serviceService.deleteApplication(id),
    onSuccess: () => {
      message.success('应用删除成功');
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '删除失败');
    },
  });

  // 更新应用配置
  const updateConfigMutation = useMutation({
    mutationFn: ({ id, config }: { id: number; config: any }) =>
      serviceService.updateApplicationConfig(id, config),
    onSuccess: () => {
      message.success('配置更新成功');
      setConfigModalVisible(false);
      configForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.message || '更新失败');
    },
  });

  const handleCreateApp = async (values: ApplicationCreateRequest) => {
    createAppMutation.mutate(values);
  };

  const handleUpdateConfig = async (values: any) => {
    if (selectedApp) {
      updateConfigMutation.mutate({
        id: selectedApp.id,
        config: values,
      });
    }
  };

  const showConfigModal = (app: Application) => {
    setSelectedApp(app);
    setConfigModalVisible(true);
    configForm.setFieldsValue(app.config || {});
  };

  const getStatusProgress = (status: string) => {
    switch (status) {
      case 'created':
        return { percent: 0, status: 'normal' as const };
      case 'deploying':
        return { percent: 50, status: 'active' as const };
      case 'running':
        return { percent: 100, status: 'success' as const };
      case 'stopped':
        return { percent: 100, status: 'normal' as const };
      case 'error':
        return { percent: 100, status: 'exception' as const };
      default:
        return { percent: 0, status: 'normal' as const };
    }
  };

  const columns = [
    {
      title: '应用名称',
      dataIndex: 'name',
      key: 'name',
      width: 180,
      render: (text: string, record: Application) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          {record.url && (
            <a
              href={record.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: '12px' }}
            >
              <LinkOutlined /> 访问链接
            </a>
          )}
        </div>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      width: 200,
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
      width: 120,
      render: (modelId: number) => {
        const model = modelsData?.results?.find((m: any) => m.id === modelId);
        return model ? (
          <div>
            <div>{model.name}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              v{model.version}
            </Text>
          </div>
        ) : (
          <Text type="secondary">未知模型</Text>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (status: string) => {
        const config = STATUS_LABELS[status] || { text: status, color: 'default' };
        const progress = getStatusProgress(status);
        
        return (
          <div>
            <Tag color={config.color}>{config.text}</Tag>
            {status === 'deploying' && (
              <Progress
                size="small"
                percent={progress.percent}
                status={progress.status}
                style={{ marginTop: '4px' }}
              />
            )}
          </div>
        );
      },
    },
    {
      title: '资源使用',
      key: 'resources',
      width: 120,
      render: (_: any, record: Application) => {
        const config = record.config || {};
        return (
          <div style={{ fontSize: '12px' }}>
            <div>CPU: {String(config.cpu) || 'N/A'}</div>
            <div>内存: {String(config.memory) || 'N/A'}</div>
            <div>副本: {String(config.replicas) || '1'}</div>
          </div>
        );
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
      width: 250,
      render: (_: any, record: Application) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
            />
          </Tooltip>
          
          <Tooltip title="监控">
            <Button
              type="text"
              icon={<MonitorOutlined />}
              size="small"
              onClick={() => {
                setSelectedApp(record);
                setMonitorModalVisible(true);
              }}
            />
          </Tooltip>

          <Tooltip title="配置">
            <Button
              type="text"
              icon={<SettingOutlined />}
              size="small"
              onClick={() => showConfigModal(record)}
            />
          </Tooltip>

          {record.status === 'stopped' || record.status === 'created' ? (
            <Tooltip title="启动">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                size="small"
                onClick={() => startAppMutation.mutate(record.id)}
                loading={startAppMutation.isPending}
              />
            </Tooltip>
          ) : record.status === 'running' ? (
            <Tooltip title="停止">
              <Button
                type="text"
                icon={<StopOutlined />}
                size="small"
                onClick={() => stopAppMutation.mutate(record.id)}
                loading={stopAppMutation.isPending}
              />
            </Tooltip>
          ) : null}

          <Popconfirm
            title="确定要删除这个应用吗？"
            onConfirm={() => deleteAppMutation.mutate(record.id)}
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
    total: appsData?.results?.length || 0,
    running: appsData?.results?.filter((app: Application) => app.status === 'running').length || 0,
    stopped: appsData?.results?.filter((app: Application) => app.status === 'stopped').length || 0,
    error: appsData?.results?.filter((app: Application) => app.status === 'error').length || 0,
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>应用管理</Title>
        <Text type="secondary">管理和监控AI应用服务</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总应用数"
              value={stats.total}
              prefix={<MonitorOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中"
              value={stats.running}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已停止"
              value={stats.stopped}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="异常"
              value={stats.error}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 资源监控提醒 */}
      {stats.running > 5 && (
        <Alert
          message="资源使用提醒"
          description="当前运行的应用较多，请注意资源使用情况"
          type="warning"
          showIcon
          closable
          style={{ marginBottom: '16px' }}
        />
      )}

      {/* 主要内容 */}
      <Card>
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              创建应用
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
          dataSource={appsData?.results || []}
          rowKey="id"
          loading={isLoading}
          {...TABLE_CONFIG}
        />
      </Card>

      {/* 创建应用对话框 */}
      <Modal
        title="创建应用"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={createAppMutation.isPending}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateApp}
        >
          <Form.Item
            label="应用名称"
            name="name"
            rules={[{ required: true, message: '请输入应用名称' }]}
          >
            <Input placeholder="请输入应用名称" />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
            rules={[{ required: true, message: '请输入应用描述' }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="请输入应用描述"
            />
          </Form.Item>

          <Form.Item
            label="应用类型"
            name="app_type"
            rules={[{ required: true, message: '请选择应用类型' }]}
            initialValue="traditional"
          >
            <Select placeholder="请选择应用类型">
              <Option value="traditional">传统应用</Option>
              <Option value="dify">Dify AI 应用</Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.app_type !== currentValues.app_type
            }
          >
            {({ getFieldValue }) => {
              const appType = getFieldValue('app_type');
              
              if (appType === 'dify') {
                return (
                  <>
                    <Form.Item
                      label="Dify 应用类型"
                      name={['dify_config', 'app_type']}
                      rules={[{ required: true, message: '请选择 Dify 应用类型' }]}
                    >
                      <Select placeholder="请选择 Dify 应用类型">
                        <Option value="chat">对话应用</Option>
                        <Option value="completion">文本生成</Option>
                        <Option value="workflow">工作流</Option>
                        <Option value="agent">智能体</Option>
                      </Select>
                    </Form.Item>

                    <Form.Item
                      label="模式"
                      name={['dify_config', 'mode']}
                      initialValue="simple"
                    >
                      <Select>
                        <Option value="simple">简单模式</Option>
                        <Option value="advanced">高级模式</Option>
                      </Select>
                    </Form.Item>

                    <Form.Item
                      label="Dify API 密钥"
                      name={['dify_config', 'api_key']}
                      rules={[{ required: true, message: '请输入 Dify API 密钥' }]}
                    >
                      <Input.Password placeholder="请输入 Dify API 密钥" />
                    </Form.Item>

                    <Form.Item
                      label="Dify API 地址"
                      name={['dify_config', 'api_url']}
                      initialValue="http://localhost:8001"
                    >
                      <Input placeholder="Dify API 地址" />
                    </Form.Item>
                  </>
                );
              }

              // 传统应用配置
              return (
                <>
                  <Form.Item
                    label="选择模型"
                    name="model"
                    rules={[{ required: true, message: '请选择模型' }]}
                  >
                    <Select
                      placeholder="请选择模型"
                      showSearch
                      filterOption={(input, option) =>
                        ((option?.label as string) || '').toLowerCase().includes(input.toLowerCase())
                      }
                    >
                      {modelsData?.results?.filter((model: any) => model.status === 'ready' || model.status === 'deployed')
                        .map((model: any) => (
                        <Option key={model.id} value={model.id}>
                          {model.name} (v{model.version})
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label="CPU限制"
                        name={['config', 'cpu']}
                        initialValue="500m"
                      >
                        <Select>
                          <Option value="100m">100m</Option>
                          <Option value="250m">250m</Option>
                          <Option value="500m">500m</Option>
                          <Option value="1000m">1000m</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="内存限制"
                        name={['config', 'memory']}
                        initialValue="512Mi"
                      >
                        <Select>
                          <Option value="256Mi">256Mi</Option>
                          <Option value="512Mi">512Mi</Option>
                          <Option value="1Gi">1Gi</Option>
                          <Option value="2Gi">2Gi</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item
                    label="副本数量"
                    name={['config', 'replicas']}
                    initialValue={1}
                  >
                    <Select>
                      <Option value={1}>1个副本</Option>
                      <Option value={2}>2个副本</Option>
                      <Option value={3}>3个副本</Option>
                    </Select>
                  </Form.Item>
                </>
              );
            }}
          </Form.Item>
        </Form>
      </Modal>

      {/* 配置更新对话框 */}
      <Modal
        title={`配置应用：${selectedApp?.name}`}
        open={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        onOk={() => configForm.submit()}
        confirmLoading={updateConfigMutation.isPending}
      >
        <Form
          form={configForm}
          layout="vertical"
          onFinish={handleUpdateConfig}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="CPU限制"
                name="cpu"
              >
                <Select>
                  <Option value="100m">100m</Option>
                  <Option value="250m">250m</Option>
                  <Option value="500m">500m</Option>
                  <Option value="1000m">1000m</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="内存限制"
                name="memory"
              >
                <Select>
                  <Option value="256Mi">256Mi</Option>
                  <Option value="512Mi">512Mi</Option>
                  <Option value="1Gi">1Gi</Option>
                  <Option value="2Gi">2Gi</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="副本数量"
            name="replicas"
          >
            <Select>
              <Option value={1}>1个副本</Option>
              <Option value={2}>2个副本</Option>
              <Option value={3}>3个副本</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="环境变量"
            name="env"
          >
            <Input.TextArea
              rows={4}
              placeholder="KEY1=value1&#10;KEY2=value2"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 应用监控模态框 */}
      <Modal
        title={`应用监控 - ${selectedApp?.name || ''}`}
        open={monitorModalVisible}
        onCancel={() => {
          setMonitorModalVisible(false);
          setSelectedApp(null);
        }}
        footer={null}
        width={1400}
        destroyOnClose
      >
        {selectedApp && (
          <ApplicationMonitor 
            applicationId={selectedApp.id}
          />
        )}
      </Modal>
    </div>
  );
}
