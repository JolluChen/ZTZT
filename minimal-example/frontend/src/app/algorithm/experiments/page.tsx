'use client';

import React, { useState } from 'react';
import { 
  Table, 
  Card, 
  Button, 
  Space, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  Select, 
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Progress,
  Drawer,
  Descriptions,
} from 'antd';
import {
  PlusOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import MainLayout from '@/components/layout/MainLayout';
import { algorithmService, dataService } from '@/services';
import { Experiment, ExperimentCreateRequest } from '@/types';
import { STATUS_LABELS, TABLE_CONFIG, ALGORITHMS } from '@/constants';
import { formatDateTime, extractErrorMessage } from '@/utils';

const { TextArea } = Input;
const { Option } = Select;

const ExperimentManagePage: React.FC = () => {
  const [isCreateModalVisible, setIsCreateModalVisible] = useState(false);
  const [isResultDrawerVisible, setIsResultDrawerVisible] = useState(false);
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment | null>(null);
  const [createForm] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取实验列表
  const { data: experimentsData, isLoading } = useQuery({
    queryKey: ['experiments'],
    queryFn: () => algorithmService.getExperiments(),
  });

  // 获取数据集列表
  const { data: datasetsData } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => dataService.getDatasets(),
  });

  // 创建实验
  const createMutation = useMutation({
    mutationFn: (data: ExperimentCreateRequest) => algorithmService.createExperiment(data),
    onSuccess: () => {
      message.success('实验创建成功！');
      setIsCreateModalVisible(false);
      createForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
    },
    onError: (error) => {
      message.error(extractErrorMessage(error));
    },
  });

  // 运行实验
  const runMutation = useMutation({
    mutationFn: (id: number) => algorithmService.runExperiment(id),
    onSuccess: () => {
      message.success('实验已开始运行！');
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
    },
    onError: (error) => {
      message.error(extractErrorMessage(error));
    },
  });

  const handleCreate = (values: any) => {
    createMutation.mutate(values);
  };

  const handleRun = (id: number) => {
    runMutation.mutate(id);
  };

  const showResults = async (experiment: Experiment) => {
    setSelectedExperiment(experiment);
    setIsResultDrawerVisible(true);
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '实验名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <Space>
          <ExperimentOutlined />
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '算法',
      dataIndex: 'algorithm',
      key: 'algorithm',
      width: 150,
      render: (algorithm: string) => {
        const algoConfig = ALGORITHMS.find(a => a.value === algorithm);
        return algoConfig?.label || algorithm;
      },
    },
    {
      title: '数据集',
      dataIndex: 'dataset',
      key: 'dataset',
      width: 120,
      render: (datasetId: number) => {
        const dataset = datasetsData?.results?.find(d => d.id === datasetId);
        return dataset?.name || `数据集 ${datasetId}`;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = STATUS_LABELS[status];
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => formatDateTime(date),
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_: any, record: Experiment) => (
        <Space>
          {record.status === 'created' && (
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleRun(record.id)}
              loading={runMutation.isPending}
            >
              运行
            </Button>
          )}
          {record.status === 'completed' && (
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => showResults(record)}
            >
              查看结果
            </Button>
          )}
          <Popconfirm
            title="确定要删除这个实验吗？"
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const getStatusStats = () => {
    const experiments = experimentsData?.results || [];
    return {
      total: experiments.length,
      running: experiments.filter(e => e.status === 'running').length,
      completed: experiments.filter(e => e.status === 'completed').length,
      failed: experiments.filter(e => e.status === 'failed').length,
    };
  };

  const stats = getStatusStats();

  return (
    <MainLayout>
      <div>
        {/* 头部统计 */}
        <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="实验总数"
                value={stats.total}
                prefix={<ExperimentOutlined style={{ color: '#1890ff' }} />}
                suffix="个"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="运行中"
                value={stats.running}
                prefix={<RocketOutlined style={{ color: '#faad14' }} />}
                suffix="个"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="已完成"
                value={stats.completed}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                suffix="个"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="成功率"
                value={stats.total > 0 ? ((stats.completed / stats.total) * 100).toFixed(1) : 0}
                prefix={<ClockCircleOutlined style={{ color: '#722ed1' }} />}
                suffix="%"
              />
            </Card>
          </Col>
        </Row>

        {/* 实验列表 */}
        <Card
          title="实验管理"
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsCreateModalVisible(true)}
            >
              创建实验
            </Button>
          }
        >
          <Table
            columns={columns}
            dataSource={experimentsData?.results || []}
            rowKey="id"
            loading={isLoading}
            {...TABLE_CONFIG}
          />
        </Card>

        {/* 创建实验模态框 */}
        <Modal
          title="创建实验"
          open={isCreateModalVisible}
          onCancel={() => {
            setIsCreateModalVisible(false);
            createForm.resetFields();
          }}
          footer={null}
          width={600}
        >
          <Form
            form={createForm}
            layout="vertical"
            onFinish={handleCreate}
          >
            <Form.Item
              name="name"
              label="实验名称"
              rules={[
                { required: true, message: '请输入实验名称' },
                { max: 100, message: '名称不能超过100个字符' },
              ]}
            >
              <Input placeholder="请输入实验名称" />
            </Form.Item>

            <Form.Item
              name="description"
              label="实验描述"
              rules={[
                { required: true, message: '请输入实验描述' },
                { max: 500, message: '描述不能超过500个字符' },
              ]}
            >
              <TextArea
                rows={4}
                placeholder="请描述实验的目标、方法等信息"
              />
            </Form.Item>

            <Form.Item
              name="algorithm"
              label="选择算法"
              rules={[{ required: true, message: '请选择算法' }]}
            >
              <Select placeholder="请选择算法">
                {ALGORITHMS.map(algo => (
                  <Option key={algo.value} value={algo.value}>
                    {algo.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="dataset"
              label="选择数据集"
              rules={[{ required: true, message: '请选择数据集' }]}
            >
              <Select placeholder="请选择数据集">
                {datasetsData?.results?.map(dataset => (
                  <Option key={dataset.id} value={dataset.id}>
                    {dataset.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={createMutation.isPending}
                >
                  创建实验
                </Button>
                <Button
                  onClick={() => {
                    setIsCreateModalVisible(false);
                    createForm.resetFields();
                  }}
                >
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>

        {/* 实验结果抽屉 */}
        <Drawer
          title="实验结果"
          placement="right"
          onClose={() => setIsResultDrawerVisible(false)}
          open={isResultDrawerVisible}
          width={600}
        >
          {selectedExperiment && (
            <div>
              <Descriptions column={1} bordered>
                <Descriptions.Item label="实验名称">
                  {selectedExperiment.name}
                </Descriptions.Item>
                <Descriptions.Item label="算法">
                  {ALGORITHMS.find(a => a.value === selectedExperiment.algorithm)?.label}
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={STATUS_LABELS[selectedExperiment.status].color}>
                    {STATUS_LABELS[selectedExperiment.status].text}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {formatDateTime(selectedExperiment.created_at)}
                </Descriptions.Item>
                <Descriptions.Item label="更新时间">
                  {formatDateTime(selectedExperiment.updated_at)}
                </Descriptions.Item>
              </Descriptions>

              {selectedExperiment.results && (
                <Card title="实验结果" style={{ marginTop: 16 }}>
                  <pre style={{ 
                    whiteSpace: 'pre-wrap', 
                    background: '#f6f8fa', 
                    padding: 16, 
                    borderRadius: 6,
                    fontSize: 12,
                  }}>
                    {JSON.stringify(selectedExperiment.results, null, 2)}
                  </pre>
                </Card>
              )}
            </div>
          )}
        </Drawer>
      </div>
    </MainLayout>
  );
};

export default ExperimentManagePage;
