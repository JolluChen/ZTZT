# Dify AI 平台使用指南

## 快速开始

### 1. 启动 AI 中台 + Dify 集成

```bash
cd /home/lsyzt/ZTZT/minimal-example

# 启动 AI 中台 + Dify 集成（默认启用）
./quick-start.sh

# 或者如果只需要传统 AI 中台功能
./quick-start.sh --no-dify
```

等待服务启动完成后，您将看到以下服务地址：
- **AI 中台前端**: http://192.168.110.88:3000
- **Dify 控制台**: http://192.168.110.88:8001
- **AI 中台 API**: http://192.168.110.88:8000

### 2. 初始化 Dify

首次使用需要初始化 Dify：

1. 访问 http://192.168.110.88:8001
2. 设置管理员账户
3. 完成初始配置

### 3. 在 AI 中台中创建 Dify 应用

1. 访问 AI 中台前端：http://192.168.110.88:3000
2. 登录系统（默认账户：admin/admin123）
3. 进入"服务中台" -> "应用管理"
4. 点击"创建应用"
5. 选择"Dify AI 应用"类型

### 4. 配置 Dify 应用

在创建应用表单中：

**基本信息：**
- 应用名称：例如"智能客服助手"
- 描述：应用功能描述

**Dify 配置：**
- **应用类型**：选择以下之一
  - `chat` - 对话应用
  - `completion` - 文本生成
  - `workflow` - 工作流
  - `agent` - 智能体

- **模式**：
  - `simple` - 简单模式
  - `advanced` - 高级模式

- **API 密钥**：从 Dify 控制台获取
- **API 地址**：默认 `http://localhost:8001`

## 获取 Dify API 密钥

1. 在 Dify 控制台中创建应用
2. 进入应用设置
3. 在"API 访问"部分获取 API Key
4. 将 API Key 粘贴到 AI 中台的应用配置中

## API 使用示例

### 创建 Dify 应用

```bash
curl -X POST http://192.168.110.88:8000/api/service/dify/applications/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "智能客服",
    "description": "基于 Dify 的智能客服应用",
    "app_type": "chat",
    "mode": "simple",
    "api_key": "app-xxxxxxxxxx",
    "api_url": "http://localhost:8001"
  }'
```

### 获取应用列表

```bash
curl -X GET http://192.168.110.88:8000/api/service/dify/applications/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 创建对话

```bash
curl -X POST http://192.168.110.88:8000/api/service/dify/applications/1/conversations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_id": 1,
    "inputs": {}
  }'
```

### 发送消息

```bash
curl -X POST http://192.168.110.88:8000/api/service/dify/applications/1/conversations/conv-123/messages/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "你好，我需要帮助",
    "inputs": {},
    "response_mode": "blocking"
  }'
```

## 前端集成示例

在 React 组件中使用 Dify 服务：

```typescript
import { serviceService } from '@/services';

// 创建 Dify 应用
const createDifyApp = async () => {
  try {
    const app = await serviceService.createDifyApplication({
      name: '智能助手',
      description: 'AI 助手应用',
      app_type: 'chat',
      mode: 'simple',
      api_key: 'app-xxxxxxxxxx',
      api_url: 'http://localhost:8001'
    });
    console.log('应用创建成功:', app);
  } catch (error) {
    console.error('创建失败:', error);
  }
};

// 发送消息
const sendMessage = async (appId: number, conversationId: string, message: string) => {
  try {
    const response = await serviceService.sendDifyMessage(appId, conversationId, {
      query: message,
      response_mode: 'blocking'
    });
    console.log('AI 回复:', response);
  } catch (error) {
    console.error('发送失败:', error);
  }
};
```

## 高级功能

### 知识库管理

```typescript
// 创建知识库
const createDataset = async (appId: number) => {
  const dataset = await serviceService.createDifyDataset(appId, {
    name: '产品知识库',
    description: '包含产品相关的问答知识'
  });
  return dataset;
};

// 获取知识库列表
const getDatasets = async (appId: number) => {
  const datasets = await serviceService.getDifyDatasets(appId);
  return datasets;
};
```

### 对话历史

```typescript
// 获取对话列表
const getConversations = async (appId: number) => {
  const conversations = await serviceService.getDifyConversations(appId);
  return conversations;
};

// 创建新对话
const startNewConversation = async (appId: number, userId: number) => {
  const conversation = await serviceService.createDifyConversation(appId, {
    user_id: userId,
    inputs: {}
  });
  return conversation;
};
```

## 监控和调试

### 查看服务状态

```bash
# 检查 Dify 服务状态
docker ps --filter "name=ai_platform_dify"

# 查看 Dify API 日志
docker logs ai_platform_dify_api

# 查看 Dify Worker 日志  
docker logs ai_platform_dify_worker

# 查看 Nginx 日志
docker logs ai_platform_dify_nginx
```

### 常见问题排查

1. **Dify 服务无法访问**
   ```bash
   # 检查容器状态
   docker ps
   
   # 检查网络连接
   docker network ls | grep ai_platform
   
   # 重启 Dify 服务
   cd docker && docker compose -f dify-docker-compose.yml --profile dify restart
   ```

2. **API 认证失败**
   - 确认 API Key 是否正确
   - 检查 Dify 控制台中的应用状态
   - 验证 API 地址配置

3. **数据库连接问题**
   ```bash
   # 检查 PostgreSQL 状态
   docker logs ai_platform_postgres
   
   # 检查 Redis 状态  
   docker logs ai_platform_redis
   ```

## 停止服务

```bash
# 停止所有服务（包括 Dify）
./stop.sh
```

## 更多资源

- [Dify 官方文档](https://docs.dify.ai)
- [AI 中台集成文档](./docs/dify-integration.md)
- [API 参考](http://192.168.110.88:8000/swagger/)

---

现在您已经可以在 AI 中台中充分利用 Dify 的强大 AI 能力了！🚀
