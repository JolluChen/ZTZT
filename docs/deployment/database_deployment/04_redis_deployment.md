# Redis 7.0 部署指南

本文档详细说明如何在物理服务器环境中部署和配置 Redis 7.0 缓存服务，用于 AI 中台项目。

## 1. 部署选项

Redis 用于缓存和临时数据存储，提高系统性能，详细键设计见 `database_design.md`。

### 1.1 Docker 部署

使用 Docker 部署 Redis 是开发环境或单节点环境的简单选择：

```bash
# 创建持久化存储卷目录
mkdir -p /data/redis/data

# 创建 Redis 配置文件
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

# 运行 Redis 实例
docker run -d --name redis \
  -p 6379:6379 \
  -v /data/redis/data:/data \
  -v /data/redis/redis.conf:/usr/local/etc/redis/redis.conf \
  --restart unless-stopped \
  redis:7.0 redis-server /usr/local/etc/redis/redis.conf
```

### 1.2 Docker Compose 部署

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

### 1.4 直接安装（裸机服务器）

如果您希望直接在物理服务器或虚拟机上安装 Redis，而不使用容器化技术：

```bash
# 安装 Redis
sudo apt update
sudo apt install -y redis-server

# 编辑 Redis 配置文件
sudo nano /etc/redis/redis.conf

# 配置 Redis 允许远程访问（如需要）
# 修改 bind 指令为：
# bind 0.0.0.0

# 设置密码
# requirepass yoursecurepassword

# 启用 AOF 持久化
# appendonly yes

# 调整内存限制
# maxmemory 1gb
# maxmemory-policy allkeys-lru

# 重启 Redis 服务
sudo systemctl restart redis-server
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
