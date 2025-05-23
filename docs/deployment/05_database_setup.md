# AI 中台 - 核心数据库建立与连接

本文档指导如何在 AI 中台项目中建立和连接核心数据库服务，主要包括 PostgreSQL、MongoDB、Weaviate、Redis 和 Kafka。

## 1. 概述

核心服务层依赖多种数据库来存储不同类型的数据：

-   **PostgreSQL 16**: 用于存储模型元数据、用户权限、系统配置、任务调度记录等结构化数据，采用模式(Schema)进行逻辑分区。
-   **MongoDB 6.0**: 用于存储日志数据、配置文件、临时缓存等半结构化或非结构化数据。
-   **Weaviate 1.22**: 用于存储 Embedding 和支持 RAG (Retrieval Augmented Generation) 的向量数据。
-   **Redis 7.0**: 用于缓存、会话管理和实时数据处理。
-   **Kafka 3.6**: 用于消息队列和数据流处理。

数据库架构与设计详情请参考 `docs/development/database_design.md`。在 Kubernetes 环境中部署这些数据库时，请参考 `03_storage_systems_kubernetes.md` 中关于持久化存储的配置。同时，请参考 `docs/ip/service_ip_port_mapping.md` 进行 IP 和端口规划。

## 2. PostgreSQL 16

### 2.1. 部署

PostgreSQL 可以在 Kubernetes 集群内部署，也可以作为外部服务接入。数据库设计详情见`docs/development/database_design.md`文档。

**Kubernetes 部署 (推荐):**

-   **Helm Chart**: 使用 Bitnami PostgreSQL Helm chart 或 Crunchy Data PostgreSQL Operator 是常见的选择。
    ```bash
    # 添加仓库
    helm repo add bitnami https://charts.bitnami.com/bitnami
    
    # 创建自定义配置文件values.yaml
    cat > postgres-values.yaml << EOF
    primary:
      persistence:
        size: 20Gi
      resources:
        requests:
          memory: "2Gi"
          cpu: "1"
        limits:
          memory: "4Gi"
          cpu: "2"
    postgresqlUsername: postgres
    postgresqlPassword: "changeThisToSecurePassword"
    postgresqlDatabase: ai_platform
    postgresql:
      extraEnvVars:
        - name: POSTGRES_INITDB_ARGS
          value: "--data-checksums"
    EOF
    
    # 安装 PostgreSQL
    helm install ai-postgres bitnami/postgresql -f postgres-values.yaml
    ```
-   **持久化存储**: 确保配置了合适的 `PersistentVolumeClaim`，建议使用SSD存储类型提高I/O性能。
-   **pgvector 扩展**: 数据中台和向量搜索功能需要在 PostgreSQL 实例中安装和启用 `pgvector` 扩展。

**外部服务:**

-   如果使用云服务商提供的 PostgreSQL (如 AWS RDS, Azure Database for PostgreSQL, Google Cloud SQL)，请遵循其官方文档进行创建和配置，并确保支持pgvector扩展。

### 2.2. 连接

-   **服务地址**:
    -   Kubernetes 内部: `<service-name>.<namespace>.svc.cluster.local` (例如: `my-postgres-postgresql.default.svc.cluster.local`)
    -   外部服务: 云服务商提供的连接端点。
-   **端口**: 默认为 `5432` (参考 `service_ip_port_mapping.md` 中的规划)。
-   **凭证**: 使用部署时设置的用户名和密码。建议使用 Kubernetes Secrets 管理敏感凭证。
-   **客户端工具**: `psql`, DBeaver, pgAdmin 等。
-   **应用程序连接**: 使用相应语言的 PostgreSQL 客户端库 (如 Python 中的 `psycopg2` 或 `asyncpg`)。

### 2.3. 安全与配置

-   配置强密码策略。
-   限制网络访问，仅允许必要的应用和服务连接。
-   定期备份。
-   根据需求调整 `postgresql.conf` 中的配置参数:
    ```
    # 连接设置
    max_connections = 200                  # 根据系统负载调整
    
    # 内存设置
    shared_buffers = '1GB'                 # 服务器内存的25%
    work_mem = '64MB'                      # 复杂查询的工作内存
    maintenance_work_mem = '256MB'         # 维护操作的内存
    
    # 日志设置
    log_statement = 'ddl'                  # 记录所有DDL语句
    log_min_duration_statement = 1000      # 记录执行时间超过1秒的查询
    
    # 查询优化
    random_page_cost = 1.1                 # SSD存储设置更低的随机页成本
    effective_cache_size = '3GB'           # 系统缓存的估计值
    ```

