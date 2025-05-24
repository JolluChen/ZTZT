# Weaviate 1.22 部署指南

本文档详细说明如何在物理服务器环境中部署和配置 Weaviate 1.22 向量数据库服务，用于 AI 中台项目的语义搜索、RAG 系统和向量存储。

## 1. 部署选项

Weaviate 用于存储和检索向量数据，支持语义搜索和 RAG (Retrieval Augmented Generation) 应用，详细类设计见 `database_design.md`。

### 1.1 Docker Compose 部署（用于本地开发/测试）

Weaviate 推荐使用 Docker Compose 进行部署，特别是当需要配置多个向量化模块时：

```bash
# 创建 docker-compose.yml 文件
cat > docker-compose-weaviate.yml << EOF
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    container_name: weaviate
    restart: unless-stopped
    ports:
      - "8088:8080"
      - "50051:50051"  # gRPC port
    volumes:
      - weaviate_data:/var/lib/weaviate
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "false"
      AUTHENTICATION_APIKEY_ENABLED: "true"
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: "changeThisToSecurePassword"  # 请替换为安全的 API 密钥
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      DEFAULT_VECTORIZER_MODULE: text2vec-transformers
      ENABLE_MODULES: text2vec-transformers,img2vec-neural,generative-openai
      CLUSTER_HOSTNAME: "node1"
    depends_on:
      - t2v-transformers
      - img2vec-neural

  t2v-transformers:
    image: semitechnologies/transformers-inference:sentence-transformers-multilingual-e5-large
    container_name: t2v-transformers
    restart: unless-stopped
    environment:
      ENABLE_CUDA: "0"  # 设置为 1 启用 GPU
      NVIDIA_VISIBLE_DEVICES: "all"  # 使用 GPU 时需要
    volumes:
      - transformer_cache:/root/.cache
      
  img2vec-neural:
    image: semitechnologies/img2vec-neural:resnet50
    container_name: img2vec-neural
    restart: unless-stopped
    environment:
      ENABLE_CUDA: "0"  # 设置为 1 启用 GPU

volumes:
  weaviate_data:
    driver: local
  transformer_cache:
    driver: local
EOF

# 启动服务
docker-compose -f docker-compose-weaviate.yml up -d
```

### 1.2 Kubernetes 部署 (推荐生产环境)

使用 Weaviate 官方提供的 Helm Chart：

```bash
# 添加仓库
helm repo add weaviate https://weaviate.github.io/weaviate-helm

# 创建自定义配置文件
cat > weaviate-values.yaml << EOF
persistence:
  enabled: true
  size: 20Gi
  storageClassName: local-storage
resources:
  requests:
    memory: "4Gi"
    cpu: "2"
  limits:
    memory: "8Gi"
    cpu: "4"
env:
  QUERY_DEFAULTS_LIMIT: "25"
  AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "false"
  AUTHENTICATION_APIKEY_ENABLED: "true"
  AUTHENTICATION_APIKEY_ALLOWED_KEYS: "changeThisToYourApiKey" # 请务必修改为安全的 API Key
  PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
modules:
  - name: text2vec-transformers
    image: semitechnologies/transformers-inference:sentence-transformers-multilingual-e5-large
    resources:
      requests:
        memory: "2Gi"
        cpu: "1"
      limits:
        memory: "4Gi"
        cpu: "2"
  - name: img2vec-neural # 添加 img2vec-neural 模块以支持图像向量化
    image: semitechnologies/img2vec-neural:resnet50
    resources:
      requests:
        memory: "2Gi"
        cpu: "1"
      limits:
        memory: "4Gi"
        cpu: "2"
  - name: generative-openai
    image: semitechnologies/generative-openai:1.4.0
replicaCount: 1
EOF

# 安装 Weaviate
helm install ai-weaviate weaviate/weaviate -f weaviate-values.yaml -n database
```

**模块选择**:
Weaviate 支持多种模块，根据实际需求选择：
- `text2vec-transformers`: 文本向量化
- `generative-openai`: 生成式 AI 功能
- `img2vec-neural`: 图像向量化

### 1.3 本地存储配置 (物理服务器)

在物理服务器上配置持久化存储：

```bash
# 创建本地存储目录
sudo mkdir -p /mnt/weaviate-data
sudo chown 1000:1000 /mnt/weaviate-data  # Weaviate 容器用户 ID

# 创建 Kubernetes PersistentVolume
cat > weaviate-pv.yaml << EOF
apiVersion: v1
kind: PersistentVolume
metadata:
  name: weaviate-pv
spec:
  capacity:
    storage: 20Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/weaviate-data
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node01  # 替换为实际的节点名称
EOF

kubectl apply -f weaviate-pv.yaml
```

## 2. 连接方式

