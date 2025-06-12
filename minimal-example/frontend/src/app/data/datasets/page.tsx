'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Button, 
  Space, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  Upload, 
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  UploadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  DatabaseOutlined,
  FileOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import MainLayout from '@/components/layout/MainLayout';
import DataPreview from '@/components/data/DataPreview';
import { dataService } from '@/services';
import { Dataset, DatasetCreateRequest } from '@/types';
import { STATUS_LABELS, TABLE_CONFIG } from '@/constants';
import { formatDateTime, formatFileSize, extractErrorMessage } from '@/utils';

const { TextArea } = Input;

const DatasetManagePage: React.FC = () => {
  const [isUploadModalVisible, setIsUploadModalVisible] = useState(false);
  const [isPreviewModalVisible, setIsPreviewModalVisible] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [uploadForm] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取数据集列表
  const { data: datasetsData, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => dataService.getDatasets(),
  });

  // 获取统计数据
  const { data: statsData } = useQuery({
    queryKey: ['data-stats'],
    queryFn: () => dataService.getDataStats(),
  });

  // 上传数据集
  const uploadMutation = useMutation({
    mutationFn: (data: DatasetCreateRequest) => dataService.createDataset(data),
    onSuccess: () => {
      message.success('数据集上传成功！');
      setIsUploadModalVisible(false);
      uploadForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
    onError: (error) => {
      message.error(extractErrorMessage(error));
    },
  });

  // 删除数据集
  const deleteMutation = useMutation({
    mutationFn: (id: number) => dataService.deleteDataset(id),
    onSuccess: () => {
      message.success('数据集删除成功！');
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
    onError: (error) => {
      message.error(extractErrorMessage(error));
    },
  });

  const handleUpload = (values: any) => {
    const { file, name, description } = values;
    
    if (!file || !file.originFileObj) {
      message.error('请选择要上传的文件');
      return;
    }

    uploadMutation.mutate({
      name,
      description,
      file: file.originFileObj,
    });
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '数据集名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Dataset) => (
        <Space>
          <FileOutlined />
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 120,
      render: (size: number) => formatFileSize(size),
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
      width: 200,
      render: (_: unknown, record: Dataset) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedDataset(record);
              setIsPreviewModalVisible(true);
            }}
          >
            预览
          </Button>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => {/* 下载数据集 */}}
          >
            下载
          </Button>
          <Popconfirm
            title="确定要删除这个数据集吗？"
            onConfirm={() => handleDelete(record.id)}
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

  return (
    <MainLayout>
      <div>
        {/* 头部统计 */}
        <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="数据集总数"
                value={statsData?.total_datasets || 0}
                prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
                suffix="个"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总存储大小"
                value={statsData?.total_size || 0}
                formatter={(value) => formatFileSize(Number(value))}
                prefix={<CloudUploadOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="今日上传"
                value={statsData?.today_uploads || 0}
                prefix={<UploadOutlined style={{ color: '#faad14' }} />}
                suffix="个"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="处理中"
                value={statsData?.processing || 0}
                prefix={<FileOutlined style={{ color: '#722ed1' }} />}
                suffix="个"
              />
            </Card>
          </Col>
        </Row>

        {/* 数据集列表 */}
        <Card
          title="数据集管理"
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsUploadModalVisible(true)}
            >
              上传数据集
            </Button>
          }
        >
          <Table
            columns={columns}
            dataSource={datasetsData?.results || []}
            rowKey="id"
            loading={isLoading}
            {...TABLE_CONFIG}
          />
        </Card>

        {/* 上传数据集模态框 */}
        <Modal
          title="上传数据集"
          open={isUploadModalVisible}
          onCancel={() => {
            setIsUploadModalVisible(false);
            uploadForm.resetFields();
          }}
          footer={null}
          width={600}
        >
          <Form
            form={uploadForm}
            layout="vertical"
            onFinish={handleUpload}
          >
            <Form.Item
              name="name"
              label="数据集名称"
              rules={[
                { required: true, message: '请输入数据集名称' },
                { max: 100, message: '名称不能超过100个字符' },
              ]}
            >
              <Input placeholder="请输入数据集名称" />
            </Form.Item>

            <Form.Item
              name="description"
              label="描述"
              rules={[
                { required: true, message: '请输入数据集描述' },
                { max: 500, message: '描述不能超过500个字符' },
              ]}
            >
              <TextArea
                rows={4}
                placeholder="请描述数据集的内容、来源、用途等信息"
              />
            </Form.Item>

            <Form.Item
              name="file"
              label="选择文件"
              rules={[{ required: true, message: '请选择要上传的文件' }]}
            >
              <Upload
                beforeUpload={() => false}
                maxCount={1}
                accept=".csv,.xlsx,.json,.txt"
              >
                <Button icon={<UploadOutlined />}>点击选择文件</Button>
              </Upload>
            </Form.Item>

            <div style={{ 
              marginBottom: 16, 
              padding: 12, 
              background: '#f6f8fa', 
              borderRadius: 6,
              fontSize: 12,
              color: '#666',
            }}>
              <div><strong>支持的文件格式：</strong></div>
              <div>• CSV文件 (.csv)</div>
              <div>• Excel文件 (.xlsx)</div>
              <div>• JSON文件 (.json)</div>
              <div>• 文本文件 (.txt)</div>
              <div><strong>文件大小限制：</strong>最大 100MB</div>
            </div>

            <Form.Item style={{ marginBottom: 0 }}>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={uploadMutation.isPending}
                >
                  上传
                </Button>
                <Button
                  onClick={() => {
                    setIsUploadModalVisible(false);
                    uploadForm.resetFields();
                  }}
                >
                  取消
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>

        {/* 数据预览组件 */}
        {selectedDataset && (
          <DataPreview 
            datasetId={selectedDataset.id}
            visible={isPreviewModalVisible}
            onClose={() => {
              setIsPreviewModalVisible(false);
              setSelectedDataset(null);
            }}
          />
        )}
      </div>
    </MainLayout>
  );
};

export default DatasetManagePage;
