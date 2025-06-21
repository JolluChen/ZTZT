'use client';

import React from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Space,
  Button,
  List,
  Progress,
  Avatar,
  Tag,
  Divider,
} from 'antd';
import {
  AppstoreOutlined,
  CloudServerOutlined,
  MonitorOutlined,
  ApiOutlined,
  RocketOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import MainLayout from '@/components/layout/MainLayout';
import { serviceService } from '@/services';

const { Title, Text, Paragraph } = Typography;

export default function ServiceOverviewPage() {
  // 获取服务统计数据
  const { data: stats } = useQuery({
    queryKey: ['service-stats'],
    queryFn: () => serviceService.getApplications(),
    select: (data) => {
      const applications = data?.results || [];
      return {
        total: applications.length,
        running: applications.filter((app: any) => app.status === 'running').length,
        stopped: applications.filter((app: any) => app.status === 'stopped').length,
        error: applications.filter((app: any) => app.status === 'error').length,
      };
    },
  });

  // 系统特性数据
  const features = [
    {
      icon: <AppstoreOutlined style={{ fontSize: '24px', color: '#1890ff' }} />,
      title: '应用编排',
      description: '通过可视化界面快速构建和部署AI应用',
    },
    {
      icon: <CloudServerOutlined style={{ fontSize: '24px', color: '#52c41a' }} />,
      title: '容器化部署',
      description: '基于容器技术实现应用的快速部署和扩缩容',
    },
    {
      icon: <MonitorOutlined style={{ fontSize: '24px', color: '#fa8c16' }} />,
      title: '实时监控',
      description: '全方位监控应用运行状态和性能指标',
    },
    {
      icon: <ApiOutlined style={{ fontSize: '24px', color: '#eb2f96' }} />,
      title: 'API网关',
      description: '统一的API接入和管理，支持多种协议',
    },
    {
      icon: <SafetyCertificateOutlined style={{ fontSize: '24px', color: '#722ed1' }} />,
      title: '安全保障',
      description: '多层次安全防护，确保应用和数据安全',
    },
    {
      icon: <ThunderboltOutlined style={{ fontSize: '24px', color: '#f5222d' }} />,
      title: '高性能',
      description: '优化的架构设计，支持高并发和低延迟',
    },
  ];

  // 最近活动数据
  const recentActivities = [
    {
      type: 'deploy',
      title: '智能客服应用部署成功',
      time: '2小时前',
      status: 'success',
    },
    {
      type: 'update',
      title: '图像识别模型更新完成',
      time: '4小时前',
      status: 'success',
    },
    {
      type: 'error',
      title: '文本分析服务异常',
      time: '6小时前',
      status: 'error',
    },
    {
      type: 'create',
      title: '新建推荐系统应用',
      time: '1天前',
      status: 'info',
    },
  ];

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'deploy':
        return <RocketOutlined style={{ color: '#52c41a' }} />;
      case 'update':
        return <MonitorOutlined style={{ color: '#1890ff' }} />;
      case 'error':
        return <SafetyCertificateOutlined style={{ color: '#f5222d' }} />;
      case 'create':
        return <AppstoreOutlined style={{ color: '#fa8c16' }} />;
      default:
        return <AppstoreOutlined />;
    }
  };

  const getStatusTag = (status: string) => {
    const statusConfig = {
      success: { color: 'green', text: '成功' },
      error: { color: 'red', text: '异常' },
      info: { color: 'blue', text: '信息' },
    };
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.info;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        {/* 页面标题 */}
        <div style={{ marginBottom: '24px' }}>
          <Title level={2}>服务概览</Title>
          <Text type="secondary">智能化应用服务管理平台</Text>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="应用总数"
                value={stats?.total || 0}
                prefix={<AppstoreOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="运行中"
                value={stats?.running || 0}
                prefix={<RocketOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="已停止"
                value={stats?.stopped || 0}
                prefix={<CloudServerOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="异常"
                value={stats?.error || 0}
                prefix={<SafetyCertificateOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 平台介绍 */}
        <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
          <Col xs={24} lg={16}>
            <Card title="平台介绍" extra={<TeamOutlined />}>
              <Paragraph>
                AI中台服务平台是一个集成化的智能应用管理系统，致力于为企业提供高效、安全、可靠的AI应用部署和管理解决方案。
              </Paragraph>
              <Paragraph>
                平台通过现代化的容器技术和微服务架构，实现了应用的快速构建、部署和扩展，支持多种AI模型的集成和管理。
              </Paragraph>
              <Paragraph>
                <strong>核心优势：</strong>
              </Paragraph>
              <ul>
                <li>简化应用部署流程，提高开发效率</li>
                <li>统一资源管理，优化成本控制</li>
                <li>实时监控预警，保障服务稳定</li>
                <li>灵活扩展架构，适应业务发展</li>
              </ul>
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="系统状态" extra={<MonitorOutlined />}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text>CPU使用率</Text>
                  <Progress percent={45} status="active" />
                </div>
                <div>
                  <Text>内存使用率</Text>
                  <Progress percent={68} status="active" />
                </div>
                <div>
                  <Text>存储使用率</Text>
                  <Progress percent={32} status="active" />
                </div>
                <div>
                  <Text>网络状态</Text>
                  <Progress percent={90} status="active" />
                </div>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* 功能特性 */}
        <Card title="平台特性" style={{ marginBottom: '24px' }}>
          <Row gutter={[24, 24]}>
            {features.map((feature, index) => (
              <Col xs={24} sm={12} lg={8} key={index}>
                <Card size="small" hoverable>
                  <Space>
                    {feature.icon}
                    <div>
                      <Title level={5} style={{ margin: 0 }}>
                        {feature.title}
                      </Title>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {feature.description}
                      </Text>
                    </div>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>

        {/* 最近活动 */}
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="最近活动" extra={<MonitorOutlined />}>
              <List
                dataSource={recentActivities}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Avatar icon={getActivityIcon(item.type)} />}
                      title={
                        <Space>
                          <span>{item.title}</span>
                          {getStatusTag(item.status)}
                        </Space>
                      }
                      description={item.time}
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="快速操作" extra={<ThunderboltOutlined />}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  type="primary"
                  icon={<AppstoreOutlined />}
                  block
                  onClick={() => window.open('http://192.168.110.88:8001', '_blank')}
                >
                  访问应用管理
                </Button>
                <Button
                  type="primary"
                  icon={<RocketOutlined />}
                  block
                  onClick={() => window.open('http://192.168.110.88:8001', '_blank')}
                >
                  创建新应用
                </Button>
                <Divider />
                <Button
                  icon={<MonitorOutlined />}
                  block
                  onClick={() => window.open('/service/applications', '_self')}
                >
                  查看监控面板
                </Button>
                <Button
                  icon={<ApiOutlined />}
                  block
                  onClick={() => window.open('/swagger/', '_blank')}
                >
                  API 文档
                </Button>
              </Space>
            </Card>
          </Col>
        </Row>
      </div>
    </MainLayout>
  );
}
