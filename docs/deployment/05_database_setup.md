# AI 中台 - 数据库系统概览

## 概述

本文档提供 AI 中台项目所用数据库系统的简要概览。所有详细的部署指南和配置说明均位于 `database_deployment` 目录下的专题文档中。

## 数据库架构

AI 中台采用多数据库架构，以满足不同类型数据的存储和处理需求：

| 数据库 | 版本 | 主要用途 | 详细文档 |
|-------|------|---------|----------|
| PostgreSQL | 16 | 结构化数据 | [部署指南](./database_deployment/01_postgresql_deployment.md) |
| MongoDB | 6.0 | 半结构化数据 | [部署指南](./database_deployment/02_mongodb_deployment.md) |
| Weaviate | 1.22 | 向量数据 | [部署指南](./database_deployment/03_weaviate_deployment.md) |
| Redis | 7.0 | 缓存系统 | [部署指南](./database_deployment/04_redis_deployment.md) |
| Kafka | 3.6 | 消息队列 | [部署指南](./database_deployment/05_kafka_deployment.md) |

## 数据分布

- **PostgreSQL**: 存储模型元数据、用户权限和系统配置
- **MongoDB**: 存储日志数据、配置文件和临时缓存
- **Weaviate**: 存储向量嵌入，支持 RAG 应用
- **Redis**: 提供缓存、会话管理和实时数据处理
- **Kafka**: 处理消息队列和数据流

## 部署方式

根据环境和需求，可选择以下部署方式：

- **直接安装**: 适用于开发环境
- **Docker 容器**: 适用于测试和小型生产环境
- **Kubernetes**: 推荐用于生产环境（详见 `03_storage_systems_kubernetes.md`）

## 管理与维护

| 管理方面 | 详细文档 |
|---------|----------|
| 监控与日常维护 | [监控与维护](./database_deployment/06_monitoring_maintenance.md) |
| 高可用性配置 | [高可用性与容灾](./database_deployment/07_high_availability.md) |
| 备份与恢复策略 | [备份与恢复](./database_deployment/08_backup_restore.md) |

## 资源规划参考

| 数据库 | CPU | 内存 | 存储 |
|-------|-----|------|------|
| PostgreSQL | 4核 | 8GB | SSD, 50GB+ |
| MongoDB | 2核 | 4GB | SSD, 20GB+ |
| Weaviate | 4核 | 8GB | SSD, 20GB+ |
| Redis | 2核 | 4GB | SSD, 10GB+ |
| Kafka | 4核 | 8GB | SSD, 50GB+ |

## 后续部署步骤

完成数据库部署后，建议按以下顺序继续：

1. 部署权限管理系统 (`07_permission_management.md`)
2. 部署 Django REST 后端 (`06_django_rest_setup.md`)
3. 部署 NodeJS 前端 (`08_nodejs_setup.md`)

更多数据库设计详情，请参考 `docs/development/database_design.md`。
    helm repo add bitnami https://charts.bitnami.com/bitnami
    
    # 创建自定义配置文件values.yaml
    cat > postgres-values.yaml << EOF
    architecture: replication
    primary:
      persistence:
        size: 20Gi
        storageClass: "local-storage"  # 使用本地存储，根据服务器环境调整
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

-   **为物理服务器配置本地存储类**:
    如果您在自己的服务器上运行Kubernetes集群，您可能需要配置本地存储类：
    
    ```bash
    # 创建本地路径存储
    sudo mkdir -p /mnt/postgres-data /mnt/mongodb-data /mnt/redis-data /mnt/kafka-data /mnt/weaviate-data
    
    # 创建StorageClass清单文件
    cat > local-storage-class.yaml << EOF
    apiVersion: storage.k8s.io/v1
    kind: StorageClass
    metadata:
      name: local-storage
    provisioner: kubernetes.io/no-provisioner
    volumeBindingMode: WaitForFirstConsumer
    EOF
    
    # 创建持久卷
    cat > postgres-pv.yaml << EOF
    apiVersion: v1
    kind: PersistentVolume
    metadata:
      name: postgres-pv
    spec:
      capacity:
        storage: 20Gi
      volumeMode: Filesystem
      accessModes:
      - ReadWriteOnce
      persistentVolumeReclaimPolicy: Retain
      storageClassName: local-storage
      local:
        path: /mnt/postgres-data
      nodeAffinity:
        required:
          nodeSelectorTerms:
          - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
              - node01  # 替换为实际的节点名称
    EOF
    
    # 应用配置
    kubectl apply -f local-storage-class.yaml
    kubectl apply -f postgres-pv.yaml
    ```
    
    对MongoDB、Redis和其他数据库也创建类似的PV。

