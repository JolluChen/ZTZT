# MongoDB 6.0 部署指南

本文档详细说明如何在物理服务器环境中部署和配置 MongoDB 6.0 数据库服务，用于 AI 中台项目。

## 0. 部署前准备

### 0.1 Docker 环境配置

如果遇到镜像拉取问题，需要配置镜像加速器：

**重要提示：** 配置 Docker daemon.json 时，避免使用已废弃或无效的参数。

```bash
# 创建 Docker 配置文件 - 仅使用有效参数
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://dockerproxy.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF

# 重启 Docker 服务
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置是否生效
docker info | grep -A 5 "Registry Mirrors"

# 验证 Docker 守护进程状态
sudo systemctl status docker
```

**故障排除提示：**
- 如果 Docker 重启失败，请检查 daemon.json 语法是否正确
- 避免使用 "max-download-attempts" 和 "download-timeout" 等无效参数
- 确保 JSON 格式正确，没有多余的逗号

### 0.2 镜像拉取策略

基于实际部署经验，推荐以下镜像拉取策略：

**策略1：官方镜像 + 镜像加速（推荐）**
```bash
# 配置镜像加速后，直接使用官方镜像
docker pull mongo:6.0
```

**策略2：使用国内镜像源（备选方案）**
```bash
# 如果官方镜像仍然拉取失败，使用阿里云镜像源
docker pull registry.cn-hangzhou.aliyuncs.com/library/mongo:6.0
docker tag registry.cn-hangzhou.aliyuncs.com/library/mongo:6.0 mongo:6.0

# 或使用腾讯云镜像源
docker pull ccr.ccs.tencentyun.com/library/mongo:6.0
docker tag ccr.ccs.tencentyun.com/library/mongo:6.0 mongo:6.0
```

**部署验证：**
```bash
# 验证镜像是否成功拉取
docker images | grep mongo

# 测试镜像是否可以正常运行
docker run --rm mongo:6.0 mongod --version
```

## 1. 部署选项

MongoDB 主要用于存储日志数据、临时缓存和配置文件，详细集合设计见 `database_design.md`。

### 1.1 Docker 部署

使用 Docker 部署 MongoDB 是开发环境或单节点环境的简单选择：

```bash
# 创建持久化存储卷目录
sudo mkdir -p /data/mongodb/data
sudo chmod 755 /data/mongodb/data

# 方案1：直接使用官方镜像（如果网络正常）
docker run -d --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=root \
  -e MONGO_INITDB_ROOT_PASSWORD=changeThisToSecurePassword \
  -p 27017:27017 \
  -v /data/mongodb/data:/data/db \
  --restart unless-stopped \
  mongo:6.0

# 方案2：使用阿里云镜像（推荐，网络稳定）
docker run -d --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=root \
  -e MONGO_INITDB_ROOT_PASSWORD=changeThisToSecurePassword \
  -p 27017:27017 \
  -v /data/mongodb/data:/data/db \
  --restart unless-stopped \
  registry.cn-hangzhou.aliyuncs.com/library/mongo:6.0

# 等待 MongoDB 启动完成
sleep 15

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

### 1.2 Docker Compose 部署（推荐）

使用 Docker Compose 简化部署和管理，这是经过验证的最佳实践方案：

**步骤1：创建 Docker Compose 配置文件**

```bash
# 创建 docker-compose-mongodb.yml
cat > docker-compose-mongodb.yml << 'EOF'
version: '3.8'

services:
  mongodb:
    image: mongo:6.0  # 使用官方镜像（配置镜像加速后可正常拉取）
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
    networks:
      - ai-platform-network

volumes:
  mongodb_data:
    driver: local

networks:
  ai-platform-network:
    driver: bridge
EOF

# 创建初始化脚本 - 包含经过验证的索引策略
cat > mongo-init.js << 'EOF'
// 切换到应用数据库
db = db.getSiblingDB('ai_platform');

// 创建应用用户
db.createUser({
  user: 'ai_platform_user',
  pwd: 'changeThisToSecurePassword',
  roles: [
    { role: 'readWrite', db: 'ai_platform' },
    { role: 'dbAdmin', db: 'ai_platform' }
  ]
});

print('=== 创建系统日志集合和索引 ===');
db.createCollection('system_logs');
// 基础时间索引 - 用于按时间范围查询
db.system_logs.createIndex({ "timestamp": 1 });
// 复合索引 - 用于按日志级别和时间查询
db.system_logs.createIndex({ "level": 1, "timestamp": 1 });
// 复合索引 - 用于按服务和时间查询
db.system_logs.createIndex({ "service": 1, "timestamp": 1 });

print('=== 创建配置集合和索引 ===');
db.createCollection('configurations');
// 唯一复合索引 - 确保同一组件、环境、版本的配置唯一性
db.configurations.createIndex({ "component": 1, "environment": 1, "version": 1 }, { unique: true });
// 活跃配置索引 - 快速查询当前生效的配置
db.configurations.createIndex({ "is_active": 1 });

