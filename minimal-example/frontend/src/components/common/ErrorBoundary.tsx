'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Card, Typography, Space, Alert } from 'antd';
import { ReloadOutlined, HomeOutlined, BugOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // 调用父组件的错误处理函数
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 记录错误到控制台
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // 这里可以添加错误上报逻辑
    // reportError(error, errorInfo);
  }

  handleReload = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleGoHome = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/dashboard';
    }
  };

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义的fallback组件，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认的错误显示组件
      return (
        <div style={{ padding: '24px', minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
          <Card style={{ maxWidth: '800px', margin: '0 auto', marginTop: '100px' }}>
            <Result
              status="error"
              title="页面出现错误"
              subTitle="抱歉，页面遇到了一些问题。请尝试刷新页面或返回首页。"
              extra={[
                <Button type="primary" key="reload" icon={<ReloadOutlined />} onClick={this.handleReload}>
                  重新加载
                </Button>,
                <Button key="home" icon={<HomeOutlined />} onClick={this.handleGoHome}>
                  返回首页
                </Button>,
              ]}
            />

            {/* 开发环境下显示详细错误信息 */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Card 
                title={
                  <Space>
                    <BugOutlined />
                    <Text strong>开发调试信息</Text>
                  </Space>
                }
                style={{ marginTop: '24px' }}
                type="inner"
              >
                <Alert
                  message="错误详情"
                  description={
                    <div>
                      <Paragraph>
                        <Text strong>错误消息:</Text>
                        <br />
                        <Text code>{this.state.error.message}</Text>
                      </Paragraph>
                      
                      <Paragraph>
                        <Text strong>错误堆栈:</Text>
                        <br />
                        <pre style={{ 
                          fontSize: '12px', 
                          backgroundColor: '#f6f8fa', 
                          padding: '8px',
                          borderRadius: '4px',
                          overflow: 'auto',
                          maxHeight: '300px'
                        }}>
                          {this.state.error.stack}
                        </pre>
                      </Paragraph>

                      {this.state.errorInfo && (
                        <Paragraph>
                          <Text strong>组件堆栈:</Text>
                          <br />
                          <pre style={{ 
                            fontSize: '12px', 
                            backgroundColor: '#f6f8fa', 
                            padding: '8px',
                            borderRadius: '4px',
                            overflow: 'auto',
                            maxHeight: '200px'
                          }}>
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </Paragraph>
                      )}
                    </div>
                  }
                  type="error"
                  showIcon
                />
              </Card>
            )}
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
