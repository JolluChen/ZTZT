'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Space,
  Button,
  Select,
  DatePicker,
  Alert,
  Typography,
  Tabs,
  Progress,
} from 'antd';
import {
  ReloadOutlined,
  DownloadOutlined,
  EyeOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { serviceService } from '@/services';
import { formatDateTime, formatNumber } from '@/utils';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface ApplicationMonitorProps {
  applicationId: number;
}

const ApplicationMonitor: React.FC<ApplicationMonitorProps> = ({ applicationId }) => {
  const [timeRange, setTimeRange] = useState('1h');
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30秒刷新

  // 获取应用状态
  const { data: statusData, refetch: refetchStatus } = useQuery({
    queryKey: ['applicationStatus', applicationId],
    queryFn: () => serviceService.getApplicationStatus(applicationId),
    refetchInterval: refreshInterval,
  });

  // 获取应用日志
  const { data: logsData } = useQuery({
    queryKey: ['applicationLogs', applicationId, timeRange],
    queryFn: () => serviceService.getApplicationLogs(applicationId, { timeRange }),
  });

  // 获取监控指标
  const { data: metricsData } = useQuery({
    queryKey: ['applicationMetrics', applicationId, timeRange],
    queryFn: () => serviceService.getApplicationMetrics(applicationId, { timeRange }),
  });

  const handleRefresh = () => {
    refetchStatus();
  };

  const handleExportLogs = () => {
    // 导出日志逻辑
    console.log('导出日志');
  };

  // 日志列配置
  const logColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (time: string) => formatDateTime(time),
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => {
        const color = {
          ERROR: 'red',
          WARN: 'orange',
          INFO: 'blue',
          DEBUG: 'gray',
        }[level] || 'default';
        return <Tag color={color}>{level}</Tag>;
      },
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 120,
    },
  ];

  // 请求统计列配置
  const requestColumns = [
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      width: 80,
      render: (method: string) => <Tag color="blue">{method}</Tag>,
    },
    {
      title: '请求数',
      dataIndex: 'count',
      key: 'count',
      width: 100,
      render: (count: number) => formatNumber(count),
    },
    {
      title: '平均响应时间',
      dataIndex: 'avg_response_time',
      key: 'avg_response_time',
      width: 120,
      render: (time: number) => `${time.toFixed(2)}ms`,
    },
    {
      title: '错误率',
      dataIndex: 'error_rate',
      key: 'error_rate',
      width: 100,
      render: (rate: number) => {
        const color = rate > 5 ? 'red' : rate > 1 ? 'orange' : 'green';
        return <Tag color={color}>{(rate * 100).toFixed(2)}%</Tag>;
      },
    },
  ];

  const tabItems = [
    {
      key: 'overview',
      label: '概览',
      children: (
        <div>
          {/* 状态卡片 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="服务状态"
                  value={statusData?.status === 'running' ? '运行中' : '已停止'}
                  valueStyle={{
                    color: statusData?.status === 'running' ? '#3f8600' : '#cf1322',
                  }}
                  prefix={
                    statusData?.status === 'running' ? (
                      <CheckCircleOutlined />
                    ) : (
                      <WarningOutlined />
                    )
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="总请求数"
                  value={statusData?.total_requests || 0}
                  formatter={(value) => formatNumber(Number(value))}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="平均响应时间"
                  value={statusData?.avg_response_time || 0}
                  precision={2}
                  suffix="ms"
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="错误率"
                  value={statusData?.error_rate || 0}
                  precision={2}
                  suffix="%"
                  valueStyle={{
                    color: (statusData?.error_rate || 0) > 5 ? '#cf1322' : '#3f8600',
                  }}
                />
              </Card>
            </Col>
          </Row>

          {/* 资源使用情况 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card title="CPU使用率" size="small">
                <Progress
                  percent={statusData?.cpu_usage || 0}
                  status={statusData?.cpu_usage > 80 ? 'exception' : 'success'}
                />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  当前: {statusData?.cpu_usage || 0}% | 平均: {statusData?.avg_cpu_usage || 0}%
                </Text>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="内存使用率" size="small">
                <Progress
                  percent={statusData?.memory_usage || 0}
                  status={statusData?.memory_usage > 80 ? 'exception' : 'success'}
                />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  当前: {statusData?.memory_usage || 0}% | 总量: {statusData?.total_memory || 0}GB
                </Text>
              </Card>
            </Col>
          </Row>

          {/* 性能图表 */}
          <Card title="性能趋势" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metricsData?.performance_trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="response_time"
                  stroke="#1890ff"
                  name="响应时间(ms)"
                />
                <Line
                  type="monotone"
                  dataKey="requests_per_minute"
                  stroke="#52c41a"
                  name="每分钟请求数"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </div>
      ),
    },
    {
      key: 'logs',
      label: '日志',
      children: (
        <div>
          <Space style={{ marginBottom: 16 }}>
            <Select
              value={timeRange}
              onChange={setTimeRange}
              style={{ width: 120 }}
            >
              <Option value="1h">最近1小时</Option>
              <Option value="6h">最近6小时</Option>
              <Option value="24h">最近24小时</Option>
              <Option value="7d">最近7天</Option>
            </Select>
            <Button icon={<DownloadOutlined />} onClick={handleExportLogs}>
              导出日志
            </Button>
          </Space>

          {logsData?.error_count > 0 && (
            <Alert
              message={`发现 ${logsData.error_count} 条错误日志`}
              type="warning"
              style={{ marginBottom: 16 }}
            />
          )}

          <Table
            columns={logColumns}
            dataSource={logsData?.logs || []}
            pagination={{
              pageSize: 50,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) =>
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
            scroll={{ y: 400 }}
            size="small"
          />
        </div>
      ),
    },
    {
      key: 'requests',
      label: '请求统计',
      children: (
        <div>
          <Card title="API请求统计" size="small">
            <Table
              columns={requestColumns}
              dataSource={metricsData?.request_stats || []}
              pagination={false}
              size="small"
            />
          </Card>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          应用监控
        </Title>
        <Space>
          <Select
            value={refreshInterval}
            onChange={setRefreshInterval}
            style={{ width: 120 }}
          >
            <Option value={10000}>10秒刷新</Option>
            <Option value={30000}>30秒刷新</Option>
            <Option value={60000}>1分钟刷新</Option>
            <Option value={0}>手动刷新</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
        </Space>
      </div>

      <Tabs items={tabItems} />
    </div>
  );
};

export default ApplicationMonitor;
