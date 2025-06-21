'use client';

import React, { useEffect } from 'react';
import { Card, Button, Typography, Space, Result } from 'antd';
import { RocketOutlined, LinkOutlined } from '@ant-design/icons';
import MainLayout from '@/components/layout/MainLayout';

const { Title, Paragraph } = Typography;

export default function CreateApplicationPage() {
  useEffect(() => {
    // 页面加载后自动跳转到8001端口
    const timer = setTimeout(() => {
      window.open('http://192.168.110.88:8001', '_blank');
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <MainLayout>
      <div style={{ padding: '24px' }}>
        <Card>
          <Result
            icon={<RocketOutlined style={{ color: '#1890ff' }} />}
            title="正在跳转到应用创建页面"
            subTitle="系统将自动跳转到应用管理平台，您也可以手动点击下方按钮"
            extra={[
              <Button
                type="primary"
                key="create"
                size="large"
                icon={<LinkOutlined />}
                onClick={() => window.open('http://192.168.110.88:8001', '_blank')}
              >
                立即创建应用
              </Button>,
              <Button
                key="back"
                onClick={() => window.history.back()}
              >
                返回上一页
              </Button>,
            ]}
          >
            <div style={{ textAlign: 'left', maxWidth: '600px', margin: '0 auto' }}>
              <Title level={4}>应用创建指南</Title>
              <Paragraph>
                在应用管理平台中，您可以：
              </Paragraph>
              <ul>
                <li>使用可视化界面快速创建AI应用</li>
                <li>选择预设的应用模板</li>
                <li>配置应用参数和资源</li>
                <li>一键部署到生产环境</li>
                <li>实时监控应用运行状态</li>
              </ul>
              <Paragraph>
                <strong>提示：</strong>请确保应用管理服务（192.168.110.88:8001）已正常启动。
              </Paragraph>
            </div>
          </Result>
        </Card>
      </div>
    </MainLayout>
  );
}
