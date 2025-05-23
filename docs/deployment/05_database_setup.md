# AI 中台 - 核心数据库建立与连接

本文档指导如何在 AI 中台项目中建立和连接核心数据库服务，主要包括 PostgreSQL、MongoDB、Weaviate、Redis 和 Kafka。本指南提供两种部署方式：Docker部署和Kubernetes集群部署。

## 1. 概述

核心服务层依赖多种数据库来存储不同类型的数据：

-   **PostgreSQL 16**: 用于存储模型元数据、用户权限、系统配置、任务调度记录等结构化数据，采用模式(Schema)进行逻辑分区。
    - 主要模式包括：`public`, `auth`, `data_platform`, `algo_platform`, `model_platform`, `service_platform`
-   **MongoDB 6.0**: 用于存储日志数据、配置文件、临时缓存等半结构化或非结构化数据。
    - 主要集合包括：`system_logs`, `configurations`, `task_status_cache`
-   **Weaviate 1.22**: 用于存储 Embedding 和支持 RAG (Retrieval Augmented Generation) 的向量数据。
    - 主要类包括：`Document`, `Image`, `ModelData`
-   **Redis 7.0**: 用于缓存、会话管理和实时数据处理。
    - 键空间前缀：`session:`, `token:`, `cache:`, `rate:api:`, `lock:`, `queue:`, `pubsub:`, `stats:`
-   **Kafka 3.6**: 用于消息队列和数据流处理。
    - 主要主题：`data-ingestion`, `model-events`, `system-logs`

数据库架构与设计详情请参考 `docs/development/database_design.md`。在 Kubernetes 环境中部署这些数据库时，请参考 `03_storage_systems_kubernetes.md` 中关于持久化存储的配置。同时，请参考 `docs/ip/service_ip_port_mapping.md` 进行 IP 和端口规划。

## 2. PostgreSQL 16

### 2.1. 部署

PostgreSQL 可以采用Docker方式部署或在Kubernetes集群内部署。数据库设计详情见`docs/development/database_design.md`文档。

#### 2.1.1 Docker部署

使用Docker部署PostgreSQL是开发环境或单节点环境的简单选择：

```bash
# 创建持久化存储卷目录
mkdir -p /data/postgres/data

# 运行PostgreSQL实例
docker run -d --name postgres16 \
  -e POSTGRES_PASSWORD=changeThisToSecurePassword \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=ai_platform \
  -e POSTGRES_INITDB_ARGS="--data-checksums" \
  -p 5432:5432 \
  -v /data/postgres/data:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16

# 安装pgvector扩展（必须）
docker exec -it postgres16 bash -c "apt-get update && apt-get install -y postgresql-16-pgvector"

# 添加pgvector扩展到数据库
docker exec -it postgres16 bash -c "psql -U postgres -d ai_platform -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
```

要配置PostgreSQL以优化性能，可以添加自定义配置：

```bash
# 创建自定义postgresql.conf
cat > /data/postgres/custom-postgres.conf << EOF
# 连接设置
max_connections = 200

# 内存设置
shared_buffers = '1GB'
work_mem = '64MB'
maintenance_work_mem = '256MB'

# 日志设置
log_statement = 'ddl'
log_min_duration_statement = 1000

# 查询优化
random_page_cost = 1.1
effective_cache_size = '3GB'
EOF

# 重新启动容器并挂载自定义配置
docker stop postgres16
docker rm postgres16
docker run -d --name postgres16 \
  -e POSTGRES_PASSWORD=changeThisToSecurePassword \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=ai_platform \
  -e POSTGRES_INITDB_ARGS="--data-checksums" \
  -p 5432:5432 \
  -v /data/postgres/data:/var/lib/postgresql/data \
  -v /data/postgres/custom-postgres.conf:/etc/postgresql/postgresql.conf \
  --restart unless-stopped \
  postgres:16 -c 'config_file=/etc/postgresql/postgresql.conf'
```

#### 2.1.2 Docker Compose部署

使用Docker Compose简化部署：