print('=== 创建任务状态缓存集合和索引 ===');
db.createCollection('task_status_cache');
// 任务ID唯一索引 - 确保任务ID唯一性
db.task_status_cache.createIndex({ "task_id": 1 }, { unique: true });
// 状态和更新时间复合索引 - 用于状态查询和排序
db.task_status_cache.createIndex({ "status": 1, "last_updated": 1 });
// 任务类型和状态复合索引 - 用于按类型过滤任务
db.task_status_cache.createIndex({ "task_type": 1, "status": 1 });
// TTL 索引：24小时后自动删除过期数据，避免缓存数据堆积
db.task_status_cache.createIndex({ "last_updated": 1 }, { expireAfterSeconds: 86400 });

print('=== 验证索引创建 ===');
print('system_logs 索引:', db.system_logs.getIndexes().length, '个');
print('configurations 索引:', db.configurations.getIndexes().length, '个');
print('task_status_cache 索引:', db.task_status_cache.getIndexes().length, '个');

print('=== MongoDB 初始化完成 ===');
EOF

**步骤2：启动和验证部署**

```bash
# 启动 MongoDB 服务
docker compose -f docker-compose-mongodb.yml up -d

# 检查容器状态
docker compose -f docker-compose-mongodb.yml ps

# 查看初始化日志，确保初始化脚本执行成功
docker compose -f docker-compose-mongodb.yml logs mongodb | grep "初始化"

# 等待初始化完成（建议等待30-60秒确保完全初始化）
Start-Sleep 30

# 验证数据库连接和初始化结果
docker exec -it mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --eval "
  print('=== 连接测试 ===');
  db.runCommand('hello');
  print('=== 验证集合创建 ===');
  db.getCollectionNames().forEach(function(name) { print('集合:', name); });
  print('=== 验证索引数量 ===');
  print('system_logs 索引数量:', db.system_logs.getIndexes().length);
  print('configurations 索引数量:', db.configurations.getIndexes().length);  
  print('task_status_cache 索引数量:', db.task_status_cache.getIndexes().length);
"
```

**步骤3：性能验证和测试**

```bash
# 插入测试数据验证索引效果
docker exec -it mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --eval "
  // 插入测试日志数据
  print('=== 插入测试数据 ===');
  for(let i = 0; i < 1000; i++) {
    db.system_logs.insertOne({
      timestamp: new Date(),
      level: i % 4 == 0 ? 'ERROR' : (i % 4 == 1 ? 'WARN' : (i % 4 == 2 ? 'INFO' : 'DEBUG')),
      service: 'test_service_' + (i % 5),
      message: 'Test log message ' + i,
      details: { test_id: i, deployment_method: 'docker-compose' }
    });
  }
  
  // 验证查询性能（使用索引）
  print('=== 验证索引使用效果 ===');
  let plan = db.system_logs.find({level: 'ERROR'}).explain('executionStats');
  print('ERROR日志查询 - 扫描文档数:', plan.executionStats.totalDocsExamined);
  print('ERROR日志查询 - 返回文档数:', plan.executionStats.totalDocsReturned);
  print('ERROR日志查询 - 使用索引:', plan.executionStats.executionStages.stage);
"
```
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

## 4. 数据库管理工具

### 4.1 MongoDB 管理脚本

基于实际部署经验，创建一个全面的数据库管理脚本：

