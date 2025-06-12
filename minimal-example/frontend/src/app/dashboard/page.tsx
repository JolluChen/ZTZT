'use client';

import React, { useState, useEffect } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Progress, 
  Tag, 
  Space,
  Button,
  List,
  Avatar,
  Divider,
  Typography,
} from 'antd';
import {
  DatabaseOutlined,
  ExperimentOutlined,
  DeploymentUnitOutlined,
  AppstoreOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useAuthStore } from '@/store/authStore';
import { formatDateTime, formatRelativeTime } from '@/utils';
import MainLayout from '@/components/layout/MainLayout';
import GPUMonitor from '@/components/monitoring/GPUMonitor';

const { Title, Text } = Typography;

// 模拟数据
const statsData = {
  datasets: 156,
  experiments: 89,
  models: 34,
  applications: 12,
};

const trendData = [
  { name: '周一', datasets: 12, experiments: 8, models: 3 },
  { name: '周二', datasets: 15, experiments: 10, models: 4 },
  { name: '周三', datasets: 8, experiments: 6, models: 2 },
  { name: '周四', datasets: 20, experiments: 12, models: 5 },
  { name: '周五', datasets: 18, experiments: 15, models: 6 },
  { name: '周六', datasets: 10, experiments: 7, models: 2 },
  { name: '周日', datasets: 14, experiments: 9, models: 4 },
];

const statusData = [
  { name: '运行中', value: 45, color: '#52c41a' },
  { name: '已停止', value: 23, color: '#faad14' },
  { name: '错误', value: 12, color: '#ff4d4f' },
  { name: '部署中', value: 8, color: '#1890ff' },
];

const recentActivities = [
  {
    id: 1,
    type: 'dataset',
    title: '用户数据集已上传',
    description: '客户行为分析数据.csv',
    user: 'admin',
    time: new Date(Date.now() - 5 * 60 * 1000),
    status: 'success',
  },
  {
    id: 2,
    type: 'experiment',
    title: '实验运行完成',
    description: '随机森林分类实验',
    user: 'data_scientist',
    time: new Date(Date.now() - 15 * 60 * 1000),
    status: 'success',
  },
  {
    id: 3,
    type: 'model',
    title: '模型部署失败',
    description: '用户推荐模型 v1.2',
    user: 'ml_engineer',
    time: new Date(Date.now() - 30 * 60 * 1000),
    status: 'error',
  },
  {
    id: 4,
    type: 'application',
    title: '应用创建成功',
    description: '智能客服应用',
    user: 'developer',
    time: new Date(Date.now() - 45 * 60 * 1000),
    status: 'success',
  },
];

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'dataset':
      return <DatabaseOutlined />;
    case 'experiment':
      return <ExperimentOutlined />;
    case 'model':
      return <DeploymentUnitOutlined />;
    case 'application':
      return <AppstoreOutlined />;
    default:
      return <ClockCircleOutlined />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'success':
      return '#52c41a';
    case 'error':
      return '#ff4d4f';
    case 'warning':
      return '#faad14';
    default:
      return '#1890ff';
  }
};