```bash
# 创建docker-compose.yml
cat > docker-compose-postgres.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:16
    container_name: postgres16
    environment:
      - POSTGRES_PASSWORD=changeThisToSecurePassword
      - POSTGRES_USER=postgres
      - POSTGRES_DB=ai_platform
      - POSTGRES_INITDB_ARGS=--data-checksums
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./custom-postgres.conf:/etc/postgresql/postgresql.conf
    command: -c 'config_file=/etc/postgresql/postgresql.conf'
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
EOF

# 创建自定义配置文件
cat > custom-postgres.conf << EOF
# 连接设置
max_connections = 200

# 内存设置
shared_buffers = '1GB'
work_mem = '64MB'
maintenance_work_mem = '256MB'

# 日志设置
log_statement = 'ddl'
log_min_duration_statement = 1000

# 查询优化
random_page_cost = 1.1
effective_cache_size = '3GB'
EOF

# 启动服务
docker-compose -f docker-compose-postgres.yml up -d

# 安装pgvector扩展
docker exec -it postgres16 bash -c "apt-get update && apt-get install -y postgresql-16-pgvector"
docker exec -it postgres16 bash -c "psql -U postgres -d ai_platform -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
```

#### 2.1.3 Kubernetes部署 (推荐生产环境)

-   **Helm Chart**: 使用 Bitnami PostgreSQL Helm chart 或 Crunchy Data PostgreSQL Operator 是常见的选择。
    ```bash
    # 添加仓库
    helm repo add bitnami https://charts.bitnami.com/bitnami
    
    # 创建自定义配置文件values.yaml
    cat > postgres-values.yaml << EOF
    architecture: replication
    primary:
      persistence:
        size: 20Gi
        storageClass: "managed-premium"  # 根据您的集群环境调整
      resources:
        requests:
          memory: "2Gi"
          cpu: "1"
        limits:
          memory: "4Gi"
          cpu: "2"
    auth:
      postgresPassword: "changeThisToSecurePassword"
      username: "ai_platform_user"
      password: "changeThisToSecurePassword"
      database: "ai_platform"
    readReplicas:
      replicaCount: 2
      persistence:
        size: 20Gi
    postgresql:
      extraEnvVars:
        - name: POSTGRES_INITDB_ARGS
          value: "--data-checksums"
    # pgvector扩展必须
    primary:
      extraInitContainers:
        - name: pgvector-setup
          image: postgres:16
          command: ["/bin/bash", "-c"]
          args:
            - >
              apt-get update &&
              apt-get install -y postgresql-16-pgvector && 
              mkdir -p /tmp/pgvector &&
              echo "CREATE EXTENSION IF NOT EXISTS vector;" > /tmp/pgvector/init.sql
          volumeMounts:
            - name: pgvector-init
              mountPath: /tmp/pgvector
      extraVolumes:
        - name: pgvector-init
          emptyDir: {}
      extraVolumeMounts:
        - name: pgvector-init
          mountPath: /docker-entrypoint-initdb.d/pgvector-init.sql
          subPath: init.sql
    EOF
    
    # 安装 PostgreSQL
    helm install ai-postgres bitnami/postgresql -f postgres-values.yaml -n database
    ```

-   **持久化存储**: 确保配置了合适的 `PersistentVolumeClaim`，建议使用SSD存储类型提高I/O性能。

-   **pgvector 扩展**: 数据中台和向量搜索功能需要在 PostgreSQL 实例中安装和启用 `pgvector` 扩展。如果通过Helm Chart方式不能正确安装扩展，可以在安装后手动执行：
    ```bash
    kubectl exec -it ai-postgres-postgresql-0 -n database -- bash -c "apt-get update && apt-get install -y postgresql-16-pgvector"
    kubectl exec -it ai-postgres-postgresql-0 -n database -- bash -c "psql -U postgres -d ai_platform -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
    ```

#### 2.1.4 外部托管服务