### 2.4. 数据库初始化

使用初始化脚本创建所需的Schema和基础表结构：

```bash
# 连接到PostgreSQL并执行初始化脚本
kubectl exec -it ai-postgres-postgresql-0 -- bash -c "psql -U postgres -d ai_platform -f /tmp/init.sql"
```

初始化脚本应该包含创建Schema、表和索引的SQL语句，参照`database_design.md`中定义的表结构。

## 3. MongoDB 6.0

### 3.1. 部署

MongoDB主要用于存储日志数据、临时缓存和配置文件，详细集合设计见`database_design.md`。

**Kubernetes 部署 (推荐):**

-   **Helm Chart**: 使用 Bitnami MongoDB Helm chart 或 MongoDB Community Operator。
    ```bash
    # 添加仓库
    helm repo add bitnami https://charts.bitnami.com/bitnami
    
    # 创建自定义配置文件
    cat > mongodb-values.yaml << EOF
    architecture: replicaset
    replicaCount: 3
    auth:
      enabled: true
      rootPassword: "changeThisToSecurePassword"
      username: "ai_platform"
      password: "changeThisToSecurePassword"
      database: "ai_platform"
    persistence:
      size: 20Gi
      storageClass: "managed-premium"  # 根据您的云环境调整
    resources:
      requests:
        memory: "1Gi"
        cpu: "0.5"
      limits:
        memory: "2Gi"
        cpu: "1"
    EOF
    
    # 安装MongoDB
    helm install ai-mongodb bitnami/mongodb -f mongodb-values.yaml
    ```
-   **副本集 (Replica Set)**: 强烈建议启用副本集以保证高可用性和数据冗余。
-   **持久化存储**: 确保配置了合适的 `PersistentVolumeClaim`。

**外部服务:**

-   使用 MongoDB Atlas 或其他云服务商提供的 MongoDB 服务。

### 3.2. 连接

-   **服务地址**:
    -   Kubernetes 内部: `<service-name>.<namespace>.svc.cluster.local` (例如: `my-mongodb.default.svc.cluster.local`)
    -   外部服务: 云服务商提供的连接字符串。
-   **端口**: 默认为 `27017` (参考 `service_ip_port_mapping.md` 中的规划)。
-   **凭证**: 使用部署时设置的用户名和密码，并配置认证。
-   **客户端工具**: `mongosh`, MongoDB Compass 等。
-   **应用程序连接**: 使用相应语言的 MongoDB 驱动程序 (如 Python 中的 `pymongo`)。

### 3.3. 安全与配置

-   启用认证 (`auth`)。
-   配置基于角色的访问控制 (RBAC)。
-   限制网络访问。
-   定期备份。

### 3.4. 集合初始化

部署后创建必要的集合并设置索引：

```bash
# 连接到MongoDB
kubectl exec -it ai-mongodb-0 -- mongo -u ai_platform -p "yourPassword" --authenticationDatabase ai_platform

# 在MongoDB shell中执行以下命令
use ai_platform

// 创建系统日志集合
db.createCollection("system_logs")
db.system_logs.createIndex({ "timestamp": 1 })
db.system_logs.createIndex({ "level": 1, "timestamp": 1 })
db.system_logs.createIndex({ "service": 1, "timestamp": 1 })

// 创建配置集合
db.createCollection("configurations")
db.configurations.createIndex({ "component": 1, "environment": 1, "version": 1 })
db.configurations.createIndex({ "is_active": 1 })

// 创建任务状态缓存集合
db.createCollection("task_status_cache")
db.task_status_cache.createIndex({ "task_id": 1 })
db.task_status_cache.createIndex({ "status": 1, "last_updated": 1 })
db.task_status_cache.createIndex({ "task_type": 1, "status": 1 })

// 设置TTL索引，自动清理过期数据
db.task_status_cache.createIndex({ "last_updated": 1 }, { expireAfterSeconds: 86400 }) // 24小时后自动删除
```

