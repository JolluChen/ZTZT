'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Progress,
  Typography,
  Alert,
  Statistic,
  Table,
  Tag,
  Space,
  Button,
  Tooltip,
} from 'antd';
import {
  ThunderboltOutlined,
  WarningOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { formatNumber } from '@/utils';

const { Title, Text } = Typography;

interface GPUInfo {
  id: number;
  name: string;
  memory_total: number;
  memory_used: number;
  memory_free: number;
  utilization: number;
  temperature: number;
  power_draw: number;
  power_limit: number;
  fan_speed: number;
  driver_version: string;
  cuda_version: string;
}

interface GPUMetrics {
  timestamp: string;
  gpu_id: number;
  utilization: number;
  memory_used: number;
  temperature: number;
  power_draw: number;
}

const GPUMonitor: React.FC = () => {
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5秒刷新
  const [selectedGPU, setSelectedGPU] = useState<number | null>(null);

  // 获取 GPU 基本信息
  const { data: gpuInfo, refetch: refetchGPUInfo } = useQuery({
    queryKey: ['gpuInfo'],
    queryFn: async () => {
      // 模拟 GPU 信息获取
      const mockGPUs: GPUInfo[] = [
        {
          id: 0,
          name: 'NVIDIA RTX 2080Ti',
          memory_total: 11264,
          memory_used: 8500,
          memory_free: 2764,
          utilization: 85,
          temperature: 72,
          power_draw: 250,
          power_limit: 320,
          fan_speed: 65,
          driver_version: '535.86',
          cuda_version: '12.3',
        },
        {
          id: 1,
          name: 'NVIDIA RTX 2080Ti',
          memory_total: 11264,
          memory_used: 6200,
          memory_free: 5064,
          utilization: 45,
          temperature: 68,
          power_draw: 180,
          power_limit: 320,
          fan_speed: 55,
          driver_version: '535.86',
          cuda_version: '12.3',
        },
      ];
      return mockGPUs;
    },
    refetchInterval: refreshInterval,
  });

  // 获取 GPU 历史指标
  const { data: gpuMetrics } = useQuery({
    queryKey: ['gpuMetrics', selectedGPU],
    queryFn: async () => {
      // 模拟历史数据
      const mockMetrics: GPUMetrics[] = [];
      const now = Date.now();
      for (let i = 29; i >= 0; i--) {
        mockMetrics.push({
          timestamp: new Date(now - i * 60000).toISOString(),
          gpu_id: selectedGPU || 0,
          utilization: Math.random() * 100,
          memory_used: Math.random() * 11264,
          temperature: 60 + Math.random() * 20,
          power_draw: 150 + Math.random() * 200,
        });
      }
      return mockMetrics;
    },
    enabled: selectedGPU !== null,
  });

  const formatBytes = (bytes: number) => {
    return `${(bytes / 1024).toFixed(1)} GB`;
  };

  const getUtilizationColor = (utilization: number) => {
    if (utilization > 90) return '#ff4d4f';
    if (utilization > 70) return '#faad14';
    return '#52c41a';
  };

  const getTemperatureColor = (temp: number) => {
    if (temp > 80) return '#ff4d4f';
    if (temp > 70) return '#faad14';
    return '#52c41a';
  };

  const columns = [
    {
      title: 'GPU ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      render: (id: number) => (
        <Tag color="blue">GPU {id}</Tag>
      ),
    },
    {
      title: '设备名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '使用率',
      dataIndex: 'utilization',
      key: 'utilization',
      width: 120,
      render: (utilization: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Progress
            percent={utilization}
            size="small"
            strokeColor={getUtilizationColor(utilization)}
            showInfo={false}
          />
          <Text style={{ fontSize: 12, minWidth: 35 }}>
            {utilization}%
          </Text>
        </div>
      ),
    },
    {
      title: '显存使用',
      key: 'memory',
      width: 160,
      render: (_: any, record: GPUInfo) => {
        const memoryPercent = (record.memory_used / record.memory_total) * 100;
        return (
          <div>
            <Progress
              percent={memoryPercent}
              size="small"
              strokeColor={memoryPercent > 90 ? '#ff4d4f' : '#1890ff'}
              showInfo={false}
            />
            <Text style={{ fontSize: 12 }}>
              {formatBytes(record.memory_used)} / {formatBytes(record.memory_total)}
            </Text>
          </div>
        );
      },
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      key: 'temperature',
      width: 80,
      render: (temp: number) => (
        <Tag color={getTemperatureColor(temp)}>
          {temp}°C
        </Tag>
      ),
    },
    {
      title: '功耗',
      key: 'power',
      width: 100,
      render: (_: any, record: GPUInfo) => (
        <Text style={{ fontSize: 12 }}>
          {record.power_draw}W / {record.power_limit}W
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: any, record: GPUInfo) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => setSelectedGPU(record.id)}
        >
          详情
        </Button>
      ),
    },
  ];

  const hasGPUs = gpuInfo && gpuInfo.length > 0;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <ThunderboltOutlined />
          GPU 监控
        </Title>
        <Button icon={<ReloadOutlined />} onClick={() => refetchGPUInfo()}>
          刷新
        </Button>
      </div>

      {!hasGPUs && (
        <Alert
          message="未检测到 GPU 设备"
          description="请确保已安装 NVIDIA 驱动和 Docker GPU 支持，并启用了 DCGM Exporter"
          type="warning"
          icon={<WarningOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

      {hasGPUs && (
        <>
          {/* GPU 概览卡片 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="GPU 总数"
                  value={gpuInfo.length}
                  prefix={<ThunderboltOutlined />}
                  suffix="块"
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="平均使用率"
                  value={gpuInfo.reduce((sum, gpu) => sum + gpu.utilization, 0) / gpuInfo.length}
                  precision={1}
                  suffix="%"
                  valueStyle={{
                    color: gpuInfo.some(gpu => gpu.utilization > 90) ? '#cf1322' : '#3f8600',
                  }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="总显存"
                  value={gpuInfo.reduce((sum, gpu) => sum + gpu.memory_total, 0) / 1024}
                  precision={1}
                  suffix="GB"
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="已用显存"
                  value={gpuInfo.reduce((sum, gpu) => sum + gpu.memory_used, 0) / 1024}
                  precision={1}
                  suffix="GB"
                  valueStyle={{
                    color: gpuInfo.some(gpu => (gpu.memory_used / gpu.memory_total) > 0.9) ? '#cf1322' : '#3f8600',
                  }}
                />
              </Card>
            </Col>
          </Row>

          {/* GPU 详细列表 */}
          <Card title="GPU 设备列表" style={{ marginBottom: 24 }}>
            <Table
              columns={columns}
              dataSource={gpuInfo}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>

          {/* GPU 历史趋势 */}
          {selectedGPU !== null && gpuMetrics && (
            <Card title={`GPU ${selectedGPU} 历史趋势`}>
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="使用率趋势" size="small">
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={gpuMetrics}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="timestamp"
                          tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                        />
                        <YAxis domain={[0, 100]} />
                        <RechartsTooltip 
                          labelFormatter={(value) => new Date(value).toLocaleString()}
                          formatter={(value: number) => [`${value.toFixed(1)}%`, '使用率']}
                        />
                        <Line
                          type="monotone"
                          dataKey="utilization"
                          stroke="#1890ff"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="温度趋势" size="small">
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={gpuMetrics}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="timestamp"
                          tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                        />
                        <YAxis domain={[40, 100]} />
                        <RechartsTooltip 
                          labelFormatter={(value) => new Date(value).toLocaleString()}
                          formatter={(value: number) => [`${value.toFixed(1)}°C`, '温度']}
                        />
                        <Line
                          type="monotone"
                          dataKey="temperature"
                          stroke="#faad14"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
              </Row>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default GPUMonitor;