-   **pgvector 扩展**: 数据中台和向量搜索功能需要在 PostgreSQL 实例中安装和启用 `pgvector` 扩展。如果通过Helm Chart方式不能正确安装扩展，可以在安装后手动执行：
    ```bash
    kubectl exec -it ai-postgres-postgresql-0 -n database -- bash -c "apt-get update && apt-get install -y postgresql-16-pgvector"
    kubectl exec -it ai-postgres-postgresql-0 -n database -- bash -c "psql -U postgres -d ai_platform -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
    ```

#### 2.1.4 直接安装（裸机服务器）

如果您希望直接在物理服务器或虚拟机上安装PostgreSQL，而不使用容器化技术，可以按照以下步骤进行：

```bash
# 更新包列表
sudo apt update

# 安装PostgreSQL 16
sudo apt install -y postgresql-16 postgresql-contrib-16

# 安装pgvector扩展
sudo apt install -y postgresql-16-pgvector

# 启动PostgreSQL服务
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 配置PostgreSQL允许远程访问（根据需要）
sudo nano /etc/postgresql/16/main/postgresql.conf
# 修改listen_addresses = '*'

sudo nano /etc/postgresql/16/main/pg_hba.conf
# 添加: host ai_platform ai_platform_user 0.0.0.0/0 md5

# 重启PostgreSQL以应用更改
sudo systemctl restart postgresql

# 创建数据库和用户
sudo -u postgres psql -c "CREATE DATABASE ai_platform;"
sudo -u postgres psql -c "CREATE USER ai_platform_user WITH ENCRYPTED PASSWORD 'strongPassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_platform TO ai_platform_user;"
sudo -u postgres psql -d ai_platform -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

配置高性能设置:

```bash
# 编辑PostgreSQL配置文件
sudo nano /etc/postgresql/16/main/postgresql.conf

# 添加以下配置（根据服务器硬件调整）
max_connections = 200
shared_buffers = '1GB'                 # 服务器内存的25%
work_mem = '64MB'
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

### 2.4. 数据库初始化与迁移

#### 2.4.1 基本初始化脚本

以下创建一个完整的初始化脚本，创建所有所需的Schema和基础表结构：

```bash
# 创建初始化脚本
cat > init_ai_platform_db.sql << 'EOF'
-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建各个模式
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS data_platform;
CREATE SCHEMA IF NOT EXISTS algo_platform;
CREATE SCHEMA IF NOT EXISTS model_platform;
CREATE SCHEMA IF NOT EXISTS service_platform;

-- Auth模式下的表结构
CREATE TABLE IF NOT EXISTS auth.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    organization_id INTEGER
);

CREATE TABLE IF NOT EXISTS auth.groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    description TEXT
);

-- 其他表结构略...根据database_design.md中的定义添加

-- 创建索引
CREATE INDEX idx_users_username ON auth.users(username);
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_org_id ON auth.users(organization_id);

-- 创建初始管理员用户 (密码为 admin123，实际使用请修改)
INSERT INTO auth.users (username, email, password_hash, is_active, is_superuser)
VALUES ('admin', 'admin@example.com', '$2b$12$ZvObSUln.TpZ9vOJUPm6mOSnVkB.Zh6qsJWhjWYQOX5fT4QL96lxW', true, true)
ON CONFLICT (username) DO NOTHING;

-- 数据平台初始化设置
CREATE TABLE IF NOT EXISTS data_platform.data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    source_type VARCHAR(50) NOT NULL,
    connection_info JSONB NOT NULL,
    created_by INTEGER REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- 向量表
CREATE TABLE IF NOT EXISTS data_platform.text_embeddings (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER,
    record_id VARCHAR(100),
    text_content TEXT,
    embedding vector(1536), -- 使用OpenAI ada模型的1536维向量
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建向量索引
CREATE INDEX idx_text_embeddings_vector ON data_platform.text_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
EOF

# 在Docker环境执行初始化脚本
docker exec -i postgres16 psql -U postgres -d ai_platform < init_ai_platform_db.sql

# 或在Kubernetes环境执行初始化脚本
kubectl exec -i ai-postgres-postgresql-0 -n database -- bash -c "cat > /tmp/init.sql" < init_ai_platform_db.sql
kubectl exec -it ai-postgres-postgresql-0 -n database -- bash -c "psql -U postgres -d ai_platform -f /tmp/init.sql"
```