### 2.1 服务地址与端口

- **Docker Compose**: `http://localhost:8088` (或配置的端口)
- **Kubernetes**: `http://<service-name>.<namespace>.svc.cluster.local:8080` (例如 `http://ai-weaviate.database.svc.cluster.local:8080`)

### 2.2 API 连接示例

使用 Python 中的 Weaviate 客户端：

```python
import weaviate
import json

# 创建客户端
client = weaviate.Client(
    url="http://localhost:8088",  # 调整为实际的 Weaviate 实例地址
    auth_client_secret=weaviate.AuthApiKey(api_key="changeThisToSecurePassword"),
    additional_headers={
        "X-OpenAI-Api-Key": "your-openai-key"  # 如果使用 OpenAI 模块则需要
    }
)

# 检查连接
print(f"Weaviate 版本: {client.get_meta().get('version')}")

# 使用示例 - 添加文档
def add_document(title, content, source, category, author=None, tags=None):
    """添加文档到 Weaviate"""
    properties = {
        "title": title,
        "content": content,
        "source": source,
        "category": category,
        "creationDate": "2023-05-01T12:00:00Z",  # 使用实际时间
    }
    
    # 添加可选字段
    if author:
        properties["author"] = author
    if tags:
        properties["tags"] = tags
        
    # 使用 Weaviate 客户端 API 添加对象
    try:
        doc_id = client.data_object.create(
            class_name="Document",
            properties=properties,
            consistency_level="ALL"  # 强一致性设置
        )
        print(f"文档添加成功，ID: {doc_id}")
        return doc_id
    except Exception as e:
        print(f"添加文档失败: {e}")
        return None

# 使用示例 - 语义搜索
def semantic_search(query, limit=5):
    """执行语义搜索"""
    try:
        result = client.query.get(
            class_name="Document", 
            properties=["title", "content", "category", "source"]
        ).with_near_text(
            {"concepts": [query]}
        ).with_limit(limit).do()
        
        return result["data"]["Get"]["Document"]
    except Exception as e:
        print(f"搜索失败: {e}")
        return []
```

## 3. 安全与配置

### 3.1 基本安全配置

- 禁用匿名访问并启用 API Key 认证
- 限制网络访问，确保只有需要的应用可以连接到 Weaviate

```bash
# 在 Docker Compose 中配置安全设置
environment:
  AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "false"
  AUTHENTICATION_APIKEY_ENABLED: "true"
  AUTHENTICATION_APIKEY_ALLOWED_KEYS: "your-secure-api-key"
```

### 3.2 性能优化

根据服务器资源调整配置：

```bash
# 调整资源配置（在 Kubernetes values.yaml 中）
resources:
  requests:
    memory: "4Gi"
    cpu: "2"
  limits:
    memory: "8Gi"
    cpu: "4"

# 配置关键环境变量
env:
  QUERY_MAXIMUM_RESULTS: "10000"
  PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
  DISK_USE_READONLY_PERCENTAGE: "95"  # 当磁盘使用率达到 95% 时转为只读模式
  ENABLE_MODULES: "text2vec-transformers,img2vec-neural,generative-openai"
  DEFAULT_VECTORIZER_MODULE: "text2vec-transformers"
```

对于具有 GPU 的环境：