```bash
# 创建 mongodb-admin.sh - 经过验证的管理工具
cat > mongodb-admin.sh << 'EOF'
#!/bin/bash

# MongoDB 管理脚本
# 用途：数据库备份、恢复、健康检查、性能监控

# 配置变量
CONTAINER_NAME="mongodb"
DB_NAME="ai_platform"
DB_USER="ai_platform_user"
DB_PASS="changeThisToSecurePassword"
BACKUP_DIR="/data/mongodb/backups"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 MongoDB 容器状态
check_mongodb_status() {
    log_info "检查 MongoDB 容器状态..."
    if docker ps | grep -q $CONTAINER_NAME; then
        log_info "MongoDB 容器正在运行"
        return 0
    else
        log_error "MongoDB 容器未运行"
        return 1
    fi
}

# 健康检查
health_check() {
    log_info "执行 MongoDB 健康检查..."
    
    if ! check_mongodb_status; then
        return 1
    fi
    
    # 检查数据库连接
    docker exec $CONTAINER_NAME mongosh -u $DB_USER -p $DB_PASS --authenticationDatabase $DB_NAME --quiet --eval "
        try {
            let result = db.runCommand('hello');
            if (result.ok === 1) {
                print('✓ 数据库连接正常');
            } else {
                print('✗ 数据库连接异常');
                quit(1);
            }
        } catch (error) {
            print('✗ 连接错误:', error.message);
            quit(1);
        }
    " || {
        log_error "数据库连接失败"
        return 1
    }
    
    # 检查集合状态
    docker exec $CONTAINER_NAME mongosh -u $DB_USER -p $DB_PASS --authenticationDatabase $DB_NAME --quiet --eval "
        let collections = ['system_logs', 'configurations', 'task_status_cache'];
        collections.forEach(function(col) {
            try {
                let count = db[col].countDocuments();
                print('✓ 集合', col, '- 文档数量:', count);
            } catch (error) {
                print('✗ 集合', col, '检查失败:', error.message);
            }
        });
    "
    
    log_info "健康检查完成"
}

# 性能监控
performance_monitor() {
    log_info "性能监控报告..."
    
    docker exec $CONTAINER_NAME mongosh -u $DB_USER -p $DB_PASS --authenticationDatabase $DB_NAME --quiet --eval "
        print('=== 数据库状态 ===');
        let dbStats = db.stats();
        print('数据库大小:', Math.round(dbStats.dataSize / 1024 / 1024), 'MB');
        print('索引大小:', Math.round(dbStats.indexSize / 1024 / 1024), 'MB');
        print('集合数量:', dbStats.collections);
        
        print('\\n=== 连接状态 ===');
        let serverStatus = db.runCommand('serverStatus');
        print('当前连接数:', serverStatus.connections.current);
        print('可用连接数:', serverStatus.connections.available);
        
        print('\\n=== 最近慢查询 ===');
        db.system.profile.find().limit(3).sort({ts: -1}).forEach(function(doc) {
            if (doc.command) {
                print('时间:', doc.ts, '- 耗时:', doc.millis, 'ms');
            }
        });
    "
}

# 数据备份
backup_database() {
    log_info "开始数据库备份..."
    
    # 创建备份目录
    mkdir -p $BACKUP_DIR
    
    # 生成备份文件名
    BACKUP_FILE="$BACKUP_DIR/mongodb_backup_$(date +%Y%m%d_%H%M%S)"
    
    # 执行备份
    docker exec $CONTAINER_NAME mongodump \
        --host localhost:27017 \
        --username $DB_USER \
        --password $DB_PASS \
        --authenticationDatabase $DB_NAME \
        --db $DB_NAME \
        --out /tmp/backup
    
    # 复制备份文件到主机
    docker cp $CONTAINER_NAME:/tmp/backup $BACKUP_FILE
    
    if [ $? -eq 0 ]; then
        log_info "备份成功: $BACKUP_FILE"
        # 压缩备份文件
        tar -czf "$BACKUP_FILE.tar.gz" -C "$BACKUP_DIR" "$(basename $BACKUP_FILE)"
        rm -rf "$BACKUP_FILE"
        log_info "备份文件已压缩: $BACKUP_FILE.tar.gz"
    else
        log_error "备份失败"
        return 1
    fi
}

# 数据恢复
restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        log_error "请指定备份文件路径"
        return 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        return 1
    fi
    
    log_warn "即将恢复数据库，这将覆盖现有数据！"
    read -p "确认继续? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "取消恢复操作"
        return 0
    fi
    
    log_info "开始数据库恢复..."
    
    # 解压备份文件
    local temp_dir="/tmp/restore_$(date +%s)"
    mkdir -p $temp_dir
    tar -xzf "$backup_file" -C $temp_dir
    
    # 复制到容器
    docker cp "$temp_dir/." $CONTAINER_NAME:/tmp/restore/
    
    # 执行恢复
    docker exec $CONTAINER_NAME mongorestore \
        --host localhost:27017 \
        --username $DB_USER \
        --password $DB_PASS \
        --authenticationDatabase $DB_NAME \
        --db $DB_NAME \
        --drop \
        /tmp/restore/$DB_NAME/
    
    if [ $? -eq 0 ]; then
        log_info "数据库恢复成功"
    else
        log_error "数据库恢复失败"
        return 1
    fi
    
    # 清理临时文件
    rm -rf $temp_dir
}

# 索引重建
rebuild_indexes() {
    log_info "重建数据库索引..."
    
    docker exec $CONTAINER_NAME mongosh -u $DB_USER -p $DB_PASS --authenticationDatabase $DB_NAME --quiet --eval "
        print('重建 system_logs 索引...');
        db.system_logs.dropIndexes();
        db.system_logs.createIndex({ 'timestamp': 1 });
        db.system_logs.createIndex({ 'level': 1, 'timestamp': 1 });
        db.system_logs.createIndex({ 'service': 1, 'timestamp': 1 });
        
        print('重建 configurations 索引...');
        db.configurations.dropIndexes();
        db.configurations.createIndex({ 'component': 1, 'environment': 1, 'version': 1 }, { unique: true });
        db.configurations.createIndex({ 'is_active': 1 });
        
        print('重建 task_status_cache 索引...');
        db.task_status_cache.dropIndexes();
        db.task_status_cache.createIndex({ 'task_id': 1 }, { unique: true });
        db.task_status_cache.createIndex({ 'status': 1, 'last_updated': 1 });
        db.task_status_cache.createIndex({ 'task_type': 1, 'status': 1 });
        db.task_status_cache.createIndex({ 'last_updated': 1 }, { expireAfterSeconds: 86400 });
        
        print('索引重建完成');
    "
}

# 清理过期数据
cleanup_expired_data() {
    log_info "清理过期数据..."
    
    docker exec $CONTAINER_NAME mongosh -u $DB_USER -p $DB_PASS --authenticationDatabase $DB_NAME --quiet --eval "
        // 清理7天前的系统日志
        let sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        let result = db.system_logs.deleteMany({ timestamp: { \$lt: sevenDaysAgo } });
        print('删除过期日志:', result.deletedCount, '条');
        
        // TTL索引会自动清理task_status_cache，这里只显示统计
        let cacheCount = db.task_status_cache.countDocuments();
        print('当前缓存任务数量:', cacheCount);
    "
}

# 显示使用帮助
show_help() {
    echo "MongoDB 管理脚本"
    echo "用法: $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  health      - 健康检查"
    echo "  monitor     - 性能监控"
    echo "  backup      - 数据备份"
    echo "  restore     - 数据恢复 (需要指定备份文件路径)"
    echo "  indexes     - 重建索引"
    echo "  cleanup     - 清理过期数据"
    echo "  help        - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 health"
    echo "  $0 backup"
    echo "  $0 restore /data/mongodb/backups/mongodb_backup_20240607_120000.tar.gz"
}

# 主函数
main() {
    case "$1" in
        "health")
            health_check
            ;;
        "monitor")
            performance_monitor
            ;;
        "backup")
            backup_database
            ;;
        "restore")
            restore_database "$2"
            ;;
        "indexes")
            rebuild_indexes
            ;;
        "cleanup")
            cleanup_expired_data
            ;;
        "help"|"")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
EOF

# 使脚本可执行
chmod +x mongodb-admin.sh
```

