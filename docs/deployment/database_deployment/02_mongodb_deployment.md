# MongoDB 6.0 部署指南

本文档详细说明如何在物理服务器环境中部署和配置 MongoDB 6.0 数据库服务，用于 AI 中台项目。

## 1. 部署选项

MongoDB 主要用于存储日志数据、临时缓存和配置文件，详细集合设计见 `database_design.md`。

### 1.1 Docker 部署

使用 Docker 部署 MongoDB 是开发环境或单节点环境的简单选择：

```bash
# 创建持久化存储卷目录
mkdir -p /data/mongodb/data

# 运行 MongoDB 实例
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

### 1.2 Docker Compose 部署

使用 Docker Compose 简化部署：

```bash
# 创建 docker-compose.yml
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

### 1.3 Kubernetes 部署 (推荐生产环境)

使用 Bitnami MongoDB Helm Chart：

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
  storageClass: "local-storage"  # 使用本地存储，或根据实际环境调整为您的存储类
resources:
  requests:
    memory: "1Gi"
    cpu: "0.5"
  limits:
    memory: "2Gi"
    cpu: "1"
EOF

# 安装 MongoDB
helm install ai-mongodb bitnami/mongodb -f mongodb-values.yaml -n database
```

**副本集 (Replica Set)**: 强烈建议启用副本集以保证高可用性和数据冗余。

### 1.4 直接安装（裸机服务器）

如果您希望直接在物理服务器或虚拟机上安装 MongoDB，而不使用容器化技术：

```bash
# 安装 MongoDB 社区版
# 导入公钥
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# 创建 MongoDB 源文件
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# 更新软件包列表
sudo apt update

# 安装 MongoDB
sudo apt install -y mongodb-org

# 启动 MongoDB 服务
sudo systemctl enable mongod
sudo systemctl start mongod

# 配置 MongoDB 允许远程访问
sudo nano /etc/mongod.conf
# 将 bindIp 改为 0.0.0.0 或者特定 IP
# 添加安全配置
# security:
#   authorization: enabled

# 重启 MongoDB 以应用更改
sudo systemctl restart mongod

# 创建管理员用户
mongosh --eval 'db.getSiblingDB("admin").createUser({user: "admin", pwd: "securePassword", roles: ["root"]})'

# 创建应用数据库和用户
mongosh --eval 'db.getSiblingDB("ai_platform").createUser({user: "ai_platform_user", pwd: "securePassword", roles: [{role: "readWrite", db: "ai_platform"}, {role: "dbAdmin", db: "ai_platform"}]})'
```

配置高性能设置：

```bash
# 编辑 MongoDB 配置文件
sudo nano /etc/mongod.conf

# 添加或修改以下配置（根据服务器硬件调整）
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2  # 设置为服务器 RAM 的 50% 左右
      
# 设置副本集（即使在单节点环境下，也有助于未来扩展）
replication:
  replSetName: "rs0"
```

## 2. 连接方式

### 2.1 服务地址与端口

- **Docker 部署**: `localhost` 或主机 IP 地址，端口 27017
- **Kubernetes 内部**: `<service-name>.<namespace>.svc.cluster.local` (例如: `ai-mongodb.database.svc.cluster.local`)
- **裸机安装**: 服务器 IP 地址，端口 27017

### 2.2 命令行连接

```bash
# Docker 部署连接
mongosh mongodb://localhost:27017/ai_platform -u ai_platform_user -p "changeThisToSecurePassword"

# Kubernetes 部署连接（从集群内部）
kubectl exec -it ai-mongodb-0 -n database -- mongosh mongodb://ai_platform_user:changeThisToSecurePassword@localhost:27017/ai_platform

# Kubernetes 部署连接（从集群外部，需要端口转发）
kubectl port-forward svc/ai-mongodb -n database 27017:27017
# 然后在另一个终端：
mongosh mongodb://ai_platform_user:changeThisToSecurePassword@localhost:27017/ai_platform
```

### 2.3 应用程序连接

使用相应语言的 MongoDB 驱动程序:

```python
from pymongo import MongoClient
import datetime

# 创建 MongoDB 客户端连接
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

## 3. 安全与配置

### 3.1 基本安全配置

- 启用认证 (`auth`):

```bash
# Docker 环境下，修改 MongoDB 配置
cat > /data/mongodb/mongod.conf << EOF
security:
  authorization: enabled
net:
  bindIp: 127.0.0.1,192.168.1.100  # 仅允许指定 IP 访问，请替换为您的实际 IP
EOF

# 重新启动 MongoDB 容器
docker restart mongodb
```

- 配置基于角色的访问控制 (RBAC):

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

### 3.2 性能优化

```bash
# 修改 MongoDB 配置文件
cat > /etc/mongod.conf.d/tuning.conf << EOF
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4  # 调整为服务器内存的 50%
      journalCompressor: zstd  # 更高效的压缩算法
      directoryForIndexes: true  # 索引单独存储
    
operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100

net:
  maxIncomingConnections: 2000
  
replication:
  oplogSizeMB: 2048  # 增加 oplog 大小

setParameter:
  internalQueryExecMaxBlockingSortBytes: 104857600  # 100MB，防止大型排序操作报错
EOF

# 应用配置
sudo systemctl restart mongod

# 或者在 Docker 中
docker restart mongodb
```

## 4. 集合初始化

部署后创建必要的集合并设置索引：

```bash
# 连接到 MongoDB
kubectl exec -it ai-mongodb-0 -- mongosh -u ai_platform -p "yourPassword" --authenticationDatabase ai_platform

# 在 MongoDB shell 中执行以下命令
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

// 设置 TTL 索引，自动清理过期数据
db.task_status_cache.createIndex({ "last_updated": 1 }, { expireAfterSeconds: 86400 }) // 24 小时后自动删除
```

## 5. 最佳实践

1. **配置副本集**：即使在单节点环境下，配置副本集也有助于未来扩展和提高可用性。
2. **定期备份**：实施定期备份策略，确保数据安全。
3. **监控连接数**：MongoDB 的默认连接数限制可能会在高负载下导致问题。
4. **合理使用索引**：为查询模式创建合适的索引，但避免过度索引。
5. **定期压缩**：定期运行压缩，释放未使用的空间。
6. **设置文档过期**：对于日志等临时数据，使用 TTL 索引自动管理数据生命周期。

## 6. 故障排除

### 6.1 常见问题

1. **连接被拒绝**
   - 确认 MongoDB 服务是否运行
   - 检查防火墙和网络配置
   - 验证认证信息是否正确

2. **性能问题**
   - 检查慢查询日志
   - 分析索引使用情况
   - 监控内存使用和缓存命中率

3. **磁盘空间不足**
   - 执行数据压缩
   - 清理日志文件
   - 实现数据归档策略

### 6.2 日志分析

检查日志以排查问题：

```bash
# 在 Docker 中查看日志
docker logs mongodb

# 在 Kubernetes 中查看日志
kubectl logs ai-mongodb-0 -n database

# 直接安装时检查日志
sudo cat /var/log/mongodb/mongod.log
```

## 相关资源

- [MongoDB 官方文档](https://docs.mongodb.com/v6.0/)
- [MongoDB Kubernetes 操作指南](https://docs.mongodb.com/kubernetes-operator/stable/)
- [MongoDB 性能优化指南](https://docs.mongodb.com/manual/core/query-optimization/)