#### 2.4.2 数据迁移与版本控制

在生产环境中，推荐使用数据库迁移工具（如Flyway或Django Migrations）来管理数据库结构的版本控制：

```bash
# 使用Flyway进行数据库迁移
mkdir -p /opt/flyway/sql
cp init_ai_platform_db.sql /opt/flyway/sql/V1__initial_schema.sql

# 准备Flyway配置
cat > /opt/flyway/conf/flyway.conf << 'EOF'
flyway.url=jdbc:postgresql://localhost:5432/ai_platform
flyway.user=postgres
flyway.password=changeThisToSecurePassword
flyway.locations=filesystem:/opt/flyway/sql
flyway.baselineOnMigrate=true
EOF

# 运行Flyway迁移
docker run --rm -v /opt/flyway/conf:/flyway/conf -v /opt/flyway/sql:/flyway/sql flyway/flyway:9.20 migrate
```

#### 2.4.3 备份原有数据和恢复

如果您需要迁移现有数据到新部署的系统：

```bash
# 从源系统导出数据
pg_dump -U postgres -h source_db_host -F c -f ai_platform_backup.dump ai_platform

# 复制到目标系统
scp ai_platform_backup.dump user@target_host:/tmp/

# 在目标系统恢复
pg_restore -U postgres -d ai_platform -v /tmp/ai_platform_backup.dump
```

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
      database: "ai_platform"    persistence:
      size: 20Gi
      storageClass: "local-storage"  # 使用本地存储，或根据实际环境调整为您的存储类
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

#### 3.1.4 直接安装（裸机服务器）

如果您希望直接在物理服务器或虚拟机上安装MongoDB，而不使用容器化技术，可以按照以下步骤进行：

```bash
# 安装MongoDB社区版
# 导入公钥
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# 创建MongoDB源文件
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# 更新软件包列表
sudo apt update

# 安装MongoDB
sudo apt install -y mongodb-org

# 启动MongoDB服务
sudo systemctl enable mongod
sudo systemctl start mongod

# 配置MongoDB允许远程访问
sudo nano /etc/mongod.conf
# 将bindIp改为 0.0.0.0 或者特定IP
# 添加安全配置
# security:
#   authorization: enabled

# 重启MongoDB以应用更改
sudo systemctl restart mongod

# 创建管理员用户
mongosh --eval 'db.getSiblingDB("admin").createUser({user: "admin", pwd: "securePassword", roles: ["root"]})'

# 创建应用数据库和用户
mongosh --eval 'db.getSiblingDB("ai_platform").createUser({user: "ai_platform_user", pwd: "securePassword", roles: [{role: "readWrite", db: "ai_platform"}, {role: "dbAdmin", db: "ai_platform"}]})'
```

配置高性能设置：

```bash
# 编辑MongoDB配置文件
sudo nano /etc/mongod.conf

# 添加或修改以下配置（根据服务器硬件调整）
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2  # 设置为服务器RAM的50%左右
      
# 设置副本集（即使在单节点环境下，也有助于未来扩展）
replication:
  replSetName: "rs0"
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

### 5.2. 连接

-   **服务地址**: `ai-redis-master.default.svc.cluster.local` (主节点)
-   **Sentinel**: `ai-redis-headless.default.svc.cluster.local:26379` (Sentinel)
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

### 8.1 监控系统配置

#### 8.1.1 Prometheus与Grafana部署

在自有服务器上部署监控系统：

```bash
# 创建监控配置目录
mkdir -p /opt/monitoring/prometheus /opt/monitoring/grafana