-   如果使用云服务商提供的托管 PostgreSQL 服务(如 AWS RDS, Azure Database for PostgreSQL, Google Cloud SQL)，请遵循其官方文档进行创建和配置，并确保支持pgvector扩展。
    ```bash
    # 以AWS为例，确认pgvector兼容性并安装扩展
    aws rds create-db-parameter-group --db-parameter-group-name pgvector-params --db-parameter-group-family postgres16 --description "Parameter group for pgvector"
    aws rds modify-db-parameter-group --db-parameter-group-name pgvector-params --parameters "ParameterName=shared_preload_libraries,ParameterValue=pgvector,ApplyMethod=pending-reboot"
    aws rds modify-db-instance --db-instance-identifier your-instance-id --db-parameter-group-name pgvector-params --apply-immediately
    ```

### 2.2. 连接

-   **服务地址**:
    -   Docker部署: `localhost` 或主机IP地址
    -   Kubernetes 内部: `<service-name>.<namespace>.svc.cluster.local` (例如: `ai-postgres-postgresql.database.svc.cluster.local`)
    -   外部服务: 云服务商提供的连接端点。
-   **端口**: 默认为 `5432` (参考 `service_ip_port_mapping.md` 中的规划)。
-   **凭证**: 使用部署时设置的用户名和密码。建议使用 Kubernetes Secrets 管理敏感凭证。
-   **客户端工具**: `psql`, DBeaver, pgAdmin 等。

#### 2.2.1 命令行连接
```bash
# Docker部署连接
psql -h localhost -p 5432 -U postgres -d ai_platform

# Kubernetes部署连接（从集群内部）
kubectl exec -it ai-postgres-postgresql-0 -n database -- psql -U postgres -d ai_platform

# Kubernetes部署连接（从集群外部，需要端口转发）
kubectl port-forward svc/ai-postgres-postgresql -n database 5432:5432
# 然后在另一个终端：
psql -h localhost -p 5432 -U postgres -d ai_platform
```

#### 2.2.2 应用程序连接
使用相应语言的 PostgreSQL 客户端库进行连接：

- Python (psycopg2):
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="ai_platform",
    user="postgres",
    password="changeThisToSecurePassword"
)

# 创建游标对象
cur = conn.cursor()

# 执行查询
cur.execute("SELECT version();")

# 获取查询结果
version = cur.fetchone()
print(f"PostgreSQL版本: {version[0]}")

# 关闭连接
cur.close()
conn.close()
```

- Python (asyncpg，异步连接):
```python
import asyncio
import asyncpg

async def run():
    # 创建连接池
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        database="ai_platform",
        user="postgres",
        password="changeThisToSecurePassword",
        min_size=5,
        max_size=20
    )
    
    # 获取连接
    async with pool.acquire() as conn:
        version = await conn.fetchval("SELECT version();")
        print(f"PostgreSQL版本: {version}")
    
    # 关闭连接池
    await pool.close()

# 运行异步函数
asyncio.run(run())
```

### 2.3. 安全与配置

#### 2.3.1 基本安全配置

-   配置强密码策略:
    ```bash
    # 修改默认密码
    docker exec -it postgres16 psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'YourStrongPassword123!';"
    
    # 或在Kubernetes中
    kubectl exec -it ai-postgres-postgresql-0 -n database -- psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'YourStrongPassword123!';"
    ```

-   限制网络访问，仅允许必要的应用和服务连接:
    ```bash
    # Docker环境下，修改pg_hba.conf
    cat > /data/postgres/pg_hba.conf << EOF
    # TYPE  DATABASE        USER            ADDRESS                 METHOD
    local   all             postgres                                peer
    host    all             postgres        127.0.0.1/32            scram-sha-256
    host    ai_platform     ai_platform_user 10.0.0.0/8             scram-sha-256
    host    all             all             0.0.0.0/0               reject
    EOF
    
    # 重新挂载配置
    docker restart postgres16
    ```

-   定期备份:
    ```bash
    # Docker环境下的备份脚本
    cat > backup-postgres.sh << EOF
    #!/bin/bash
    TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="/backup/postgres"
    mkdir -p \$BACKUP_DIR
    
    docker exec -t postgres16 pg_dumpall -c -U postgres > \$BACKUP_DIR/postgres_\$TIMESTAMP.sql
    
    # 保留最近30天的备份
    find \$BACKUP_DIR -name "postgres_*.sql" -type f -mtime +30 -delete
    EOF
    
    chmod +x backup-postgres.sh
    
    # 添加到crontab
    echo "0 2 * * * /path/to/backup-postgres.sh" | crontab -
    ```

#### 2.3.2 性能优化配置

根据需求调整 `postgresql.conf` 中的配置参数:

```
# 连接设置
max_connections = 200                  # 根据系统负载调整