### 4.2 管理脚本使用示例

```bash
# 执行健康检查
./mongodb-admin.sh health

# 性能监控
./mongodb-admin.sh monitor

# 数据备份
./mongodb-admin.sh backup

# 数据恢复（指定备份文件）
./mongodb-admin.sh restore /data/mongodb/backups/mongodb_backup_20240607_120000.tar.gz

# 重建索引
./mongodb-admin.sh indexes

# 清理过期数据
./mongodb-admin.sh cleanup
```

### 集合结构详情

#### `system_logs`

用于存储系统各个模块和服务的运行日志。

| 字段名      | 数据类型   | 索引 | 描述                                     |
| ----------- | ---------- | ---- | ---------------------------------------- |
| `_id`       | ObjectId   | 自动 | 文档唯一ID                               |
| `timestamp` | ISODate    | 是   | 日志记录时间                             |
| `level`     | String     | 是   | 日志级别 (INFO, WARN, ERROR, DEBUG)        |
| `service`   | String     | 是   | 产生日志的服务或模块名                   |
| `message`   | String     |      | 日志消息主体                             |
| `details`   | Object     |      | 附加的结构化日志信息 (例如：用户ID, 请求ID) |

**索引:**
*   `{ "timestamp": 1 }`
*   `{ "level": 1, "timestamp": 1 }`
*   `{ "service": 1, "timestamp": 1 }`

#### `configurations`

用于存储系统组件的配置信息，支持版本化和环境区分。

| 字段名        | 数据类型 | 索引 | 描述                                     |
| ------------- | -------- | ---- | ---------------------------------------- |
| `_id`         | ObjectId | 自动 | 文档唯一ID                               |
| `component`   | String   | 是   | 配置所属的组件名 (例如：data_pipeline, api_gateway) |
| `environment` | String   | 是   | 配置适用的环境 (例如：development, staging, production) |
| `version`     | String   | 是   | 配置版本号                               |
| `config_data` | Object   |      | 具体的配置内容 (JSON格式)                |
| `is_active`   | Boolean  | 是   | 当前配置是否生效                         |
| `created_at`  | ISODate  |      | 配置创建时间                             |
| `updated_at`  | ISODate  |      | 配置最后更新时间                         |

**索引:**
*   `{ "component": 1, "environment": 1, "version": 1 }` (唯一索引确保组合唯一性)
*   `{ "is_active": 1 }`

#### `task_status_cache`

用于缓存异步任务的状态，方便快速查询，并利用 TTL 自动清理过期数据。

| 字段名         | 数据类型   | 索引 | 描述                                     |
| -------------- | ---------- | ---- | ---------------------------------------- |
| `_id`          | ObjectId   | 自动 | 文档唯一ID                               |
| `task_id`      | String     | 是   | 任务的唯一标识符                         |
| `task_type`    | String     | 是   | 任务类型 (例如：data_processing, model_training) |
| `status`       | String     | 是   | 任务当前状态 (例如：PENDING, RUNNING, COMPLETED, FAILED) |
| `progress`     | Number     |      | 任务进度 (例如：0-100)                   |
| `result_url`   | String     |      | 任务结果存储位置 (如果适用)                |
| `error_message`| String     |      | 任务失败时的错误信息                     |
| `created_at`   | ISODate    |      | 任务创建时间                             |
| `last_updated` | ISODate    | 是   | 任务状态最后更新时间 (用于TTL)           |

**索引:**
*   `{ "task_id": 1 }` (唯一索引)
*   `{ "status": 1, "last_updated": 1 }`
*   `{ "task_type": 1, "status": 1 }`
*   `{ "last_updated": 1 }` (TTL 索引, `expireAfterSeconds: 86400`)

