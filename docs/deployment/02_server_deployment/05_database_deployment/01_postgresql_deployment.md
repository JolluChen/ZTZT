# PostgreSQL 16 部署指南

[![Ubuntu 24.04 LTS](https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420?style=flat-square&logo=ubuntu)](https://ubuntu.com/) [![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/) [![pgvector](https://img.shields.io/badge/pgvector-0.7.0-4CAF50?style=flat-square)](https://github.com/pgvector/pgvector)

**部署阶段**: 第二阶段 - 服务器部署  
**预计时间**: 1.5-2.5小时  
**难度级别**: ⭐⭐⭐  
**前置要求**: [系统环境配置](../01_environment_setup.md) 完成

本文档详细说明如何在 Ubuntu 24.04 LTS 物理服务器环境中部署和配置 PostgreSQL 16 数据库服务，专为 AI 中台项目优化，包含 pgvector 向量扩展支持。

## 📋 部署概览

| 组件 | 版本 | 用途 | 部署时间 |
|------|------|------|----------|
| PostgreSQL | 16.x | 主数据库 | 45-60分钟 |
| pgvector | 0.7.0 | 向量存储 | 15-20分钟 |
| 配置优化 | - | 性能调优 | 20-30分钟 |
| 安全配置 | - | 访问控制 | 15-25分钟 |

## 1. 部署策略选择

根据您的环境和需求选择最适合的部署方式。推荐的部署策略基于 Ubuntu 24.04 LTS 优化：

### 1.1 推荐部署方式对比

| 部署方式 | 适用环境 | 复杂度 | 维护难度 | 性能 | 高可用 |
|----------|----------|--------|----------|------|--------|
| **APT 直接安装** | 生产环境 | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Docker 单实例 | 开发/测试 | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Docker Compose | 小规模生产 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Kubernetes | 大规模生产 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 1.2 Ubuntu 24.04 LTS 原生安装（推荐）

Ubuntu 24.04 LTS 提供了优化的 PostgreSQL 16 包，是生产环境的最佳选择：

```bash
# 1. 更新系统包索引
sudo apt update && sudo apt upgrade -y

# 2. 安装 PostgreSQL 16 及相关组件
sudo apt install -y \
    postgresql-16 \
    postgresql-client-16 \
    postgresql-contrib-16 \
    postgresql-16-pgvector \
    postgresql-common \
    build-essential

# 3. 验证安装版本
psql --version
# 应显示: psql (PostgreSQL) 16.x

# 4. 检查服务状态
sudo systemctl status postgresql
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 5. 验证 pgvector 扩展可用性
sudo -u postgres psql -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
```

### 1.3 Docker 部署（开发/测试环境）

使用 Docker 部署 PostgreSQL 适用于开发环境或单节点测试环境：

```bash
# 创建持久化存储目录
sudo mkdir -p /opt/ai-platform/data/postgres
sudo chown -R 999:999 /opt/ai-platform/data/postgres

# 创建 PostgreSQL 配置文件
sudo mkdir -p /opt/ai-platform/config/postgres
sudo tee /opt/ai-platform/config/postgres/postgresql.conf > /dev/null << EOF
# PostgreSQL 16 配置 - 针对 Ubuntu 24.04 LTS 优化
listen_addresses = '*'
port = 5432
max_connections = 200

# 内存配置（根据服务器规格调整）
shared_buffers = '1GB'
work_mem = '64MB'
maintenance_work_mem = '256MB'
effective_cache_size = '3GB'

# WAL 配置
wal_level = 'replica'
max_wal_size = '1GB'
min_wal_size = '80MB'
checkpoint_completion_target = 0.9

# 查询优化
random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 100

# 日志配置
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_statement = 'ddl'
log_min_duration_statement = 1000
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# 其他优化
autovacuum = on
track_activities = on
track_counts = on
EOF

# 运行 PostgreSQL 16 容器
docker run -d \
  --name ai-platform-postgres \
  --restart unless-stopped \
  -e POSTGRES_PASSWORD=AI_Platform_2024_Secure \
  -e POSTGRES_USER=ai_platform \
  -e POSTGRES_DB=ai_platform_db \
  -e POSTGRES_INITDB_ARGS="--data-checksums --locale=C.UTF-8" \
  -p 5432:5432 \
  -v /opt/ai-platform/data/postgres:/var/lib/postgresql/data \
  -v /opt/ai-platform/config/postgres/postgresql.conf:/etc/postgresql/postgresql.conf \
  postgres:16-alpine \
  postgres -c 'config_file=/etc/postgresql/postgresql.conf'

# 等待数据库启动
sleep 30

# 安装 pgvector 扩展
docker exec ai-platform-postgres psql -U ai_platform -d ai_platform_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 验证扩展安装
docker exec ai-platform-postgres psql -U ai_platform -d ai_platform_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

### 1.4 Docker Compose 部署（小规模生产环境）

使用 Docker Compose 管理 PostgreSQL 服务：

```bash
# 创建项目目录
sudo mkdir -p /opt/ai-platform/docker/postgres
cd /opt/ai-platform/docker/postgres

# 创建 Docker Compose 配置
sudo tee docker-compose.yml > /dev/null << EOF
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: ai-platform-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ai_platform
      POSTGRES_PASSWORD: AI_Platform_2024_Secure
      POSTGRES_DB: ai_platform_db
      POSTGRES_INITDB_ARGS: "--data-checksums --locale=C.UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
      - ./config/postgresql.conf:/etc/postgresql/postgresql.conf
    command: postgres -c 'config_file=/etc/postgresql/postgresql.conf'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai_platform -d ai_platform_db"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - ai-platform-network

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: ai-platform-postgres-exporter
    restart: unless-stopped
    environment:
      DATA_SOURCE_NAME: "postgresql://ai_platform:AI_Platform_2024_Secure@postgres:5432/ai_platform_db?sslmode=disable"
    ports:
      - "9187:9187"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - ai-platform-network

volumes:
  postgres_data:
    driver: local

networks:
  ai-platform-network:
    driver: bridge
EOF

# 创建配置目录
sudo mkdir -p config init-scripts

# 创建 PostgreSQL 配置文件
sudo tee config/postgresql.conf > /dev/null << EOF
# PostgreSQL 16 生产配置 - Ubuntu 24.04 LTS 优化
listen_addresses = '*'
port = 5432
max_connections = 200

# 内存配置
shared_buffers = '1GB'
work_mem = '64MB'
maintenance_work_mem = '256MB'
effective_cache_size = '3GB'
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# WAL 配置
wal_level = 'replica'
max_wal_size = '2GB'
min_wal_size = '160MB'
checkpoint_completion_target = 0.9
wal_buffers = '16MB'

# 查询优化
random_page_cost = 1.1
effective_io_concurrency = 200
seq_page_cost = 1.0

# 日志配置
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_statement = 'ddl'
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# 自动清理
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min

# 统计信息
track_activities = on
track_counts = on
track_io_timing = on
track_functions = pl

# 安全配置
ssl = off
password_encryption = scram-sha-256
EOF

# 创建初始化脚本
sudo tee init-scripts/01-extensions.sql > /dev/null << EOF
-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 验证扩展安装
SELECT extname, extversion FROM pg_extension 
WHERE extname IN ('vector', 'uuid-ossp', 'btree_gin', 'pg_stat_statements');
EOF

# 启动服务
sudo docker-compose up -d

# 验证服务状态
sudo docker-compose ps
sudo docker-compose logs postgres
```

## 2. Ubuntu 24.04 LTS 原生安装配置

### 2.1 完整安装流程

```bash
# 1. 系统环境准备
sudo apt update && sudo apt upgrade -y

# 2. 安装 PostgreSQL 16 完整套件
sudo apt install -y \
    postgresql-16 \
    postgresql-client-16 \
    postgresql-contrib-16 \
    postgresql-16-pgvector \
    postgresql-plpython3-16 \
    postgresql-server-dev-16 \
    libpq-dev \
    build-essential

# 3. 验证安装
sudo systemctl status postgresql
psql --version

# 4. 配置 PostgreSQL 服务
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 5. 设置 PostgreSQL 用户密码
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'AI_Platform_2024_Secure';"
```

### 2.2 数据库和用户配置

```bash
# 1. 创建 AI 平台专用数据库和用户
sudo -u postgres createdb ai_platform_db --encoding=UTF8 --locale=C.UTF-8

# 2. 创建应用用户
sudo -u postgres psql << EOF
-- 创建应用用户
CREATE USER ai_platform WITH ENCRYPTED PASSWORD 'AI_Platform_App_2024';

-- 授予数据库权限
GRANT ALL PRIVILEGES ON DATABASE ai_platform_db TO ai_platform;

-- 创建只读用户（用于监控和报表）
CREATE USER ai_platform_readonly WITH ENCRYPTED PASSWORD 'AI_Platform_RO_2024';
GRANT CONNECT ON DATABASE ai_platform_db TO ai_platform_readonly;
\c ai_platform_db
GRANT USAGE ON SCHEMA public TO ai_platform_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_platform_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ai_platform_readonly;

-- 安装必要扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 验证扩展
SELECT extname, extversion FROM pg_extension 
WHERE extname IN ('vector', 'uuid-ossp', 'btree_gin', 'pg_stat_statements');
EOF
```

### 2.3 PostgreSQL 性能优化配置

```bash
# 1. 备份原始配置
sudo cp /etc/postgresql/16/main/postgresql.conf /etc/postgresql/16/main/postgresql.conf.backup

# 2. 应用优化配置
sudo tee /etc/postgresql/16/main/postgresql.conf > /dev/null << EOF
# PostgreSQL 16 生产配置 - Ubuntu 24.04 LTS
# 自动生成于 $(date)

#------------------------------------------------------------------------------
# 连接和认证
#------------------------------------------------------------------------------
listen_addresses = 'localhost,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16'
port = 5432
max_connections = 200
superuser_reserved_connections = 3

#------------------------------------------------------------------------------
# 内存配置 (根据服务器内存调整)
#------------------------------------------------------------------------------
shared_buffers = '2GB'                    # 系统内存的 25%
work_mem = '64MB'                         # 每个查询操作的内存
maintenance_work_mem = '512MB'            # 维护操作内存
effective_cache_size = '6GB'              # 操作系统缓存估计
max_parallel_workers_per_gather = 4      # 并行查询工作进程
max_parallel_workers = 8                 # 最大并行工作进程
max_parallel_maintenance_workers = 4     # 并行维护工作进程

#------------------------------------------------------------------------------
# WAL (Write-Ahead Logging) 配置
#------------------------------------------------------------------------------
wal_level = 'replica'
wal_buffers = '16MB'
max_wal_size = '2GB'
min_wal_size = '160MB'
checkpoint_completion_target = 0.9
checkpoint_timeout = '15min'
archive_mode = off                        # 根据备份需求调整

#------------------------------------------------------------------------------
# 查询计划器配置
#------------------------------------------------------------------------------
random_page_cost = 1.1                   # SSD 存储优化
seq_page_cost = 1.0
cpu_tuple_cost = 0.01
cpu_index_tuple_cost = 0.005
cpu_operator_cost = 0.0025
effective_io_concurrency = 200           # SSD 并发 I/O
maintenance_io_concurrency = 10

#------------------------------------------------------------------------------
# 统计信息收集
#------------------------------------------------------------------------------
track_activities = on
track_counts = on
track_io_timing = on
track_functions = pl
stats_temp_directory = 'pg_stat_tmp'
shared_preload_libraries = 'pg_stat_statements'

#------------------------------------------------------------------------------
# 自动清理配置
#------------------------------------------------------------------------------
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 30s
autovacuum_vacuum_threshold = 50
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.05

#------------------------------------------------------------------------------
# 日志配置
#------------------------------------------------------------------------------
logging_collector = on
log_destination = 'stderr'
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_file_mode = 0600
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_messages = warning
log_min_error_statement = error
log_min_duration_statement = 1000        # 记录超过 1 秒的查询
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_statement = 'ddl'
log_temp_files = 0
log_timezone = 'Asia/Shanghai'

#------------------------------------------------------------------------------
# 本地化配置
#------------------------------------------------------------------------------
datestyle = 'iso, mdy'
timezone = 'Asia/Shanghai'
lc_messages = 'en_US.UTF-8'
lc_monetary = 'en_US.UTF-8'
lc_numeric = 'en_US.UTF-8'
lc_time = 'en_US.UTF-8'
default_text_search_config = 'pg_catalog.english'

#------------------------------------------------------------------------------
# 安全配置
#------------------------------------------------------------------------------
ssl = off                                 # 根据需求启用
password_encryption = scram-sha-256
row_security = on

#------------------------------------------------------------------------------
# 其他优化配置
#------------------------------------------------------------------------------
default_statistics_target = 100
synchronous_commit = on
wal_sync_method = fdatasync
full_page_writes = on
wal_compression = on
huge_pages = try
EOF

# 3. 配置客户端认证
sudo tee /etc/postgresql/16/main/pg_hba.conf > /dev/null << EOF
# PostgreSQL Client Authentication Configuration File
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             postgres                                peer
local   all             all                                     md5

# IPv4 local connections:
host    all             all             127.0.0.1/32            scram-sha-256
host    ai_platform_db  ai_platform     10.0.0.0/8              scram-sha-256
host    ai_platform_db  ai_platform     172.16.0.0/12           scram-sha-256
host    ai_platform_db  ai_platform     192.168.0.0/16          scram-sha-256

# IPv6 local connections:
host    all             all             ::1/128                 scram-sha-256

# 监控用户连接
host    ai_platform_db  ai_platform_readonly  10.0.0.0/8       scram-sha-256
host    ai_platform_db  ai_platform_readonly  172.16.0.0/12    scram-sha-256
host    ai_platform_db  ai_platform_readonly  192.168.0.0/16   scram-sha-256
EOF

# 4. 重启 PostgreSQL 应用配置
sudo systemctl restart postgresql

# 5. 验证配置
sudo systemctl status postgresql
sudo -u postgres psql -c "SHOW shared_buffers;"
sudo -u postgres psql -c "SHOW work_mem;"
```

### 2.4 系统级别优化

```bash
# 1. 配置系统内核参数
sudo tee -a /etc/sysctl.conf > /dev/null << EOF

# PostgreSQL 优化参数
# 共享内存配置
kernel.shmmax = 17179869184               # 16GB
kernel.shmall = 4194304                   # 16GB / 4KB
kernel.shmmni = 4096

# 信号量配置
kernel.sem = 250 32000 100 128

# 网络配置
net.core.somaxconn = 1024
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_keepalive_time = 7200
net.ipv4.tcp_keepalive_intvl = 75
net.ipv4.tcp_keepalive_probes = 9

# 内存管理
vm.swappiness = 1
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.overcommit_memory = 2
vm.overcommit_ratio = 90
EOF

# 应用内核参数
sudo sysctl -p

# 2. 配置系统限制
sudo tee /etc/security/limits.d/postgresql.conf > /dev/null << EOF
postgres soft nofile 65536
postgres hard nofile 65536
postgres soft nproc 32768
postgres hard nproc 32768
EOF

# 3. 配置 systemd 服务限制
sudo mkdir -p /etc/systemd/system/postgresql.service.d
sudo tee /etc/systemd/system/postgresql.service.d/override.conf > /dev/null << EOF
[Service]
LimitNOFILE=65536
LimitNPROC=32768
EOF

# 重载 systemd 配置
sudo systemctl daemon-reload
sudo systemctl restart postgresql
```

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

## 3. 数据库架构初始化

### 3.1 AI 平台数据库模式创建

```bash
# 创建数据库初始化脚本
sudo mkdir -p /opt/ai-platform/scripts/database
sudo tee /opt/ai-platform/scripts/database/01_init_schemas.sql > /dev/null << 'EOF'
-- AI 中台数据库初始化脚本
-- 版本: 2024.1
-- 兼容: PostgreSQL 16.x + pgvector 0.7.0

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 验证扩展安装
SELECT extname, extversion FROM pg_extension 
WHERE extname IN ('vector', 'uuid-ossp', 'btree_gin', 'pg_stat_statements');

-- 创建应用模式
CREATE SCHEMA IF NOT EXISTS auth AUTHORIZATION ai_platform;
CREATE SCHEMA IF NOT EXISTS data_platform AUTHORIZATION ai_platform;
CREATE SCHEMA IF NOT EXISTS algo_platform AUTHORIZATION ai_platform;
CREATE SCHEMA IF NOT EXISTS model_platform AUTHORIZATION ai_platform;
CREATE SCHEMA IF NOT EXISTS service_platform AUTHORIZATION ai_platform;
CREATE SCHEMA IF NOT EXISTS monitoring AUTHORIZATION ai_platform;

-- 设置搜索路径
ALTER USER ai_platform SET search_path = auth, data_platform, algo_platform, model_platform, service_platform, public;

-- 创建通用函数
CREATE OR REPLACE FUNCTION public.update_modified_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

COMMENT ON FUNCTION public.update_modified_time() IS '自动更新记录修改时间的触发器函数';
EOF

# 创建认证模块表结构
sudo tee /opt/ai-platform/scripts/database/02_auth_schema.sql > /dev/null << 'EOF'
-- 认证模块表结构

-- 用户表
CREATE TABLE IF NOT EXISTS auth.users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    is_staff BOOLEAN DEFAULT false,
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    profile_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户组表
CREATE TABLE IF NOT EXISTS auth.groups (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(150) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户组关联表
CREATE TABLE IF NOT EXISTS auth.user_groups (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth.users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES auth.groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, group_id)
);

-- JWT 黑名单表（用于登出管理）
CREATE TABLE IF NOT EXISTS auth.jwt_blacklist (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES auth.users(id) ON DELETE CASCADE,
    blacklisted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON auth.users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON auth.users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_uuid ON auth.users(uuid);
CREATE INDEX IF NOT EXISTS idx_groups_name ON auth.groups(name);
CREATE INDEX IF NOT EXISTS idx_user_groups_user ON auth.user_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_group ON auth.user_groups(group_id);
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_jti ON auth.jwt_blacklist(jti);
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_expires ON auth.jwt_blacklist(expires_at);

-- 创建触发器
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.update_modified_time();

CREATE TRIGGER trigger_groups_updated_at
    BEFORE UPDATE ON auth.groups
    FOR EACH ROW EXECUTE FUNCTION public.update_modified_time();
EOF

# 创建数据平台表结构
sudo tee /opt/ai-platform/scripts/database/03_data_platform_schema.sql > /dev/null << 'EOF'
-- 数据平台模块表结构

-- 数据源表
CREATE TABLE IF NOT EXISTS data_platform.data_sources (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(100) NOT NULL,
    connection_config JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 数据集表
CREATE TABLE IF NOT EXISTS data_platform.datasets (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    data_source_id INTEGER REFERENCES data_platform.data_sources(id),
    schema_definition JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    row_count BIGINT DEFAULT 0,
    size_bytes BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 文本向量存储表
CREATE TABLE IF NOT EXISTS data_platform.text_embeddings (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    dataset_id INTEGER REFERENCES data_platform.datasets(id) ON DELETE CASCADE,
    record_id VARCHAR(255),
    text_content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 模型维度
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 数据处理任务表
CREATE TABLE IF NOT EXISTS data_platform.processing_tasks (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    input_dataset_id INTEGER REFERENCES data_platform.datasets(id),
    output_dataset_id INTEGER REFERENCES data_platform.datasets(id),
    config JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_data_sources_type ON data_platform.data_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_data_sources_active ON data_platform.data_sources(is_active);
CREATE INDEX IF NOT EXISTS idx_datasets_source ON data_platform.datasets(data_source_id);
CREATE INDEX IF NOT EXISTS idx_datasets_active ON data_platform.datasets(is_active);
CREATE INDEX IF NOT EXISTS idx_text_embeddings_dataset ON data_platform.text_embeddings(dataset_id);
CREATE INDEX IF NOT EXISTS idx_text_embeddings_record ON data_platform.text_embeddings(record_id);

-- 创建向量相似度搜索索引
CREATE INDEX IF NOT EXISTS idx_text_embeddings_vector_cosine 
ON data_platform.text_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_text_embeddings_vector_l2 
ON data_platform.text_embeddings USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- 创建触发器
CREATE TRIGGER trigger_data_sources_updated_at
    BEFORE UPDATE ON data_platform.data_sources
    FOR EACH ROW EXECUTE FUNCTION public.update_modified_time();

CREATE TRIGGER trigger_datasets_updated_at
    BEFORE UPDATE ON data_platform.datasets
    FOR EACH ROW EXECUTE FUNCTION public.update_modified_time();

CREATE TRIGGER trigger_processing_tasks_updated_at
    BEFORE UPDATE ON data_platform.processing_tasks
    FOR EACH ROW EXECUTE FUNCTION public.update_modified_time();
EOF

# 执行数据库初始化
sudo -u postgres psql -d ai_platform_db -f /opt/ai-platform/scripts/database/01_init_schemas.sql
sudo -u postgres psql -d ai_platform_db -f /opt/ai-platform/scripts/database/02_auth_schema.sql
sudo -u postgres psql -d ai_platform_db -f /opt/ai-platform/scripts/database/03_data_platform_schema.sql

# 验证表创建
sudo -u postgres psql -d ai_platform_db -c "\dt auth.*"
sudo -u postgres psql -d ai_platform_db -c "\dt data_platform.*"
```

### 3.2 初始数据配置

```bash
# 创建初始数据脚本
sudo tee /opt/ai-platform/scripts/database/04_initial_data.sql > /dev/null << 'EOF'
-- 初始数据配置

-- 创建默认管理员用户
INSERT INTO auth.users (username, email, password_hash, first_name, last_name, is_active, is_superuser, is_staff)
VALUES (
    'admin',
    'admin@ai-platform.local',
    '$2b$12$ZvObSUln.TpZ9vOJUPm6mOSnVkB.Zh6qsJWhjWYQOX5fT4QL96lxW',  -- 密码: admin123
    'System',
    'Administrator',
    true,
    true,
    true
) ON CONFLICT (username) DO NOTHING;

-- 创建默认用户组
INSERT INTO auth.groups (name, description, permissions) VALUES
('administrators', '系统管理员组', '["all"]'),
('data_scientists', '数据科学家组', '["data_platform.*", "model_platform.read"]'),
('algorithm_developers', '算法开发者组', '["algo_platform.*", "data_platform.read"]'),
('model_engineers', '模型工程师组', '["model_platform.*", "service_platform.read"]'),
('service_operators', '服务运维组', '["service_platform.*", "monitoring.read"]'),
('viewers', '只读用户组', '["*.read"]')
ON CONFLICT (name) DO NOTHING;

-- 将管理员用户加入管理员组
INSERT INTO auth.user_groups (user_id, group_id)
SELECT u.id, g.id 
FROM auth.users u, auth.groups g 
WHERE u.username = 'admin' AND g.name = 'administrators'
ON CONFLICT (user_id, group_id) DO NOTHING;

-- 创建示例数据源
INSERT INTO data_platform.data_sources (name, description, source_type, connection_config, created_by) VALUES
('本地文件系统', '本地文件系统数据源', 'filesystem', '{"base_path": "/opt/ai-platform/data"}', 1),
('示例数据库', '示例PostgreSQL数据源', 'postgresql', '{"host": "localhost", "port": 5432, "database": "ai_platform_db"}', 1)
ON CONFLICT DO NOTHING;
EOF

# 执行初始数据配置
sudo -u postgres psql -d ai_platform_db -f /opt/ai-platform/scripts/database/04_initial_data.sql

# 验证初始数据
sudo -u postgres psql -d ai_platform_db -c "SELECT username, email, is_superuser FROM auth.users;"
sudo -u postgres psql -d ai_platform_db -c "SELECT name, description FROM auth.groups;"
```
## 4. 备份与恢复策略

### 4.1 自动备份配置

```bash
# 创建备份目录
sudo mkdir -p /opt/ai-platform/backups/postgresql
sudo chown postgres:postgres /opt/ai-platform/backups/postgresql

# 创建备份脚本
sudo tee /opt/ai-platform/scripts/backup_postgresql.sh > /dev/null << 'EOF'
#!/bin/bash
# PostgreSQL 自动备份脚本
# 作者: AI Platform Team
# 版本: 2024.1

set -euo pipefail

# 配置变量
DB_NAME="ai_platform_db"
DB_USER="ai_platform"
BACKUP_DIR="/opt/ai-platform/backups/postgresql"
RETENTION_DAYS=30
LOG_FILE="/var/log/postgresql_backup.log"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 创建备份文件名
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="${BACKUP_DIR}/ai_platform_${TIMESTAMP}.dump"

log "开始备份数据库: $DB_NAME"

# 执行备份
if pg_dump -U "$DB_USER" -h localhost -F c -b -v -f "$BACKUP_FILE" "$DB_NAME" 2>> "$LOG_FILE"; then
    log "备份成功: $BACKUP_FILE"
    
    # 压缩备份文件
    gzip "$BACKUP_FILE"
    log "备份文件已压缩: ${BACKUP_FILE}.gz"
    
    # 清理旧备份
    find "$BACKUP_DIR" -name "*.dump.gz" -mtime +$RETENTION_DAYS -delete
    log "已清理 $RETENTION_DAYS 天前的备份文件"
    
    # 验证备份文件
    BACKUP_SIZE=$(stat -c%s "${BACKUP_FILE}.gz")
    if [ "$BACKUP_SIZE" -gt 1024 ]; then
        log "备份验证成功，文件大小: $BACKUP_SIZE 字节"
    else
        log "警告：备份文件大小异常: $BACKUP_SIZE 字节"
        exit 1
    fi
else
    log "错误：备份失败"
    exit 1
fi

log "备份完成"
EOF

# 设置执行权限
sudo chmod +x /opt/ai-platform/scripts/backup_postgresql.sh

# 配置定时任务
sudo tee /etc/cron.d/postgresql-backup > /dev/null << 'EOF'
# PostgreSQL 自动备份 - 每日凌晨 2:00 执行
0 2 * * * postgres /opt/ai-platform/scripts/backup_postgresql.sh
# 每周日凌晨 3:00 执行完整备份和维护
0 3 * * 0 postgres /usr/bin/vacuumdb -U ai_platform -d ai_platform_db --analyze --verbose
EOF

# 创建恢复脚本
sudo tee /opt/ai-platform/scripts/restore_postgresql.sh > /dev/null << 'EOF'
#!/bin/bash
# PostgreSQL 恢复脚本

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "用法: $0 <备份文件路径>"
    echo "示例: $0 /opt/ai-platform/backups/postgresql/ai_platform_20241201_020000.dump.gz"
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME="ai_platform_db"
DB_USER="ai_platform"

echo "警告：此操作将覆盖现有数据库 $DB_NAME"
read -p "确认继续？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 1
fi

echo "开始恢复数据库..."

# 如果是压缩文件，先解压
if [[ "$BACKUP_FILE" == *.gz ]]; then
    TEMP_FILE="/tmp/restore_temp.dump"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# 停止应用连接（可选）
echo "建议在恢复前停止应用服务以避免连接冲突"

# 执行恢复
if pg_restore -U "$DB_USER" -h localhost -d "$DB_NAME" -v --clean --if-exists "$RESTORE_FILE"; then
    echo "恢复成功"
else
    echo "恢复失败"
    exit 1
fi

# 清理临时文件
if [[ "$BACKUP_FILE" == *.gz ]]; then
    rm -f "$TEMP_FILE"
fi

echo "数据库恢复完成"
EOF

sudo chmod +x /opt/ai-platform/scripts/restore_postgresql.sh
```

### 4.2 监控与健康检查

```bash
# 创建健康检查脚本
sudo tee /opt/ai-platform/scripts/health_check_postgresql.sh > /dev/null << 'EOF'
#!/bin/bash
# PostgreSQL 健康检查脚本

set -euo pipefail

DB_NAME="ai_platform_db"
DB_USER="ai_platform"
ALERT_EMAIL="admin@ai-platform.local"

# 检查数据库连接
check_connection() {
    if pg_isready -h localhost -p 5432 -U "$DB_USER" -d "$DB_NAME" &> /dev/null; then
        echo "✓ 数据库连接正常"
        return 0
    else
        echo "✗ 数据库连接失败"
        return 1
    fi
}

# 检查数据库大小
check_database_size() {
    SIZE=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | xargs)
    echo "✓ 数据库大小: $SIZE"
}

# 检查连接数
check_connections() {
    CONNECTIONS=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" | xargs)
    MAX_CONNECTIONS=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SHOW max_connections;" | xargs)
    echo "✓ 活跃连接数: $CONNECTIONS/$MAX_CONNECTIONS"
    
    if [ "$CONNECTIONS" -gt $((MAX_CONNECTIONS * 80 / 100)) ]; then
        echo "⚠ 警告：连接数过高"
        return 1
    fi
}

# 检查慢查询
check_slow_queries() {
    SLOW_QUERIES=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '30 seconds';" | xargs)
    echo "✓ 慢查询数量: $SLOW_QUERIES"
    
    if [ "$SLOW_QUERIES" -gt 5 ]; then
        echo "⚠ 警告：慢查询过多"
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    DISK_USAGE=$(df /var/lib/postgresql/ | awk 'NR==2 {print $5}' | sed 's/%//')
    echo "✓ 磁盘使用率: ${DISK_USAGE}%"
    
    if [ "$DISK_USAGE" -gt 85 ]; then
        echo "⚠ 警告：磁盘空间不足"
        return 1
    fi
}

# 主检查函数
main() {
    echo "PostgreSQL 健康检查 - $(date)"
    echo "================================="
    
    local exit_code=0
    
    check_connection || exit_code=1
    check_database_size || exit_code=1
    check_connections || exit_code=1
    check_slow_queries || exit_code=1
    check_disk_space || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        echo "================================="
        echo "✓ 所有检查通过"
    else
        echo "================================="
        echo "✗ 发现问题，请检查上述警告"
    fi
    
    return $exit_code
}

main "$@"
EOF

sudo chmod +x /opt/ai-platform/scripts/health_check_postgresql.sh

# 配置定期健康检查
sudo tee -a /etc/cron.d/postgresql-backup > /dev/null << 'EOF'
# PostgreSQL 健康检查 - 每15分钟执行一次
*/15 * * * * postgres /opt/ai-platform/scripts/health_check_postgresql.sh >> /var/log/postgresql_health.log 2>&1
EOF
```

## 5. 性能优化与调优

### 5.1 查询性能优化

```bash
# 创建性能分析脚本
sudo tee /opt/ai-platform/scripts/performance_analysis.sql > /dev/null << 'EOF'
-- PostgreSQL 性能分析查询

-- 1. 查看最慢的查询
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- 2. 查看数据库大小统计
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname IN ('auth', 'data_platform', 'algo_platform', 'model_platform', 'service_platform')
ORDER BY schemaname, tablename;

-- 3. 查看索引使用情况
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- 4. 查看未使用的索引
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 
ORDER BY pg_relation_size(indexrelid) DESC;

-- 5. 查看表的统计信息
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables 
ORDER BY n_dead_tup DESC;
EOF

# 运行性能分析
sudo -u postgres psql -d ai_platform_db -f /opt/ai-platform/scripts/performance_analysis.sql
```

## 6. 安全配置最佳实践

### 6.1 密码和访问控制

```bash
# 1. 定期更换数据库密码
sudo -u postgres psql -c "ALTER USER ai_platform PASSWORD 'New_Secure_Password_2024';"

# 2. 配置密码复杂度要求
sudo tee -a /etc/postgresql/16/main/postgresql.conf > /dev/null << 'EOF'
# 密码安全配置
password_encryption = scram-sha-256
shared_preload_libraries = 'passwordcheck'
EOF

# 3. 启用连接加密（推荐生产环境）
sudo -u postgres openssl req -new -x509 -days 365 -nodes -text \
    -out /etc/ssl/certs/postgresql.crt \
    -keyout /etc/ssl/private/postgresql.key \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=AI-Platform/CN=ai-platform.local"

sudo chown postgres:postgres /etc/ssl/private/postgresql.key
sudo chmod 600 /etc/ssl/private/postgresql.key

# 更新配置启用 SSL
sudo sed -i "s/#ssl = off/ssl = on/" /etc/postgresql/16/main/postgresql.conf
sudo sed -i "s/#ssl_cert_file = ''/ssl_cert_file = '\/etc\/ssl\/certs\/postgresql.crt'/" /etc/postgresql/16/main/postgresql.conf
sudo sed -i "s/#ssl_key_file = ''/ssl_key_file = '\/etc\/ssl\/private\/postgresql.key'/" /etc/postgresql/16/main/postgresql.conf
```

### 6.2 网络安全配置

```bash
# 1. 配置防火墙规则
sudo ufw allow from 10.0.0.0/8 to any port 5432
sudo ufw allow from 172.16.0.0/12 to any port 5432
sudo ufw allow from 192.168.0.0/16 to any port 5432
sudo ufw deny 5432

# 2. 配置fail2ban防止暴力破解
sudo apt install -y fail2ban

sudo tee /etc/fail2ban/jail.d/postgresql.conf > /dev/null << 'EOF'
[postgresql]
enabled = true
port = 5432
filter = postgresql
logpath = /var/log/postgresql/postgresql-*.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

sudo systemctl restart fail2ban
```

## 7. 故障排除指南

### 7.1 常见问题诊断

```bash
# 创建故障排除脚本
sudo tee /opt/ai-platform/scripts/troubleshoot_postgresql.sh > /dev/null << 'EOF'
#!/bin/bash
# PostgreSQL 故障排除脚本

echo "PostgreSQL 故障排除工具"
echo "======================"

# 1. 检查服务状态
echo "1. 检查 PostgreSQL 服务状态："
sudo systemctl status postgresql

# 2. 检查端口监听
echo -e "\n2. 检查端口监听："
sudo netstat -tlnp | grep :5432

# 3. 检查进程
echo -e "\n3. 检查 PostgreSQL 进程："
ps aux | grep postgres

# 4. 检查日志
echo -e "\n4. 最近的错误日志："
sudo tail -20 /var/log/postgresql/postgresql-16-main.log

# 5. 检查连接
echo -e "\n5. 测试数据库连接："
sudo -u postgres pg_isready -h localhost -p 5432

# 6. 检查磁盘空间
echo -e "\n6. 检查磁盘空间："
df -h /var/lib/postgresql/

# 7. 检查内存使用
echo -e "\n7. 检查内存使用："
free -h

# 8. 检查配置文件语法
echo -e "\n8. 检查配置文件语法："
sudo -u postgres postgres --check-config

echo -e "\n故障排除完成"
EOF

sudo chmod +x /opt/ai-platform/scripts/troubleshoot_postgresql.sh
```

### 7.2 性能问题解决

```bash
# 创建性能问题解决脚本
sudo tee /opt/ai-platform/scripts/fix_performance_issues.sql > /dev/null << 'EOF'
-- PostgreSQL 性能问题修复查询

-- 1. 重建统计信息
ANALYZE;

-- 2. 清理死元组
VACUUM ANALYZE;

-- 3. 重建索引（谨慎使用）
-- REINDEX DATABASE ai_platform_db;

-- 4. 更新扩展统计信息
SELECT pg_stat_reset();

-- 5. 检查锁等待
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    backend_start,
    query_start,
    state,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY query_start;

-- 6. 检查阻塞查询
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.GRANTED;
EOF
```

## 8. 集成验证

### 8.1 连接测试脚本

```bash
# 创建集成测试脚本
sudo tee /opt/ai-platform/scripts/test_postgresql_integration.py > /dev/null << 'EOF'
#!/usr/bin/env python3
"""
PostgreSQL 集成测试脚本
验证数据库安装和配置是否正确
"""

import psycopg2
import json
import sys
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ai_platform_db',
    'user': 'ai_platform',
    'password': 'AI_Platform_2024_Secure'
}

def test_connection():
    """测试数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ 数据库连接成功")
        print(f"  版本: {version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False

def test_extensions():
    """测试扩展安装"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查 pgvector 扩展
        cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        if result:
            print(f"✓ pgvector 扩展已安装: {result[1]}")
        else:
            print("✗ pgvector 扩展未安装")
            return False
            
        # 测试向量操作
        cursor.execute("SELECT '[1,2,3]'::vector;")
        print("✓ 向量操作测试通过")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 扩展测试失败: {e}")
        return False

def test_schemas():
    """测试模式创建"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        expected_schemas = ['auth', 'data_platform', 'algo_platform', 'model_platform', 'service_platform']
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name IN %s;", (tuple(expected_schemas),))
        results = [row[0] for row in cursor.fetchall()]
        
        for schema in expected_schemas:
            if schema in results:
                print(f"✓ 模式 {schema} 已创建")
            else:
                print(f"✗ 模式 {schema} 未找到")
                return False
                
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 模式测试失败: {e}")
        return False

def test_performance():
    """测试基本性能"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 测试向量相似度搜索性能
        start_time = datetime.now()
        cursor.execute("""
            CREATE TEMPORARY TABLE temp_vectors AS 
            SELECT generate_series(1, 1000) as id, 
                   array_to_string(array(select random() from generate_series(1, 1536)), ',')::vector as embedding;
        """)
        
        cursor.execute("""
            SELECT id FROM temp_vectors 
            ORDER BY embedding <-> '[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]'::vector 
            LIMIT 10;
        """)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✓ 向量搜索性能测试通过 (耗时: {duration:.3f}秒)")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 性能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("PostgreSQL 集成测试")
    print("==================")
    
    tests = [
        ("数据库连接", test_connection),
        ("扩展安装", test_extensions),
        ("模式创建", test_schemas),
        ("性能测试", test_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n正在执行: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"测试失败: {test_name}")
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过，PostgreSQL 配置正确")
        sys.exit(0)
    else:
        print("✗ 部分测试失败，请检查配置")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

# 安装测试依赖
sudo apt install -y python3-psycopg2

# 设置执行权限
sudo chmod +x /opt/ai-platform/scripts/test_postgresql_integration.py

# 运行集成测试
sudo python3 /opt/ai-platform/scripts/test_postgresql_integration.py
```

## 📚 相关文档

- **前置步骤**: [系统环境配置](../01_environment_setup.md)
- **后续步骤**: [Redis 7.0 部署](./04_redis_deployment.md)
- **相关配置**: [权限管理配置](../07_permission_management.md)
- **监控配置**: [数据库监控与维护](./06_monitoring_maintenance.md)

## 🔗 外部资源

- [PostgreSQL 16 官方文档](https://www.postgresql.org/docs/16/)
- [pgvector 扩展文档](https://github.com/pgvector/pgvector)
- [Ubuntu 24.04 LTS PostgreSQL 包](https://packages.ubuntu.com/noble/postgresql-16)
- [PostgreSQL 性能调优指南](https://wiki.postgresql.org/wiki/Performance_Optimization)

---

**下一步**: 继续部署 [Redis 缓存服务](./04_redis_deployment.md)