# 内存设置 (调整为实际服务器内存的比例)
shared_buffers = '1GB'                 # 服务器内存的25%
work_mem = '64MB'                      # 复杂查询的工作内存
maintenance_work_mem = '256MB'         # 维护操作的内存

# 日志设置
log_statement = 'ddl'                  # 记录所有DDL语句
log_min_duration_statement = 1000      # 记录执行时间超过1秒的查询

# 查询优化
random_page_cost = 1.1                 # SSD存储设置更低的随机页成本
effective_cache_size = '3GB'           # 系统缓存的估计值

# WAL (Write-Ahead Log)配置
wal_level = 'replica'                  # 支持逻辑复制
max_wal_size = '1GB'                   # 自动检查点间隔
min_wal_size = '80MB'

# 并行查询设置
max_parallel_workers_per_gather = 4    # 每次查询的最大并行工作者数
max_parallel_workers = 8               # 系统的最大并行工作者数
```

在Docker环境中应用配置:
```bash
docker restart postgres16
```

在Kubernetes环境中应用配置:
```bash
# 创建ConfigMap
kubectl create configmap postgres-config -n database --from-file=postgresql.conf=/path/to/postgresql.conf

# 修改deployment挂载ConfigMap (省略详细步骤，通常通过Helm Chart的values文件配置)
```

### 2.4. 数据库初始化

使用初始化脚本创建所需的Schema和基础表结构：

```bash
# 连接到PostgreSQL并执行初始化脚本
kubectl exec -it ai-postgres-postgresql-0 -- bash -c "psql -U postgres -d ai_platform -f /tmp/init.sql"
```

初始化脚本应该包含创建Schema（如 `public`, `auth`, `data_platform`, `algo_platform`, `model_platform`, `service_platform`）、表和索引的SQL语句，参照`database_design.md`中定义的表结构。
**重要**: 确保初始化脚本中包含以下命令以启用 `pgvector` 扩展：
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
这将为后续创建向量嵌入表（如 `data_platform.text_embeddings`）提供支持。

## 3. MongoDB 6.0

### 3.1. 部署

MongoDB主要用于存储日志数据、临时缓存和配置文件，详细集合设计见`database_design.md`。

#### 3.1.1 Docker部署

使用Docker部署MongoDB是开发环境或单节点环境的简单选择：

```bash
# 创建持久化存储卷目录
mkdir -p /data/mongodb/data

# 运行MongoDB实例
docker run -d --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=root \
  -e MONGO_INITDB_ROOT_PASSWORD=changeThisToSecurePassword \
  -p 27017:27017 \
  -v /data/mongodb/data:/data/db \
  --restart unless-stopped \
  mongo:6.0

# 创建应用数据库和用户
docker exec -it mongodb mongosh -u root -p changeThisToSecurePassword --eval '
  db = db.getSiblingDB("ai_platform");
  db.createUser({
    user: "ai_platform_user",
    pwd: "changeThisToSecurePassword",
    roles: [
      { role: "readWrite", db: "ai_platform" },
      { role: "dbAdmin", db: "ai_platform" }
    ]
  });
  print("数据库用户创建成功");
'
```

#### 3.1.2 Docker Compose部署

使用Docker Compose简化部署：

```bash
# 创建docker-compose.yml
cat > docker-compose-mongodb.yml << EOF
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: mongodb
    environment:
      - MONGO_INITDB_ROOT_USERNAME=root
      - MONGO_INITDB_ROOT_PASSWORD=changeThisToSecurePassword
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    restart: unless-stopped