```

## 5. 最佳实践与经验总结

### 5.1 部署最佳实践

**1. 镜像拉取策略**
- 优先配置 Docker 镜像加速器，使用官方镜像
- 准备备用镜像源以应对网络问题
- 验证镜像拉取成功后再进行部署

**2. 初始化脚本设计**
- 使用单一初始化脚本包含所有配置
- 为索引创建添加详细注释和验证
- 设置唯一约束防止数据重复
- 使用 TTL 索引自动管理临时数据

**3. 容器配置优化**
- 使用持久化卷确保数据安全
- 配置适当的重启策略（unless-stopped）
- 设置专用网络提高安全性

### 5.2 索引策略

**经过验证的索引方案：**

```javascript
// 系统日志集合索引
db.system_logs.createIndex({ "timestamp": 1 });                    // 时间范围查询
db.system_logs.createIndex({ "level": 1, "timestamp": 1 });        // 按级别过滤 + 时间排序
db.system_logs.createIndex({ "service": 1, "timestamp": 1 });      // 按服务过滤 + 时间排序

// 配置集合索引
db.configurations.createIndex({ "component": 1, "environment": 1, "version": 1 }, { unique: true }); // 确保配置唯一性
db.configurations.createIndex({ "is_active": 1 });                 // 快速查询活跃配置

// 任务缓存集合索引
db.task_status_cache.createIndex({ "task_id": 1 }, { unique: true }); // 任务ID唯一性
db.task_status_cache.createIndex({ "status": 1, "last_updated": 1 }); // 状态查询和排序
db.task_status_cache.createIndex({ "task_type": 1, "status": 1 });    // 按类型和状态过滤
db.task_status_cache.createIndex({ "last_updated": 1 }, { expireAfterSeconds: 86400 }); // TTL自动清理
```

### 5.3 运维管理

**1. 定期维护任务**
- 每日自动备份数据库
- 每周清理过期日志数据
- 每月执行性能分析和索引优化

**2. 监控指标**
- 连接数使用率（建议 < 80%）
- 内存缓存命中率（建议 > 95%）
- 查询响应时间（建议 < 100ms）
- 磁盘使用率（建议 < 80%）

**3. 安全措施**
- 使用强密码和专用用户账号
- 限制网络访问范围
- 定期更新 MongoDB 版本
- 启用审计日志（生产环境）

### 5.4 性能优化

**1. 内存配置**
```bash
# 根据服务器内存调整 WiredTiger 缓存
# 建议设置为可用内存的 50-60%
# 在 docker-compose.yml 中添加：
command: ["mongod", "--wiredTigerCacheSizeGB", "4"]
```

**2. 连接池配置**
```python
# Python 应用连接配置示例
from pymongo import MongoClient

client = MongoClient(
    "mongodb://ai_platform_user:password@localhost:27017/ai_platform",
    maxPoolSize=50,           # 最大连接数
    minPoolSize=10,           # 最小连接数
    maxIdleTimeMS=30000,      # 连接空闲超时
    serverSelectionTimeoutMS=5000,  # 服务器选择超时
    socketTimeoutMS=20000,    # Socket 超时
    connectTimeoutMS=10000,   # 连接超时
    retryWrites=True          # 启用重试写入
)
```

**3. 批量操作优化**
```javascript
// 批量插入示例
db.system_logs.insertMany([
    // 批量数据
], { ordered: false });  // 无序插入提高性能

// 批量更新示例
db.task_status_cache.bulkWrite([
    { updateOne: { filter: { task_id: "task1" }, update: { $set: { status: "COMPLETED" } } } },
    { updateOne: { filter: { task_id: "task2" }, update: { $set: { status: "FAILED" } } } }
]);
```

### 5.5 故障预防

**1. 数据备份策略**
- 每日增量备份
- 每周全量备份  
- 备份文件异地存储
- 定期测试恢复流程

**2. 容量规划**
- 预估数据增长趋势
- 设置磁盘使用告警（80%）
- 配置日志轮转和清理
- 实施数据归档策略

**3. 高可用性配置**
```yaml
# 生产环境推荐使用副本集
# docker-compose-mongodb-replica.yml 示例
version: '3.8'
services:
  mongodb-primary:
    image: mongo:6.0
    command: ["mongod", "--replSet", "rs0", "--bind_ip_all"]
    # ... 其他配置
  
  mongodb-secondary1:
    image: mongo:6.0  
    command: ["mongod", "--replSet", "rs0", "--bind_ip_all"]
    # ... 其他配置
    
  mongodb-secondary2:
    image: mongo:6.0
    command: ["mongod", "--replSet", "rs0", "--bind_ip_all"] 
    # ... 其他配置
```

### 5.6 部署检查清单

**部署前检查：**
- [ ] Docker 环境配置正确
- [ ] 镜像源配置生效
- [ ] 存储空间充足（建议 > 20GB）
- [ ] 网络端口可用（27017）

**部署后验证：**
- [ ] 容器状态正常运行
- [ ] 数据库连接成功
- [ ] 集合和索引创建完成
- [ ] 测试数据插入和查询
- [ ] 管理脚本功能正常

**运维准备：**
- [ ] 备份策略配置
- [ ] 监控脚本部署
- [ ] 告警机制设置
- [ ] 文档和流程记录

## 6. 故障排除

### 6.1 Docker 环境常见问题

**问题1: Docker daemon.json 配置错误**
```bash
# 错误症状：Docker 服务启动失败
sudo systemctl status docker
# 如果看到 "invalid daemon configuration file" 错误

