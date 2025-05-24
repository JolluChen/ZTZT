# PostgreSQL 16 部署指南

本文档详细说明如何在物理服务器环境中部署和配置 PostgreSQL 16 数据库服务，用于 AI 中台项目。

## 1. 部署选项

PostgreSQL 可以采用多种方式部署，根据您的环境和需求选择合适的方式。

### 1.1 Docker 部署

使用 Docker 部署 PostgreSQL 是开发环境或单节点环境的简单选择：

```bash
# 创建持久化存储卷目录
mkdir -p /data/postgres/data

# 运行 PostgreSQL 实例
docker run -d --name postgres16 \
  -e POSTGRES_PASSWORD=changeThisToSecurePassword \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=ai_platform \
  -e POSTGRES_INITDB_ARGS="--data-checksums" \
  -p 5432:5432 \
  -v /data/postgres/data:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16

# 安装 pgvector 扩展（必须）
docker exec -it postgres16 bash -c "apt-get update && apt-get install -y postgresql-16-pgvector"

# 添加 pgvector 扩展到数据库
docker exec -it postgres16 bash -c "psql -U postgres -d ai_platform -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
```

配置 PostgreSQL 以优化性能：

```bash
# 创建自定义 postgresql.conf
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

### 1.2 Docker Compose 部署

使用 Docker Compose 简化部署：

```bash
# 创建 docker-compose.yml
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

# 安装 pgvector 扩展
docker exec -it postgres16 bash -c "apt-get update && apt-get install -y postgresql-16-pgvector"
docker exec -it postgres16 bash -c "psql -U postgres -d ai_platform -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
```

### 1.3 Kubernetes 部署（推荐生产环境）

使用 Bitnami PostgreSQL Helm Chart：

```bash
# 添加仓库
helm repo add bitnami https://charts.bitnami.com/bitnami

# 创建自定义配置文件 values.yaml
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
# pgvector 扩展必须
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

为物理服务器配置本地存储类：

```bash
# 创建本地路径存储
sudo mkdir -p /mnt/postgres-data

# 创建 StorageClass 清单文件
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

### 1.4 直接安装（裸机服务器）

如果您希望直接在物理服务器或虚拟机上安装 PostgreSQL，而不使用容器化技术：

```bash
# 更新包列表
sudo apt update

# 安装 PostgreSQL 16
sudo apt install -y postgresql-16 postgresql-contrib-16

# 安装 pgvector 扩展
sudo apt install -y postgresql-16-pgvector

# 启动 PostgreSQL 服务
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 配置 PostgreSQL 允许远程访问（根据需要）
sudo nano /etc/postgresql/16/main/postgresql.conf
# 修改 listen_addresses = '*'

sudo nano /etc/postgresql/16/main/pg_hba.conf
# 添加: host ai_platform ai_platform_user 0.0.0.0/0 md5

# 重启 PostgreSQL 以应用更改
sudo systemctl restart postgresql

# 创建数据库和用户
sudo -u postgres psql -c "CREATE DATABASE ai_platform;"
sudo -u postgres psql -c "CREATE USER ai_platform_user WITH ENCRYPTED PASSWORD 'strongPassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_platform TO ai_platform_user;"
sudo -u postgres psql -d ai_platform -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

配置高性能设置：

```bash
# 编辑 PostgreSQL 配置文件
sudo nano /etc/postgresql/16/main/postgresql.conf

# 添加以下配置（根据服务器硬件调整）
max_connections = 200
shared_buffers = '1GB'                 # 服务器内存的25%
work_mem = '64MB'
maintenance_work_mem = '256MB'         # 维护操作的内存

# 日志设置
log_statement = 'ddl'                  # 记录所有 DDL 语句
log_min_duration_statement = 1000      # 记录执行时间超过 1 秒的查询

# 查询优化
random_page_cost = 1.1                 # SSD 存储设置更低的随机页成本
effective_cache_size = '3GB'           # 系统缓存的估计值

# WAL (Write-Ahead Log) 配置
wal_level = 'replica'                  # 支持逻辑复制
max_wal_size = '1GB'                   # 自动检查点间隔
min_wal_size = '80MB'

# 并行查询设置
max_parallel_workers_per_gather = 4    # 每次查询的最大并行工作者数
max_parallel_workers = 8               # 系统的最大并行工作者数
```

## 2. 连接方式

### 2.1 服务地址与端口