# 创建Prometheus配置
cat > /opt/monitoring/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongodb-exporter:9216']
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka-exporter:9308']
EOF

# 部署监控服务
docker-compose -f docker-compose-monitoring.yml up -d
```

监控服务Docker Compose配置：

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:v2.42.0
    container_name: prometheus
    volumes:
      - /opt/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    restart: unless-stopped
    
  grafana:
    image: grafana/grafana:9.4.7
    container_name: grafana
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=changeThisToSecurePassword
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    restart: unless-stopped
    depends_on:
      - prometheus
      
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.12.0
    container_name: postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:password@postgres16:5432/postgres?sslmode=disable"
    ports:
      - "9187:9187"
    restart: unless-stopped
    
  mongodb-exporter:
    image: percona/mongodb_exporter:0.34
    container_name: mongodb-exporter
    command:
      - '--mongodb.uri=mongodb://ai_platform_user:password@mongodb:27017/ai_platform'
    ports:
      - "9216:9216"
    restart: unless-stopped
    
  redis-exporter:
    image: oliver006/redis_exporter:v1.46.0
    container_name: redis-exporter
    environment:
      REDIS_ADDR: "redis:6379"
      REDIS_PASSWORD: "changeThisToSecurePassword"
    ports:
      - "9121:9121"
    restart: unless-stopped
    
  kafka-exporter:
    image: danielqsj/kafka-exporter:v1.7.0
    container_name: kafka-exporter
    command:
      - '--kafka.server=kafka:9092'
    ports:
      - "9308:9308"
    restart: unless-stopped
    
volumes:
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

#### 8.1.2 自定义告警配置

为数据库服务配置关键指标告警：

```bash
# 创建告警规则配置
cat > /opt/monitoring/prometheus/alert_rules.yml << EOF
groups:
- name: database-alerts
  rules:
  - alert: PostgreSQLHighConnections
    expr: sum(pg_stat_activity_count{datname="ai_platform"}) > 150
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "PostgreSQL 连接数过高"
      description: "数据库 ai_platform 连接数已超过150，当前值: {{ $value }}"
      
  - alert: RedisHighMemoryUsage
    expr: redis_memory_used_bytes / redis_memory_max_bytes * 100 > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis 内存使用率过高"
      description: "Redis 内存使用率已超过80%，当前值: {{ $value }}%"
      
  - alert: MongoDBReplicationLag
    expr: mongodb_replset_member_optime_date{state="SECONDARY"} - on(set) group_left() mongodb_replset_member_optime_date{state="PRIMARY"} > 60
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "MongoDB 复制延迟"
      description: "MongoDB 副本集复制延迟超过60秒，当前值: {{ $value }}s"
EOF
```

### 8.2 性能调优

#### 8.2.1 PostgreSQL性能调优

针对AI中台特定工作负载的PostgreSQL优化:

```bash
# 创建性能优化配置
cat > /etc/postgresql/16/main/conf.d/tuning.conf << EOF
# 内存设置 - 根据实际服务器内存调整
shared_buffers = '4GB'               # 服务器内存的25%
effective_cache_size = '12GB'        # 服务器内存的50-75%
work_mem = '128MB'                   # 复杂查询的工作内存，根据并发查询数调整
maintenance_work_mem = '512MB'       # 维护操作的内存
max_worker_processes = 8             # CPU核心数
max_parallel_workers_per_gather = 4  # CPU核心数的一半
max_parallel_workers = 8             # CPU核心数

# 针对向量搜索优化
random_page_cost = 1.1               # 使用SSD时设置更低
default_statistics_target = 500      # 提高统计信息精度

# WAL配置
wal_buffers = '16MB'                 # 默认是shared_buffers的1/32
checkpoint_timeout = '15min'         # 较长的检查点间隔减少I/O峰值
checkpoint_completion_target = 0.9   # 拉长检查点完成时间，减轻I/O影响
max_wal_size = '4GB'                 # WAL大小限制