volumes:
  mongodb_data:
    driver: local
EOF

# 创建初始化脚本
cat > mongo-init.js << EOF
db = db.getSiblingDB('ai_platform');

db.createUser({
  user: 'ai_platform_user',
  pwd: 'changeThisToSecurePassword',
  roles: [
    { role: 'readWrite', db: 'ai_platform' },
    { role: 'dbAdmin', db: 'ai_platform' }
  ]
});

// 创建系统日志集合
db.createCollection('system_logs');
db.system_logs.createIndex({ "timestamp": 1 });
db.system_logs.createIndex({ "level": 1, "timestamp": 1 });
db.system_logs.createIndex({ "service": 1, "timestamp": 1 });

// 创建配置集合
db.createCollection('configurations');
db.configurations.createIndex({ "component": 1, "environment": 1, "version": 1 });
db.configurations.createIndex({ "is_active": 1 });

// 创建任务状态缓存集合
db.createCollection('task_status_cache');
db.task_status_cache.createIndex({ "task_id": 1 });
db.task_status_cache.createIndex({ "status": 1, "last_updated": 1 });
db.task_status_cache.createIndex({ "task_type": 1, "status": 1 });
db.task_status_cache.createIndex({ "last_updated": 1 }, { expireAfterSeconds: 86400 });

print('MongoDB初始化完成');
EOF

# 启动服务
docker-compose -f docker-compose-mongodb.yml up -d
```

#### 3.1.3 Kubernetes部署 (推荐生产环境)

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
    helm install ai-mongodb bitnami/mongodb -f mongodb-values.yaml -n database
    ```
-   **副本集 (Replica Set)**: 强烈建议启用副本集以保证高可用性和数据冗余。
-   **持久化存储**: 确保配置了合适的 `PersistentVolumeClaim`。

#### 3.1.4 外部托管服务

-   使用 MongoDB Atlas 或其他云服务商提供的 MongoDB 服务。
    ```bash
    # 以MongoDB Atlas为例，使用atlas CLI创建集群
    atlas setup --skip-sample-data
    atlas clusters create myCluster --provider AWS --region us-east-1 --tier M10
    
    # 创建数据库用户
    atlas dbusers create --username ai_platform_user --password "changeThisToSecurePassword" --role readWriteAnyDatabase
    
    # 获取连接字符串
    atlas clusters connectionStrings describe myCluster
    ```

### 3.2. 连接

-   **服务地址**:
    -   Docker部署: `localhost` 或主机IP地址
    -   Kubernetes 内部: `<service-name>.<namespace>.svc.cluster.local` (例如: `ai-mongodb.database.svc.cluster.local`)
    -   外部服务: 云服务商提供的连接字符串。
-   **端口**: 默认为 `27017` (参考 `service_ip_port_mapping.md` 中的规划)。
-   **凭证**: 使用部署时设置的用户名和密码，并配置认证。
-   **客户端工具**: `mongosh`, MongoDB Compass 等。

#### 3.2.1 命令行连接
```bash
# Docker部署连接
mongosh mongodb://localhost:27017/ai_platform -u ai_platform_user -p "changeThisToSecurePassword"

# Kubernetes部署连接（从集群内部）
kubectl exec -it ai-mongodb-0 -n database -- mongosh mongodb://ai_platform_user:changeThisToSecurePassword@localhost:27017/ai_platform

# Kubernetes部署连接（从集群外部，需要端口转发）
kubectl port-forward svc/ai-mongodb -n database 27017:27017
# 然后在另一个终端：
mongosh mongodb://ai_platform_user:changeThisToSecurePassword@localhost:27017/ai_platform
```

#### 3.2.2 应用程序连接
使用相应语言的 MongoDB 驱动程序:

