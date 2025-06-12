# Weaviate 1.22 部署指南

# Weaviate 1.22 部署指南

本文档详细说明如何在物理服务器环境中部署和配置 Weaviate 1.22 向量数据库服务，用于 AI 中台项目的语义搜索、RAG 系统和向量存储。

> **🎯 实际部署指南**: 本文档基于实际部署经验进行优化，提供了简化部署方式、管理脚本以及离线环境支持，确保在各种环境下都能成功部署。

## 📋 目录

1. [部署选项](#1-部署选项)
   - [🚀 快速开始 - 简化部署（推荐）](#-快速开始---简化部署推荐)
   - [完整功能版部署](#11-docker-compose-部署完整功能版)
   - [Kubernetes 部署](#12-kubernetes-部署-推荐生产环境)
   - [本地存储配置](#13-本地存储配置-物理服务器)

2. [连接方式](#2-连接方式)
   - [服务地址与端口](#21-服务地址与端口)
   - [API 连接示例](#22-api-连接示例)

3. [安全与配置](#3-安全与配置)
   - [基本安全配置](#31-基本安全配置)
   - [性能优化](#32-性能优化)

4. [数据模式初始化](#4-数据模式初始化)
   - [简化版模式](#41-简化版模式无向量模块依赖)
   - [完整版模式](#42-完整版模式带向量模块)
   - [部署验证](#43-部署验证)

5. [备份与恢复](#5-备份与恢复)

6. [最佳实践](#6-最佳实践)

7. [故障排除](#7-故障排除)
   - [常见问题](#71-常见问题)
   - [离线环境支持](#72-离线air-gapped环境支持)
   - [日志分析与监控](#73-日志分析与监控)
   - [故障恢复](#74-故障恢复)

8. [安全加固](#8-安全加固)

9. [升级指南](#9-升级指南)

10. [部署总结](#10-部署总结)

---

## 1. 部署选项

Weaviate 用于存储和检索向量数据，支持语义搜索和 RAG (Retrieval Augmented Generation) 应用，详细类设计见 `database_design.md`。

### 🚀 快速开始 - 简化部署（推荐）

对于大多数用户，推荐使用简化的独立部署方式，无需外部向量模块依赖：

```bash
# 创建简化的 Docker Compose 配置
cat > docker-compose-weaviate-simple.yml << EOF
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    container_name: weaviate-simple
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
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: "weaviate-api-key-2024"  # 生产环境请使用更安全的密钥
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      DEFAULT_VECTORIZER_MODULE: "none"  # 不使用向量化模块，支持自定义向量
      ENABLE_MODULES: ""  # 空模块列表，减少依赖
      CLUSTER_HOSTNAME: "node1"
      # 离线环境优化配置
      DISABLE_TELEMETRY: "true"
      GO_GC: "25"  # 优化垃圾回收
      LIMIT_RESOURCES: "true"

volumes:
  weaviate_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/weaviate/data  # 使用本地目录挂载

EOF

# 创建数据目录
sudo mkdir -p /opt/weaviate/data
sudo chown 1000:1000 /opt/weaviate/data

# 启动简化版 Weaviate
docker compose -f docker-compose-weaviate-simple.yml up -d

# 验证部署
docker ps | grep weaviate
curl -f http://localhost:8088/v1/meta || echo "等待服务启动..."
```

#### 管理脚本

创建便于管理的脚本：

```bash
# 创建 Weaviate 管理脚本
cat > manage-weaviate.sh << 'EOF'
#!/bin/bash

# Weaviate 管理脚本
# 用法: ./manage-weaviate.sh [start|stop|restart|status|logs|backup|restore]

COMPOSE_FILE="docker-compose-weaviate-simple.yml"
WEAVIATE_URL="http://localhost:8088"
API_KEY="weaviate-api-key-2024"
BACKUP_DIR="/opt/weaviate/backups"

function start_weaviate() {
    echo "🚀 启动 Weaviate 服务..."
    docker compose -f $COMPOSE_FILE up -d
    
    echo "⏳ 等待服务就绪..."
    for i in {1..30}; do
        if curl -sf $WEAVIATE_URL/v1/meta >/dev/null 2>&1; then
            echo "✅ Weaviate 服务已就绪"
            echo "📡 服务地址: $WEAVIATE_URL"
            echo "🔑 API Key: $API_KEY"
            return 0
        fi
        sleep 2
    done
    echo "❌ 服务启动超时"
    return 1
}

function stop_weaviate() {
    echo "🛑 停止 Weaviate 服务..."
    docker compose -f $COMPOSE_FILE down
}

function restart_weaviate() {
    stop_weaviate
    sleep 2
    start_weaviate
}

function show_status() {
    echo "📊 Weaviate 服务状态:"
    docker compose -f $COMPOSE_FILE ps
    echo ""
    echo "🔗 连接测试:"
    curl -s $WEAVIATE_URL/v1/meta | jq '.version // "连接失败"' 2>/dev/null || echo "❌ 无法连接到 Weaviate"
}

function show_logs() {
    echo "📋 查看 Weaviate 日志:"
    docker compose -f $COMPOSE_FILE logs -f --tail=50
}

function backup_data() {
    echo "💾 创建 Weaviate 备份..."
    mkdir -p $BACKUP_DIR
    BACKUP_ID="backup-$(date +%Y%m%d_%H%M%S)"
    
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "{\"id\":\"$BACKUP_ID\"}" \
        $WEAVIATE_URL/v1/backups/filesystem
    
    echo "✅ 备份已创建: $BACKUP_ID"
}

function restore_data() {
    echo "🔄 可用备份列表:"
    curl -s -H "Authorization: Bearer $API_KEY" $WEAVIATE_URL/v1/backups/filesystem | jq '.[] | .id' 2>/dev/null || echo "无可用备份"
    
    echo "请输入要恢复的备份ID:"
    read BACKUP_ID
    
    if [ -n "$BACKUP_ID" ]; then
        curl -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $API_KEY" \
            -d '{}' \
            $WEAVIATE_URL/v1/backups/filesystem/$BACKUP_ID/restore
        echo "✅ 恢复操作已启动"
    fi
}

case "$1" in
    start)
        start_weaviate
        ;;
    stop)
        stop_weaviate
        ;;
    restart)
        restart_weaviate
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_data
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|backup|restore}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动 Weaviate 服务"
        echo "  stop    - 停止 Weaviate 服务"
        echo "  restart - 重启 Weaviate 服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看服务日志"
        echo "  backup  - 创建数据备份"
        echo "  restore - 恢复数据备份"
        exit 1
        ;;
esac
EOF

# 设置执行权限
chmod +x manage-weaviate.sh

# 使用示例
echo "✅ 管理脚本已创建，使用方法:"
echo "  ./manage-weaviate.sh start    # 启动服务"
echo "  ./manage-weaviate.sh status   # 查看状态"
echo "  ./manage-weaviate.sh logs     # 查看日志"
```

### 1.1 Docker Compose 部署（完整功能版）

当需要完整的向量化模块支持时使用此配置：

```bash
# 创建完整功能的 docker-compose.yml 文件
cat > docker-compose-weaviate-full.yml << EOF
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

# 启动完整功能版服务
docker compose -f docker-compose-weaviate-full.yml up -d
```

> **⚠️ 注意**: 完整功能版需要下载大型向量模型，首次启动可能需要较长时间。如果在离线环境中部署，请使用上面的简化版本。

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

### 4.1 简化版模式（无向量模块依赖）

对于使用简化部署的用户，可以使用以下模式配置：

```bash
# 创建简化 schema 配置文件 schema-simple.json
cat > schema-simple.json << EOF
{
  "classes": [
    {
      "class": "Document",
      "description": "A document with manual vector support for semantic search",
      "vectorizer": "none",
      "vectorIndexConfig": {
        "distance": "cosine"
      },
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
      "class": "Embeddings",
      "description": "General purpose embeddings storage",
      "vectorizer": "none",
      "vectorIndexConfig": {
        "distance": "cosine"
      },
      "properties": [
        {
          "name": "text",
          "dataType": ["text"],
          "description": "Original text content"
        },
        {
          "name": "metadata",
          "dataType": ["object"],
          "description": "Additional metadata as JSON object"
        },
        {
          "name": "source",
          "dataType": ["text"],
          "description": "Source identifier"
        },
        {
          "name": "createdAt",
          "dataType": ["date"],
          "description": "Creation timestamp"
        }
      ]
    }
  ]
}
EOF

# 应用简化模式
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer weaviate-api-key-2024" \
  -d @schema-simple.json \
  http://localhost:8088/v1/schema
```

#### 使用简化模式的 Python 示例

```python
import weaviate
import numpy as np

# 连接到简化版 Weaviate
client = weaviate.Client(
    url="http://localhost:8088",
    auth_client_secret=weaviate.AuthApiKey(api_key="weaviate-api-key-2024")
)

def add_document_with_vector(title, content, vector, source="manual", category="general"):
    """添加带有自定义向量的文档"""
    properties = {
        "title": title,
        "content": content,
        "source": source,
        "category": category,
        "creationDate": "2024-01-01T12:00:00Z"
    }
    
    try:
        doc_id = client.data_object.create(
            class_name="Document",
            properties=properties,
            vector=vector  # 传入预计算的向量
        )
        print(f"文档添加成功，ID: {doc_id}")
        return doc_id
    except Exception as e:
        print(f"添加文档失败: {e}")
        return None

def semantic_search_with_vector(query_vector, limit=5):
    """使用向量进行语义搜索"""
    try:
        result = client.query.get(
            class_name="Document", 
            properties=["title", "content", "category", "source"]
        ).with_near_vector(
            {"vector": query_vector}
        ).with_limit(limit).do()
        
        return result["data"]["Get"]["Document"]
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

# 示例：添加文档（需要外部向量化）
sample_vector = np.random.rand(384).tolist()  # 示例向量，实际使用时需要真实的embedding
add_document_with_vector("示例文档", "这是一个示例文档内容", sample_vector)
```

### 4.2 完整版模式（带向量模块）

部署后需要使用 Weaviate 客户端或 API 初始化数据模式：

```bash
# 创建完整版 schema 配置文件 schema-full.json
cat > schema-full.json << EOF
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

# 使用 curl 应用完整版 schema
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${WEAVIATE_API_KEY:-yourWeaviateApiKey}" \
  -d @schema-full.json \
  http://localhost:8088/v1/schema
```

### 4.3 部署验证

无论使用哪种部署方式，都应该验证部署是否成功：

```bash
# 检查服务状态
curl -f http://localhost:8088/v1/meta

# 检查模式是否创建成功
curl -H "Authorization: Bearer weaviate-api-key-2024" \
     http://localhost:8088/v1/schema

# 使用管理脚本检查
./manage-weaviate.sh status
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

## 7. 故障排除

### 7.1 常见问题

#### 📡 连接问题
1. **服务无法启动**:
   ```bash
   # 检查端口占用
   netstat -tlnp | grep 8088
   
   # 检查Docker服务状态
   docker ps -a | grep weaviate
   
   # 查看启动日志
   ./manage-weaviate.sh logs
   ```

2. **API连接失败**:
   ```bash
   # 验证服务是否可访问
   curl -f http://localhost:8088/v1/meta
   
   # 检查API密钥
   curl -H "Authorization: Bearer weaviate-api-key-2024" \
        http://localhost:8088/v1/schema
   ```

3. **网络配置问题**:
   ```bash
   # 检查防火墙规则
   sudo ufw status
   
   # 临时开放端口（测试用）
   sudo ufw allow 8088/tcp
   ```

#### 🐛 性能问题
1. **内存不足**:
   ```bash
   # 检查内存使用
   docker stats weaviate-simple
   
   # 调整内存限制（在docker-compose中）
   deploy:
     resources:
       limits:
         memory: 2G
   ```

2. **查询速度慢**:
   ```bash
   # 检查索引状态
   curl -H "Authorization: Bearer weaviate-api-key-2024" \
        "http://localhost:8088/v1/schema/Document"
   
   # 优化向量索引配置
   "vectorIndexConfig": {
     "distance": "cosine",
     "efConstruction": 128,
     "maxConnections": 16
   }
   ```

#### 💾 数据问题
1. **导入数据失败**:
   ```bash
   # 验证数据格式
   curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer weaviate-api-key-2024" \
     -d '{"class":"Document","properties":{"title":"test"}}' \
     http://localhost:8088/v1/objects
   
   # 检查模式定义
   curl -H "Authorization: Bearer weaviate-api-key-2024" \
        http://localhost:8088/v1/schema
   ```

2. **向量维度不匹配**:
   ```python
   # 检查向量维度
   import numpy as np
   vector = np.random.rand(384).tolist()  # 确保维度正确
   
   # 验证向量格式
   assert len(vector) == 384
   assert all(isinstance(x, (int, float)) for x in vector)
   ```

### 7.2 离线/Air-gapped环境支持

#### 🔌 完全离线部署
对于无法访问外网的环境，使用简化版部署：

```bash
# 1. 使用简化版配置（无外部依赖）
cat > docker-compose-offline.yml << EOF
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    container_name: weaviate-offline
    restart: unless-stopped
    ports:
      - "8088:8080"
    volumes:
      - weaviate_data:/var/lib/weaviate
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "false"
      AUTHENTICATION_APIKEY_ENABLED: "true"
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: "weaviate-offline-key"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      DEFAULT_VECTORIZER_MODULE: "none"
      ENABLE_MODULES: ""
      CLUSTER_HOSTNAME: "offline-node"
      # 离线环境专用配置
      DISABLE_TELEMETRY: "true"
      PROMETHEUS_MONITORING_ENABLED: "false"
      ASYNC_INDEXING: "false"
      
volumes:
  weaviate_data:
    driver: local
EOF

# 2. 预加载镜像（如果有镜像文件）
docker load -i weaviate-1.22.4.tar

# 3. 启动离线版本
docker compose -f docker-compose-offline.yml up -d
```

#### 📦 镜像准备
```bash
# 在有网络的环境中准备镜像
docker pull semitechnologies/weaviate:1.22.4
docker save semitechnologies/weaviate:1.22.4 -o weaviate-1.22.4.tar

# 传输到离线环境后加载
docker load -i weaviate-1.22.4.tar
```

#### 🛠️ 离线配置验证
```bash
# 创建离线验证脚本
cat > verify-offline.sh << 'EOF'
#!/bin/bash

echo "🔍 验证离线 Weaviate 部署..."

# 检查容器状态
if docker ps | grep -q weaviate-offline; then
    echo "✅ 容器运行正常"
else
    echo "❌ 容器未运行"
    exit 1
fi

# 检查API响应
if curl -sf http://localhost:8088/v1/meta >/dev/null; then
    echo "✅ API服务正常"
else
    echo "❌ API服务异常"
    exit 1
fi

# 检查模式创建
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer weaviate-offline-key" \
  -d '{"class":"TestClass","vectorizer":"none","properties":[{"name":"text","dataType":["text"]}]}' \
  http://localhost:8088/v1/schema >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ 模式创建功能正常"
    # 清理测试类
    curl -X DELETE \
      -H "Authorization: Bearer weaviate-offline-key" \
      http://localhost:8088/v1/schema/TestClass >/dev/null 2>&1
else
    echo "❌ 模式创建功能异常"
fi

echo "🎉 离线部署验证完成"
EOF

chmod +x verify-offline.sh
./verify-offline.sh
```

### 7.3 日志分析与监控

#### 📊 日志收集
```bash
# 使用管理脚本查看日志
./manage-weaviate.sh logs

# 手动查看Docker日志
docker logs weaviate-simple -f --tail 100

# 在Kubernetes中查看日志
kubectl logs -f ai-weaviate-0 -n database

# 查看模块日志（完整版）
docker logs t2v-transformers -f
```

#### 📈 性能监控
```bash
# 1. 创建监控脚本
cat > monitor-weaviate.sh << 'EOF'
#!/bin/bash

echo "=== Weaviate 监控报告 $(date) ==="

# 容器状态
echo "📦 容器状态:"
docker stats --no-stream weaviate-simple 2>/dev/null || echo "容器未运行"

# API健康检查
echo -e "\n🔍 API健康状态:"
curl -sf http://localhost:8088/v1/meta | jq -r '.version // "API无响应"'

# 磁盘使用
echo -e "\n💾 磁盘使用:"
docker exec weaviate-simple df -h /var/lib/weaviate 2>/dev/null || echo "无法获取磁盘信息"

# 数据统计
echo -e "\n📊 数据统计:"
curl -sf -H "Authorization: Bearer weaviate-api-key-2024" \
     "http://localhost:8088/v1/schema" | \
     jq -r '.classes[]? | "\(.class): \(.description // "无描述")"' || echo "无法获取模式信息"

echo -e "\n=== 监控完成 ==="
EOF

chmod +x monitor-weaviate.sh

# 运行监控
./monitor-weaviate.sh
```

#### 🚨 告警配置
```bash
# 创建简单的健康检查脚本
cat > health-check.sh << 'EOF'
#!/bin/bash

# 配置
API_URL="http://localhost:8088"
API_KEY="weaviate-api-key-2024"
MAX_RESPONSE_TIME=5

# 健康检查函数
check_health() {
    local start_time=$(date +%s)
    
    # 检查API响应
    response=$(curl -sf -m $MAX_RESPONSE_TIME \
                   -H "Authorization: Bearer $API_KEY" \
                   "$API_URL/v1/meta" 2>/dev/null)
    
    local end_time=$(date +%s)
    local response_time=$((end_time - start_time))
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        echo "✅ 健康检查通过 (响应时间: ${response_time}s)"
        return 0
    else
        echo "❌ 健康检查失败 (响应时间: ${response_time}s)"
        return 1
    fi
}

# 检查容器状态
check_container() {
    if docker ps | grep -q weaviate-simple; then
        echo "✅ 容器运行正常"
        return 0
    else
        echo "❌ 容器未运行"
        return 1
    fi
}

# 执行检查
echo "🔍 执行 Weaviate 健康检查..."
container_ok=0
api_ok=0

check_container && container_ok=1
check_health && api_ok=1

# 结果汇总
if [ $container_ok -eq 1 ] && [ $api_ok -eq 1 ]; then
    echo "🎉 所有检查通过"
    exit 0
else
    echo "⚠️  存在问题，请检查日志"
    echo "建议运行: ./manage-weaviate.sh logs"
    exit 1
fi
EOF

chmod +x health-check.sh

# 设置定时检查（可选）
# echo "*/5 * * * * /path/to/health-check.sh" | crontab -
```

#### 📋 维护任务
```bash
# 创建维护脚本
cat > maintain-weaviate.sh << 'EOF'
#!/bin/bash

echo "🛠️  开始 Weaviate 维护任务..."

# 1. 清理旧日志
echo "📝 清理容器日志..."
docker exec weaviate-simple sh -c 'find /var/log -name "*.log" -mtime +7 -delete' 2>/dev/null || true

# 2. 检查磁盘空间
echo "💾 检查磁盘空间..."
usage=$(docker exec weaviate-simple df /var/lib/weaviate | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$usage" -gt 80 ]; then
    echo "⚠️  磁盘使用率过高: ${usage}%"
else
    echo "✅ 磁盘使用率正常: ${usage}%"
fi

# 3. 数据一致性检查
echo "🔍 数据一致性检查..."
result=$(curl -sf -H "Authorization: Bearer weaviate-api-key-2024" \
              "http://localhost:8088/v1/schema" | jq -r '.classes | length')
if [ "$result" ]; then
    echo "✅ 发现 $result 个数据类"
else
    echo "⚠️  无法获取模式信息"
fi

# 4. 内存使用检查
echo "🧠 内存使用检查..."
mem_usage=$(docker stats --no-stream weaviate-simple --format "{{.MemPerc}}" | sed 's/%//')
if [ "${mem_usage%.*}" -gt 80 ]; then
    echo "⚠️  内存使用率过高: ${mem_usage}%"
else
    echo "✅ 内存使用率正常: ${mem_usage}%"
fi

echo "🎉 维护任务完成"
EOF

chmod +x maintain-weaviate.sh
```

### 7.4 故障恢复

#### 🔄 自动重启策略
```bash
# 在manage-weaviate.sh中已包含自动重启功能
./manage-weaviate.sh restart

# 检查重启后状态
sleep 10
./manage-weaviate.sh status
```

#### 💾 数据恢复流程
```bash
# 1. 停止服务
./manage-weaviate.sh stop

# 2. 恢复数据（如果有备份）
# docker volume create weaviate_data_backup
# docker run --rm -v weaviate_data:/source -v weaviate_data_backup:/backup alpine cp -r /source/. /backup/

# 3. 启动服务
./manage-weaviate.sh start

# 4. 验证恢复
./manage-weaviate.sh status
```

## 8. 安全加固

### 8.1 API密钥管理
```bash
# 生成安全的API密钥
API_KEY=$(openssl rand -hex 32)
echo "生成的API密钥: $API_KEY"

# 更新Docker Compose配置中的API密钥
sed -i "s/weaviate-api-key-2024/$API_KEY/g" docker-compose-weaviate-simple.yml
```

### 8.2 网络安全
```bash
# 限制访问IP（在生产环境中）
# 修改docker-compose配置，使用自定义网络
networks:
  weaviate-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 8.3 数据加密
```bash
# 启用数据静态加密（需要企业版或自定义实现）
# 在环境变量中添加：
PERSISTENCE_DATA_ENCRYPTION: "true"
PERSISTENCE_ENCRYPTION_KEY: "your-encryption-key"
```

## 9. 升级指南

### 9.1 版本升级
```bash
# 1. 备份当前数据
./manage-weaviate.sh backup

# 2. 停止服务
./manage-weaviate.sh stop

# 3. 更新镜像版本
sed -i 's/weaviate:1.22.4/weaviate:1.23.0/g' docker-compose-weaviate-simple.yml

# 4. 启动新版本
./manage-weaviate.sh start

# 5. 验证升级
./manage-weaviate.sh status
curl -H "Authorization: Bearer weaviate-api-key-2024" http://localhost:8088/v1/meta | jq .version
```

### 9.2 配置迁移
```bash
# 迁移配置到新版本时的注意事项
echo "升级前请检查:"
echo "1. 新版本的模式兼容性"
echo "2. API变更情况"
echo "3. 环境变量配置变化"
echo "4. 模块依赖更新"
```

## 10. 部署总结

### 10.1 推荐部署路径

#### 🎯 快速部署（推荐大多数用户）
1. 使用简化版 Docker Compose 配置
2. 部署无向量模块依赖的 Weaviate
3. 使用外部向量化服务或预计算向量
4. 适用于离线环境和资源受限环境

#### 🔧 完整功能部署
1. 使用完整版 Docker Compose 配置
2. 包含文本和图像向量化模块
3. 需要额外的计算资源和网络访问
4. 适用于需要内置向量化的场景

#### 🏭 生产环境部署
1. 使用 Kubernetes + Helm Chart
2. 配置持久化存储和资源限制
3. 实施监控、备份和安全策略
4. 设置负载均衡和高可用

### 10.2 关键配置检查清单

- [ ] **安全配置**: API密钥已设置且安全
- [ ] **存储配置**: 持久化卷已正确配置
- [ ] **网络配置**: 端口和防火墙规则已设置
- [ ] **资源配置**: 内存和CPU限制已合理设置
- [ ] **备份策略**: 定期备份已配置
- [ ] **监控告警**: 健康检查和监控已部署
- [ ] **模式初始化**: 数据模式已正确创建
- [ ] **连接测试**: API连接已验证

### 10.3 常用命令速查

```bash
# 服务管理
./manage-weaviate.sh start|stop|restart|status

# 查看日志
./manage-weaviate.sh logs

# 健康检查
./health-check.sh

# 监控状态
./monitor-weaviate.sh

# 维护任务
./maintain-weaviate.sh

# API测试
curl -H "Authorization: Bearer weaviate-api-key-2024" http://localhost:8088/v1/meta
```

### 10.4 下一步建议

1. **集成开发**: 根据 `database_design.md` 中的设计实现数据访问层
2. **性能优化**: 根据实际使用情况调整向量索引参数
3. **扩展部署**: 考虑集群部署以支持更高负载
4. **监控完善**: 集成专业监控系统如 Prometheus + Grafana

## 相关资源

### 📚 官方文档
- [Weaviate 官方文档](https://weaviate.io/developers/weaviate) - 完整的官方文档
- [Weaviate Python 客户端](https://weaviate.io/developers/weaviate/client-libraries/python) - Python SDK文档
- [Weaviate 架构设计](https://weaviate.io/developers/weaviate/concepts/schema) - 数据模式设计指南
- [Weaviate 语义搜索教程](https://weaviate.io/developers/weaviate/tutorials/semantic-search) - 语义搜索实现

### 🛠️ 部署相关
- [Docker Compose 最佳实践](https://docs.docker.com/compose/production/)
- [Kubernetes Helm Charts](https://helm.sh/docs/best_practices/)
- [Weaviate Helm Chart](https://github.com/weaviate/weaviate-helm)

### 🔧 配置和优化
- [向量索引优化](https://weaviate.io/developers/weaviate/config-refs/schema/vector-index) - 性能调优指南
- [模块配置参考](https://weaviate.io/developers/weaviate/modules) - 各种模块的配置说明
- [认证和授权](https://weaviate.io/developers/weaviate/configuration/authentication) - 安全配置

### 🐍 开发集成
- [Python 客户端示例](https://github.com/weaviate/weaviate-python-client/tree/main/docs/examples)
- [REST API 参考](https://weaviate.io/developers/weaviate/api/rest) - 完整的API文档
- [GraphQL API 参考](https://weaviate.io/developers/weaviate/api/graphql) - GraphQL查询语法

### 📊 监控和运维
- [Prometheus 监控配置](https://weaviate.io/developers/weaviate/configuration/monitoring)
- [日志管理最佳实践](https://weaviate.io/developers/weaviate/configuration/logging)
- [备份和恢复策略](https://weaviate.io/developers/weaviate/configuration/backups)

### 🏗️ 项目相关
- `database_design.md` - 数据库设计文档（本项目）
- `server_setup.md` - 服务器基础环境配置
- `docker_deployment.md` - Docker 容器化部署指南

### 🆘 社区支持
- [Weaviate 社区论坛](https://forum.weaviate.io/)
- [GitHub Issues](https://github.com/weaviate/weaviate/issues)
- [Slack 社区](https://weaviate.io/slack)

---

> **📝 文档维护**: 本文档基于 Weaviate 1.22.4 版本编写，如遇到版本差异问题请参考官方最新文档。
> 
> **🔄 最后更新**: 2024年1月 | **📧 反馈**: 如发现问题或建议改进，请提交issue或联系维护团队。