# 查询优化
enable_partitionwise_join = on       # 针对分区表优化
enable_partitionwise_aggregate = on  # 针对分区表优化
EOF
```

#### 8.2.2 MongoDB性能调优

```bash
# 创建MongoDB性能配置
cat > /etc/mongod.conf.d/tuning.conf << EOF
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4  # 调整为服务器内存的50%
      journalCompressor: zstd  # 更高效的压缩算法
      directoryForIndexes: true  # 索引单独存储
    
operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100

net:
  maxIncomingConnections: 2000
  
replication:
  oplogSizeMB: 2048  # 增加oplog大小

setParameter:
  internalQueryExecMaxBlockingSortBytes: 104857600  # 100MB，防止大型排序操作报错
EOF
```

#### 8.2.3 Redis性能调优

```bash
# Redis优化配置
cat > /etc/redis/redis.conf.d/tuning.conf << EOF
# 内存管理
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 10

# 持久化
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# 连接和网络
tcp-backlog 511
timeout 0
tcp-keepalive 300
EOF
```

### 8.3 备份策略

创建自动化备份脚本，在物理服务器环境中使用:

```bash
# 创建备份目录
mkdir -p /backup/postgres /backup/mongodb /backup/redis

# 创建备份脚本
cat > /opt/ai-platform/database_backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT="/backup"
RETENTION_DAYS=30

# PostgreSQL备份
echo "开始备份PostgreSQL..."
if docker ps | grep -q postgres16; then
    docker exec postgres16 pg_dumpall -U postgres | gzip > $BACKUP_ROOT/postgres/postgres_$DATE.sql.gz
else 
    PGPASSWORD="yourPassword" pg_dumpall -h localhost -U postgres | gzip > $BACKUP_ROOT/postgres/postgres_$DATE.sql.gz
fi

# MongoDB备份
echo "开始备份MongoDB..."
if docker ps | grep -q mongodb; then
    docker exec mongodb mongodump --username ai_platform_user --password "changeThisToSecurePassword" --authenticationDatabase ai_platform --out /tmp/dump
    docker cp mongodb:/tmp/dump $BACKUP_ROOT/mongodb/mongodb_$DATE
else
    mongodump --uri="mongodb://ai_platform_user:changeThisToSecurePassword@localhost:27017/ai_platform" --out=$BACKUP_ROOT/mongodb/mongodb_$DATE
fi

# Redis备份
echo "开始备份Redis..."
if docker ps | grep -q redis; then
    docker exec redis redis-cli -a "changeThisToSecurePassword" SAVE
    docker cp redis:/data/dump.rdb $BACKUP_ROOT/redis/redis_$DATE.rdb
else
    redis-cli -a "changeThisToSecurePassword" SAVE
    cp /var/lib/redis/dump.rdb $BACKUP_ROOT/redis/redis_$DATE.rdb
fi

# 清理过期备份
echo "清理过期备份..."
find $BACKUP_ROOT/postgres -name "postgres_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
find $BACKUP_ROOT/mongodb -type d -name "mongodb_*" -mtime +$RETENTION_DAYS -exec rm -rf {} \;
find $BACKUP_ROOT/redis -name "redis_*.rdb" -type f -mtime +$RETENTION_DAYS -delete

echo "备份完成，时间: $(date)"
EOF

chmod +x /opt/ai-platform/database_backup.sh

