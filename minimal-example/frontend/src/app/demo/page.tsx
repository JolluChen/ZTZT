'use client';

import React, { useState } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Alert,
  Divider,
  Tag,
  Modal, // 添加 Modal 导入
} from 'antd';
import {
  DatabaseOutlined,
  CloudUploadOutlined,
  MonitorOutlined,
  SecurityScanOutlined,
  BugOutlined,
} from '@ant-design/icons';
import MainLayout from '@/components/layout/MainLayout';
import DataPreview from '@/components/data/DataPreview';
import ModelDeploy from '@/components/model/ModelDeploy';
import ApplicationMonitor from '@/components/service/ApplicationMonitor';
import PermissionGuard from '@/components/common/PermissionGuard';
import ErrorBoundary from '@/components/common/ErrorBoundary';

const { Title, Text, Paragraph } = Typography;

// 模拟一个会出错的组件来测试错误边界
const ErrorComponent = () => {
  const [shouldError, setShouldError] = useState(false);
  
  if (shouldError) {
    throw new Error('这是一个测试错误：模拟组件崩溃');
  }
  
  return (
    <Button 
      danger 
      onClick={() => setShouldError(true)}
      icon={<BugOutlined />}
    >
      点击触发错误（测试错误边界）
    </Button>
  );
};

