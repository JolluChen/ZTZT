# Redis 部署配置指南

[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28.8-326CE5?style=flat-square&logo=kubernetes)](https://kubernetes.io/) [![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=flat-square&logo=redis)](https://redis.io/) [![Bitnami](https://img.shields.io/badge/Helm-Bitnami-FF6B6B?style=flat-square&logo=helm)](https://github.com/bitnami/charts/tree/main/bitnami/redis)

**配置阶段**: 第二阶段 - 数据库配置  
**实际部署状态**: ✅ Redis 已在 Kubernetes 集群中运行  
**当前状态**: `redis-master-0` (1/1 Running, 28+ 小时) in `database` namespace  
**前置条件**: [环境部署](../../01_environment_deployment/03_storage_systems_kubernetes.md) 完成

本文档详细说明 Redis 在 AI 中台项目中的配置管理、性能优化、监控维护等实用指南。Redis 部署步骤已在环境部署阶段完成，本文档专注于配置优化和日常管理。

## 📊 当前部署状态

```bash
# 当前 Redis 实例状态
kubectl get pods -n database -l app.kubernetes.io/name=redis
# NAME             READY   STATUS    RESTARTS   AGE
# redis-master-0   1/1     Running   0          28h

# 使用配置
Architecture: standalone (单节点)
Storage Class: local-storage
Persistence Size: 5Gi
Authentication: Enabled (password: redis-2024)
```

## 📋 配置管理概览

> **注意**: Redis 部署已在 Kubernetes 集群中完成，详见 [环境部署文档](../../01_environment_deployment/03_storage_systems_kubernetes.md)。本文档专注于 Redis 配置优化、性能调优和日常维护管理。

| 配置项 | 推荐方案 | 配置时间 | 维护难度 |
|--------|----------|----------|----------|
| 连接配置 | Kubernetes Service | 10分钟 | ⭐ |
| 性能调优 | 内存与持久化优化 | 20分钟 | ⭐⭐ |
| 安全配置 | 密码与ACL管理 | 15分钟 | ⭐⭐ |
| 监控配置 | Redis Exporter | 15分钟 | ⭐⭐ |
| 备份策略 | 自动备份脚本 | 20分钟 | ⭐⭐⭐ |

## 1. Redis 连接配置 (Kubernetes 环境)

### 1.1 服务地址与端口

当前 Redis 在 Kubernetes 集群中通过以下地址访问：

```bash
# 集群内部访问
Service Name: ai-redis-master.database.svc.cluster.local
Port: 6379

# 从集群外部访问 (通过端口转发)
kubectl port-forward svc/ai-redis-master -n database 6379:6379
```

### 1.2 认证信息

```yaml
# Redis 连接凭据 (已配置)
Username: default
Password: redis-2024
Database: 0 (默认)
```

### 1.3 命令行连接

```bash
# 从 Kubernetes 集群内部连接
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024

# 从集群外部连接 (需要端口转发)
kubectl port-forward svc/ai-redis-master -n database 6379:6379 &
redis-cli -h localhost -p 6379 -a redis-2024

# 基本连接测试
redis-cli -h localhost -p 6379 -a redis-2024 ping
# 预期输出: PONG
```

### 1.4 应用程序连接配置

```python
# Python Redis 连接配置
import redis

# 集群内部应用连接
def connect_kubernetes_redis():
    return redis.Redis(
        host='ai-redis-master.database.svc.cluster.local',
        port=6379,
        password='redis-2024',
        db=0,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )

# 连接池配置 (推荐生产使用)
def create_redis_pool():
    pool = redis.ConnectionPool(
        host='ai-redis-master.database.svc.cluster.local',
        port=6379,
        password='redis-2024',
        db=0,
        decode_responses=True,
        max_connections=50,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    return redis.Redis(connection_pool=pool)
```

```javascript
// Node.js Redis 连接配置
const redis = require('redis');

const client = redis.createClient({
    host: 'ai-redis-master.database.svc.cluster.local',
    port: 6379,
    password: 'redis-2024',
    db: 0,
    connectTimeout: 5000,
    lazyConnect: true,
    retryDelayOnFailover: 100,
    retryDelayOnClusterDown: 300,
    maxRetriesPerRequest: 3
});

client.on('error', (err) => {
    console.log('Redis Client Error', err);
});

await client.connect();
```

## 2. Redis 配置优化

### 2.1 当前配置查看

```bash
# 查看当前 Redis 配置
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG GET "*"

# 查看内存使用情况
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 INFO memory

# 查看持久化配置
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG GET save
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG GET appendonly
```

### 2.2 内存优化配置

```bash
# 设置最大内存限制 (当前 Pod 限制为 2Gi)
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET maxmemory 1800MB

# 设置内存淘汰策略
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET maxmemory-policy allkeys-lru

# 启用 key 过期扫描
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET activedefrag yes

# 保存配置到文件
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG REWRITE
```

### 2.3 性能调优参数

```bash
# 网络优化
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET tcp-keepalive 300
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET timeout 0

# 持久化优化
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET appendfsync everysec
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET no-appendfsync-on-rewrite yes

# 慢日志配置
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET slowlog-log-slower-than 10000
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET slowlog-max-len 128

# 客户端连接优化
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET maxclients 1000
```

### 2.4 监控慢查询

```bash
# 查看慢查询日志
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 SLOWLOG GET 10

# 清空慢查询日志
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 SLOWLOG RESET

# 实时监控 Redis 命令
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 MONITOR
```

## 3. 键空间设计与管理

### 3.1 AI 中台键命名规范

根据 AI 中台项目需求，采用以下键命名规范：

```bash
# 会话数据 (TTL: 24小时)
session:user:<user_id>              # 用户会话信息
session:admin:<admin_id>            # 管理员会话信息
session:token:<token_id>            # 令牌映射关系

# 缓存数据 (TTL: 1-6小时)
cache:user:<user_id>                # 用户信息缓存
cache:model:<model_id>              # 模型元数据缓存
cache:config:<config_key>           # 系统配置缓存
cache:api:response:<hash>           # API 响应缓存

# API 速率限制 (TTL: 1小时)
rate:api:user:<user_id>             # 用户 API 请求计数
rate:api:ip:<ip_address>            # IP 请求计数
rate:api:endpoint:<endpoint>        # 端点请求计数

# 分布式锁 (TTL: 30秒-5分钟)
lock:resource:<resource_id>         # 资源锁定状态
lock:job:<job_id>                   # 作业执行锁
lock:model:<model_id>               # 模型训练锁

# 异步任务队列
queue:job:high                      # 高优先级作业队列
queue:job:normal                    # 普通优先级作业队列
queue:job:low                       # 低优先级作业队列
queue:notification                  # 通知队列

# 发布/订阅通道
pubsub:system                       # 系统广播通道
pubsub:model:events                 # 模型事件通知
pubsub:alerts                       # 警报通知通道

# 统计数据 (TTL: 7天)
stats:user:active:daily             # 日活跃用户统计
stats:api:calls:hourly              # 小时API调用统计
stats:performance:realtime          # 实时性能指标
```

### 3.2 键过期时间策略

```bash
# 设置不同类型键的默认过期时间
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 <<EOF
# 会话数据 - 24小时
SETEX session:user:example 86400 "user_session_data"

# 短期缓存 - 1小时
SETEX cache:api:response:abc123 3600 "cached_response"

# 速率限制 - 1小时滑动窗口
SETEX rate:api:user:123 3600 "100"

# 分布式锁 - 30秒
SETEX lock:resource:model_training 30 "locked_by_worker_1"

# 统计数据 - 7天
SETEX stats:api:calls:2024120114 604800 "1250"
EOF
```

### 3.3 键空间监控脚本

```bash
# 创建键空间监控脚本
cat > /tmp/redis_keyspace_monitor.py << 'EOF'
#!/usr/bin/env python3
# Redis 键空间监控脚本

import redis
import time
from collections import defaultdict

def connect_redis():
    return redis.Redis(
        host='localhost',  # 通过端口转发连接
        port=6379,
        password='redis-2024',
        decode_responses=True
    )

def monitor_keyspace(r):
    """监控键空间分布"""
    pattern_counts = defaultdict(int)
    total_keys = 0
    
    # 获取所有键
    for key in r.scan_iter(match="*"):
        total_keys += 1
        prefix = key.split(':')[0] if ':' in key else 'other'
        pattern_counts[prefix] += 1
    
    print(f"=== Redis 键空间分析 ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")
    print(f"总键数: {total_keys}")
    print("\n键前缀分布:")
    for prefix, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_keys) * 100 if total_keys > 0 else 0
        print(f"  {prefix:15}: {count:6} ({percentage:5.1f}%)")
    
    # 内存使用情况
    memory_info = r.info('memory')
    used_memory_mb = memory_info['used_memory'] / 1024 / 1024
    print(f"\n内存使用: {used_memory_mb:.2f} MB")
    
    # 过期键统计
    expired_keys = r.info('stats')['expired_keys']
    print(f"已过期键数: {expired_keys}")

if __name__ == "__main__":
    try:
        r = connect_redis()
        monitor_keyspace(r)
    except redis.ConnectionError:
        print("错误: 无法连接到 Redis。请确保端口转发已启动：")
        print("kubectl port-forward svc/ai-redis-master -n database 6379:6379")
EOF

chmod +x /tmp/redis_keyspace_monitor.py

# 运行监控 (需要先启动端口转发)
# kubectl port-forward svc/ai-redis-master -n database 6379:6379 &
# python3 /tmp/redis_keyspace_monitor.py
```

## 4. 监控与性能分析

### 4.1 Redis 性能监控

```bash
# 查看 Redis 运行状态
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 INFO

# 查看内存使用详情
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 INFO memory

# 查看客户端连接
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CLIENT LIST

# 实时监控命令执行
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 MONITOR
```

### 4.2 部署 Redis Exporter

```yaml
# 创建 Redis Exporter 部署
cat > redis-exporter.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-exporter
  namespace: database
  labels:
    app: redis-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-exporter
  template:
    metadata:
      labels:
        app: redis-exporter
    spec:
      containers:
      - name: redis-exporter
        image: oliver006/redis_exporter:v1.55.0
        ports:
        - containerPort: 9121
          name: metrics
        env:
        - name: REDIS_ADDR
          value: "redis://ai-redis-master.database.svc.cluster.local:6379"
        - name: REDIS_PASSWORD
          value: "redis-2024"
        - name: REDIS_EXPORTER_INCL_SYSTEM_METRICS
          value: "true"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"

---
apiVersion: v1
kind: Service
metadata:
  name: redis-exporter
  namespace: database
  labels:
    app: redis-exporter
spec:
  ports:
  - port: 9121
    targetPort: 9121
    name: metrics
  selector:
    app: redis-exporter
EOF

# 部署 Redis Exporter
kubectl apply -f redis-exporter.yaml

# 验证部署
kubectl get pods -n database -l app=redis-exporter
kubectl get svc -n database redis-exporter
```

### 4.3 创建监控脚本

```bash
# 创建本地监控脚本目录
mkdir -p /tmp/redis-monitoring

# 创建性能监控脚本
cat > /tmp/redis-monitoring/redis_performance.py << 'EOF'
#!/usr/bin/env python3
"""Redis 性能监控脚本"""

import redis
import time
import json
from datetime import datetime

class RedisMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',  # 通过端口转发连接
            port=6379,
            password='redis-2024',
            decode_responses=True
        )
    
    def get_memory_info(self):
        """获取内存使用信息"""
        info = self.redis_client.info('memory')
        return {
            'used_memory_human': info.get('used_memory_human'),
            'used_memory_peak_human': info.get('used_memory_peak_human'),
            'maxmemory_human': info.get('maxmemory_human'),
            'mem_fragmentation_ratio': info.get('mem_fragmentation_ratio'),
            'used_memory_overhead': info.get('used_memory_overhead')
        }
    
    def get_performance_info(self):
        """获取性能信息"""
        info = self.redis_client.info('stats')
        return {
            'total_commands_processed': info.get('total_commands_processed'),
            'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec'),
            'keyspace_hits': info.get('keyspace_hits'),
            'keyspace_misses': info.get('keyspace_misses'),
            'expired_keys': info.get('expired_keys'),
            'evicted_keys': info.get('evicted_keys')
        }
    
    def get_client_info(self):
        """获取客户端连接信息"""
        info = self.redis_client.info('clients')
        return {
            'connected_clients': info.get('connected_clients'),
            'client_recent_max_input_buffer': info.get('client_recent_max_input_buffer'),
            'client_recent_max_output_buffer': info.get('client_recent_max_output_buffer')
        }
    
    def calculate_hit_rate(self, stats):
        """计算缓存命中率"""
        hits = stats.get('keyspace_hits', 0)
        misses = stats.get('keyspace_misses', 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0
    
    def monitor(self):
        """执行监控"""
        try:
            # 获取各类信息
            memory_info = self.get_memory_info()
            performance_info = self.get_performance_info()
            client_info = self.get_client_info()
            
            # 计算命中率
            hit_rate = self.calculate_hit_rate(performance_info)
            
            # 构建监控报告
            report = {
                'timestamp': datetime.now().isoformat(),
                'memory': memory_info,
                'performance': performance_info,
                'clients': client_info,
                'hit_rate_percent': round(hit_rate, 2)
            }
            
            # 输出报告
            print("=" * 60)
            print(f"Redis 监控报告 - {report['timestamp']}")
            print("=" * 60)
            print(f"内存使用: {memory_info['used_memory_human']}")
            print(f"内存峰值: {memory_info['used_memory_peak_human']}")
            print(f"碎片率: {memory_info['mem_fragmentation_ratio']:.2f}")
            print(f"连接数: {client_info['connected_clients']}")
            print(f"每秒操作: {performance_info['instantaneous_ops_per_sec']}")
            print(f"命中率: {hit_rate:.2f}%")
            print(f"过期键数: {performance_info['expired_keys']}")
            print(f"淘汰键数: {performance_info['evicted_keys']}")
            
            return report
            
        except redis.ConnectionError:
            print("错误: 无法连接到 Redis")
            print("请确保端口转发已启动: kubectl port-forward svc/ai-redis-master -n database 6379:6379")
            return None
        except Exception as e:
            print(f"监控过程中发生错误: {e}")
            return None

if __name__ == "__main__":
    monitor = RedisMonitor()
    monitor.monitor()
EOF

chmod +x /tmp/redis-monitoring/redis_performance.py

# 创建持续监控脚本
cat > /tmp/redis-monitoring/continuous_monitor.sh << 'EOF'
#!/bin/bash
# Redis 持续监控脚本

echo "启动 Redis 持续监控..."
echo "按 Ctrl+C 停止监控"

# 启动端口转发
kubectl port-forward svc/ai-redis-master -n database 6379:6379 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!

# 等待端口转发就绪
sleep 3

# 监控循环
while true; do
    python3 /tmp/redis-monitoring/redis_performance.py
    echo ""
    echo "下次监控将在 30 秒后开始..."
    sleep 30
done

# 清理端口转发
kill $PORT_FORWARD_PID 2>/dev/null
EOF

chmod +x /tmp/redis-monitoring/continuous_monitor.sh
```## 5. 备份与恢复策略

### 5.1 Kubernetes 环境备份

```bash
# 创建备份脚本目录
mkdir -p /tmp/redis-backup

# 创建 Kubernetes Redis 备份脚本
cat > /tmp/redis-backup/backup_k8s_redis.sh << 'EOF'
#!/bin/bash
# Kubernetes Redis 备份脚本

NAMESPACE="database"
POD_NAME="redis-master-0"
BACKUP_DIR="/tmp/redis-backup/data"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# 创建备份目录
mkdir -p ${BACKUP_DIR}/{daily,weekly,monthly}

echo "开始备份 Redis 数据 - ${TIMESTAMP}"

# 1. 触发 RDB 备份
echo "触发 RDB 保存..."
kubectl exec ${POD_NAME} -n ${NAMESPACE} -- redis-cli -a redis-2024 BGSAVE

# 2. 等待备份完成
echo "等待备份完成..."
while true; do
    status=$(kubectl exec ${POD_NAME} -n ${NAMESPACE} -- redis-cli -a redis-2024 LASTSAVE)
    sleep 2
    new_status=$(kubectl exec ${POD_NAME} -n ${NAMESPACE} -- redis-cli -a redis-2024 LASTSAVE)
    if [ "$status" != "$new_status" ]; then
        break
    fi
done

# 3. 复制 RDB 文件
echo "复制备份文件..."
kubectl cp ${NAMESPACE}/${POD_NAME}:/data/dump.rdb ${BACKUP_DIR}/daily/redis_${TIMESTAMP}.rdb

# 4. 压缩备份文件
gzip ${BACKUP_DIR}/daily/redis_${TIMESTAMP}.rdb
echo "备份完成: redis_${TIMESTAMP}.rdb.gz"

# 5. 创建最新备份链接
ln -sf ${BACKUP_DIR}/daily/redis_${TIMESTAMP}.rdb.gz ${BACKUP_DIR}/latest_backup.rdb.gz

# 6. 周备份和月备份
DAY_OF_WEEK=$(date +%u)
DAY_OF_MONTH=$(date +%d)

if [ "$DAY_OF_WEEK" -eq 7 ]; then
    cp ${BACKUP_DIR}/daily/redis_${TIMESTAMP}.rdb.gz ${BACKUP_DIR}/weekly/redis_week_$(date +%Y%m%d).rdb.gz
    echo "创建周备份完成"
fi

if [ "$DAY_OF_MONTH" -eq 01 ]; then
    cp ${BACKUP_DIR}/daily/redis_${TIMESTAMP}.rdb.gz ${BACKUP_DIR}/monthly/redis_month_$(date +%Y%m%d).rdb.gz
    echo "创建月备份完成"
fi

# 7. 清理旧备份
find ${BACKUP_DIR}/daily -name "redis_*.rdb.gz" -mtime +7 -delete
find ${BACKUP_DIR}/weekly -name "redis_week_*.rdb.gz" -mtime +30 -delete
find ${BACKUP_DIR}/monthly -name "redis_month_*.rdb.gz" -mtime +365 -delete

echo "Redis 备份任务完成 - $(date)"
EOF

chmod +x /tmp/redis-backup/backup_k8s_redis.sh

# 创建定时备份任务
echo "# Redis 备份任务 - 每天凌晨 2 点执行" >> /tmp/redis_backup_cron
echo "0 2 * * * /tmp/redis-backup/backup_k8s_redis.sh >> /tmp/redis-backup/backup.log 2>&1" >> /tmp/redis_backup_cron

# 添加到 crontab
crontab /tmp/redis_backup_cron
```

### 5.2 数据恢复脚本

```bash
# 创建 Redis 数据恢复脚本
cat > /tmp/redis-backup/restore_k8s_redis.sh << 'EOF'
#!/bin/bash
# Kubernetes Redis 数据恢复脚本

NAMESPACE="database"
POD_NAME="redis-master-0"
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <备份文件路径>"
    echo "示例: $0 /tmp/redis-backup/data/daily/redis_20241201_020000.rdb.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "准备恢复 Redis 数据..."
echo "备份文件: $BACKUP_FILE"
echo "目标 Pod: $POD_NAME"

# 1. 停止 Redis 写操作
echo "设置 Redis 为只读模式..."
kubectl exec ${POD_NAME} -n ${NAMESPACE} -- redis-cli -a redis-2024 CONFIG SET stop-writes-on-bgsave-error no

# 2. 准备备份文件
TEMP_FILE="/tmp/restore_dump.rdb"
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
else
    cp "$BACKUP_FILE" "$TEMP_FILE"
fi

# 3. 备份当前数据
echo "备份当前数据..."
kubectl exec ${POD_NAME} -n ${NAMESPACE} -- redis-cli -a redis-2024 BGSAVE
kubectl cp ${NAMESPACE}/${POD_NAME}:/data/dump.rdb /tmp/redis_current_backup_$(date +%Y%m%d_%H%M%S).rdb

# 4. 复制恢复文件到 Pod
echo "复制恢复数据到 Pod..."
kubectl cp "$TEMP_FILE" ${NAMESPACE}/${POD_NAME}:/tmp/restore_dump.rdb

# 5. 停止 Redis 进程并替换数据文件
echo "停止 Redis 并替换数据文件..."
kubectl exec ${POD_NAME} -n ${NAMESPACE} -- sh -c "
    redis-cli -a redis-2024 SHUTDOWN NOSAVE || true
    mv /data/dump.rdb /data/dump.rdb.old 2>/dev/null || true
    mv /tmp/restore_dump.rdb /data/dump.rdb
    chown redis:root /data/dump.rdb
"

# 6. 重启 Redis Pod
echo "重启 Redis Pod..."
kubectl delete pod ${POD_NAME} -n ${NAMESPACE}

# 7. 等待 Pod 重新启动
echo "等待 Pod 重新启动..."
kubectl wait --for=condition=Ready pod/${POD_NAME} -n ${NAMESPACE} --timeout=60s

# 8. 验证恢复
echo "验证数据恢复..."
sleep 5
KEYS_COUNT=$(kubectl exec ${POD_NAME} -n ${NAMESPACE} -- redis-cli -a redis-2024 DBSIZE)
echo "恢复后键数量: $KEYS_COUNT"

# 9. 恢复正常配置
kubectl exec ${POD_NAME} -n ${NAMESPACE} -- redis-cli -a redis-2024 CONFIG SET stop-writes-on-bgsave-error yes

# 清理临时文件
rm -f "$TEMP_FILE"

echo "Redis 数据恢复完成!"
EOF

chmod +x /tmp/redis-backup/restore_k8s_redis.sh
```

### 5.3 备份验证脚本

```bash
# 创建备份验证脚本
cat > /tmp/redis-backup/verify_backup.sh << 'EOF'
#!/bin/bash
# Redis 备份验证脚本

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <备份文件路径>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "验证 Redis 备份文件: $BACKUP_FILE"

# 1. 检查文件大小
FILE_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
echo "备份文件大小: $FILE_SIZE 字节"

# 2. 如果是压缩文件，检查压缩完整性
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "检查压缩文件完整性..."
    if gunzip -t "$BACKUP_FILE"; then
        echo "✅ 压缩文件完整性验证通过"
    else
        echo "❌ 压缩文件损坏"
        exit 1
    fi
fi

# 3. 启动临时 Redis 实例验证数据
echo "启动临时 Redis 实例验证数据..."
TEMP_DIR="/tmp/redis_verify_$$"
mkdir -p "$TEMP_DIR"

# 解压备份文件到临时目录
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" > "$TEMP_DIR/dump.rdb"
else
    cp "$BACKUP_FILE" "$TEMP_DIR/dump.rdb"
fi

# 启动临时 Redis 实例
docker run --rm -d \
    --name redis-verify-$$ \
    -v "$TEMP_DIR:/data" \
    -p 16379:6379 \
    redis:7.0-alpine \
    redis-server --port 6379 --dir /data

# 等待 Redis 启动
sleep 3

# 验证数据加载
if docker exec redis-verify-$$ redis-cli ping > /dev/null 2>&1; then
    KEYS_COUNT=$(docker exec redis-verify-$$ redis-cli DBSIZE)
    echo "✅ 备份验证成功"
    echo "   包含键数量: $KEYS_COUNT"
    
    # 显示一些示例键
    echo "   示例键:"
    docker exec redis-verify-$$ redis-cli --scan --count 5 | head -5 | sed 's/^/     /'
else
    echo "❌ 备份验证失败"
fi

# 清理临时实例和文件
docker stop redis-verify-$$ > /dev/null 2>&1
rm -rf "$TEMP_DIR"

echo "备份验证完成"
EOF

chmod +x /tmp/redis-backup/verify_backup.sh
```

## 6. 故障排除指南

### 6.1 连接问题排查

```bash
# 1. 检查 Pod 状态
kubectl get pods -n database -l app.kubernetes.io/name=redis
kubectl describe pod redis-master-0 -n database

# 2. 检查服务状态
kubectl get svc -n database -l app.kubernetes.io/name=redis

# 3. 查看 Redis 日志
kubectl logs redis-master-0 -n database

# 4. 测试连接
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 ping

# 5. 端口转发测试
kubectl port-forward svc/ai-redis-master -n database 6379:6379 &
redis-cli -h localhost -p 6379 -a redis-2024 ping
```

### 6.2 性能问题诊断

```bash
# 创建性能诊断脚本
cat > /tmp/redis_diagnose.py << 'EOF'
#!/usr/bin/env python3
"""Redis 性能诊断脚本"""

import redis
import time

def diagnose_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, password='redis-2024', decode_responses=True)
        
        print("=== Redis 性能诊断报告 ===")
        
        # 基本信息
        info = r.info()
        print(f"Redis 版本: {info['redis_version']}")
        print(f"运行时间: {info['uptime_in_days']} 天")
        
        # 内存诊断
        memory_info = r.info('memory')
        used_memory_mb = memory_info['used_memory'] / 1024 / 1024
        peak_memory_mb = memory_info['used_memory_peak'] / 1024 / 1024
        fragmentation_ratio = memory_info.get('mem_fragmentation_ratio', 0)
        
        print(f"\n--- 内存使用 ---")
        print(f"当前内存: {used_memory_mb:.2f} MB")
        print(f"峰值内存: {peak_memory_mb:.2f} MB")
        print(f"碎片率: {fragmentation_ratio:.2f}")
        
        if fragmentation_ratio > 1.5:
            print("⚠️  内存碎片率较高，建议优化")
        
        # 性能统计
        stats = r.info('stats')
        hits = stats.get('keyspace_hits', 0)
        misses = stats.get('keyspace_misses', 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        print(f"\n--- 性能统计 ---")
        print(f"缓存命中率: {hit_rate:.2f}%")
        print(f"每秒操作数: {stats.get('instantaneous_ops_per_sec', 0)}")
        print(f"总处理命令: {stats.get('total_commands_processed', 0)}")
        
        if hit_rate < 80:
            print("⚠️  缓存命中率较低，检查缓存策略")
        
        # 慢查询
        slow_queries = r.slowlog_len()
        print(f"\n--- 慢查询 ---")
        print(f"慢查询数量: {slow_queries}")
        
        if slow_queries > 0:
            print("最近的慢查询:")
            for query in r.slowlog_get(5):
                duration_ms = query['duration'] / 1000
                print(f"  {duration_ms:.2f}ms: {' '.join(query['command'])}")
        
        # 客户端连接
        clients_info = r.info('clients')
        print(f"\n--- 客户端连接 ---")
        print(f"当前连接数: {clients_info.get('connected_clients', 0)}")
        print(f"最大输入缓冲: {clients_info.get('client_recent_max_input_buffer', 0)}")
        print(f"最大输出缓冲: {clients_info.get('client_recent_max_output_buffer', 0)}")
        
        # 持久化状态
        print(f"\n--- 持久化状态 ---")
        print(f"最后保存时间: {time.ctime(r.lastsave())}")
        print(f"AOF 状态: {'启用' if info.get('aof_enabled', 0) else '禁用'}")
        
        print("\n=== 诊断完成 ===")
        
    except redis.ConnectionError:
        print("错误: 无法连接到 Redis")
        print("请确保端口转发已启动: kubectl port-forward svc/ai-redis-master -n database 6379:6379")
    except Exception as e:
        print(f"诊断过程中发生错误: {e}")

if __name__ == "__main__":
    diagnose_redis()
EOF

chmod +x /tmp/redis_diagnose.py
```

### 6.3 常见问题解决方案

#### 6.3.1 内存使用过高

```bash
# 检查内存使用
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 INFO memory

# 分析大键
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 --bigkeys

# 设置内存限制
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET maxmemory 1800MB
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET maxmemory-policy allkeys-lru
```

#### 6.3.2 连接数过多

```bash
# 查看客户端连接
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CLIENT LIST

# 设置最大连接数
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET maxclients 1000

# 杀死空闲连接
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CLIENT KILL TYPE normal SKIPME yes
```

#### 6.3.3 性能下降

```bash
# 查看慢查询
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 SLOWLOG GET 10

# 清空慢查询日志
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 SLOWLOG RESET

# 优化配置
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET tcp-keepalive 300
kubectl exec -it redis-master-0 -n database -- redis-cli -a redis-2024 CONFIG SET timeout 0
```

## 7. 备选部署方案

> **说明**: 以下为备选部署方案，仅在特殊情况下使用。当前推荐使用 Kubernetes 部署方式。

### 7.1 Docker 单实例部署

适用于开发测试环境：

```bash
# 创建 Docker 数据目录
mkdir -p /tmp/redis-docker/{data,conf}

# 创建 Redis 配置文件
cat > /tmp/redis-docker/conf/redis.conf << 'EOF'
port 6379
bind 0.0.0.0
protected-mode yes
requirepass redis-2024

# 持久化配置
dir /data
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# 内存配置
maxmemory 1gb
maxmemory-policy allkeys-lru

# 安全配置
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG ""
EOF

# 启动 Redis 容器
docker run -d \
  --name redis-standalone \
  --restart=unless-stopped \
  -p 6379:6379 \
  -v /tmp/redis-docker/data:/data \
  -v /tmp/redis-docker/conf/redis.conf:/etc/redis/redis.conf \
  redis:7.0-alpine redis-server /etc/redis/redis.conf

# 验证部署
docker logs redis-standalone
docker exec redis-standalone redis-cli -a redis-2024 ping
```

### 7.2 Ubuntu 物理服务器部署

适用于需要最大性能的场景：

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装 Redis
sudo apt install -y redis-server redis-tools

# 备份原始配置
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# 创建优化配置
sudo tee /etc/redis/redis.conf > /dev/null << 'EOF'
# Redis 生产配置
bind 127.0.0.1 192.168.0.0/16
protected-mode yes
port 6379
timeout 300
tcp-keepalive 300

# 持久化配置
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# 内存配置
maxmemory 4gb
maxmemory-policy allkeys-lru

# 安全配置
requirepass redis-2024
EOF

# 重启服务
sudo systemctl restart redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server
```

### 7.3 Docker Compose 集群部署

适用于需要高可用的本地环境：

```yaml
# 创建 docker-compose.yml
cat > /tmp/redis-cluster-compose.yml << 'EOF'
version: '3.8'

services:
  redis-master:
    image: redis:7.0-alpine
    container_name: redis-master
    restart: unless-stopped
    ports:
      - "6379:6379"
    command: redis-server --requirepass redis-2024 --appendonly yes
    volumes:
      - redis_master_data:/data

  redis-replica:
    image: redis:7.0-alpine
    container_name: redis-replica
    restart: unless-stopped
    ports:
      - "6380:6379"
    command: redis-server --replicaof redis-master 6379 --masterauth redis-2024 --requirepass redis-2024
    volumes:
      - redis_replica_data:/data
    depends_on:
      - redis-master

  redis-sentinel:
    image: redis:7.0-alpine
    container_name: redis-sentinel
    restart: unless-stopped
    ports:
      - "26379:26379"
    command: >
      sh -c "echo 'port 26379
      sentinel monitor mymaster redis-master 6379 1
      sentinel auth-pass mymaster redis-2024
      sentinel down-after-milliseconds mymaster 5000
      sentinel failover-timeout mymaster 10000' > /etc/sentinel.conf &&
      redis-server /etc/sentinel.conf --sentinel"
    depends_on:
      - redis-master
      - redis-replica

volumes:
  redis_master_data:
  redis_replica_data:
EOF

# 启动集群
docker compose -f /tmp/redis-cluster-compose.yml up -d

# 验证集群状态
docker exec redis-sentinel redis-cli -p 26379 sentinel masters
```

## 相关资源

- **文档职责分工**:
  - [环境部署](../../01_environment_deployment/03_storage_systems_kubernetes.md): Redis 在 Kubernetes 中的实际部署步骤
  - 本文档: Redis 配置优化、性能调优、监控维护和故障排查
- **相关配置文件**: 
  - `redis-values.yaml`: Helm Chart 配置文件
  - `redis-pv.yaml`: 持久化存储配置
- **外部资源**:
  - [Redis 官方文档](https://redis.io/documentation)
  - [Redis 命令参考](https://redis.io/commands)
  - [Bitnami Redis Helm Chart](https://github.com/bitnami/charts/tree/main/bitnami/redis)