- Python (pymongo):
```python
from pymongo import MongoClient

# 创建MongoDB客户端连接
client = MongoClient(
    "mongodb://ai_platform_user:changeThisToSecurePassword@localhost:27017/ai_platform"
)

# 获取数据库
db = client.ai_platform

# 获取集合
system_logs = db.system_logs

# 插入文档示例
result = system_logs.insert_one({
    "timestamp": datetime.datetime.now(),
    "level": "INFO",
    "service": "user_service",
    "message": "User login successful",
    "details": {"user_id": "user123", "ip": "192.168.1.100"}
})

print(f"插入文档ID: {result.inserted_id}")

# 查询文档示例
logs = system_logs.find({"level": "INFO"}).limit(10)
for log in logs:
    print(log)

# 关闭连接
client.close()
```

### 3.3. 安全与配置

#### 3.3.1 基本安全配置

-   启用认证 (`auth`):
    ```bash
    # Docker环境下，修改MongoDB配置
    cat > /data/mongodb/mongod.conf << EOF
    security:
      authorization: enabled
    net:
      bindIp: 127.0.0.1,192.168.1.100  # 仅允许指定IP访问，请替换为您的实际IP
    EOF
    
    # 重新启动MongoDB容器
    docker restart mongodb
    ```

-   配置基于角色的访问控制 (RBAC):
    ```bash
    # 创建只读用户
    docker exec -it mongodb mongosh -u root -p changeThisToSecurePassword --eval '
      db = db.getSiblingDB("ai_platform");
      db.createUser({
        user: "readonly_user",
        pwd: "readOnlyPassword",
        roles: [
          { role: "read", db: "ai_platform" }
        ]
      });
      print("只读用户创建成功");
    '
    ```

-   定期备份:
    ```bash
    # Docker环境下的备份脚本
    cat > backup-mongodb.sh << EOF
    #!/bin/bash
    TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="/backup/mongodb"
    mkdir -p \$BACKUP_DIR
    
    docker exec -it mongodb mongodump --username root --password changeThisToSecurePassword --authenticationDatabase admin --db ai_platform --out /dump
    docker cp mongodb:/dump \$BACKUP_DIR/mongodb_\$TIMESTAMP
    
    # 保留最近30天的备份
    find \$BACKUP_DIR -type d -name "mongodb_*" -mtime +30 -exec rm -rf {} \;
    EOF
    
    chmod +x backup-mongodb.sh
    
    # 添加到crontab
    echo "0 3 * * * /path/to/backup-mongodb.sh" | crontab -
    ```

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

#### 4.1.1 Docker Compose部署（用于本地开发/测试）

Weaviate推荐使用Docker Compose进行部署，特别是当需要配置多个向量化模块时：

```bash
# 创建docker-compose.yml文件
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
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: "changeThisToSecurePassword"  # 请替换为安全的API密钥
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
      ENABLE_CUDA: "0"  # 设置为1启用GPU
      NVIDIA_VISIBLE_DEVICES: "all"  # 使用GPU时需要
    volumes:
      - transformer_cache:/root/.cache
      
  img2vec-neural:
    image: semitechnologies/img2vec-neural:resnet50
    container_name: img2vec-neural
    restart: unless-stopped
    environment:
      ENABLE_CUDA: "0"  # 设置为1启用GPU

volumes:
  weaviate_data:
    driver: local
  transformer_cache:
    driver: local
EOF

# 启动服务
docker-compose -f docker-compose-weaviate.yml up -d
```

#### 4.1.2 Kubernetes部署 (推荐生产环境)

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
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: "changeThisToYourApiKey" # 请务必修改为安全的API Key
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
    modules:
      - name: text2vec-transformers
        image: semitechnologies/transformers-inference:sentence-transformers-multilingual-e5-large
      - name: img2vec-neural # 添加 img2vec-neural 模块以支持图像向量化
        image: semitechnologies/img2vec-neural:resnet50 # 您可以根据需求选择不同的模型标签
      - name: generative-openai
        image: semitechnologies/generative-openai:1.4.0
    replicaCount: 1
    EOF
    
    # 安装Weaviate
    helm install ai-weaviate weaviate/weaviate -f weaviate-values.yaml -n database
    ```
-   **模块 (Modules)**: Weaviate 支持多种模块，根据实际需求选择：
    - `text2vec-transformers`: 文本向量化
    - `generative-openai`: 生成式AI功能
    - `img2vec-neural`: 图像向量化
-   **持久化存储**: 确保配置了合适的 `PersistentVolumeClaim`。

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
# 创建schema配置文件 schema.json
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

# 使用curl应用schema (请确保WEAVIATE_API_KEY环境变量已设置或直接替换API Key)
# 注意: 如果您的Weaviate服务端口与默认的8080不同 (例如8088), 请相应修改URL。
curl -X POST \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${WEAVIATE_API_KEY:-yourWeaviateApiKey}" \\
  -d @schema.json \\
  http://ai-weaviate.default.svc.cluster.local:8080/v1/schema
```