# 解决方案：验证并修复 daemon.json
sudo cat /etc/docker/daemon.json  # 检查当前配置
sudo systemctl stop docker
# 移除无效参数，只保留有效的镜像源配置
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://dockerproxy.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
EOF
sudo systemctl start docker
```

**问题2: 镜像拉取超时或失败**
```bash
# 错误症状：pull timeout 或 connection refused
# 解决方案：使用多个镜像源策略
docker pull mongo:6.0 || \
docker pull registry.cn-hangzhou.aliyuncs.com/library/mongo:6.0 && \
docker tag registry.cn-hangzhou.aliyuncs.com/library/mongo:6.0 mongo:6.0
```

### 6.2 MongoDB 部署问题

**问题3: 初始化脚本未执行**
```bash
# 错误症状：集合或索引未创建
# 排查步骤：
docker compose -f docker-compose-mongodb.yml logs mongodb | grep -i "init"

# 解决方案：手动执行初始化
docker exec -it mongodb mongosh -u root -p changeThisToSecurePassword --eval "
  load('/docker-entrypoint-initdb.d/mongo-init.js')
"

# 验证初始化结果
docker exec -it mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --eval "
  db.getCollectionNames();
  db.system_logs.getIndexes().length;
"
```

**问题4: 连接认证失败**
```bash
# 错误症状：Authentication failed
# 排查步骤：
docker exec -it mongodb mongosh -u root -p changeThisToSecurePassword --eval "
  db.getSiblingDB('admin').getUsers();
  db.getSiblingDB('ai_platform').getUsers();
"

# 解决方案：重新创建用户
docker exec -it mongodb mongosh -u root -p changeThisToSecurePassword --eval "
  use ai_platform;
  db.dropUser('ai_platform_user');
  db.createUser({
    user: 'ai_platform_user',
    pwd: 'changeThisToSecurePassword',
    roles: [
      { role: 'readWrite', db: 'ai_platform' },
      { role: 'dbAdmin', db: 'ai_platform' }
    ]
  });
"
```

### 6.3 性能问题诊断

**问题5: 查询性能慢**
```bash
# 启用查询分析器
docker exec -it mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --eval "
  db.setProfilingLevel(2, { slowms: 100 });
"

# 查看慢查询
docker exec -it mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --eval "
  db.system.profile.find().limit(5).sort({ts: -1}).pretty();
"

# 分析查询计划
docker exec -it mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --eval "
  db.system_logs.find({level: 'ERROR'}).explain('executionStats');
"
```

**问题6: 内存使用过高**
```bash
# 检查内存使用情况
docker exec -it mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --eval "
  let stats = db.runCommand('serverStatus');
  print('WiredTiger 缓存大小:', Math.round(stats.wiredTiger.cache['maximum bytes configured'] / 1024 / 1024), 'MB');
  print('当前使用缓存:', Math.round(stats.wiredTiger.cache['bytes currently in the cache'] / 1024 / 1024), 'MB');
"

# 优化缓存配置（重启时生效）
# 在 docker-compose.yml 中添加：
# command: ["mongod", "--wiredTigerCacheSizeGB", "2"]
```

### 6.4 数据一致性检查

**问题7: 数据损坏或丢失**
```bash
# 执行数据库修复（仅在必要时使用）
docker exec -it mongodb mongosh -u root -p changeThisToSecurePassword --eval "
  db.runCommand({repairDatabase: 1});
"

# 验证集合完整性
docker exec -it mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --eval "
  ['system_logs', 'configurations', 'task_status_cache'].forEach(function(collection) {
    try {
      let count = db[collection].countDocuments();
      let sampleDoc = db[collection].findOne();
      print('集合:', collection, '- 文档数:', count, sampleDoc ? '✓' : '✗');
    } catch (e) {
      print('集合:', collection, '- 错误:', e.message);
    }
  });
"
```

### 6.5 容器重启和恢复

**问题8: 容器异常停止**
```bash
# 检查容器状态和日志
docker compose -f docker-compose-mongodb.yml ps
docker compose -f docker-compose-mongodb.yml logs --tail=50 mongodb

# 强制重启服务
docker compose -f docker-compose-mongodb.yml restart mongodb

# 如果持续失败，重新部署
docker compose -f docker-compose-mongodb.yml down
docker volume ls | grep mongodb  # 检查数据卷是否存在
docker compose -f docker-compose-mongodb.yml up -d
```

### 6.6 监控和预警

**设置基础监控脚本：**
```bash
# 创建监控脚本
cat > mongodb-monitor.sh << 'EOF'
#!/bin/bash
# MongoDB 基础监控

CONTAINER_NAME="mongodb"
LOG_FILE="/var/log/mongodb-monitor.log"

# 检查容器状态
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "$(date): MongoDB 容器未运行" >> $LOG_FILE
    # 可以在这里添加告警逻辑
    exit 1
fi

# 检查连接数
CONN_COUNT=$(docker exec $CONTAINER_NAME mongosh --quiet --eval "db.runCommand('serverStatus').connections.current" 2>/dev/null || echo "N/A")
echo "$(date): 当前连接数: $CONN_COUNT" >> $LOG_FILE

# 检查磁盘使用
DISK_USAGE=$(docker exec $CONTAINER_NAME du -sh /data/db 2>/dev/null || echo "N/A")
echo "$(date): 磁盘使用: $DISK_USAGE" >> $LOG_FILE