- **Docker 部署**: `localhost` 或主机 IP 地址，端口 5432
- **Kubernetes 内部**: `<service-name>.<namespace>.svc.cluster.local` (例如: `ai-postgres-postgresql.database.svc.cluster.local`)，端口 5432
- **裸机安装**: 服务器 IP 地址，端口 5432

### 2.2 命令行连接

```bash
# Docker 部署连接
psql -h localhost -p 5432 -U postgres -d ai_platform

# Kubernetes 部署连接（从集群内部）
kubectl exec -it ai-postgres-postgresql-0 -n database -- psql -U postgres -d ai_platform

# Kubernetes 部署连接（从集群外部，需要端口转发）
kubectl port-forward svc/ai-postgres-postgresql -n database 5432:5432
# 然后在另一个终端：
psql -h localhost -p 5432 -U postgres -d ai_platform
```

### 2.3 应用程序连接

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

## 3. 安全与配置

### 3.1 基本安全配置

- 配置强密码策略:

```bash
# 修改默认密码
docker exec -it postgres16 psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'YourStrongPassword123!';"

# 或在 Kubernetes 中
kubectl exec -it ai-postgres-postgresql-0 -n database -- psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'YourStrongPassword123!';"
```

- 限制网络访问，仅允许必要的应用和服务连接:

```bash
# Docker 环境下，修改 pg_hba.conf
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

### 3.2 性能优化配置

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

## 4. 数据库初始化与迁移

### 4.1 基本初始化脚本

以下创建一个完整的初始化脚本，创建所需的 Schema 和基础表结构：

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

### `auth` 模式表结构

#### `auth.users`

| 列名             | 数据类型                  | 约束/描述                                  |
| ---------------- | ------------------------- | ------------------------------------------ |
| id               | SERIAL                    | PRIMARY KEY                                |
| username         | VARCHAR(150)              | UNIQUE, NOT NULL                           |
| email            | VARCHAR(254)              | UNIQUE, NOT NULL                           |
| password_hash    | VARCHAR(255)              | NOT NULL                                   |
| first_name       | VARCHAR(150)              |                                            |
| last_name        | VARCHAR(150)              |                                            |
| is_active        | BOOLEAN                   | DEFAULT true                               |
| is_superuser     | BOOLEAN                   | DEFAULT false                              |
| date_joined      | TIMESTAMP WITH TIME ZONE  | DEFAULT NOW()                              |
| last_login       | TIMESTAMP WITH TIME ZONE  |                                            |
| organization_id  | INTEGER                   |                                            |

#### `auth.groups`

| 列名        | 数据类型     | 约束/描述        |
| ----------- | ------------ | ---------------- |
| id          | SERIAL       | PRIMARY KEY      |
| name        | VARCHAR(150) | UNIQUE, NOT NULL |
| description | TEXT         |                  |

---

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

### `data_platform` 模式表结构

#### `data_platform.data_sources`

| 列名            | 数据类型                 | 约束/描述                                     |
| --------------- | ------------------------ | --------------------------------------------- |
| id              | SERIAL                   | PRIMARY KEY                                   |
| name            | VARCHAR(200)             | NOT NULL                                      |
| description     | TEXT                     |                                               |
| source_type     | VARCHAR(50)              | NOT NULL                                      |
| connection_info | JSONB                    | NOT NULL                                      |
| created_by      | INTEGER                  | REFERENCES auth.users(id)                     |
| created_at      | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                                 |
| updated_at      | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                                 |
| is_active       | BOOLEAN                  | DEFAULT true                                  |

-- 向量表
CREATE TABLE IF NOT EXISTS data_platform.text_embeddings (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER,
    record_id VARCHAR(100),
    text_content TEXT,
    embedding vector(1536), -- 使用OpenAI ada模型的1536维向量
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

#### `data_platform.text_embeddings`

| 列名         | 数据类型                 | 约束/描述                                     |
| ------------ | ------------------------ | --------------------------------------------- |
| id           | SERIAL                   | PRIMARY KEY                                   |
| dataset_id   | INTEGER                  |                                               |
| record_id    | VARCHAR(100)             |                                               |
| text_content | TEXT                     |                                               |
| embedding    | vector(1536)             | 使用OpenAI ada模型的1536维向量                 |
| created_at   | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                                 |

-- 创建向量索引
CREATE INDEX idx_text_embeddings_vector ON data_platform.text_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

### `algo_platform`, `model_platform`, `service_platform` 模式表结构

这些模式的表结构将根据 `05_database_setup_new.md` 中定义的实体和关系进行创建。请参考该文档中的 "表结构和关系" 部分获取高级概述，并在后续的开发迭代中，在此处补充详细的 DDL 和 Markdown 表格。

**示例 (algo_platform.algorithms):**

```sql
-- algo_platform 模式下的表结构 (示例)
CREATE TABLE IF NOT EXISTS algo_platform.algorithms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50),
    source_code_url VARCHAR(512),
    created_by INTEGER REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (name, version)
);
```

| 列名            | 数据类型                 | 约束/描述                                     |
| --------------- | ------------------------ | --------------------------------------------- |
| id              | SERIAL                   | PRIMARY KEY                                   |
| name            | VARCHAR(255)             | NOT NULL                                      |
| description     | TEXT                     |                                               |
| version         | VARCHAR(50)              |                                               |
| source_code_url | VARCHAR(512)             |                                               |
| created_by      | INTEGER                  | REFERENCES auth.users(id)                     |
| created_at      | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                                 |
| updated_at      | TIMESTAMP WITH TIME ZONE | DEFAULT NOW()                                 |
|                 |                          | UNIQUE (name, version)                        |

EOF

# 在Docker环境执行初始化脚本
docker exec -i postgres16 psql -U postgres -d ai_platform < init_ai_platform_db.sql

# 或在Kubernetes环境执行初始化脚本
kubectl exec -i ai-postgres-postgresql-0 -n database -- bash -c "cat > /tmp/init.sql" < init_ai_platform_db.sql
kubectl exec -it ai-postgres-postgresql-0 -n database -- bash -c "psql -U postgres -d ai_platform -f /tmp/init.sql"
```