## 4. Weaviate 1.22

### 4.1. 部署

Weaviate用于存储和检索向量数据，支持语义搜索和RAG应用，详细类设计见`database_design.md`。

**Kubernetes 部署 (推荐):**

-   **Helm Chart**: Weaviate 官方提供了 Helm chart。
    ```bash
    # 添加仓库
    helm repo add weaviate https://weaviate.github.io/weaviate-helm
    
    # 创建自定义配置文件
    cat > weaviate-values.yaml << EOF
    persistence:
      enabled: true
      size: 20Gi
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
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: "changeThisToYourApiKey"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
    modules:
      - name: text2vec-transformers
        image: semitechnologies/transformers-inference:sentence-transformers-multilingual-e5-large
      - name: generative-openai
        image: semitechnologies/generative-openai:1.4.0
    replicaCount: 1
    EOF
    
    # 安装Weaviate
    helm install ai-weaviate weaviate/weaviate -f weaviate-values.yaml
    ```
-   **模块 (Modules)**: Weaviate 支持多种模块，根据实际需求选择：
    - `text2vec-transformers`: 文本向量化
    - `generative-openai`: 生成式AI功能
    - `img2vec-neural`: 图像向量化
-   **持久化存储**: 确保配置了合适的 `PersistentVolumeClaim`。

**Docker Compose (用于本地开发/测试):**

-   参考 Weaviate 官方文档提供的 `docker-compose.yml` 文件。

### 4.2. 连接

-   **服务地址**:
    -   Kubernetes 内部: `<service-name>.<namespace>.svc.cluster.local` (例如: `weaviate.default.svc.cluster.local`)
-   **端口**:
    -   HTTP: 默认为 `8080` (参考 `service_ip_port_mapping.md` 中的规划，如 `8088`)。
    -   gRPC: 默认为 `50051`。
-   **客户端库**: Weaviate 提供了多种语言的客户端库 (如 Python `weaviate-client`)。

### 4.3. 安全与配置

-   **认证与授权**: 启用 API Key 认证，限制匿名访问。
-   **数据模式 (Schema)**: 在使用前定义好数据模式，参考`database_design.md`中的类设计。
-   **备份与恢复**: 参考 Weaviate 官方文档进行备份策略配置。

### 4.4. 初始化数据模式

部署后需要使用Weaviate客户端或API初始化数据模式：

```bash
# 创建schema配置文件
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
        }
      ]
    }
  ]
}
EOF

# 使用curl应用schema
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${WEAVIATE_API_KEY}" \
  -d @schema.json \
  http://ai-weaviate.default.svc.cluster.local:8080/v1/schema
```

## 5. Redis 7.0

### 5.1. 部署

Redis用于缓存和临时数据存储，提高系统性能，详细键设计见`database_design.md`。

**Kubernetes 部署 (推荐):**

-   **Helm Chart**: 使用 Bitnami Redis Helm chart。
    ```bash
    # 添加仓库
    helm repo add bitnami https://charts.bitnami.com/bitnami
    
    # 创建自定义配置文件
    cat > redis-values.yaml << EOF
    architecture: replication
    auth:
      enabled: true
      password: "changeThisToSecurePassword"
    master:
      persistence:
        size: 8Gi
      resources:
        requests:
          memory: "1Gi"
          cpu: "0.5"
        limits:
          memory: "2Gi"
          cpu: "1"
    replica:
      replicaCount: 2
      persistence:
        size: 8Gi
    sentinel:
      enabled: true
    EOF
    
    # 安装Redis
    helm install ai-redis bitnami/redis -f redis-values.yaml
    ```
-   **持久化配置**: 根据实际需求配置RDB和AOF持久化策略。

### 5.2. 连接

-   **服务地址**:
    -   Kubernetes 内部: `ai-redis-master.default.svc.cluster.local` (主节点)
    -   Sentinel: `ai-redis-headless.default.svc.cluster.local:26379` (Sentinel)
-   **端口**: 默认为 `6379`
-   **认证**: 使用配置的密码认证
-   **应用程序连接**: 使用相应语言的Redis客户端库，建议支持连接池和哨兵/集群模式