# 简单健康检查
docker exec $CONTAINER_NAME mongosh --quiet --eval "db.runCommand('hello')" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "$(date): 健康检查: 正常" >> $LOG_FILE
else
    echo "$(date): 健康检查: 异常" >> $LOG_FILE
fi
EOF

chmod +x mongodb-monitor.sh

# 设置定时执行（每5分钟检查一次）
# crontab -e
# */5 * * * * /path/to/mongodb-monitor.sh
```

## 7. 部署验证与测试

### 7.1 完整部署验证脚本

```bash
# 创建部署验证脚本
cat > verify-mongodb-deployment.sh << 'EOF'
#!/bin/bash

# MongoDB 部署验证脚本
# 验证所有部署步骤是否成功完成

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

echo "=== MongoDB 部署验证开始 ==="

# 1. 检查容器状态
info "检查 MongoDB 容器状态..."
if docker ps | grep -q "mongodb"; then
    success "MongoDB 容器正在运行"
else
    error "MongoDB 容器未运行"
    exit 1
fi

# 2. 检查端口监听
info "检查端口监听状态..."
if netstat -tulpn 2>/dev/null | grep -q ":27017" || ss -tulpn 2>/dev/null | grep -q ":27017"; then
    success "端口 27017 正在监听"
else
    error "端口 27017 未监听"
    exit 1
fi

# 3. 验证 root 用户连接
info "验证 root 用户连接..."
if docker exec mongodb mongosh -u root -p changeThisToSecurePassword --quiet --eval "db.runCommand('hello')" >/dev/null 2>&1; then
    success "root 用户连接成功"
else
    error "root 用户连接失败"
    exit 1
fi

# 4. 验证应用用户连接
info "验证应用用户连接..."
if docker exec mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --quiet --eval "db.runCommand('hello')" >/dev/null 2>&1; then
    success "应用用户连接成功"
else
    error "应用用户连接失败"
    exit 1
fi

# 5. 验证数据库和集合
info "验证数据库和集合..."
collections=$(docker exec mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --quiet --eval "db.getCollectionNames().join(',')")

expected_collections=("system_logs" "configurations" "task_status_cache")
for collection in "${expected_collections[@]}"; do
    if echo "$collections" | grep -q "$collection"; then
        success "集合 $collection 存在"
    else
        error "集合 $collection 不存在"
        exit 1
    fi
done

# 6. 验证索引
info "验证索引创建..."
for collection in "${expected_collections[@]}"; do
    index_count=$(docker exec mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --quiet --eval "db.$collection.getIndexes().length")
    if [ "$index_count" -gt 1 ]; then
        success "集合 $collection 的索引已创建（$index_count 个）"
    else
        error "集合 $collection 的索引创建失败"
        exit 1
    fi
done

# 7. 测试数据操作
info "测试数据插入和查询..."
docker exec mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --quiet --eval "
    // 插入测试数据
    db.system_logs.insertOne({
        timestamp: new Date(),
        level: 'INFO',
        service: 'deployment_verification',
        message: 'Test log entry for deployment verification',
        details: { test: true, timestamp: new Date().getTime() }
    });
    
    // 查询测试数据
    let result = db.system_logs.findOne({service: 'deployment_verification'});
    if (result) {
        print('数据操作测试成功');
    } else {
        print('数据操作测试失败');
        quit(1);
    }
    
    // 清理测试数据
    db.system_logs.deleteMany({service: 'deployment_verification'});
" >/dev/null 2>&1

if [ $? -eq 0 ]; then
    success "数据操作测试通过"
else
    error "数据操作测试失败"
    exit 1
fi

