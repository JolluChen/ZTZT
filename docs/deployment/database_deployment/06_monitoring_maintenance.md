# 数据库监控与维护指南

本文档提供了AI中台数据库系统的监控、维护和运维最佳实践指南，以确保数据库服务的稳定性、性能和可用性。

## 目录
- [监控策略概述](#监控策略概述)
- [监控工具](#监控工具)
  - [Prometheus与Grafana](#prometheus与grafana)
  - [数据库原生监控工具](#数据库原生监控工具)
  - [自定义监控脚本](#自定义监控脚本)
- [关键性能指标](#关键性能指标)
  - [PostgreSQL指标](#postgresql指标)
  - [MongoDB指标](#mongodb指标)
  - [Weaviate指标](#weaviate指标)
  - [Redis指标](#redis指标)
  - [Kafka指标](#kafka指标)
- [性能优化](#性能优化)
  - [SQL优化](#sql优化)
  - [索引优化](#索引优化)
  - [查询缓存](#查询缓存)
  - [配置调优](#配置调优)
- [日常维护任务](#日常维护任务)
  - [索引维护](#索引维护)
  - [统计信息更新](#统计信息更新)
  - [数据清理](#数据清理)
  - [日志管理](#日志管理)
- [告警系统](#告警系统)
- [容量规划](#容量规划)
- [故障排查](#故障排查)

## 监控策略概述

有效的数据库监控策略是确保AI中台高可用和高性能的基础。监控策略应当包括以下几个方面：

1. **实时监控**：捕获数据库实时运行状态和性能指标
2. **趋势分析**：通过历史数据分析性能趋势，预测潜在问题
3. **主动告警**：设置适当的阈值，在问题发生前提供预警
4. **全面覆盖**：监控所有数据库组件，包括主从节点、集群状态等
5. **性能影响最小化**：确保监控本身不会对系统产生过大负载

## 监控工具

### Prometheus与Grafana

Prometheus和Grafana是监控数据库系统的黄金组合，提供了强大的数据收集、存储和可视化能力。

#### Prometheus配置

1. 在每个数据库服务器上安装相应的Exporter：

```bash
# PostgreSQL Exporter
docker run -d --name postgres_exporter \
  -p 9187:9187 \
  -e DATA_SOURCE_NAME="postgresql://user:password@postgresql:5432/postgres?sslmode=disable" \
  quay.io/prometheuscommunity/postgres-exporter

# MongoDB Exporter
docker run -d --name mongodb_exporter \
  -p 9216:9216 \
  -e MONGODB_URI="mongodb://user:password@mongodb:27017" \
  percona/mongodb_exporter

# Redis Exporter
docker run -d --name redis_exporter \
  -p 9121:9121 \
  -e REDIS_ADDR=redis://redis:6379 \
  oliver006/redis_exporter

# Node Exporter (服务器指标)
docker run -d --name node_exporter \
  -p 9100:9100 \
  --restart=always \
  -v "/proc:/host/proc:ro" \
  -v "/sys:/host/sys:ro" \
  -v "/:/rootfs:ro" \
  quay.io/prometheus/node-exporter
```

2. Prometheus配置文件示例（prometheus.yml）：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

rule_files:
  - "rules/database_alerts.yml"

scrape_configs:
  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres_exporter:9187']
        labels:
          instance: 'primary_db'

  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongodb_exporter:9216']
        labels:
          instance: 'document_db'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
        labels:
          instance: 'cache_db'

  - job_name: 'weaviate'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['weaviate:8080']
        labels:
          instance: 'vector_db'

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka_exporter:9308']
        labels:
          instance: 'message_queue'

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['node_exporter:9100']
        labels:
          instance: 'db_server'
```

3. 告警规则示例（database_alerts.yml）：

```yaml
groups:
- name: database_alerts
  rules:
  - alert: PostgreSQLHighConnections
    expr: sum(pg_stat_activity_count) > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "PostgreSQL high connection count"
      description: "PostgreSQL instance has more than 100 connections for 5 minutes"

  - alert: MongoDBReplicationLag
    expr: mongodb_mongod_replset_member_optime_date{state="SECONDARY"} - on(set) group_left mongodb_mongod_replset_member_optime_date{state="PRIMARY"} > 10
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "MongoDB replication lag"
      description: "MongoDB replication lag is more than 10 seconds for 5 minutes"

  - alert: RedisMemoryHigh
    expr: redis_memory_used_bytes / redis_memory_max_bytes * 100 > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis memory usage high"
      description: "Redis is using more than 80% of its available memory for 5 minutes"
```

### Grafana仪表板

为各数据库系统配置Grafana仪表板：

1. PostgreSQL仪表板：使用Grafana仪表板ID 9628或14557
2. MongoDB仪表板：使用Grafana仪表板ID 7353或2583
3. Redis仪表板：使用Grafana仪表板ID 763
4. Weaviate仪表板：创建自定义仪表板监控请求延迟、内存使用等
5. Kafka仪表板：使用Grafana仪表板ID 7589

### 数据库原生监控工具

除了Prometheus外，也可以使用各数据库系统自带的监控工具：

#### PostgreSQL

1. pg_stat_statements扩展：跟踪SQL查询性能

```sql
-- 启用扩展
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 查看慢查询
SELECT query, calls, total_exec_time/calls as avg_time, rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

2. 使用pgBadger分析PostgreSQL日志：

```bash
# 安装pgBadger
apt-get install pgbadger

# 生成报告
pgbadger /var/log/postgresql/postgresql-16-main.log -o /var/www/html/pgbadger/index.html
```

#### MongoDB

使用MongoDB Compass或mongo shell监控命令：

```javascript
// 服务器状态
db.serverStatus()

// 复制集状态
rs.status()

// 数据库性能统计
db.stats()

// 慢查询分析
db.getSiblingDB('admin').system.profile.find({millis: {$gt: 100}}).pretty()
```

#### Redis

使用Redis CLI监控命令：

```bash
# 监控命令
redis-cli monitor

# 查看统计信息
redis-cli info

# 延迟测试
redis-cli --latency
```

### 自定义监控脚本

对于特定的监控需求，可以编写自定义脚本。例如，检查PostgreSQL连接数的Python脚本：

```python
#!/usr/bin/env python3
import psycopg2
import sys
import datetime

def check_connections():
    try:
        conn = psycopg2.connect(
            host="your_db_host",
            database="postgres",
            user="your_user",
            password="your_password"
        )
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM pg_stat_activity")
        connections = cur.fetchone()[0]
        
        cur.execute("SHOW max_connections")
        max_connections = int(cur.fetchone()[0])
        
        usage_percent = (connections / max_connections) * 100
        
        print(f"{datetime.datetime.now()} - Current connections: {connections}/{max_connections} ({usage_percent:.2f}%)")
        
        if usage_percent > 80:
            print("WARNING: High connection usage")
            # 添加告警逻辑，如发送邮件或调用告警API
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_connections()
```

## 关键性能指标

### PostgreSQL指标

| 指标 | 描述 | 推荐阈值 | 优化方案 |
|------|------|----------|----------|
| 连接数 | 当前活跃连接数 | <80% max_connections | 使用连接池，增加max_connections |
| 缓存命中率 | 缓存命中与总访问的比率 | >95% | 增加shared_buffers |
| 慢查询 | 执行时间超过阈值的查询 | <1% | 优化SQL，添加索引 |
| 表膨胀 | 由于VACUUM不足导致的表大小增长 | <10% | 调整autovacuum参数 |
| 锁等待 | 等待锁的会话数 | <5 | 优化事务，减少长事务 |
| 复制延迟 | 主从复制的延迟时间 | <10s | 提高网络带宽，增加WAL发送进程 |

### MongoDB指标

| 指标 | 描述 | 推荐阈值 | 优化方案 |
|------|------|----------|----------|
| 操作延迟 | 读/写操作的延迟时间 | 读<100ms, 写<200ms | 优化索引，增加内存 |
| 连接数 | 当前连接数 | <80% max_connections | 使用连接池 |
| 队列长度 | 等待执行的操作数 | <10 | 增加服务器资源 |
| 内存使用 | WiredTiger缓存使用率 | <80% | 增加缓存大小 |
| 复制延迟 | 从节点复制延迟 | <10s | 提高网络带宽 |
| 锁争用 | 锁冲突率 | <5% | 优化查询模式 |

### Weaviate指标

| 指标 | 描述 | 推荐阈值 | 优化方案 |
|------|------|----------|----------|
| 查询延迟 | 向量检索操作延迟 | <200ms | 优化索引参数，增加资源 |
| QPS | 每秒查询数 | 稳定且无增长趋势 | 增加节点，负载均衡 |
| 内存使用 | 向量索引内存占用 | <80% | 增加内存，优化向量维度 |
| 索引构建时间 | 重建索引所需时间 | 根据数据量而定 | 增加CPU资源 |
| 错误率 | 查询错误百分比 | <0.1% | 检查错误日志，修复错误 |

### Redis指标

| 指标 | 描述 | 推荐阈值 | 优化方案 |
|------|------|----------|----------|
| 内存使用率 | 已用内存/最大内存 | <80% | 设置过期时间，增加内存 |
| 命令执行率 | 每秒执行的命令数 | 根据硬件而定 | 批处理命令，优化客户端 |
| 响应时间 | 命令执行延迟 | <1ms | 减少大键值对，避免慢命令 |
| 缓存命中率 | 缓存命中与总请求比率 | >80% | 调整过期策略 |
| 阻塞命令 | 造成服务器阻塞的命令 | 无 | 避免KEYS等O(N)命令 |
| 复制延迟 | 主从复制延迟 | <1s | 提高网络带宽 |

### Kafka指标

| 指标 | 描述 | 推荐阈值 | 优化方案 |
|------|------|----------|----------|
| 消息积压 | 未消费的消息数量 | 取决于业务 | 增加消费者，提高消费能力 |
| 生产延迟 | 消息发送延迟 | <100ms | 优化生产者配置，增加资源 |
| 消费延迟 | 消息消费延迟 | <500ms | 优化消费者代码，增加分区 |
| 副本同步 | 同步副本的数量 | >=min.insync.replicas | 检查网络和磁盘性能 |
| 磁盘使用率 | 日志数据占用磁盘比例 | <80% | 调整保留策略，增加存储 |

## 性能优化

### SQL优化

PostgreSQL查询优化技巧：

1. 使用EXPLAIN ANALYZE分析查询计划：

```sql
EXPLAIN ANALYZE SELECT * FROM ai_models WHERE model_type = 'text-generation' AND updated_at > now() - interval '7 days';
```

2. 避免使用SELECT *，只选择需要的字段
3. 使用适当的索引
4. 合理使用JOIN，避免笛卡尔积
5. 使用合适的数据类型
6. 对大表进行分区

### 索引优化

1. PostgreSQL索引优化：

```sql
-- 为常用查询条件创建索引
CREATE INDEX idx_ai_models_model_type ON ai_models(model_type);

-- 为排序和过滤条件创建组合索引
CREATE INDEX idx_ai_models_type_updated ON ai_models(model_type, updated_at);

-- 为全文搜索创建GIN索引
CREATE INDEX idx_documents_content ON documents USING GIN (to_tsvector('english', content));
```

2. MongoDB索引优化：

```javascript
// 创建单字段索引
db.ai_tasks.createIndex({ "status": 1 });

// 创建复合索引
db.ai_tasks.createIndex({ "user_id": 1, "created_at": -1 });

// 创建TTL索引
db.temporary_results.createIndex({ "created_at": 1 }, { expireAfterSeconds: 86400 });

// 为文本搜索创建索引
db.documents.createIndex({ "content": "text" });
```

3. Weaviate向量索引优化：

```yaml
# weaviate类定义中优化HNSW索引参数
class_schema:
  vectorIndexConfig:
    skip: false
    efConstruction: 256  # 增加构建质量
    maxConnections: 64   # 增加连接数以提高准确性
    ef: 128              # 增加搜索质量
```

### 查询缓存

1. 使用Redis缓存频繁查询结果：

```python
import redis
import json
import hashlib

redis_client = redis.Redis(host='redis_host', port=6379, db=0)

def get_user_preferences(user_id):
    # 生成缓存键
    cache_key = f"user_preferences:{user_id}"
    
    # 尝试从缓存获取
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # 缓存未命中，从数据库获取
    db_result = db.query(f"SELECT * FROM user_preferences WHERE user_id = {user_id}")
    
    # 存入缓存，设置30分钟过期
    redis_client.setex(cache_key, 1800, json.dumps(db_result))
    
    return db_result
```

2. 使用PostgreSQL的materialized view：

```sql
-- 创建物化视图
CREATE MATERIALIZED VIEW monthly_usage_stats AS
SELECT user_id, 
       model_id,
       date_trunc('month', created_at) as month,
       count(*) as usage_count,
       sum(tokens) as total_tokens
FROM ai_model_usage
GROUP BY user_id, model_id, date_trunc('month', created_at);

-- 创建索引以加速查询
CREATE INDEX idx_monthly_usage_user ON monthly_usage_stats(user_id, month);

-- 按需刷新视图
REFRESH MATERIALIZED VIEW monthly_usage_stats;
```

### 配置调优

1. PostgreSQL配置优化：

```ini
# 内存配置
shared_buffers = 8GB                  # 建议为系统内存的25%
work_mem = 64MB                       # 复杂排序和哈希操作的内存
maintenance_work_mem = 1GB            # 维护操作的内存
effective_cache_size = 24GB           # 系统缓存估计值，约为系统内存的75%

# 写入性能
wal_buffers = 16MB                    # WAL缓冲区大小
synchronous_commit = off              # 降低持久性以提高性能
wal_writer_delay = 200ms              # WAL写入延迟

# 后台写入器
bgwriter_delay = 200ms                # 后台写入器延迟
bgwriter_lru_maxpages = 1000          # 每轮最大写入页数

# 自动清理
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
```

2. MongoDB配置优化：

```yaml
# mongod.conf
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 8                  # WiredTiger缓存大小
      journalCompressor: zstd         # 日志压缩算法
    collectionConfig:
      blockCompressor: zstd           # 集合数据压缩算法

operationProfiling:
  mode: slowOp                        # 记录慢操作
  slowOpThresholdMs: 100              # 慢操作阈值(毫秒)

net:
  maxIncomingConnections: 2000        # 最大连接数

setParameter:
  maxTransactionLockRequestTimeoutMillis: 5000  # 事务锁超时
  cursorTimeoutMillis: 600000                   # 游标超时
```

3. Redis配置优化：

```conf
# redis.conf
maxmemory 8gb                        # 最大内存
maxmemory-policy allkeys-lru         # LRU淘汰策略
slowlog-log-slower-than 10000        # 慢日志阈值(微秒)
slowlog-max-len 128                  # 慢日志长度
tcp-keepalive 300                    # TCP保活时间
timeout 0                            # 客户端连接超时(0=永不超时)
hz 10                                # 后台任务频率
```

## 日常维护任务

### 索引维护

1. PostgreSQL索引维护：

```sql
-- 重建索引
REINDEX TABLE ai_models;

-- 分析表统计信息
ANALYZE ai_models;

-- 查找未使用的索引
SELECT schemaname || '.' || relname as table,
       indexrelname as index,
       idx_scan as index_scans
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY table, index;
```

2. MongoDB索引维护：

```javascript
// 查看索引使用情况
db.ai_tasks.aggregate([
  { $indexStats: { } }
]);

// 重建索引
db.runCommand({ compact: "ai_tasks" });

// 删除未使用的索引
db.ai_tasks.dropIndex("unused_index_name");
```

### 统计信息更新

1. PostgreSQL统计信息更新：

```sql
-- 更新单表统计
ANALYZE ai_models;

-- 更新所有表统计
ANALYZE VERBOSE;

-- 调整统计样本大小
ALTER TABLE large_table SET (autovacuum_analyze_scale_factor = 0.01);
```

2. MongoDB统计信息：

```javascript
// 查看集合统计
db.ai_tasks.stats();

// 查看数据库统计
db.stats();

// 查看索引大小
db.ai_tasks.stats().indexSizes;
```

### 数据清理

1. PostgreSQL数据清理：

```sql
-- 手动VACUUM
VACUUM VERBOSE ai_models;

-- 完全VACUUM（锁表）
VACUUM FULL ai_models;

-- 清理旧数据
DELETE FROM ai_model_usage WHERE created_at < now() - interval '1 year';
```

2. MongoDB数据清理：

```javascript
// 删除旧数据
db.model_usage.deleteMany({ 
  created_at: { $lt: new Date(new Date().setFullYear(new Date().getFullYear() - 1)) } 
});

// 创建TTL索引自动过期
db.temp_data.createIndex({ "created_at": 1 }, { expireAfterSeconds: 604800 }); // 7天过期
```

3. Redis数据清理：

```bash
# 设置过期时间
redis-cli EXPIRE cache:user:1234 86400

# 使用SCAN删除匹配模式的键
redis-cli --scan --pattern "temp:*" | xargs redis-cli DEL

# 手动清理过期键
redis-cli KEYS "temp:*" | xargs redis-cli DEL
```

### 日志管理

1. 日志轮转：

```bash
# PostgreSQL日志轮转配置 (postgresql.conf)
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
```

2. 日志压缩和存档：

```bash
# 使用logrotate管理日志
cat > /etc/logrotate.d/mongodb << EOF
/var/log/mongodb/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 mongodb mongodb
    sharedscripts
    postrotate
        /bin/kill -SIGUSR1 \$(cat /var/run/mongodb/mongod.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF
```

## 告警系统

使用AlertManager与Prometheus集成，处理和路由告警：

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'username'
  smtp_auth_password: 'password'

route:
  group_by: ['alertname', 'instance']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'team-dba'
  routes:
  - match:
      severity: critical
    receiver: 'team-dba-pager'
    repeat_interval: 1h
  - match:
      severity: warning
    receiver: 'team-dba'

receivers:
- name: 'team-dba'
  email_configs:
  - to: 'dba-team@example.com'
    send_resolved: true

- name: 'team-dba-pager'
  email_configs:
  - to: 'dba-oncall@example.com'
    send_resolved: true
  webhook_configs:
  - url: 'http://pager.example.com/trigger'
    send_resolved: true
```

## 容量规划

容量规划策略：

1. **监控增长趋势**：记录并分析数据大小、查询数量的历史趋势
2. **预测未来需求**：基于历史数据和业务计划预测未来6-12个月的需求
3. **资源分配策略**：
   - 数据库服务器：留出50%余量
   - 存储空间：预留100%余量
   - 连接数：预留30%余量

示例容量规划工具（Python脚本）：

```python
#!/usr/bin/env python3
import psycopg2
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

# 连接数据库
conn = psycopg2.connect("dbname=postgres user=postgres password=password host=localhost")
cur = conn.cursor()

# 查询数据库大小历史数据
cur.execute("""
    SELECT date_trunc('day', collected_at) as day, 
           database_size_bytes 
    FROM db_size_history 
    WHERE database_name = 'ai_platform' 
    ORDER BY day
""")
results = cur.fetchall()

# 转换为DataFrame
df = pd.DataFrame(results, columns=['day', 'size'])
df['day'] = pd.to_datetime(df['day'])
df.set_index('day', inplace=True)

# 绘制历史趋势
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['size']/1024/1024/1024, marker='o', linestyle='-')
plt.title('AI Platform Database Size (GB)')
plt.xlabel('Date')
plt.ylabel('Size (GB)')
plt.grid(True)

# 预测未来趋势
if len(df) > 30:  # 至少需要30天数据
    # 计算平均日增长率
    growth_rate = (df['size'].iloc[-1] - df['size'].iloc[0]) / len(df)
    
    # 预测未来180天
    last_date = df.index[-1]
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=180)
    future_df = pd.DataFrame(index=future_dates)
    future_df['size'] = [df['size'].iloc[-1] + growth_rate * i for i in range(1, 181)]
    
    # 绘制预测
    plt.plot(future_df.index, future_df['size']/1024/1024/1024, marker='.', linestyle='--', color='red')
    plt.axhline(y=your_disk_size, color='green', linestyle='-', label='Current Disk Size')
    
    # 计算预计达到磁盘上限的日期
    if growth_rate > 0:
        days_until_full = (your_disk_size*1024*1024*1024 - df['size'].iloc[-1]) / growth_rate
        full_date = last_date + timedelta(days=int(days_until_full))
        plt.axvline(x=full_date, color='orange', linestyle='--', label=f'Disk Full ({full_date.strftime("%Y-%m-%d")})')

plt.legend()
plt.savefig('/var/www/html/capacity/db_size_forecast.png')

# 关闭连接
cur.close()
conn.close()
```

## 故障排查

常见数据库问题及解决方案：

### PostgreSQL常见问题

1. **连接数耗尽**：

```sql
-- 查看当前连接
SELECT count(*) FROM pg_stat_activity;

-- 查找空闲连接
SELECT pid, application_name, client_addr, state, query, 
       now() - state_change as state_duration
FROM pg_stat_activity
WHERE state = 'idle'
ORDER BY state_change;

-- 终止空闲连接
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND now() - state_change > interval '1 hour';
```

2. **高CPU使用率**：

```sql
-- 查找消耗CPU的查询
SELECT pid, client_addr, state, query, 
       now() - query_start as duration
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

3. **磁盘空间不足**：

```sql
-- 查找大表
SELECT nspname || '.' || relname AS "relation",
       pg_size_pretty(pg_total_relation_size(C.oid)) AS "total_size"
FROM pg_class C
LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
WHERE nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(C.oid) DESC
LIMIT 20;

-- 查找膨胀表
SELECT schemaname, tablename, 
       pg_size_pretty(table_size) AS table_size,
       pg_size_pretty(bloat_size) AS bloat_size,
       round(100*bloat_size/table_size) AS bloat_percentage
FROM public.pgstattuple_bloat_estimation()
ORDER BY bloat_size DESC
LIMIT 20;
```

### MongoDB常见问题

1. **连接超时**：

```javascript
// 查看当前连接
db.currentOp(true);

// 检查连接限制
db.serverStatus().connections;
```

2. **慢查询**：

```javascript
// 开启查询分析器
db.setProfilingLevel(1, 100);  // 记录超过100ms的操作

// 查看慢查询
db.system.profile.find({millis: {$gt: 100}}).sort({ts: -1});
```

3. **索引缺失**：

```javascript
// 查看查询计划
db.ai_tasks.find({status: "running", user_id: "123"}).explain("executionStats");

// 创建索引
db.ai_tasks.createIndex({status: 1, user_id: 1});
```

### Redis常见问题

1. **内存使用过高**：

```bash
# 查看内存使用
redis-cli info memory

# 查找大键
redis-cli --bigkeys

# 内存分析
redis-cli memory usage <key>
```

2. **高延迟**：

```bash
# 查看延迟
redis-cli --latency

# 检查慢日志
redis-cli slowlog get 10

# 检查阻塞命令
redis-cli --stat
```

3. **连接问题**：

```bash
# 查看客户端连接
redis-cli client list

# 查看网络统计
redis-cli info clients
```

### 通用恢复步骤

1. **备份与恢复**：
   - 确保有最新的备份
   - 测试恢复过程
   - 记录恢复时间(RTO)和恢复点(RPO)

2. **故障处理流程**：
   - 识别问题
   - 隔离影响
   - 实施临时解决方案
   - 应用永久修复
   - 事后分析

3. **故障报告模板**：
   - 问题描述
   - 影响范围
   - 根本原因
   - 解决过程
   - 预防措施