## 5. Redis 7.0

### 5.1. 部署

Redis用于缓存和临时数据存储，提高系统性能，详细键设计见`database_design.md`。

#### 5.1.1 Docker部署

使用Docker部署Redis是开发环境或单节点环境的简单选择：

```bash
# 创建持久化存储卷目录
mkdir -p /data/redis/data

# 创建Redis配置文件
cat > /data/redis/redis.conf << EOF
# 基本配置
port 6379
bind 0.0.0.0
protected-mode yes
requirepass changeThisToSecurePassword

# 持久化配置
dir /data
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# 内存管理
maxmemory 1gb
maxmemory-policy allkeys-lru

# 连接设置
timeout 0
tcp-keepalive 300
EOF

# 运行Redis实例
docker run -d --name redis \
  -p 6379:6379 \
  -v /data/redis/data:/data \
  -v /data/redis/redis.conf:/usr/local/etc/redis/redis.conf \
  --restart unless-stopped \
  redis:7.0 redis-server /usr/local/etc/redis/redis.conf
```

#### 5.1.2 Docker Compose部署

使用Docker Compose简化部署：

```bash
# 创建docker-compose.yml
cat > docker-compose-redis.yml << EOF
version: '3.8'

services:
  redis:
    image: redis:7.0
    container_name: redis
    command: redis-server /usr/local/etc/redis/redis.conf
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    restart: unless-stopped

volumes:
  redis_data:
    driver: local
EOF

# 创建Redis配置文件
cat > redis.conf << EOF
# 基本配置
port 6379
bind 0.0.0.0
protected-mode yes
requirepass changeThisToSecurePassword

# 持久化配置
dir /data
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# 内存管理
maxmemory 1gb
maxmemory-policy allkeys-lru

# 连接设置
timeout 0
tcp-keepalive 300
EOF

# 启动服务
docker-compose -f docker-compose-redis.yml up -d
```

#### 5.1.3 Kubernetes部署 (推荐生产环境)

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
    helm install ai-redis bitnami/redis -f redis-values.yaml -n database
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

#### 6.1.1 Docker Compose部署（开发/测试环境）

对于开发或测试环境，可以使用Docker Compose部署Kafka和Zookeeper：

```bash
# 创建docker-compose文件
cat > docker-compose-kafka.yml << EOF
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.3.2
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
      - zookeeper_log:/var/lib/zookeeper/log
    restart: unless-stopped

  kafka:
    image: confluentinc/cp-kafka:7.3.2
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9094:9094"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9094
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_JMX_PORT: 9101
      KAFKA_JMX_HOSTNAME: localhost
    volumes:
      - kafka_data:/var/lib/kafka/data
    restart: unless-stopped

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    depends_on:
      - kafka
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181
    restart: unless-stopped

volumes:
  zookeeper_data:
    driver: local
  zookeeper_log:
    driver: local
  kafka_data:
    driver: local
EOF

# 启动服务
docker-compose -f docker-compose-kafka.yml up -d

# 创建主题
docker exec -it kafka kafka-topics --create --topic data-ingestion --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
docker exec -it kafka kafka-topics --create --topic model-events --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
docker exec -it kafka kafka-topics --create --topic system-logs --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
```

#### 6.1.2 Kubernetes部署 (推荐生产环境)

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
    helm install ai-kafka bitnami/kafka -f kafka-values.yaml -n database
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