# 添加到crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/ai-platform/database_backup.sh") | crontab -
```

### 8.4 维护计划

建立物理服务器数据库维护计划：

1. **定期维护时间表**:
   - 每周低峰期(如周日凌晨2:00-4:00)进行常规维护
   - 每月一次大型维护(如月末周日凌晨)

2. **常规维护任务**:
   ```bash
   # PostgreSQL维护脚本
   cat > /opt/ai-platform/pg_maintenance.sh << 'EOF'
   #!/bin/bash
   # 日志文件
   LOG_FILE="/var/log/ai-platform/db_maintenance.log"
   
   echo "$(date): 开始PostgreSQL维护..." >> $LOG_FILE
   
   # 连接到PostgreSQL
   PGPASSWORD=yourPassword psql -U postgres -d ai_platform << EOF_SQL
   -- 更新统计信息
   ANALYZE VERBOSE;
   
   -- 索引维护
   REINDEX DATABASE ai_platform;
   
   -- 回收空间
   VACUUM FULL VERBOSE;
   
   -- 清理未使用的索引
   SELECT
     indexrelid::regclass as index_name,
     relid::regclass as table_name,
     'DROP INDEX ' || indexrelid::regclass || ';' as drop_statement
   FROM pg_stat_user_indexes
   WHERE idx_scan = 0 AND idx_tup_read = 0 AND idx_tup_fetch = 0;
   EOF_SQL
   
   echo "$(date): PostgreSQL维护完成" >> $LOG_FILE
   EOF
   
   chmod +x /opt/ai-platform/pg_maintenance.sh
   ```

3. **系统核心表监控**:
   ```bash
   # 创建系统表监控脚本
   cat > /opt/ai-platform/db_table_monitor.sh << 'EOF'
   #!/bin/bash
   # 监控重要表的大小和增长速率
   PGPASSWORD=yourPassword psql -U postgres -d ai_platform -c "
   SELECT
     nspname || '.' || relname AS table,
     pg_size_pretty(pg_total_relation_size(C.oid)) AS total_size,
     pg_size_pretty(pg_relation_size(C.oid)) AS table_size,
     pg_size_pretty(pg_total_relation_size(C.oid) - pg_relation_size(C.oid)) AS index_size
   FROM pg_class C
   LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
   WHERE nspname IN ('auth', 'data_platform', 'algo_platform', 'model_platform', 'service_platform')
   AND C.relkind = 'r'
   ORDER BY pg_total_relation_size(C.oid) DESC
   LIMIT 20;" > /var/log/ai-platform/table_sizes.log
   EOF
   
   chmod +x /opt/ai-platform/db_table_monitor.sh
   
   # 添加到crontab
   (crontab -l 2>/dev/null; echo "0 3 * * 0 /opt/ai-platform/pg_maintenance.sh") | crontab -
   (crontab -l 2>/dev/null; echo "0 0 * * * /opt/ai-platform/db_table_monitor.sh") | crontab -
   ```

4. **性能指标监控与报警**:
   - 集成Prometheus和Grafana进行可视化监控
   - 建立关键指标自动报警机制
   - 记录性能基线，定期对比

## 9. 高可用性和容灾配置

### 9.1 PostgreSQL高可用配置

针对物理服务器环境的多节点部署：

```bash
# PostgreSQL主节点配置
sudo nano /etc/postgresql/16/main/postgresql.conf

# 添加以下配置
listen_addresses = '*'
wal_level = 'replica'
max_wal_senders = 10
wal_keep_size = '1GB'

# 配置pg_hba.conf允许复制连接
sudo nano /etc/postgresql/16/main/pg_hba.conf
# 添加以下行
host replication replicator 192.168.1.0/24 md5

# 在主节点创建复制用户
sudo -u postgres psql -c "CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'secure_password';"

# 备节点配置
sudo pg_basebackup -h 192.168.1.10 -D /var/lib/postgresql/16/main -U replicator -P -v

# 备节点postgresql.conf配置
echo "primary_conninfo = 'host=192.168.1.10 port=5432 user=replicator password=secure_password'" | sudo tee -a /etc/postgresql/16/main/postgresql.conf
touch /var/lib/postgresql/16/main/standby.signal

# 重启备节点PostgreSQL
sudo systemctl restart postgresql
```

### 9.2 MongoDB副本集配置

```bash
# 在所有节点的/etc/mongod.conf中添加以下配置
replication:
   replSetName: "rs0"
   
# 重启MongoDB服务
sudo systemctl restart mongod

# 在主节点初始化副本集
mongosh --eval 'rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "192.168.1.10:27017", priority: 2 },
    { _id: 1, host: "192.168.1.11:27017", priority: 1 },
    { _id: 2, host: "192.168.1.12:27017", arbiterOnly: true }
  ]
})'
```

### 9.3 异地容灾备份

```bash
# 创建自动备份并同步到异地服务器的脚本
cat > /opt/backup-sync.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/$DATE"
REMOTE_SERVER="backup-server.local"
REMOTE_DIR="/mnt/backup"

# 创建备份目录
mkdir -p $BACKUP_DIR

