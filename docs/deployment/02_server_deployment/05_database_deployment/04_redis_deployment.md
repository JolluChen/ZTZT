# Redis 7.0 部署指南

[![Ubuntu 24.04 LTS](https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420?style=flat-square&logo=ubuntu)](https://ubuntu.com/) [![Redis 7.0](https://img.shields.io/badge/Redis-7.0-DC382D?style=flat-square&logo=redis)](https://redis.io/) [![高性能缓存](https://img.shields.io/badge/Performance-High-4CAF50?style=flat-square)](https://redis.io/docs/management/optimization/)

**部署阶段**: 第二阶段 - 服务器部署  
**预计时间**: 45分钟-1.5小时  
**难度级别**: ⭐⭐  
**前置要求**: [PostgreSQL 16 部署](./01_postgresql_deployment.md) 完成

本文档详细说明如何在 Ubuntu 24.04 LTS 物理服务器环境中部署和配置 Redis 7.0 缓存服务，专为 AI 中台项目优化，包含高可用性和监控配置。

## 📋 部署概览

| 组件 | 版本 | 用途 | 部署时间 |
|------|------|------|----------|
| Redis Server | 7.0.x | 主缓存服务 | 20-30分钟 |
| Redis Sentinel | 7.0.x | 高可用监控 | 15-20分钟 |
| 性能调优 | - | 配置优化 | 10-15分钟 |
| 监控配置 | - | Redis Exporter | 10-15分钟 |

## 1. 部署策略选择

Redis 在 AI 中台项目中用于缓存、会话存储和临时数据管理。根据详细键设计规范（参考 `database_design.md`），选择最适合的部署方式：

### 1.1 推荐部署方式对比

| 部署方式 | 适用环境 | 复杂度 | 维护难度 | 性能 | 高可用 |
|----------|----------|--------|----------|------|--------|
| **APT 直接安装** | 生产环境 | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Docker 单实例 | 开发/测试 | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Docker Compose | 小规模生产 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Kubernetes | 大规模生产 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 1.2 Ubuntu 24.04 LTS 原生安装（推荐）

Ubuntu 24.04 LTS 提供了最新的 Redis 7.0 包，是生产环境的最佳选择：

```bash
# 1. 更新系统包索引
sudo apt update && sudo apt upgrade -y

# 2. 安装 Redis 7.0 及工具
sudo apt install -y \
    redis-server \
    redis-tools \
    redis-sentinel \
    python3-redis \
    build-essential

# 3. 验证安装版本
redis-server --version
redis-cli --version

# 4. 检查服务状态
sudo systemctl status redis-server
sudo systemctl enable redis-server
```

### 1.3 生产级配置

```bash
# 1. 备份原始配置
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# 2. 创建优化的 Redis 配置
sudo tee /etc/redis/redis.conf > /dev/null << 'EOF'
# Redis 7.0 生产配置 - Ubuntu 24.04 LTS 优化
# 自动生成于 $(date)

################################## 网络 #####################################
bind 127.0.0.1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16
protected-mode yes
port 6379
tcp-backlog 511
timeout 300
tcp-keepalive 300

################################# TLS/SSL ####################################
# TLS/SSL 配置（生产环境启用）
# port 0
# tls-port 6380
# tls-cert-file redis.crt
# tls-key-file redis.key
# tls-ca-cert-file ca.crt

################################# 通用配置 ###################################
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16

################################ 快照配置 ####################################
# 持久化配置 - 根据数据重要性调整
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

################################# 复制配置 ###################################
# replica-serve-stale-data yes
# replica-read-only yes
# repl-diskless-sync no
# repl-diskless-sync-delay 5

################################## 安全配置 ##################################
requirepass AI_Platform_Redis_2024_Secure
# rename-command FLUSHDB ""
# rename-command FLUSHALL ""
# rename-command KEYS ""
# rename-command CONFIG "CONFIG_b840fc02d524045429941cc15f59e41cb7be6c52"

################################### 客户端配置 ################################
maxclients 10000

############################## 内存管理配置 ##################################
maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

############################# 延迟释放配置 ####################################
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
replica-lazy-flush yes

############################ AOF 持久化配置 ###################################
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes

################################ LUA 脚本配置 #################################
lua-time-limit 5000

################################ 慢日志配置 ###################################
slowlog-log-slower-than 10000
slowlog-max-len 128

################################ 延迟监控配置 #################################
latency-monitor-threshold 100

############################# 事件通知配置 ####################################
notify-keyspace-events Ex

############################### 高级配置 ####################################
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes

# ACL 配置
aclfile /etc/redis/users.acl
EOF

# 3. 创建 ACL 用户配置
sudo tee /etc/redis/users.acl > /dev/null << 'EOF'
# Redis ACL 用户配置

# 默认用户 - 仅允许基本操作
user default on >AI_Platform_Redis_2024_Secure ~* &* -@all +@read +@write +@list +@hash +@set +@sorted_set +@string +@bitmap +@hyperloglog +@geo +@stream +@pubsub +@transaction +info +ping +auth

# AI 平台应用用户
user ai_platform on >AI_Platform_App_Redis_2024 ~ai:* ~session:* ~cache:* +@all -@dangerous

# 只读监控用户
user monitor on >Monitor_Redis_2024 ~* +@read +info +ping +client +config +latency +memory +slowlog

# 管理员用户
user admin on >Admin_Redis_2024 ~* +@all
EOF

# 4. 设置正确的权限
sudo chown redis:redis /etc/redis/redis.conf
sudo chown redis:redis /etc/redis/users.acl
sudo chmod 640 /etc/redis/redis.conf
sudo chmod 640 /etc/redis/users.acl

# 5. 创建必要的目录
sudo mkdir -p /var/lib/redis /var/log/redis /var/run/redis
sudo chown redis:redis /var/lib/redis /var/log/redis /var/run/redis
sudo chmod 750 /var/lib/redis /var/log/redis /var/run/redis

# 6. 重启 Redis 服务
sudo systemctl restart redis-server
sudo systemctl status redis-server
```

### 1.4 系统级别优化

```bash
# 1. 配置系统内核参数
sudo tee -a /etc/sysctl.conf > /dev/null << 'EOF'

# Redis 优化参数
# 内存过量使用处理
vm.overcommit_memory = 1

# 禁用透明大页
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag

# 网络优化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# 文件描述符限制
fs.file-max = 100000
EOF

# 应用内核参数
sudo sysctl -p

# 2. 配置透明大页禁用（永久生效）
sudo tee /etc/systemd/system/disable-thp.service > /dev/null << 'EOF'
[Unit]
Description=Disable Transparent Huge Pages (THP)
DefaultDependencies=no
After=sysinit.target local-fs.target
Before=redis.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo never > /sys/kernel/mm/transparent_hugepage/enabled'
ExecStart=/bin/sh -c 'echo never > /sys/kernel/mm/transparent_hugepage/defrag'

[Install]
WantedBy=basic.target
EOF

sudo systemctl enable disable-thp.service
sudo systemctl start disable-thp.service

# 3. 配置系统限制
sudo tee /etc/security/limits.d/redis.conf > /dev/null << 'EOF'
redis soft nofile 65535
redis hard nofile 65535
redis soft nproc 32768
redis hard nproc 32768
redis soft memlock unlimited
redis hard memlock unlimited
EOF

# 4. 配置 systemd 服务限制
sudo mkdir -p /etc/systemd/system/redis-server.service.d
sudo tee /etc/systemd/system/redis-server.service.d/override.conf > /dev/null << 'EOF'
[Service]
LimitNOFILE=65535
LimitNPROC=32768
LimitMEMLOCK=infinity
OOMScoreAdjust=-900
EOF

# 重载 systemd 配置
sudo systemctl daemon-reload
sudo systemctl restart redis-server
```

### 1.5 Docker 部署（开发/测试环境）

使用 Docker Compose 简化部署：

```bash
# 创建 docker-compose.yml
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

# 创建 Redis 配置文件
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

### 1.3 Kubernetes 部署 (推荐生产环境)

使用 Bitnami Redis Helm Chart：

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
    storageClass: "local-storage"
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
    storageClass: "local-storage"
sentinel:
  enabled: true
EOF

# 安装 Redis
helm install ai-redis bitnami/redis -f redis-values.yaml -n database
```

### 1.4 Docker 部署方案

适用于开发环境和容器化部署需求：

```bash
# 创建 Redis 数据目录
sudo mkdir -p /opt/redis/data
sudo mkdir -p /opt/redis/conf
sudo mkdir -p /opt/redis/logs

# 创建 Redis 配置文件
sudo tee /opt/redis/conf/redis.conf > /dev/null << 'EOF'
# Redis 7.0 Docker 配置
bind 0.0.0.0
port 6379
protected-mode yes
requirepass AI_Platform_Redis_2024_Docker

# 持久化配置
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfilename "appendonly.aof"

# 内存配置
maxmemory 1gb
maxmemory-policy allkeys-lru

# 安全配置
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command DEBUG ""
rename-command CONFIG AI_REDIS_CONFIG_2024

# 日志配置
loglevel notice
logfile "/var/log/redis/redis.log"
EOF

# 启动 Redis 容器
docker run -d \
  --name ai-redis \
  --restart=unless-stopped \
  -p 6379:6379 \
  -v /opt/redis/data:/data \
  -v /opt/redis/conf/redis.conf:/etc/redis/redis.conf \
  -v /opt/redis/logs:/var/log/redis \
  redis:7.0-alpine redis-server /etc/redis/redis.conf

# 验证部署
docker logs ai-redis
docker exec ai-redis redis-cli -a AI_Platform_Redis_2024_Docker ping
```

### 1.5 Docker Compose 部署

适用于本地开发和小规模生产环境：

```yaml
# 创建 docker-compose.yml
sudo tee /opt/redis/docker-compose.yml > /dev/null << 'EOF'
version: '3.8'

services:
  redis:
    image: redis:7.0-alpine
    container_name: ai-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - ./data:/data
      - ./conf/redis.conf:/etc/redis/redis.conf
      - ./logs:/var/log/redis
    command: redis-server /etc/redis/redis.conf
    environment:
      - REDIS_PASSWORD=AI_Platform_Redis_2024_Compose
    networks:
      - ai-platform-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "AI_Platform_Redis_2024_Compose", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: redis-exporter
    restart: unless-stopped
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://redis:6379
      - REDIS_PASSWORD=AI_Platform_Redis_2024_Compose
    depends_on:
      - redis
    networks:
      - ai-platform-network

networks:
  ai-platform-network:
    driver: bridge

volumes:
  redis-data:
    driver: local
EOF

# 启动服务
cd /opt/redis
docker-compose up -d

# 验证部署
docker-compose ps
docker-compose logs redis
```

## 2. Redis Sentinel 高可用部署

Redis Sentinel 提供自动故障切换和监控功能，确保生产环境的高可用性。

### 2.1 Sentinel 集群配置

```bash
# 创建 Sentinel 配置目录
sudo mkdir -p /opt/redis/sentinel/{conf,data,logs}

# 创建主服务器 Sentinel 配置
sudo tee /opt/redis/sentinel/conf/sentinel-1.conf > /dev/null << 'EOF'
# Redis Sentinel 配置 - 节点 1
port 26379
sentinel announce-ip 192.168.1.10
sentinel announce-port 26379

# 监控配置
sentinel monitor ai-redis-master 192.168.1.10 6379 2
sentinel auth-pass ai-redis-master AI_Platform_Redis_2024_Secure
sentinel down-after-milliseconds ai-redis-master 5000
sentinel parallel-syncs ai-redis-master 1
sentinel failover-timeout ai-redis-master 10000

# 日志配置
logfile "/var/log/redis/sentinel-1.log"
loglevel notice

# 安全配置
requirepass AI_Platform_Sentinel_2024
sentinel auth-user ai-redis-master monitor

# 脚本配置
sentinel client-reconfig-script ai-redis-master /opt/redis/scripts/notify.sh
EOF

# 创建从服务器 Sentinel 配置
sudo tee /opt/redis/sentinel/conf/sentinel-2.conf > /dev/null << 'EOF'
# Redis Sentinel 配置 - 节点 2
port 26379
sentinel announce-ip 192.168.1.11
sentinel announce-port 26379

# 监控配置
sentinel monitor ai-redis-master 192.168.1.10 6379 2
sentinel auth-pass ai-redis-master AI_Platform_Redis_2024_Secure
sentinel down-after-milliseconds ai-redis-master 5000
sentinel parallel-syncs ai-redis-master 1
sentinel failover-timeout ai-redis-master 10000

# 日志配置
logfile "/var/log/redis/sentinel-2.log"
loglevel notice

# 安全配置
requirepass AI_Platform_Sentinel_2024
sentinel auth-user ai-redis-master monitor
EOF

# 创建第三个 Sentinel 配置
sudo tee /opt/redis/sentinel/conf/sentinel-3.conf > /dev/null << 'EOF'
# Redis Sentinel 配置 - 节点 3
port 26379
sentinel announce-ip 192.168.1.12
sentinel announce-port 26379

# 监控配置
sentinel monitor ai-redis-master 192.168.1.10 6379 2
sentinel auth-pass ai-redis-master AI_Platform_Redis_2024_Secure
sentinel down-after-milliseconds ai-redis-master 5000
sentinel parallel-syncs ai-redis-master 1
sentinel failover-timeout ai-redis-master 10000

# 日志配置
logfile "/var/log/redis/sentinel-3.log"
loglevel notice

# 安全配置
requirepass AI_Platform_Sentinel_2024
sentinel auth-user ai-redis-master monitor
EOF
```

### 2.2 启动 Sentinel 集群

```bash
# 创建 Sentinel 启动脚本
sudo tee /opt/redis/scripts/start-sentinel.sh > /dev/null << 'EOF'
#!/bin/bash
# Redis Sentinel 启动脚本

REDIS_HOME="/opt/redis"
CONF_DIR="${REDIS_HOME}/sentinel/conf"
LOG_DIR="${REDIS_HOME}/sentinel/logs"

# 确保日志目录存在
mkdir -p ${LOG_DIR}

# 启动 Sentinel 实例
redis-sentinel ${CONF_DIR}/sentinel-1.conf --daemonize yes
redis-sentinel ${CONF_DIR}/sentinel-2.conf --daemonize yes
redis-sentinel ${CONF_DIR}/sentinel-3.conf --daemonize yes

echo "Redis Sentinel 集群已启动"
echo "检查状态: redis-cli -p 26379 sentinel masters"
EOF

# 设置脚本权限
sudo chmod +x /opt/redis/scripts/start-sentinel.sh

# 创建故障切换通知脚本
sudo tee /opt/redis/scripts/notify.sh > /dev/null << 'EOF'
#!/bin/bash
# Redis 故障切换通知脚本

MASTER_NAME=$1
ROLE=$2
STATE=$3
FROM_IP=$4
FROM_PORT=$5
TO_IP=$6
TO_PORT=$7

LOG_FILE="/var/log/redis/failover.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[${TIMESTAMP}] Redis故障切换: ${MASTER_NAME} ${ROLE} ${STATE} ${FROM_IP}:${FROM_PORT} -> ${TO_IP}:${TO_PORT}" >> ${LOG_FILE}

# 可以在这里添加邮件通知或其他告警逻辑
# 例如：发送邮件、推送到监控系统等
EOF

# 设置通知脚本权限
sudo chmod +x /opt/redis/scripts/notify.sh

# 启动 Sentinel 集群
sudo /opt/redis/scripts/start-sentinel.sh
```

### 2.3 验证 Sentinel 部署

```bash
# 检查 Sentinel 状态
redis-cli -p 26379 -a AI_Platform_Sentinel_2024 sentinel masters
redis-cli -p 26379 -a AI_Platform_Sentinel_2024 sentinel slaves ai-redis-master
redis-cli -p 26379 -a AI_Platform_Sentinel_2024 sentinel sentinels ai-redis-master

# 测试故障切换（谨慎操作）
# redis-cli -p 26379 -a AI_Platform_Sentinel_2024 sentinel failover ai-redis-master
```

### 1.5 本地存储配置 (物理服务器上的 Kubernetes)

在物理服务器上配置 Kubernetes 本地存储：

```bash
# 创建本地存储目录
sudo mkdir -p /mnt/redis-data
sudo chmod 777 /mnt/redis-data

# 创建 Kubernetes PersistentVolume
cat > redis-pv.yaml << EOF
apiVersion: v1
kind: PersistentVolume
metadata:
  name: redis-pv-master
spec:
  capacity:
    storage: 8Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/redis-data/master
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node01  # 替换为实际的主节点名称

---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: redis-pv-replica-0
spec:
  capacity:
    storage: 8Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/redis-data/replica-0
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node02  # 替换为实际的从节点名称
EOF

# 应用配置
kubectl apply -f redis-pv.yaml
```

## 2. 连接方式

### 2.1 服务地址与端口

- **Docker 部署**: `localhost` 或主机 IP 地址，端口 6379
- **Kubernetes 部署**:
  - 主节点: `ai-redis-master.database.svc.cluster.local:6379`
  - 从节点: `ai-redis-replicas.database.svc.cluster.local:6379`
  - 哨兵: `ai-redis-headless.database.svc.cluster.local:26379`
- **裸机安装**: 服务器 IP 地址，端口 6379

### 2.2 命令行连接

```bash
# Docker 部署连接
docker exec -it redis redis-cli -a "changeThisToSecurePassword"

# Kubernetes 部署连接（从集群内部）
kubectl exec -it ai-redis-master-0 -n database -- redis-cli -a "changeThisToSecurePassword"

# Kubernetes 部署连接（从集群外部，需要端口转发）
kubectl port-forward svc/ai-redis-master -n database 6379:6379
# 然后在另一个终端：
redis-cli -h localhost -p 6379 -a "changeThisToSecurePassword"
```

### 2.3 应用程序连接

使用相应语言的 Redis 客户端库：

```python
import redis
from redis.sentinel import Sentinel

# 直接连接 Redis（单节点）
def connect_single_redis():
    r = redis.Redis(
        host='localhost',
        port=6379,
        password='changeThisToSecurePassword',
        db=0,
        decode_responses=True  # 自动将字节解码为字符串
    )
    # 测试连接
    print(f"Redis 版本: {r.info()['redis_version']}")
    return r

# 连接 Redis 哨兵集群
def connect_sentinel_redis():
    sentinel = Sentinel([
        ('ai-redis-headless.database.svc.cluster.local', 26379),
    ], socket_timeout=1.0, password='changeThisToSecurePassword')
    
    # 获取主节点连接
    master = sentinel.master_for(
        'mymaster',  # 通常为 'mymaster'，根据具体配置可能不同
        socket_timeout=0.5,
        password='changeThisToSecurePassword',
        db=0,
        decode_responses=True
    )
    
    # 获取从节点连接（用于读操作）
    slave = sentinel.slave_for(
        'mymaster',
        socket_timeout=0.5,
        password='changeThisToSecurePassword',
        db=0,
        decode_responses=True
    )
    
    return master, slave

# Redis 连接池（推荐生产环境使用）
def create_redis_pool():
    pool = redis.ConnectionPool(
        host='localhost',
        port=6379,
        password='changeThisToSecurePassword',
        db=0,
        decode_responses=True,
        max_connections=100  # 最大连接数
    )
    return redis.Redis(connection_pool=pool)
```

## 3. 安全与优化配置

### 3.1 基本安全配置

- 设置强密码认证：

```bash
# 在 Redis 配置文件中设置密码
requirepass yourStrongPassword

# 使用命令行设置密码
redis-cli
> AUTH current_password
> CONFIG SET requirepass "new_strong_password"
> CONFIG REWRITE
```

- 禁用危险命令：

```bash
# 在配置文件中添加
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG ""
rename-command EVAL ""
```

### 3.2 性能优化

根据服务器配置调整 Redis 参数：

```bash
# Redis 优化配置
cat > /etc/redis/redis.conf.d/tuning.conf << EOF
# 内存管理
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 10

# 持久化
save 900 1      # 15分钟内至少1个键变更
save 300 10     # 5分钟内至少10个键变更
save 60 10000   # 1分钟内至少10000个键变更
appendonly yes
appendfsync everysec

# 连接和网络
tcp-backlog 511
timeout 0
tcp-keepalive 300

# 高级优化
activedefrag yes  # 开启主动碎片整理
EOF
```

## 4. 键空间设计

根据 `database_design.md` 中定义的前缀分类，以下是每种前缀的使用场景和示例：

```
# 会话数据
session:user:<user_id> - 存储用户会话信息，包括登录状态、权限等
session:admin:<admin_id> - 管理员会话信息

# 令牌存储
token:access:<token_id> - 访问令牌
token:refresh:<token_id> - 刷新令牌
token:api:<api_key> - API 访问密钥

# 缓存数据
cache:user:<user_id> - 用户信息缓存
cache:model:<model_id> - 模型元数据缓存
cache:config:<config_key> - 系统配置缓存

# API 请求速率限制
rate:api:user:<user_id> - 用户 API 请求计数
rate:api:ip:<ip_address> - IP 请求计数
rate:api:endpoint:<endpoint> - 端点请求计数

# 分布式锁
lock:resource:<resource_id> - 资源锁定状态
lock:job:<job_id> - 作业执行锁

# 异步任务队列
queue:job - 作业队列
queue:notification - 通知队列
queue:log - 日志队列

# 发布/订阅通道
pubsub:system - 系统广播通道
pubsub:model-events - 模型事件通知通道
pubsub:alerts - 警报通知通道

# 统计数据
stats:user:active - 活跃用户统计
stats:api:calls - API 调用统计
stats:performance - 系统性能指标
```

## 5. 备份策略

创建自动备份脚本：

```bash
# 创建备份脚本
cat > redis-backup.sh << EOF
#!/bin/bash
# Redis 备份脚本

DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/redis"
mkdir -p \$BACKUP_DIR

# 执行备份
if [ -n "\$(docker ps -q -f name=redis)" ]; then
  # Docker 环境
  echo "在 Docker 中执行备份..."
  docker exec redis redis-cli -a "changeThisToSecurePassword" SAVE
  docker cp redis:/data/dump.rdb \$BACKUP_DIR/redis_\$DATE.rdb
else
  # 直接安装环境
  echo "在本地环境执行备份..."
  redis-cli -a "changeThisToSecurePassword" SAVE
  cp /var/lib/redis/dump.rdb \$BACKUP_DIR/redis_\$DATE.rdb
fi

# 保留最近30天的备份
find \$BACKUP_DIR -name "redis_*.rdb" -type f -mtime +30 -delete
echo "备份完成: \$BACKUP_DIR/redis_\$DATE.rdb"
EOF

# 设置脚本权限
chmod +x redis-backup.sh

# 添加到 crontab
(crontab -l 2>/dev/null; echo "0 1 * * * /path/to/redis-backup.sh") | crontab -
```

## 6. 高可用性配置

### 6.1 哨兵配置 (物理服务器)

在多台服务器上设置 Redis 哨兵：

```bash
# 创建哨兵配置
cat > sentinel.conf << EOF
port 26379
dir /tmp
sentinel monitor mymaster redis-master 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 60000
sentinel parallel-syncs mymaster 1
sentinel auth-pass mymaster changeThisToSecurePassword
EOF

# 启动哨兵服务
redis-server sentinel.conf --sentinel
```

### 6.2 Docker Compose 哨兵配置

```bash
# 创建 Docker Compose 配置
cat > docker-compose-redis-sentinel.yml << EOF
version: '3.8'

services:
  redis-master:
    image: redis:7.0
    container_name: redis-master
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - ./redis-master.conf:/usr/local/etc/redis/redis.conf
      - redis_master_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  redis-replica-1:
    image: redis:7.0
    container_name: redis-replica-1
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - ./redis-replica.conf:/usr/local/etc/redis/redis.conf
      - redis_replica1_data:/data
    ports:
      - "6380:6379"
    depends_on:
      - redis-master
    restart: unless-stopped
    
  redis-replica-2:
    image: redis:7.0
    container_name: redis-replica-2
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - ./redis-replica.conf:/usr/local/etc/redis/redis.conf
      - redis_replica2_data:/data
    ports:
      - "6381:6379"
    depends_on:
      - redis-master
    restart: unless-stopped

  redis-sentinel-1:
    image: redis:7.0
    container_name: redis-sentinel-1
    command: redis-server /usr/local/etc/redis/sentinel.conf --sentinel
    volumes:
      - ./sentinel-1.conf:/usr/local/etc/redis/sentinel.conf
    ports:
      - "26379:26379"
    depends_on:
      - redis-master
    restart: unless-stopped

  redis-sentinel-2:
    image: redis:7.0
    container_name: redis-sentinel-2
    command: redis-server /usr/local/etc/redis/sentinel.conf --sentinel
    volumes:
      - ./sentinel-2.conf:/usr/local/etc/redis/sentinel.conf
    ports:
      - "26380:26379"
    depends_on:
      - redis-master
    restart: unless-stopped
    
  redis-sentinel-3:
    image: redis:7.0
    container_name: redis-sentinel-3
    command: redis-server /usr/local/etc/redis/sentinel.conf --sentinel
    volumes:
      - ./sentinel-3.conf:/usr/local/etc/redis/sentinel.conf
    ports:
      - "26381:26379"
    depends_on:
      - redis-master
    restart: unless-stopped

volumes:
  redis_master_data:
    driver: local
  redis_replica1_data:
    driver: local
  redis_replica2_data:
    driver: local
EOF
```

## 7. 最佳实践

1. **使用连接池**:
   - 使用语言客户端提供的连接池功能
   - 合理配置连接池大小，避免连接过多或过少

2. **适当设置过期时间**:
   - 为缓存数据设置合理的 TTL (Time To Live)
   - 避免存储过多不必要的长期数据

3. **批量操作**:
   - 使用 Pipeline 或 MULTI/EXEC 批量操作命令
   - 减少网络往返，提高性能

4. **内存管理**:
   - 定期监控内存使用情况，设置合适的 maxmemory
   - 根据业务需求选择合适的淘汰策略

5. **避免大键**:
   - 避免存储特别大的键值对
   - 对于大型数据，考虑分割或使用其他存储方式

## 6. 监控与性能调优

### 6.1 Redis Exporter 部署

```bash
# 下载并安装 Redis Exporter
cd /tmp
wget https://github.com/oliver006/redis_exporter/releases/download/v1.55.0/redis_exporter-v1.55.0.linux-amd64.tar.gz
tar xzf redis_exporter-v1.55.0.linux-amd64.tar.gz
sudo mv redis_exporter-v1.55.0.linux-amd64/redis_exporter /usr/local/bin/

# 创建 systemd 服务
sudo tee /etc/systemd/system/redis-exporter.service > /dev/null << 'EOF'
[Unit]
Description=Redis Exporter
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=redis
Group=redis
ExecStart=/usr/local/bin/redis_exporter \
  -redis.addr=localhost:6379 \
  -redis.password=AI_Platform_Redis_2024_Secure \
  -web.listen-address=:9121 \
  -redis.password-file=/etc/redis/redis_exporter_password
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 创建密码文件
echo "AI_Platform_Redis_2024_Secure" | sudo tee /etc/redis/redis_exporter_password > /dev/null
sudo chown redis:redis /etc/redis/redis_exporter_password
sudo chmod 600 /etc/redis/redis_exporter_password

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable redis-exporter
sudo systemctl start redis-exporter
```

### 6.2 性能监控脚本

```bash
# 创建监控脚本目录
sudo mkdir -p /opt/redis/monitoring

# 创建性能监控脚本
sudo tee /opt/redis/monitoring/redis_monitor.sh > /dev/null << 'EOF'
#!/bin/bash
# Redis 性能监控脚本

REDIS_CLI="redis-cli -a AI_Platform_Redis_2024_Secure"
LOG_FILE="/var/log/redis/performance.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 创建日志目录
mkdir -p /var/log/redis

# 获取 Redis 信息
MEMORY_USAGE=$($REDIS_CLI INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
CONNECTED_CLIENTS=$($REDIS_CLI INFO clients | grep connected_clients | cut -d: -f2 | tr -d '\r')
KEYSPACE_HITS=$($REDIS_CLI INFO stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
KEYSPACE_MISSES=$($REDIS_CLI INFO stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')

# 计算命中率
if [ "$KEYSPACE_MISSES" != "0" ]; then
    HIT_RATE=$(echo "scale=2; $KEYSPACE_HITS / ($KEYSPACE_HITS + $KEYSPACE_MISSES) * 100" | bc)
else
    HIT_RATE="100.00"
fi

# 记录监控数据
echo "[${TIMESTAMP}] Memory: ${MEMORY_USAGE}, Clients: ${CONNECTED_CLIENTS}, Hit Rate: ${HIT_RATE}%" >> ${LOG_FILE}

# 检查内存使用警告
MEMORY_BYTES=$($REDIS_CLI INFO memory | grep used_memory: | cut -d: -f2 | tr -d '\r')
MAX_MEMORY=$($REDIS_CLI CONFIG GET maxmemory | tail -1)

if [ "$MAX_MEMORY" != "0" ] && [ "$MEMORY_BYTES" -gt $((MAX_MEMORY * 80 / 100)) ]; then
    echo "[${TIMESTAMP}] WARNING: Redis memory usage above 80%" >> ${LOG_FILE}
fi

# 检查慢查询
SLOW_QUERIES=$($REDIS_CLI SLOWLOG LEN)
if [ "$SLOW_QUERIES" -gt 10 ]; then
    echo "[${TIMESTAMP}] WARNING: ${SLOW_QUERIES} slow queries detected" >> ${LOG_FILE}
fi
EOF

# 设置权限
sudo chmod +x /opt/redis/monitoring/redis_monitor.sh

# 创建 cron 任务
echo "*/5 * * * * /opt/redis/monitoring/redis_monitor.sh" | sudo crontab -u redis -
```

### 6.3 健康检查脚本

```bash
# 创建健康检查脚本
sudo tee /opt/redis/monitoring/health_check.sh > /dev/null << 'EOF'
#!/bin/bash
# Redis 健康检查脚本

REDIS_CLI="redis-cli -a AI_Platform_Redis_2024_Secure"
EXIT_CODE=0

echo "==================== Redis 健康检查 ===================="
echo "检查时间: $(date)"
echo ""

# 1. 检查 Redis 服务状态
echo "1. 检查 Redis 服务状态..."
if systemctl is-active --quiet redis-server; then
    echo "   ✅ Redis 服务运行正常"
else
    echo "   ❌ Redis 服务未运行"
    EXIT_CODE=1
fi

# 2. 检查连接性
echo "2. 检查 Redis 连接性..."
if $REDIS_CLI ping > /dev/null 2>&1; then
    echo "   ✅ Redis 连接正常"
else
    echo "   ❌ Redis 连接失败"
    EXIT_CODE=1
fi

# 3. 检查内存使用
echo "3. 检查内存使用..."
MEMORY_USAGE=$($REDIS_CLI INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
echo "   当前内存使用: ${MEMORY_USAGE}"

# 4. 检查客户端连接数
echo "4. 检查客户端连接..."
CONNECTED_CLIENTS=$($REDIS_CLI INFO clients | grep connected_clients | cut -d: -f2 | tr -d '\r')
echo "   当前连接数: ${CONNECTED_CLIENTS}"

# 5. 检查持久化状态
echo "5. 检查持久化状态..."
LAST_SAVE=$($REDIS_CLI LASTSAVE)
echo "   最后保存时间: $(date -d @${LAST_SAVE})"

# 6. 检查复制状态（如果有从库）
echo "6. 检查复制状态..."
ROLE=$($REDIS_CLI INFO replication | grep role | cut -d: -f2 | tr -d '\r')
echo "   当前角色: ${ROLE}"

if [ "$ROLE" = "master" ]; then
    CONNECTED_SLAVES=$($REDIS_CLI INFO replication | grep connected_slaves | cut -d: -f2 | tr -d '\r')
    echo "   连接的从库数: ${CONNECTED_SLAVES}"
fi

# 7. 检查慢查询
echo "7. 检查慢查询..."
SLOW_QUERIES=$($REDIS_CLI SLOWLOG LEN)
echo "   慢查询数量: ${SLOW_QUERIES}"

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "🎉 Redis 健康检查完成，所有检查项通过"
else
    echo "⚠️  Redis 健康检查发现问题，请检查上述错误"
fi

exit $EXIT_CODE
EOF

# 设置权限
sudo chmod +x /opt/redis/monitoring/health_check.sh

# 运行健康检查
sudo -u redis /opt/redis/monitoring/health_check.sh
```

## 7. 备份与恢复策略

### 7.1 自动备份脚本

```bash
# 创建备份目录
sudo mkdir -p /opt/redis/backups/{daily,weekly,monthly}

# 创建备份脚本
sudo tee /opt/redis/backups/backup_redis.sh > /dev/null << 'EOF'
#!/bin/bash
# Redis 自动备份脚本

REDIS_CLI="redis-cli -a AI_Platform_Redis_2024_Secure"
BACKUP_DIR="/opt/redis/backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
DATE=$(date '+%Y%m%d')

# 创建备份目录
mkdir -p ${BACKUP_DIR}/daily
mkdir -p ${BACKUP_DIR}/weekly
mkdir -p ${BACKUP_DIR}/monthly

# 执行 RDB 备份
echo "开始 Redis 备份: $(date)"
$REDIS_CLI BGSAVE

# 等待备份完成
while [ $($REDIS_CLI LASTSAVE) -eq $($REDIS_CLI LASTSAVE) ]; do
    sleep 1
done

# 复制 RDB 文件
if [ -f /var/lib/redis/dump.rdb ]; then
    cp /var/lib/redis/dump.rdb ${BACKUP_DIR}/daily/dump_${TIMESTAMP}.rdb
    
    # 压缩备份文件
    gzip ${BACKUP_DIR}/daily/dump_${TIMESTAMP}.rdb
    
    echo "备份完成: dump_${TIMESTAMP}.rdb.gz"
    
    # 创建软链接到最新备份
    ln -sf ${BACKUP_DIR}/daily/dump_${TIMESTAMP}.rdb.gz ${BACKUP_DIR}/latest_backup.rdb.gz
else
    echo "错误: 找不到 RDB 文件"
    exit 1
fi

# 如果是周日，创建周备份
if [ $(date +%u) -eq 7 ]; then
    cp ${BACKUP_DIR}/daily/dump_${TIMESTAMP}.rdb.gz ${BACKUP_DIR}/weekly/dump_week_${DATE}.rdb.gz
    echo "创建周备份: dump_week_${DATE}.rdb.gz"
fi

# 如果是月初，创建月备份
if [ $(date +%d) -eq 01 ]; then
    cp ${BACKUP_DIR}/daily/dump_${TIMESTAMP}.rdb.gz ${BACKUP_DIR}/monthly/dump_month_${DATE}.rdb.gz
    echo "创建月备份: dump_month_${DATE}.rdb.gz"
fi

# 清理旧备份
find ${BACKUP_DIR}/daily -name "dump_*.rdb.gz" -mtime +7 -delete
find ${BACKUP_DIR}/weekly -name "dump_week_*.rdb.gz" -mtime +30 -delete
find ${BACKUP_DIR}/monthly -name "dump_month_*.rdb.gz" -mtime +365 -delete

echo "备份任务完成: $(date)"
EOF

# 设置权限
sudo chmod +x /opt/redis/backups/backup_redis.sh

# 添加到 crontab（每天凌晨2点备份）
echo "0 2 * * * /opt/redis/backups/backup_redis.sh >> /var/log/redis/backup.log 2>&1" | sudo crontab -u redis -
```

### 7.2 恢复脚本

```bash
# 创建恢复脚本
sudo tee /opt/redis/backups/restore_redis.sh > /dev/null << 'EOF'
#!/bin/bash
# Redis 恢复脚本

BACKUP_FILE=$1
REDIS_DATA_DIR="/var/lib/redis"

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <备份文件路径>"
    echo "示例: $0 /opt/redis/backups/daily/dump_20241201_020000.rdb.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "准备恢复 Redis 数据..."
echo "备份文件: $BACKUP_FILE"

# 停止 Redis 服务
echo "停止 Redis 服务..."
sudo systemctl stop redis-server

# 备份当前数据文件
if [ -f "${REDIS_DATA_DIR}/dump.rdb" ]; then
    mv "${REDIS_DATA_DIR}/dump.rdb" "${REDIS_DATA_DIR}/dump.rdb.backup.$(date +%Y%m%d_%H%M%S)"
    echo "当前数据已备份"
fi

# 解压并恢复数据文件
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" > "${REDIS_DATA_DIR}/dump.rdb"
else
    cp "$BACKUP_FILE" "${REDIS_DATA_DIR}/dump.rdb"
fi

# 设置正确的权限
chown redis:redis "${REDIS_DATA_DIR}/dump.rdb"
chmod 660 "${REDIS_DATA_DIR}/dump.rdb"

# 启动 Redis 服务
echo "启动 Redis 服务..."
sudo systemctl start redis-server

# 验证恢复
sleep 3
if redis-cli -a AI_Platform_Redis_2024_Secure ping > /dev/null 2>&1; then
    echo "✅ Redis 恢复成功"
    echo "键数量: $(redis-cli -a AI_Platform_Redis_2024_Secure DBSIZE)"
else
    echo "❌ Redis 恢复失败"
    exit 1
fi
EOF

# 设置权限
sudo chmod +x /opt/redis/backups/restore_redis.sh
```

## 8. 故障排除

### 8.1 常见问题

1. **连接被拒绝**
   - 检查 Redis 服务是否运行
   - 验证网络连通性和防火墙配置
   - 确认认证密码是否正确

2. **内存不足**
   - 检查 maxmemory 设置
   - 监控 used_memory 和 used_memory_peak 指标
   - 适当调整淘汰策略或增加内存

3. **性能下降**
   - 检查慢日志 (`SLOWLOG GET`)
   - 监控命中率和延迟
   - 调整持久化策略

### 8.2 性能监控

```bash
# 检查 Redis 信息
redis-cli -a "yourpassword" INFO

# 监控内存使用
redis-cli -a "yourpassword" INFO memory

# 查看客户端连接
redis-cli -a "yourpassword" CLIENT LIST

# 查看慢日志
redis-cli -a "yourpassword" SLOWLOG GET
```

## 相关资源

- [Redis 官方文档](https://redis.io/documentation)
- [Redis 命令参考](https://redis.io/commands)
- [Redis 持久化指南](https://redis.io/topics/persistence)
- [Redis 哨兵文档](https://redis.io/topics/sentinel)