```yaml
# Transformers 模块启用 GPU
t2v-transformers:
  environment:
    ENABLE_CUDA: "1"
    NVIDIA_VISIBLE_DEVICES: "0"  # 使用第一个 GPU
  deploy:
    resources:
      reservations:
        devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## 4. 数据模式初始化

部署后需要使用 Weaviate 客户端或 API 初始化数据模式：

```bash
# 创建 schema 配置文件 schema.json
cat > schema.json << EOF
{
  "classes": [
    {
      "class": "Document",
      "description": "A document with vector representation for semantic search",
      "vectorizer": "text2vec-transformers",
      "properties": [
        {
          "name": "title",
          "dataType": ["text"],
          "description": "The title of the document"
        },
        {
          "name": "content",
          "dataType": ["text"],
          "description": "The content of the document"
        },
        {
          "name": "source",
          "dataType": ["text"],
          "description": "Source of the document"
        },
        {
          "name": "category",
          "dataType": ["text"],
          "description": "Category of the document"
        },
        {
          "name": "creationDate",
          "dataType": ["date"],
          "description": "The date this document was created"
        },
        {
          "name": "author",
          "dataType": ["text"],
          "description": "Author of the document"
        },
        {
          "name": "tags",
          "dataType": ["text[]"],
          "description": "Tags associated with the document"
        }
      ]
    },
    {
      "class": "Image",
      "description": "Images with vector embeddings",
      "vectorizer": "img2vec-neural",
      "properties": [
        {
          "name": "filename",
          "dataType": ["text"],
          "description": "The filename of the image"
        },
        {
          "name": "caption",
          "dataType": ["text"],
          "description": "Caption or description of the image"
        },
        {
          "name": "mimeType",
          "dataType": ["text"],
          "description": "MIME type of the image"
        },
        {
          "name": "imageUrl",
          "dataType": ["text"],
          "description": "URL to the image file"
        },
        {
          "name": "resolution",
          "dataType": ["text"],
          "description": "Resolution of the image"
        },
        {
          "name": "tags",
          "dataType": ["text[]"],
          "description": "Tags associated with the image"
        },
        {
          "name": "uploadDate",
          "dataType": ["date"],
          "description": "Upload date of the image"
        }
      ]
    },
    {
      "class": "ModelData",
      "description": "Data related to machine learning models",
      "vectorizer": "text2vec-transformers",
      "properties": [
        {
          "name": "modelName",
          "dataType": ["text"],
          "description": "Name of the model"
        },
        {
          "name": "modelDescription",
          "dataType": ["text"],
          "description": "Description of the model"
        },
        {
          "name": "framework",
          "dataType": ["text"],
          "description": "Framework used (PyTorch, TensorFlow, etc.)"
        },
        {
          "name": "metrics",
          "dataType": ["text"],
          "description": "Model performance metrics as JSON string"
        },
        {
          "name": "useCase",
          "dataType": ["text"],
          "description": "Use case for this model"
        },
        {
          "name": "version",
          "dataType": ["text"],
          "description": "Version of the model"
        },
        {
          "name": "createdBy",
          "dataType": ["text"],
          "description": "Creator of the model"
        }
      ]
    }
  ]
}
EOF

# 使用 curl 应用 schema (请确保 WEAVIATE_API_KEY 环境变量已设置或直接替换 API Key)
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${WEAVIATE_API_KEY:-yourWeaviateApiKey}" \
  -d @schema.json \
  http://localhost:8088/v1/schema
```

## 5. 备份与恢复

### 5.1 创建备份

使用 Weaviate 的备份 API：

```bash
# 创建备份
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${WEAVIATE_API_KEY:-yourWeaviateApiKey}" \
  -d '{"id":"backup-'$(date +%Y%m%d)'"}' \
  http://localhost:8088/v1/backups/filesystem
```

### 5.2 恢复备份

```bash
# 恢复备份
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${WEAVIATE_API_KEY:-yourWeaviateApiKey}" \
  -d '{}' \
  http://localhost:8088/v1/backups/filesystem/backup-20230501/restore
```

## 6. 最佳实践

1. **数据模式设计**：
   - 仔细规划您的类和属性，以便有效地组织和检索数据
   - 考虑将经常一起查询的数据分组到同一个类中
   - 为属性建立适当的索引类型

2. **向量化策略**：
   - 选择适合您数据和用例的向量化模型
   - 考虑在 `text2vec-transformers` 和 `text2vec-openai` 等选项之间进行选择
   - 针对多语言需求，选择多语言模型如 `multilingual-e5-large`

3. **资源规划**：
   - 为向量化模块分配足够的内存和 CPU/GPU 资源
   - 监控系统性能，根据需要调整资源分配
   - 对于大型数据集，考虑使用 GPU 加速向量化过程

4. **安全最佳实践**：
   - 始终使用 API 密钥身份验证
   - 限制网络访问
   - 定期更新 Weaviate 和其模块版本
   - 定期备份重要数据

## 7. 故障排除

### 7.1 常见问题

1. **连接问题**:
   - 验证 Weaviate 服务是否运行 `docker ps | grep weaviate`
   - 检查网络配置和防火墙规则
   - 验证 API 密钥是否正确

2. **性能问题**:
   - 检查日志中是否有内存不足或资源限制警告
   - 验证向量化模块是否正常工作
   - 监控查询延迟和资源使用情况

3. **导入数据失败**:
   - 检查数据格式是否符合架构定义
   - 验证向量化模块是否正常运行
   - 检查是否存在批处理大小、内存限制问题

### 7.2 日志分析

```bash
# 在 Docker 中查看日志
docker logs weaviate

# 在 Kubernetes 中查看日志
kubectl logs -f ai-weaviate-0 -n database

# 查看模块日志
docker logs t2v-transformers
```

## 相关资源

- [Weaviate 官方文档](https://weaviate.io/developers/weaviate)
- [Weaviate Python 客户端](https://weaviate.io/developers/weaviate/client-libraries/python)
- [Weaviate 架构设计](https://weaviate.io/developers/weaviate/concepts/schema)
- [Weaviate 语义搜索教程](https://weaviate.io/developers/weaviate/tutorials/semantic-search)