# PostgreSQL备份
pg_dumpall -U postgres > $BACKUP_DIR/postgres_full.sql
gzip $BACKUP_DIR/postgres_full.sql

# MongoDB备份
mongodump --out=$BACKUP_DIR/mongodb

# 同步到异地服务器
rsync -avz --delete $BACKUP_DIR $REMOTE_SERVER:$REMOTE_DIR/

# 保留30天的备份
find /backup -type d -name "20*" -mtime +30 | xargs rm -rf
EOF

chmod +x /opt/backup-sync.sh

# 添加到crontab
echo "0 2 * * * /opt/backup-sync.sh" | sudo tee -a /etc/crontab
```

## 10. 总结与最佳实践

### 10.1 自有服务器部署方案总结

在自有物理服务器环境部署AI中台核心数据库时，主要有以下部署方案：

1. **直接安装方案**:
   - 适用于小规模部署或资源有限的情况
   - 管理简单，易于维护
   - 缺点：扩展性和弹性不足

2. **Docker容器化方案**:
   - 适用于单节点或小型集群部署
   - 易于管理和版本控制
   - 隔离性好，便于升级和回滚
   - 建议在开发、测试和小规模生产环境中使用

3. **Kubernetes部署方案**:
   - 适用于多节点大型生产环境
   - 提供自动扩缩容、自动恢复等高级功能
   - 资源管理更精细
   - 管理较复杂，需要更多专业知识

### 10.2 数据库选择建议

- **PostgreSQL**: 核心关系型数据库，用于存储结构化数据
- **MongoDB**: 半结构化数据、配置、日志数据存储
- **Weaviate**: AI应用的向量数据库，支持语义检索
- **Redis**: 缓存和会话管理
- **Kafka**: 消息队列和数据流处理

### 10.3 部署策略建议

1. **分阶段部署**:
   - 第一阶段：在单服务器上通过Docker部署基本数据服务，验证功能
   - 第二阶段：迁移到多节点Kubernetes集群
   - 第三阶段：实现跨区域高可用部署

2. **资源分配指南**:
   | 数据库     | CPU最小要求 | 内存最小要求 | 存储推荐配置               |
   |------------|-------------|--------------|----------------------------|
   | PostgreSQL | 4核         | 8GB          | SSD, 50GB+                 |
   | MongoDB    | 2核         | 4GB          | SSD, 20GB+                 |
   | Weaviate   | 4核         | 8GB          | SSD, 20GB+                 |
   | Redis      | 2核         | 4GB          | SSD, 10GB+                 |
   | Kafka      | 4核         | 8GB          | SSD, 50GB+ (根据数据量调整)|

3. **网络配置**:
   - 数据库服务之间推荐使用内部专用网络
   - 启用防火墙，仅开放必要端口
   - 考虑使用TLS/SSL加密所有数据库连接

4. **物理服务器分布**:
   - 核心数据库服务应使用专用物理服务器
   - 关键数据库服务应跨机架部署
   - 考虑数据存储和计算资源分离

### 10.4 下一步部署建议

完成核心数据库的部署后，建议按照以下顺序继续进行AI中台的部署工作：

1. 部署权限管理系统，参考 `07_permission_management.md`
2. 部署Django REST后端服务，参考 `06_django_rest_setup.md`
3. 部署NodeJS前端服务，参考 `08_nodejs_setup.md`
4. 配置监控与日志系统，确保能够有效监控整个平台的运行状态

在部署过程中，持续关注以下方面：

- 安全性：定期更新密码，审计访问日志
- 性能：监控系统资源使用情况，及时优化配置
- 可用性：定期测试备份恢复流程和故障转移机制
- 扩展性：随业务需求增长，适时扩展资源

---

**备注**: 本部署文档中的配置参数仅为参考值，请根据实际物理服务器的硬件配置和业务需求进行适当调整。在生产环境部署前，强烈建议在测试环境中完成充分测试。

**后续步骤**:
完成核心数据库的部署和配置后，可以继续部署应用层的具体服务，并配置它们连接到这些数据库实例。请参考`docs/development/database_design.md`了解各应用使用的数据库表设计和访问模式。