# 8. 验证 TTL 索引
info "验证 TTL 索引配置..."
ttl_check=$(docker exec mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --quiet --eval "
    let indexes = db.task_status_cache.getIndexes();
    let ttlIndex = indexes.find(idx => idx.expireAfterSeconds !== undefined);
    if (ttlIndex && ttlIndex.expireAfterSeconds === 86400) {
        print('TTL索引配置正确');
    } else {
        print('TTL索引配置错误');
        quit(1);
    }
")

if echo "$ttl_check" | grep -q "TTL索引配置正确"; then
    success "TTL 索引配置正确"
else
    error "TTL 索引配置错误"
    exit 1
fi

# 9. 性能基准测试
info "执行基础性能测试..."
docker exec mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform --quiet --eval "
    // 批量插入测试
    let start = new Date();
    let docs = [];
    for (let i = 0; i < 1000; i++) {
        docs.push({
            timestamp: new Date(),
            level: 'INFO',
            service: 'performance_test',
            message: 'Performance test message ' + i,
            details: { index: i }
        });
    }
    db.system_logs.insertMany(docs);
    let insertTime = new Date() - start;
    print('插入1000条记录耗时:', insertTime, 'ms');
    
    // 查询测试
    start = new Date();
    let count = db.system_logs.countDocuments({service: 'performance_test'});
    let queryTime = new Date() - start;
    print('查询', count, '条记录耗时:', queryTime, 'ms');
    
    // 清理测试数据
    db.system_logs.deleteMany({service: 'performance_test'});
    
    if (insertTime < 5000 && queryTime < 1000) {
        print('性能测试通过');
    } else {
        print('性能测试失败 - 插入耗时:', insertTime, 'ms, 查询耗时:', queryTime, 'ms');
        quit(1);
    }
" >/dev/null 2>&1

if [ $? -eq 0 ]; then
    success "性能测试通过"
else
    error "性能测试失败"
    exit 1
fi

echo ""
echo "=== MongoDB 部署验证完成 ==="
success "所有验证项目均已通过！"
echo ""
echo "部署摘要:"
echo "- MongoDB 6.0 容器运行正常"
echo "- 数据库和用户配置正确"
echo "- 所有集合和索引创建成功"
echo "- 数据操作功能正常"
echo "- TTL 索引配置生效"
echo "- 基础性能满足要求"
echo ""
echo "下一步："
echo "1. 配置应用程序连接字符串"
echo "2. 设置定期备份任务"
echo "3. 配置监控和告警"
echo "4. 根据实际负载调整性能参数"

EOF

chmod +x verify-mongodb-deployment.sh
```

### 7.2 执行部署验证

```bash
# 运行完整的部署验证
./verify-mongodb-deployment.sh

# 如果验证失败，可以运行单独的检查项目
# 检查容器状态
docker compose -f docker-compose-mongodb.yml ps

# 检查日志
docker compose -f docker-compose-mongodb.yml logs mongodb

# 手动连接测试
docker exec -it mongodb mongosh -u ai_platform_user -p changeThisToSecurePassword --authenticationDatabase ai_platform
```

### 7.3 应用程序集成测试

**Python 连接测试：**
```python
#!/usr/bin/env python3
# test-mongodb-connection.py

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, AuthenticationFailed
import datetime
import sys

def test_mongodb_connection():
    """测试 MongoDB 连接和基本操作"""
    
    try:
        # 创建连接
        client = MongoClient(
            "mongodb://ai_platform_user:changeThisToSecurePassword@localhost:27017/ai_platform",
            serverSelectionTimeoutMS=5000
        )
        
        # 测试连接
        client.admin.command('hello')
        print("✓ MongoDB 连接成功")
        
        # 获取数据库
        db = client.ai_platform
        
        # 测试集合访问
        collections = db.list_collection_names()
        expected_collections = ['system_logs', 'configurations', 'task_status_cache']
        
        for collection_name in expected_collections:
            if collection_name in collections:
                print(f"✓ 集合 {collection_name} 可访问")
            else:
                print(f"✗ 集合 {collection_name} 不存在")
                return False
        
        # 测试数据操作
        test_doc = {
            "timestamp": datetime.datetime.now(),
            "level": "INFO",
            "service": "python_test",
            "message": "Python 连接测试",
            "details": {"test": True}
        }
        
        # 插入测试
        result = db.system_logs.insert_one(test_doc)
        print(f"✓ 数据插入成功，ID: {result.inserted_id}")
        
        # 查询测试
        found_doc = db.system_logs.find_one({"_id": result.inserted_id})
        if found_doc:
            print("✓ 数据查询成功")
        else:
            print("✗ 数据查询失败")
            return False
        
        # 清理测试数据
        db.system_logs.delete_one({"_id": result.inserted_id})
        print("✓ 测试数据清理完成")
        
        # 测试索引使用
        explain_result = db.system_logs.find({"level": "INFO"}).explain()
        if explain_result['executionStats']['totalDocsExamined'] <= explain_result['executionStats']['totalDocsReturned'] * 2:
            print("✓ 索引使用正常")
        else:
            print("⚠ 查询可能未使用索引，请检查索引配置")
        
        client.close()
        print("\n🎉 MongoDB 集成测试全部通过！")
        return True
        
    except ConnectionFailure:
        print("✗ MongoDB 连接失败")
        return False
    except AuthenticationFailed:
        print("✗ MongoDB 认证失败")
        return False
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1)
```

**运行 Python 测试：**
```bash
# 安装依赖
pip install pymongo

# 运行测试
python3 test-mongodb-connection.py
```

## 相关资源

### 官方文档
- [MongoDB 6.0 官方文档](https://docs.mongodb.com/v6.0/)
- [MongoDB Docker 部署指南](https://hub.docker.com/_/mongo)
- [MongoDB Kubernetes 操作指南](https://docs.mongodb.com/kubernetes-operator/stable/)

### 性能调优
- [MongoDB 性能优化指南](https://docs.mongodb.com/manual/core/query-optimization/)
- [WiredTiger 存储引擎调优](https://docs.mongodb.com/manual/core/wiredtiger/)
- [索引优化最佳实践](https://docs.mongodb.com/manual/applications/indexes/)

### 运维监控
- [MongoDB 监控最佳实践](https://docs.mongodb.com/manual/administration/monitoring/)
- [MongoDB 备份恢复策略](https://docs.mongodb.com/manual/core/backups/)
- [MongoDB 安全配置指南](https://docs.mongodb.com/manual/security/)

---

**文档版本：** 基于 MongoDB 6.0 实际部署经验优化  
**最后更新：** 2024年6月7日  
**适用环境：** Docker、Docker Compose、Kubernetes、物理服务器