### 4.2 数据迁移与版本控制

在生产环境中，推荐使用数据库迁移工具（如 Flyway 或 Django Migrations）来管理数据库结构的版本控制：

```bash
# 使用 Flyway 进行数据库迁移
mkdir -p /opt/flyway/sql
cp init_ai_platform_db.sql /opt/flyway/sql/V1__initial_schema.sql

# 准备 Flyway 配置
cat > /opt/flyway/conf/flyway.conf << 'EOF'
flyway.url=jdbc:postgresql://localhost:5432/ai_platform
flyway.user=postgres
flyway.password=changeThisToSecurePassword
flyway.locations=filesystem:/opt/flyway/sql
flyway.baselineOnMigrate=true
EOF

# 运行 Flyway 迁移
docker run --rm -v /opt/flyway/conf:/flyway/conf -v /opt/flyway/sql:/flyway/sql flyway/flyway:9.20 migrate
```

### 4.3 备份原有数据和恢复

如果您需要迁移现有数据到新部署的系统：

```bash
# 从源系统导出数据
pg_dump -U postgres -h source_db_host -F c -f ai_platform_backup.dump ai_platform

# 复制到目标系统
scp ai_platform_backup.dump user@target_host:/tmp/

# 在目标系统恢复
pg_restore -U postgres -d ai_platform -v /tmp/ai_platform_backup.dump
```

## 5. 最佳实践

1. **定期更新密码**：定期更改数据库密码，确保密码符合强度要求。
2. **设置资源限制**：避免单个查询或连接占用过多资源。
3. **监控连接数**：保持足够但不过量的连接数，避免连接溢出。
4. **定期备份**：建立定期备份策略，确保数据安全性。
5. **使用连接池**：在应用程序与数据库之间配置连接池，优化连接管理。
6. **定期分析**：定期执行 `ANALYZE` 命令更新统计信息，优化查询计划。
7. **正确索引**：为经常查询的列创建适当的索引，但避免过度索引。

## 6. 故障排除

### 6.1 常见问题

1. **连接被拒绝**
   - 检查 PostgreSQL 服务是否运行
   - 确认 `pg_hba.conf` 配置允许指定地址连接
   - 验证防火墙配置

2. **性能问题**
   - 检查慢查询日志
   - 确认磁盘I/O是否成为瓶颈
   - 验证索引使用情况

3. **磁盘空间不足**
   - 执行 `VACUUM FULL` 回收空间
   - 清理日志文件
   - 扩展磁盘容量

### 6.2 日志分析

检查日志以排查问题：

```bash
# 在 Docker 中查看日志
docker logs postgres16

# 在 Kubernetes 中查看日志
kubectl logs ai-postgres-postgresql-0 -n database

# 直接安装时检查系统日志
sudo grep -i postgres /var/log/syslog
```

## 相关资源

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [pgvector 扩展](https://github.com/pgvector/pgvector)
- [PostgreSQL Kubernetes 操作指南](https://github.com/zalando/postgres-operator)