export default function ComponentDemoPage() {
  const [dataPreviewVisible, setDataPreviewVisible] = useState(false);
  const [modelDeployVisible, setModelDeployVisible] = useState(false);
  const [monitorVisible, setMonitorVisible] = useState(false);

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        <div style={{ marginBottom: '24px' }}>
          <Title level={2}>组件功能演示</Title>
          <Text type="secondary">
            展示新集成的功能组件：数据预览、模型部署、应用监控、权限控制和错误边界
          </Text>
        </div>

        {/* 功能概览 */}
        <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <DatabaseOutlined style={{ fontSize: '32px', color: '#1890ff', marginBottom: '16px' }} />
                <Title level={4}>数据预览</Title>
                <Text>在线预览数据集内容和统计信息</Text>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <CloudUploadOutlined style={{ fontSize: '32px', color: '#52c41a', marginBottom: '16px' }} />
                <Title level={4}>模型部署</Title>
                <Text>分步骤的模型部署流程</Text>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <MonitorOutlined style={{ fontSize: '32px', color: '#faad14', marginBottom: '16px' }} />
                <Title level={4}>应用监控</Title>
                <Text>实时监控应用性能和日志</Text>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <SecurityScanOutlined style={{ fontSize: '32px', color: '#f5222d', marginBottom: '16px' }} />
                <Title level={4}>权限控制</Title>
                <Text>细粒度的权限管理系统</Text>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 组件演示区域 */}
        <Card title="组件功能演示" style={{ marginBottom: '24px' }}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 数据预览演示 */}
            <div>
              <Title level={4}>数据预览组件</Title>
              <Paragraph>
                <Text>
                  点击下方按钮可以打开数据预览组件，查看模拟的数据集内容。
                  组件包含数据表格、统计信息和图表分析功能。
                </Text>
              </Paragraph>
              <Button 
                type="primary" 
                icon={<DatabaseOutlined />}
                onClick={() => setDataPreviewVisible(true)}
              >
                打开数据预览
              </Button>
              <Tag style={{ marginLeft: '8px' }} color="blue">已集成到数据集管理页面</Tag>
            </div>

            <Divider />

            {/* 模型部署演示 */}
            <div>
              <Title level={4}>模型部署组件</Title>
              <Paragraph>
                <Text>
                  模型部署组件提供了分步骤的部署流程，包括环境配置、资源设置和部署确认。
                </Text>
              </Paragraph>
              <Button 
                type="primary" 
                icon={<CloudUploadOutlined />}
                onClick={() => setModelDeployVisible(true)}
              >
                打开模型部署
              </Button>
              <Tag style={{ marginLeft: '8px' }} color="green">已集成到模型管理页面</Tag>
            </div>

            <Divider />

            {/* 应用监控演示 */}
            <div>
              <Title level={4}>应用监控组件</Title>
              <Paragraph>
                <Text>
                  应用监控组件可以实时查看应用的性能指标、资源使用情况和运行日志。
                </Text>
              </Paragraph>
              <Button 
                type="primary" 
                icon={<MonitorOutlined />}
                onClick={() => setMonitorVisible(true)}
              >
                打开应用监控
              </Button>
              <Tag style={{ marginLeft: '8px' }} color="orange">已集成到应用管理页面</Tag>
            </div>

            <Divider />

            {/* 权限控制演示 */}
            <div>
              <Title level={4}>权限控制组件</Title>
              <Paragraph>
                <Text>
                  权限控制组件可以根据用户权限动态显示或隐藏页面元素。
                  当前演示环境默认拥有基础数据查看权限。
                </Text>
              </Paragraph>
              <Space wrap>
                <PermissionGuard permissions={['dataset_read']}>
                  <Button type="primary">有权限的按钮</Button>
                </PermissionGuard>
                
                <PermissionGuard permissions={['admin_super']}>
                  <Button danger>无权限的按钮（不显示）</Button>
                </PermissionGuard>

                <PermissionGuard permissions={['dataset_read']}>
                  <Tag color="success">有权限的标签</Tag>
                </PermissionGuard>
              </Space>
              <div style={{ marginTop: '8px' }}>
                <Tag color="blue">已集成到权限管理页面</Tag>
              </div>
            </div>

            <Divider />

            {/* 错误边界演示 */}
            <div>
              <Title level={4}>错误边界组件</Title>
              <Paragraph>
                <Text>
                  错误边界组件可以捕获子组件的JavaScript错误，防止整个页面崩溃。
                  点击下方按钮可以触发一个测试错误。
                </Text>
              </Paragraph>
              <ErrorBoundary
                onError={(error, errorInfo) => {
                  console.log('错误被捕获:', error, errorInfo);
                }}
              >
                <ErrorComponent />
              </ErrorBoundary>
              <div style={{ marginTop: '8px' }}>
                <Tag color="red">已集成到主布局组件</Tag>
              </div>
            </div>
          </Space>
        </Card>

        {/* 使用指南 */}
        <Card title="使用指南">
          <Row gutter={[24, 24]}>
            <Col span={12}>
              <Alert
                message="数据集页面"
                description="在数据集管理页面，点击'预览'按钮可以查看数据内容和统计信息。"
                type="info"
                showIcon
              />
            </Col>
            <Col span={12}>
              <Alert
                message="模型页面"
                description="在模型管理页面，点击'部署'按钮可以启动模型部署流程。"
                type="success"
                showIcon
              />
            </Col>
            <Col span={12}>
              <Alert
                message="应用页面"
                description="在应用管理页面，点击'监控'按钮可以查看应用运行状态。"
                type="warning"
                showIcon
              />
            </Col>
            <Col span={12}>
              <Alert
                message="权限管理"
                description="在系统设置中可以管理用户角色和权限配置。"
                type="error"
                showIcon
              />
            </Col>
          </Row>
        </Card>

        {/* 组件模态框 */}
        <DataPreview
          datasetId={1}
          visible={dataPreviewVisible}
          onClose={() => setDataPreviewVisible(false)}
        />

        <ModelDeploy
          modelId={1}
          visible={modelDeployVisible}
          onClose={() => setModelDeployVisible(false)}
        />

        <Modal
          title="应用监控"
          open={monitorVisible}
          onCancel={() => setMonitorVisible(false)}
          footer={null}
          width="80%" // 您可以根据需要调整宽度
          destroyOnClose // 关闭时销毁 Modal 里的子元素
        >
          <ApplicationMonitor
            applicationId={1}
            // visible 和 onClose 属性已移除
          />
        </Modal>
      </div>
    </MainLayout>
  );
}