### 5.3. 安全与优化

-   配置密码和ACL
-   限制内存使用，设置合理的淘汰策略
-   监控命中率和内存使用情况
-   定期持久化备份

## 6. Kafka 3.6

### 6.1. 部署

Kafka用于消息队列和数据流处理。

**Kubernetes 部署 (推荐):**

-   **Helm Chart**: 使用 Bitnami Kafka Helm chart。
    ```bash
    # 添加仓库
    helm repo add bitnami https://charts.bitnami.com/bitnami
    
    # 创建自定义配置文件
    cat > kafka-values.yaml << EOF
    replicaCount: 3
    persistence:
      size: 20Gi
    resources:
      requests:
        memory: "2Gi"
        cpu: "1"
      limits:
        memory: "4Gi"
        cpu: "2"
    zookeeper:
      enabled: true
      persistence:
        size: 8Gi
    auth:
      clientProtocol: sasl
      interBrokerProtocol: sasl
      sasl:
        mechanisms: plain
        user: user
        password: "changeThisToSecurePassword"
    EOF
    
    # 安装Kafka
    helm install ai-kafka bitnami/kafka -f kafka-values.yaml
    ```

### 6.2. 连接

-   **服务地址**: `ai-kafka.default.svc.cluster.local:9092`
-   **认证**: 使用SASL认证
-   **Topic设计**: 根据应用需求创建主题，设置合适的分区数和复制因子

### 6.3. 初始化配置

创建系统所需的基本主题：

```bash
# 连接到Kafka容器
kubectl exec -it ai-kafka-0 -- bash

# 创建主题
kafka-topics.sh --create --bootstrap-server localhost:9092 \
  --topic data-ingestion --partitions 3 --replication-factor 2 \
  --command-config /opt/bitnami/kafka/config/client.properties

kafka-topics.sh --create --bootstrap-server localhost:9092 \
  --topic model-events --partitions 3 --replication-factor 2 \
  --command-config /opt/bitnami/kafka/config/client.properties

kafka-topics.sh --create --bootstrap-server localhost:9092 \
  --topic system-logs --partitions 3 --replication-factor 2 \
  --command-config /opt/bitnami/kafka/config/client.properties
```

## 7. 数据库连接管理

-   **环境变量**: 推荐使用环境变量来配置应用程序的数据库连接信息。
-   **Kubernetes Secrets**: 将数据库凭证等敏感信息存储在 Kubernetes Secrets 中，并通过环境变量或卷挂载的方式注入到应用 Pod 中。
    ```bash
    # 创建数据库凭证的Secret
    kubectl create secret generic db-credentials \
      --from-literal=postgres-password="yourPostgresPassword" \
      --from-literal=mongodb-password="yourMongoPassword" \
      --from-literal=redis-password="yourRedisPassword" \
      --from-literal=weaviate-apikey="yourWeaviateApiKey" \
      --from-literal=kafka-password="yourKafkaPassword"
    ```
-   **连接池**: 在应用程序中使用数据库连接池以提高性能和资源利用率。

## 8. 数据库监控与维护

### 8.1 Prometheus监控

为所有数据库服务配置Prometheus监控，监控关键指标：

- PostgreSQL: 连接数、缓存命中率、锁等待、查询延迟
- MongoDB: 操作延迟、连接数、内存使用、写入队列
- Redis: 命中率、内存使用、客户端连接数、延迟
- Kafka: 消息延迟、消费者延迟、磁盘使用率

### 8.2 备份策略

```bash
# 创建PostgreSQL定期备份CronJob
kubectl apply -f postgres-backup-cronjob.yaml

# 创建MongoDB定期备份CronJob
kubectl apply -f mongodb-backup-cronjob.yaml
```

### 8.3 维护计划

- 定期在低峰期进行维护操作
- 定期清理日志和临时数据
- 监控和优化索引性能
- 定期验证备份有效性

---

**后续步骤**:
完成核心数据库的部署和配置后，可以继续部署应用层的具体服务，并配置它们连接到这些数据库实例。请参考`docs/development/database_design.md`了解各应用使用的数据库表设计和访问模式。
