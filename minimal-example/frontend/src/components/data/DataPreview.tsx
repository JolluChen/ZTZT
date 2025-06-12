'use client';

import React, { useState } from 'react';
import { Table, Card, Tabs, Tag, Button, Space, Typography, Spin, message } from 'antd';
import { DownloadOutlined, FileTextOutlined, BarChartOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { dataService } from '@/services';
import { formatFileSize } from '@/utils';

const { Title, Text } = Typography;

interface DataPreviewProps {
  datasetId: number;
  visible: boolean;
  onClose: () => void;
}

const DataPreview: React.FC<DataPreviewProps> = ({ datasetId, visible, onClose }) => {
  const [activeTab, setActiveTab] = useState('preview');

  // 获取数据预览
  const { data: previewData, isLoading } = useQuery({
    queryKey: ['dataPreview', datasetId],
    queryFn: () => dataService.previewDataset(datasetId),
    enabled: visible && !!datasetId,
  });

  // 获取数据统计
  const { data: statsData } = useQuery({
    queryKey: ['dataStats', datasetId],
    queryFn: () => dataService.getDatasetStats(datasetId),
    enabled: visible && !!datasetId,
  });

  const handleDownload = async () => {
    try {
      message.loading('正在下载数据集...', 0);
      await dataService.downloadDataset(datasetId);
      message.destroy();
      message.success('下载成功');
    } catch (error) {
      message.destroy();
      message.error('下载失败');
    }
  };

  const columns = previewData?.columns?.map((col: string, index: number) => ({
    title: col,
    dataIndex: col,
    key: col,
    width: 150,
    ellipsis: true,
    render: (text: unknown) => {
      if (typeof text === 'string' && text.length > 50) {
        return text.substring(0, 50) + '...';
      }
      return String(text);
    },
  })) || [];

  const dataSource = previewData?.data?.map((row: Record<string, unknown>, index: number) => ({
    ...row,
    key: index,
  })) || [];

  const statsColumns = [
    {
      title: '字段名',
      dataIndex: 'column',
      key: 'column',
    },
    {
      title: '数据类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: '非空值数量',
      dataIndex: 'non_null_count',
      key: 'non_null_count',
    },
    {
      title: '缺失值数量',
      dataIndex: 'null_count',
      key: 'null_count',
      render: (count: number) => (
        <Tag color={count > 0 ? 'red' : 'green'}>{count}</Tag>
      ),
    },
    {
      title: '唯一值数量',
      dataIndex: 'unique_count',
      key: 'unique_count',
    },
  ];

  const tabItems = [
    {
      key: 'preview',
      label: (
        <span>
          <FileTextOutlined />
          数据预览
        </span>
      ),
      children: (
        <div>
          <Space style={{ marginBottom: 16 }}>
            <Text strong>
              显示前 {Math.min(previewData?.total || 0, 100)} 行，共 {previewData?.total || 0} 行
            </Text>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleDownload}
            >
              下载完整数据
            </Button>
          </Space>
          <Table
            columns={columns}
            dataSource={dataSource}
            pagination={false}
            scroll={{ x: 'max-content', y: 400 }}
            size="small"
            loading={isLoading}
          />
        </div>
      ),
    },
    {
      key: 'stats',
      label: (
        <span>
          <BarChartOutlined />
          统计信息
        </span>
      ),
      children: (
        <div>
          {statsData && (
            <div style={{ marginBottom: 16 }}>
              <Space direction="vertical" size="small">
                <Text>
                  <strong>总行数：</strong>{statsData.total_rows?.toLocaleString()}
                </Text>
                <Text>
                  <strong>总列数：</strong>{statsData.total_columns}
                </Text>
                <Text>
                  <strong>文件大小：</strong>{formatFileSize(statsData.file_size || 0)}
                </Text>
                <Text>
                  <strong>内存使用：</strong>{formatFileSize(statsData.memory_usage || 0)}
                </Text>
              </Space>
            </div>
          )}
          <Table
            columns={statsColumns}
            dataSource={statsData?.column_stats || []}
            pagination={false}
            size="small"
          />
        </div>
      ),
    },
  ];

  if (!visible) return null;

  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>
            数据预览
          </Title>
          <Button onClick={onClose}>关闭</Button>
        </div>
      }
      style={{ height: '80vh', overflow: 'auto' }}
    >
      <Spin spinning={isLoading}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Spin>
    </Card>
  );
};

export default DataPreview;