const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 模拟数据加载
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return '上午好';
    if (hour < 18) return '下午好';
    return '晚上好';
  };

  return (
    <MainLayout>
      <div>
        {/* 欢迎区域 */}
        <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Card style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
              <div style={{ color: 'white' }}>
                <Title level={2} style={{ color: 'white', margin: 0 }}>
                  {getGreeting()}，{user?.first_name || user?.username}！
                </Title>
                <Text style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: 16 }}>
                  欢迎回到AI中台管理系统，今天也要加油哦！
                </Text>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 统计卡片 */}
        <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card loading={loading}>
              <Statistic
                title="数据集总数"
                value={statsData.datasets}
                prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
                suffix="个"
              />
              <Progress 
                percent={78} 
                size="small" 
                showInfo={false} 
                strokeColor="#1890ff"
                style={{ marginTop: 8 }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                相比上月增长 12%
              </Text>
            </Card>
          </Col>
          
          <Col xs={24} sm={12} lg={6}>
            <Card loading={loading}>
              <Statistic
                title="实验总数"
                value={statsData.experiments}
                prefix={<ExperimentOutlined style={{ color: '#52c41a' }} />}
                suffix="个"
              />
              <Progress 
                percent={65} 
                size="small" 
                showInfo={false} 
                strokeColor="#52c41a"
                style={{ marginTop: 8 }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                相比上月增长 8%
              </Text>
            </Card>
          </Col>
          
          <Col xs={24} sm={12} lg={6}>
            <Card loading={loading}>
              <Statistic
                title="模型总数"
                value={statsData.models}
                prefix={<DeploymentUnitOutlined style={{ color: '#faad14' }} />}
                suffix="个"
              />
              <Progress 
                percent={45} 
                size="small" 
                showInfo={false} 
                strokeColor="#faad14"
                style={{ marginTop: 8 }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                相比上月增长 15%
              </Text>
            </Card>
          </Col>
          
          <Col xs={24} sm={12} lg={6}>
            <Card loading={loading}>
              <Statistic
                title="应用总数"
                value={statsData.applications}
                prefix={<AppstoreOutlined style={{ color: '#722ed1' }} />}
                suffix="个"
              />
              <Progress 
                percent={30} 
                size="small" 
                showInfo={false} 
                strokeColor="#722ed1"
                style={{ marginTop: 8 }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                相比上月增长 25%
              </Text>
            </Card>
          </Col>
        </Row>

        {/* 图表区域 */}
        <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
          <Col xs={24} lg={16}>
            <Card title="活动趋势" loading={loading}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="datasets" 
                    stroke="#1890ff" 
                    strokeWidth={2}
                    name="数据集"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="experiments" 
                    stroke="#52c41a" 
                    strokeWidth={2}
                    name="实验"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="models" 
                    stroke="#faad14" 
                    strokeWidth={2}
                    name="模型"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
          
          <Col xs={24} lg={8}>
            <Card title="服务状态分布" loading={loading}>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>

        {/* 最近活动 */}
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={16}>
            <Card title="最近活动" loading={loading}>
              <List
                itemLayout="horizontal"
                dataSource={recentActivities}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={
                        <Avatar 
                          icon={getActivityIcon(item.type)} 
                          style={{ backgroundColor: getStatusColor(item.status) }}
                        />
                      }
                      title={
                        <Space>
                          <span>{item.title}</span>
                          <Tag color={getStatusColor(item.status)}>
                            {item.status === 'success' ? '成功' : 
                             item.status === 'error' ? '失败' : '进行中'}
                          </Tag>
                        </Space>
                      }
                      description={
                        <div>
                          <div>{item.description}</div>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {item.user} · {formatRelativeTime(item.time)}
                          </Text>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          
          <Col xs={24} lg={8}>
            <Card title="快速操作" loading={loading}>
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Button type="primary" block icon={<DatabaseOutlined />}>
                  上传数据集
                </Button>
                <Button block icon={<ExperimentOutlined />}>
                  创建实验
                </Button>
                <Button block icon={<DeploymentUnitOutlined />}>
                  部署模型
                </Button>
                <Button block icon={<AppstoreOutlined />}>
                  创建应用
                </Button>
                <Button block icon={<ThunderboltOutlined />}>
                  GPU 监控
                </Button>
              </Space>
              
              <Divider />
              
              <div>
                <Title level={5}>系统状态</Title>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>CPU使用率</Text>
                    <Text>45%</Text>
                  </div>
                  <Progress percent={45} size="small" />
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>内存使用率</Text>
                    <Text>68%</Text>
                  </div>
                  <Progress percent={68} size="small" />
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>存储使用率</Text>
                    <Text>32%</Text>
                  </div>
                  <Progress percent={32} size="small" />
                </Space>
              </div>
            </Card>
          </Col>
        </Row>

        {/* GPU 监控区域 */}
        <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <GPUMonitor />
          </Col>
        </Row>
      </div>
    </MainLayout>
  );
};

export default DashboardPage;
