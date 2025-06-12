'use client';

import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Button,
  Card,
  Space,
  Typography,
  Alert,
  Steps,
  Spin,
  message,
} from 'antd';
import { CloudUploadOutlined, SettingOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { modelService } from '@/services';

const { Title, Text } = Typography;
const { Option } = Select;

interface ModelDeployProps {
  modelId: number;
  visible: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const ModelDeploy: React.FC<ModelDeployProps> = ({
  modelId,
  visible,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [deployConfig, setDeployConfig] = useState<Record<string, unknown>>({});
  const queryClient = useQueryClient();

  // 部署模型
  const deployMutation = useMutation({
    mutationFn: (config: Record<string, unknown>) => 
      modelService.deployModel(modelId, config),
    onSuccess: () => {
      message.success('模型部署成功');
      queryClient.invalidateQueries({ queryKey: ['models'] });
      onSuccess?.();
      handleClose();
    },
    onError: () => {
      message.error('模型部署失败');
    },
  });

  const handleClose = () => {
    setCurrentStep(0);
    setDeployConfig({});
    form.resetFields();
    onClose();
  };

  const handleNext = async () => {
    try {
      const values = await form.validateFields();
      setDeployConfig({ ...deployConfig, ...values });
      setCurrentStep(currentStep + 1);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const handlePrev = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleDeploy = async () => {
    try {
      const finalConfig = { ...deployConfig };
      await deployMutation.mutateAsync(finalConfig);
    } catch (error) {
      console.error('部署失败:', error);
    }
  };

  const steps = [
    {
      title: '基础配置',
      icon: <SettingOutlined />,
    },
    {
      title: '资源配置',
      icon: <CloudUploadOutlined />,
    },
    {
      title: '确认部署',
      icon: <CheckCircleOutlined />,
    },
  ];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Form form={form} layout="vertical">
            <Form.Item
              name="name"
              label="部署名称"
              rules={[{ required: true, message: '请输入部署名称' }]}
            >
              <Input placeholder="请输入部署名称" />
            </Form.Item>
            
            <Form.Item
              name="description"
              label="描述"
            >
              <Input.TextArea rows={3} placeholder="请输入描述信息" />
            </Form.Item>
            
            <Form.Item
              name="environment"
              label="部署环境"
              rules={[{ required: true, message: '请选择部署环境' }]}
            >
              <Select placeholder="请选择部署环境">
                <Option value="development">开发环境</Option>
                <Option value="staging">测试环境</Option>
                <Option value="production">生产环境</Option>
              </Select>
            </Form.Item>
            
            <Form.Item
              name="version"
              label="版本标签"
              initialValue="v1.0.0"
            >
              <Input placeholder="请输入版本标签" />
            </Form.Item>
          </Form>
        );

      case 1:
        return (
          <Form form={form} layout="vertical">
            <Alert
              message="资源配置"
              description="请根据模型的复杂度和预期负载配置合适的资源"
              type="info"
              style={{ marginBottom: 16 }}
            />
            
            <Form.Item
              name="cpu"
              label="CPU (核)"
              initialValue={2}
              rules={[{ required: true, message: '请输入CPU配置' }]}
            >
              <InputNumber
                min={1}
                max={16}
                step={1}
                style={{ width: '100%' }}
                addonAfter="核"
              />
            </Form.Item>
            
            <Form.Item
              name="memory"
              label="内存 (GB)"
              initialValue={4}
              rules={[{ required: true, message: '请输入内存配置' }]}
            >
              <InputNumber
                min={1}
                max={64}
                step={1}
                style={{ width: '100%' }}
                addonAfter="GB"
              />
            </Form.Item>
            
            <Form.Item
              name="gpu"
              label="GPU数量"
              initialValue={0}
            >
              <InputNumber
                min={0}
                max={8}
                step={1}
                style={{ width: '100%' }}
                addonAfter="块"
              />
            </Form.Item>
            
            <Form.Item
              name="replicas"
              label="副本数量"
              initialValue={1}
              rules={[{ required: true, message: '请输入副本数量' }]}
            >
              <InputNumber
                min={1}
                max={10}
                step={1}
                style={{ width: '100%' }}
                addonAfter="个"
              />
            </Form.Item>
            
            <Form.Item
              name="auto_scaling"
              label="自动扩缩容"
              valuePropName="checked"
              initialValue={false}
            >
              <Switch />
            </Form.Item>
            
            <Form.Item
              name="max_replicas"
              label="最大副本数"
              dependencies={['auto_scaling']}
              rules={[
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (getFieldValue('auto_scaling') && !value) {
                      return Promise.reject(new Error('启用自动扩缩容时必须设置最大副本数'));
                    }
                    return Promise.resolve();
                  },
                }),
              ]}
            >
              <InputNumber
                min={1}
                max={20}
                step={1}
                style={{ width: '100%' }}
                addonAfter="个"
                disabled={!form.getFieldValue('auto_scaling')}
              />
            </Form.Item>
          </Form>
        );

      case 2:
        return (
          <div>
            <Alert
              message="确认部署配置"
              description="请仔细检查以下配置信息，确认无误后点击部署"
              type="warning"
              style={{ marginBottom: 16 }}
            />
            
            <Card title="基础配置" size="small" style={{ marginBottom: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>部署名称：</Text>
                  <Text>{deployConfig.name}</Text>
                </div>
                <div>
                  <Text strong>描述：</Text>
                  <Text>{deployConfig.description || '无'}</Text>
                </div>
                <div>
                  <Text strong>部署环境：</Text>
                  <Text>{deployConfig.environment}</Text>
                </div>
                <div>
                  <Text strong>版本标签：</Text>
                  <Text>{deployConfig.version}</Text>
                </div>
              </Space>
            </Card>
            
            <Card title="资源配置" size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>CPU：</Text>
                  <Text>{deployConfig.cpu} 核</Text>
                </div>
                <div>
                  <Text strong>内存：</Text>
                  <Text>{deployConfig.memory} GB</Text>
                </div>
                <div>
                  <Text strong>GPU：</Text>
                  <Text>{deployConfig.gpu || 0} 块</Text>
                </div>
                <div>
                  <Text strong>副本数量：</Text>
                  <Text>{deployConfig.replicas} 个</Text>
                </div>
                <div>
                  <Text strong>自动扩缩容：</Text>
                  <Text>{deployConfig.auto_scaling ? '启用' : '禁用'}</Text>
                </div>
                {deployConfig.auto_scaling && (
                  <div>
                    <Text strong>最大副本数：</Text>
                    <Text>{deployConfig.max_replicas} 个</Text>
                  </div>
                )}
              </Space>
            </Card>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Modal
      title={
        <Title level={4} style={{ margin: 0 }}>
          模型部署
        </Title>
      }
      open={visible}
      onCancel={handleClose}
      width={800}
      footer={null}
    >
      <Steps
        current={currentStep}
        style={{ marginBottom: 24 }}
        items={steps}
      />

      <Spin spinning={deployMutation.isPending}>
        <div style={{ minHeight: 300 }}>
          {renderStepContent()}
        </div>
      </Spin>

      <div style={{ marginTop: 24, textAlign: 'right' }}>
        <Space>
          {currentStep > 0 && (
            <Button onClick={handlePrev}>
              上一步
            </Button>
          )}
          
          {currentStep < steps.length - 1 ? (
            <Button type="primary" onClick={handleNext}>
              下一步
            </Button>
          ) : (
            <Button
              type="primary"
              onClick={handleDeploy}
              loading={deployMutation.isPending}
            >
              开始部署
            </Button>
          )}
          
          <Button onClick={handleClose}>
            取消
          </Button>
        </Space>
      </div>
    </Modal>
  );
};

export default ModelDeploy;
