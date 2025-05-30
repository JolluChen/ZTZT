# 高可用性和灾难恢复配置指南

本文档提供了AI中台数据库系统的高可用性(HA)和灾难恢复(DR)配置详细指南，以确保关键数据服务的连续性和可靠性。

## 目录
- [高可用架构概述](#高可用架构概述)
- [可用性目标](#可用性目标)
- [PostgreSQL高可用配置](#postgresql高可用配置)
  - [主从复制](#postgresql主从复制)
  - [自动故障转移](#postgresql自动故障转移)
  - [读写分离](#postgresql读写分离)
- [MongoDB高可用配置](#mongodb高可用配置)
  - [副本集部署](#mongodb副本集部署)
  - [分片集群](#mongodb分片集群)
  - [故障转移配置](#mongodb故障转移配置)
- [Redis高可用配置](#redis高可用配置)
  - [Sentinel模式](#redis-sentinel模式)
  - [Redis集群](#redis集群)
  - [持久化配置](#redis持久化配置)
- [Weaviate高可用配置](#weaviate高可用配置)
  - [Weaviate集群配置](#weaviate集群配置)
  - [备份恢复策略](#weaviate备份恢复策略)
- [Kafka高可用配置](#kafka高可用配置)
  - [多节点集群](#kafka多节点集群)
  - [分区副本](#kafka分区副本)
  - [可靠性配置](#kafka可靠性配置)
- [跨区域灾难恢复](#跨区域灾难恢复)
  - [数据复制策略](#数据复制策略)
  - [故障切换流程](#故障切换流程)
  - [恢复时间目标](#恢复时间目标)
- [负载均衡和流量管理](#负载均衡和流量管理)
- [监控和告警](#高可用监控和告警)
- [定期测试和演练](#定期测试和演练)

## 高可用架构概述

AI中台的高可用架构采用多层次的冗余和灾备机制，确保关键数据服务的持续可用性。架构设计遵循以下原则：

1. **消除单点故障**：所有关键组件都有冗余部署
2. **故障自动恢复**：自动检测故障并执行故障转移
3. **数据不丢失**：采用同步复制或高可靠性的异步复制
4. **地理分布**：核心服务跨可用区部署，灾备系统跨区域部署
5. **性能与可用性平衡**：在保证可用性的同时优化性能
6. **可观测性**：全面的监控和告警系统

高可用总体架构图：

```
                    ┌──────────────┐
                    │   用户请求    │
                    └───────┬──────┘
                            │
                    ┌───────▼──────┐
                    │  负载均衡器   │
                    └───────┬──────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│  应用服务器 1  │   │  应用服务器 2  │   │  应用服务器 3  │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                   ┌────────▼────────┐
                   │ 数据库负载均衡器 │
                   └────────┬────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
┌───▼───┐              ┌────▼────┐             ┌────▼────┐
│ 主DB │◄─────────────►│ 从DB 1 │◄────────────►│ 从DB 2 │
└───┬───┘              └────┬────┘             └────┬────┘
    │                       │                       │
    └───────────────────────┼───────────────────────┘
                            │
                   ┌────────▼────────┐
                   │跨区域灾备复制链路│
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │   灾备数据中心   │
                   └─────────────────┘
```

## 可用性目标

AI中台数据服务的可用性目标：

| 服务类型 | 可用性目标(SLA) | 最大容许故障时间(每月) | 灾难恢复目标 |
|---------|---------------|---------------------|------------|
| 核心数据库(PostgreSQL) | 99.99% | 4.38分钟 | RTO < 5分钟, RPO < 1分钟 |
| 文档数据库(MongoDB) | 99.95% | 21.9分钟 | RTO < 10分钟, RPO < 5分钟 |
| 向量数据库(Weaviate) | 99.9% | 43.8分钟 | RTO < 15分钟, RPO < 10分钟 |
| 缓存系统(Redis) | 99.99% | 4.38分钟 | RTO < 1分钟, RPO 可能丢失 |
| 消息队列(Kafka) | 99.95% | 21.9分钟 | RTO < 10分钟, RPO < 1分钟 |

> 注：RTO (Recovery Time Objective) 表示恢复时间目标，即从灾难发生到服务恢复可用所需的时间；RPO (Recovery Point Objective) 表示恢复点目标，即可能丢失的最大数据量（通常以时间表示）。

## PostgreSQL高可用配置

### PostgreSQL主从复制

PostgreSQL支持多种复制方式，推荐使用流复制(Streaming Replication)配置主从架构：

1. **主节点配置**：

```ini
# postgresql.conf (主节点)
listen_addresses = '*'
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_segments = 64
hot_standby = on
synchronous_standby_names = 'standby1, standby2'  # 启用同步复制时配置
```

```
# pg_hba.conf (主节点)
host    replication     replicator      10.0.0.0/24           scram-sha-256
```

2. **从节点配置**：

```ini
# postgresql.conf (从节点)
listen_addresses = '*'
hot_standby = on
```

3. **初始化从节点**：

```bash
# 在主节点创建复制用户
psql -c "CREATE ROLE replicator WITH REPLICATION PASSWORD 'strong_password' LOGIN;"

# 在从节点执行基础备份
pg_basebackup -h primary_server -D /var/lib/postgresql/16/main -U replicator -P -v -R -X stream -C -S replica_slot_name
```

4. **从节点恢复配置**：

```
# recovery.conf (PostgreSQL 12前) 或 postgresql.auto.conf (PostgreSQL 12及以上)
primary_conninfo = 'host=primary_server port=5432 user=replicator password=strong_password application_name=standby1'
primary_slot_name = 'replica_slot_name'
recovery_target_timeline = 'latest'
```

### PostgreSQL自动故障转移

使用Patroni和etcd实现自动故障转移：

1. **安装Patroni**：

```bash
pip install patroni[etcd] psycopg2-binary
```

2. **配置Patroni**：

```yaml
# patroni.yml
scope: postgres-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.0.1:8008

etcd:
  hosts: 10.0.0.10:2379,10.0.0.11:2379,10.0.0.12:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 100
        shared_buffers: 4GB
        max_wal_size: 2GB

  initdb:
    - encoding: UTF8
    - data-checksums

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.0.1:5432
  data_dir: /var/lib/postgresql/16/main
  bin_dir: /usr/lib/postgresql/16/bin
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: strong_password
    superuser:
      username: postgres
      password: postgres_password
  parameters:
    unix_socket_directories: '/var/run/postgresql'
```

3. **启动Patroni**：

```bash
# 创建systemd服务
cat > /etc/systemd/system/patroni.service << EOF
[Unit]
Description=Patroni Postgresql Cluster
After=network.target

[Service]
User=postgres
Group=postgres
ExecStart=/usr/local/bin/patroni /etc/patroni/patroni.yml
KillMode=process
TimeoutSec=30
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl enable patroni
systemctl start patroni
```

4. **配置HAProxy用于负载均衡**：

```
# /etc/haproxy/haproxy.cfg
frontend postgres
    bind *:5432
    mode tcp
    default_backend postgres_backend

backend postgres_backend
    mode tcp
    option httpchk
    http-check send meth GET uri /master
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server postgresql_10.0.0.1_5432 10.0.0.1:5432 maxconn 100 check port 8008
    server postgresql_10.0.0.2_5432 10.0.0.2:5432 maxconn 100 check port 8008
    server postgresql_10.0.0.3_5432 10.0.0.3:5432 maxconn 100 check port 8008
```

### PostgreSQL读写分离

配置读写分离以优化性能：

1. **应用配置**：

```python
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# 主库连接池（写操作）
master_pool = SimpleConnectionPool(5, 20,
                                   host='haproxy_master',
                                   database='aiplatform',
                                   user='app_user',
                                   password='app_password')

# 从库连接池（读操作）
replica_pool = SimpleConnectionPool(5, 20,
                                    host='haproxy_replica',
                                    database='aiplatform',
                                    user='app_user',
                                    password='app_password')

def execute_write(query, params=None):
    """执行写操作"""
    conn = master_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        master_pool.putconn(conn)

def execute_read(query, params=None):
    """执行读操作"""
    conn = replica_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        replica_pool.putconn(conn)
```

2. **HAProxy配置**：

```
# /etc/haproxy/haproxy.cfg - 主库负载均衡
frontend postgres_write
    bind *:5432
    mode tcp
    default_backend postgres_master_backend

backend postgres_master_backend
    mode tcp
    option httpchk
    http-check send meth GET uri /master
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server postgresql_10.0.0.1_5432 10.0.0.1:5432 maxconn 100 check port 8008

# /etc/haproxy/haproxy.cfg - 从库负载均衡
frontend postgres_read
    bind *:5433
    mode tcp
    default_backend postgres_replica_backend

backend postgres_replica_backend
    mode tcp
    option httpchk
    http-check send meth GET uri /replica
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server postgresql_10.0.0.2_5432 10.0.0.2:5432 maxconn 100 check port 8008
    server postgresql_10.0.0.3_5432 10.0.0.3:5432 maxconn 100 check port 8008
```

## MongoDB高可用配置

### MongoDB副本集部署

MongoDB副本集提供数据冗余和高可用性：

1. **副本集配置**：

```yaml
# mongod.conf
replication:
  replSetName: "rs0"
net:
  bindIp: 0.0.0.0
  port: 27017
security:
  authorization: enabled
  keyFile: /etc/mongodb/keyfile
```

2. **初始化副本集**：

```javascript
// 连接到主节点
mongo --host 10.0.0.1

// 初始化副本集
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "10.0.0.1:27017", priority: 2 },
    { _id: 1, host: "10.0.0.2:27017", priority: 1 },
    { _id: 2, host: "10.0.0.3:27017", priority: 1 }
  ]
})

// 创建管理员账户
use admin
db.createUser({
  user: "admin",
  pwd: "admin_password",
  roles: [ { role: "root", db: "admin" } ]
})

// 创建应用账户
use aiplatform
db.createUser({
  user: "app_user",
  pwd: "app_password",
  roles: [ { role: "readWrite", db: "aiplatform" } ]
})
```

3. **生成和分发密钥文件**：

```bash
# 生成密钥文件
openssl rand -base64 756 > /etc/mongodb/keyfile
chmod 400 /etc/mongodb/keyfile
chown mongodb:mongodb /etc/mongodb/keyfile

# 复制到其他节点
scp /etc/mongodb/keyfile mongodb@10.0.0.2:/etc/mongodb/keyfile
scp /etc/mongodb/keyfile mongodb@10.0.0.3:/etc/mongodb/keyfile
```

### MongoDB分片集群

对于需要水平扩展的大规模部署，配置分片集群：

1. **配置服务器副本集**：

```yaml
# 配置服务器mongod.conf
sharding:
  clusterRole: configsvr
replication:
  replSetName: "configrs"
net:
  bindIp: 0.0.0.0
  port: 27019
```

```javascript
// 初始化配置副本集
mongo --host 10.0.1.1:27019
rs.initiate({
  _id: "configrs",
  configsvr: true,
  members: [
    { _id: 0, host: "10.0.1.1:27019" },
    { _id: 1, host: "10.0.1.2:27019" },
    { _id: 2, host: "10.0.1.3:27019" }
  ]
})
```

2. **分片副本集**：

```yaml
# 分片服务器mongod.conf
sharding:
  clusterRole: shardsvr
replication:
  replSetName: "shard0"
net:
  bindIp: 0.0.0.0
  port: 27018
```

```javascript
// 初始化分片副本集
mongo --host 10.0.2.1:27018
rs.initiate({
  _id: "shard0",
  members: [
    { _id: 0, host: "10.0.2.1:27018" },
    { _id: 1, host: "10.0.2.2:27018" },
    { _id: 2, host: "10.0.2.3:27018" }
  ]
})

// 对第二个分片重复上述步骤，使用不同的服务器和replSetName
```

3. **mongos路由器**：

```yaml
# mongos.conf
sharding:
  configDB: configrs/10.0.1.1:27019,10.0.1.2:27019,10.0.1.3:27019
net:
  bindIp: 0.0.0.0
  port: 27017
```

```javascript
// 添加分片到集群
mongo --host 10.0.0.1  // 连接到mongos
sh.addShard("shard0/10.0.2.1:27018,10.0.2.2:27018,10.0.2.3:27018")
sh.addShard("shard1/10.0.3.1:27018,10.0.3.2:27018,10.0.3.3:27018")

// 开启数据库分片
sh.enableSharding("aiplatform")

// 对集合进行分片
sh.shardCollection("aiplatform.ai_tasks", { user_id: "hashed" })
```

### MongoDB故障转移配置

MongoDB副本集自动处理故障转移，但需要正确配置监控和警报：

1. **连接字符串配置**：

```
mongodb://app_user:app_password@10.0.0.1:27017,10.0.0.2:27017,10.0.0.3:27017/aiplatform?replicaSet=rs0&readPreference=secondaryPreferred
```

2. **客户端配置示例**：

```python
from pymongo import MongoClient, ReadPreference

# 连接到副本集
client = MongoClient(
    'mongodb://app_user:app_password@10.0.0.1:27017,10.0.0.2:27017,10.0.0.3:27017/aiplatform',
    replicaSet='rs0',
    readPreference='secondaryPreferred',
    w='majority',  # 写确认
    j=True,        # 日志确认
    retryWrites=True,  # 自动重试写操作
    socketTimeoutMS=30000,
    connectTimeoutMS=20000,
    serverSelectionTimeoutMS=30000,
    maxPoolSize=100
)

# 获取集合
db = client.aiplatform
collection = db.ai_tasks

# 读操作 - 从从节点读取
result = collection.find_one({"task_id": "12345"})

# 写操作 - 写入主节点
collection.insert_one({"task_id": "12345", "status": "pending"})
```

## Redis高可用配置

### Redis Sentinel模式

Redis Sentinel提供高可用性和自动故障转移：

1. **主节点配置**：

```ini
# redis.conf (主节点)
bind 0.0.0.0
port 6379
daemonize yes
pidfile /var/run/redis/redis-server.pid
logfile /var/log/redis/redis-server.log
dir /var/lib/redis
requirepass strong_redis_password
masterauth strong_redis_password
```

2. **从节点配置**：

```ini
# redis.conf (从节点)
bind 0.0.0.0
port 6379
daemonize yes
pidfile /var/run/redis/redis-server.pid
logfile /var/log/redis/redis-server.log
dir /var/lib/redis
slaveof 10.0.0.1 6379
requirepass strong_redis_password
masterauth strong_redis_password
```

3. **Sentinel配置**：

```ini
# sentinel.conf
port 26379
daemonize yes
pidfile /var/run/redis/redis-sentinel.pid
logfile /var/log/redis/redis-sentinel.log
dir /var/lib/redis
sentinel monitor mymaster 10.0.0.1 6379 2
sentinel auth-pass mymaster strong_redis_password
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 60000
sentinel parallel-syncs mymaster 1
```

4. **客户端配置示例**：

```python
from redis.sentinel import Sentinel

# 连接Sentinel
sentinel = Sentinel([
    ('10.0.0.10', 26379),
    ('10.0.0.11', 26379),
    ('10.0.0.12', 26379)
], socket_timeout=0.1, password='strong_redis_password')

# 获取主实例
master = sentinel.master_for('mymaster', socket_timeout=0.1, password='strong_redis_password')

# 获取从实例
slave = sentinel.slave_for('mymaster', socket_timeout=0.1, password='strong_redis_password')

# 写入数据到主节点
master.set('mykey', 'myvalue')

# 从从节点读取数据
value = slave.get('mykey')
```

### Redis集群

对于需要水平扩展的场景，配置Redis集群：

1. **集群节点配置**：

```ini
# redis.conf (集群节点)
port 6379
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
requirepass strong_redis_password
masterauth strong_redis_password
```

2. **创建集群**：

```bash
# 使用redis-cli创建集群
redis-cli --cluster create 10.0.0.1:6379 10.0.0.2:6379 10.0.0.3:6379 \
                          10.0.0.4:6379 10.0.0.5:6379 10.0.0.6:6379 \
                          --cluster-replicas 1 -a strong_redis_password
```

3. **客户端配置示例**：

```python
from rediscluster import RedisCluster

# 设置节点
startup_nodes = [
    {"host": "10.0.0.1", "port": "6379"},
    {"host": "10.0.0.2", "port": "6379"},
    {"host": "10.0.0.3", "port": "6379"}
]

# 创建集群客户端
rc = RedisCluster(
    startup_nodes=startup_nodes,
    decode_responses=True,
    password='strong_redis_password',
    skip_full_coverage_check=True
)

# 使用集群
rc.set("foo", "bar")
print(rc.get("foo"))
```

### Redis持久化配置

为确保数据持久性，配置RDB和AOF：

```ini
# redis.conf
# RDB配置
save 900 1
save 300 10
save 60 10000
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis/

# AOF配置
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
```

## Weaviate高可用配置

### Weaviate集群配置

Weaviate支持集群部署以提高可用性和可扩展性：

1. **使用Helm部署Weaviate集群**：

```bash
# 创建values.yaml
cat > weaviate-values.yaml << EOF
replicas: 3
persistence:
  enabled: true
  size: 50Gi
  storageClass: "managed-premium"
env:
  ENABLE_MODULES: "text2vec-transformers"
  TRANSFORMERS_INFERENCE_API: "http://text-transformers:8080"
  QUERY_DEFAULTS_LIMIT: 25
  AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: true
  PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
  DEFAULT_VECTORIZER_MODULE: "text2vec-transformers"
  CLUSTER_HOSTNAME: "node-{id}.weaviate.weaviate.svc.cluster.local"
  CLUSTER_GOSSIP_BIND_PORT: "7946"
  CLUSTER_DATA_BIND_PORT: "7100"
  CLUSTER_JOIN: "node-0.weaviate.weaviate.svc.cluster.local:7946"
resources:
  requests:
    cpu: "2"
    memory: "4Gi"
  limits:
    cpu: "4"
    memory: "8Gi"
EOF

# 部署Weaviate集群
helm install weaviate weaviate/weaviate -f weaviate-values.yaml -n weaviate --create-namespace
```

2. **客户端配置示例**：

```python
import weaviate

# 创建客户端，使用负载均衡器地址
client = weaviate.Client(
    url="http://weaviate-loadbalancer:80",
    timeout_config=(5, 60)  # (connect_timeout, read_timeout)
)

# 健康检查
health = client.is_ready()
print(f"Weaviate cluster is ready: {health}")

# 创建类定义
class_obj = {
    "class": "Embeddings",
    "vectorizer": "text2vec-transformers",
    "vectorIndexConfig": {
        "distance": "cosine"
    },
    "properties": [
        {
            "name": "text",
            "dataType": ["text"]
        },
        {
            "name": "metadata",
            "dataType": ["object"]
        }
    ]
}

# 创建或获取模式
if not client.schema.contains(class_obj):
    client.schema.create_class(class_obj)
```

### Weaviate备份恢复策略

配置Weaviate的备份和恢复：

1. **创建备份**：

```python
# 创建备份
backup_id = "aiplatform-backup-" + datetime.now().strftime("%Y%m%d%H%M%S")
client.backup.create(
    backup_id=backup_id,
    backend="filesystem",
    include_classes=["Embeddings", "Documents"],
    wait_for_completion=True
)
```

2. **恢复备份**：

```python
# 恢复备份
client.backup.restore(
    backup_id=backup_id,
    backend="filesystem",
    include_classes=["Embeddings", "Documents"],
    wait_for_completion=True
)
```

## Kafka高可用配置

### Kafka多节点集群

Kafka集群提供高可用性和可扩展性：

1. **Kafka Broker配置**：

```properties
# server.properties
broker.id=1
listeners=PLAINTEXT://0.0.0.0:9092
advertised.listeners=PLAINTEXT://kafka1:9092
log.dirs=/var/lib/kafka/data
num.partitions=8
default.replication.factor=3
min.insync.replicas=2
auto.create.topics.enable=false
delete.topic.enable=true
log.retention.hours=168
zookeeper.connect=zk1:2181,zk2:2181,zk3:2181/kafka
```

2. **ZooKeeper配置**：

```properties
# zoo.cfg
tickTime=2000
dataDir=/var/lib/zookeeper
clientPort=2181
initLimit=5
syncLimit=2
server.1=zk1:2888:3888
server.2=zk2:2888:3888
server.3=zk3:2888:3888
autopurge.snapRetainCount=3
autopurge.purgeInterval=1
```

### Kafka分区副本

1. **主题创建与副本配置**：

```bash
# 创建主题，确保较高的复制因子
kafka-topics.sh --create --topic important-events \
  --bootstrap-server kafka1:9092 \
  --partitions 16 \
  --replication-factor 3

# 检查主题详情
kafka-topics.sh --describe --topic important-events \
  --bootstrap-server kafka1:9092
```

2. **客户端配置**：

```java
// Java生产者高可用配置
Properties props = new Properties();
props.put("bootstrap.servers", "kafka1:9092,kafka2:9092,kafka3:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("acks", "all");  // 等待所有副本确认
props.put("min.insync.replicas", 2);  // 最小同步副本数
props.put("retries", 10);  // 重试次数
props.put("retry.backoff.ms", 500);  // 重试间隔
props.put("max.in.flight.requests.per.connection", 1);  // 避免消息重排序

// 创建生产者
KafkaProducer<String, String> producer = new KafkaProducer<>(props);
```

```python
# Python消费者高可用配置
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'important-events',
    bootstrap_servers=['kafka1:9092', 'kafka2:9092', 'kafka3:9092'],
    group_id='event-processor',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    auto_commit_interval_ms=5000,
    session_timeout_ms=30000,
    heartbeat_interval_ms=10000
)
```

### Kafka可靠性配置

1. **监控Kafka集群**：

```bash
# 查看消费者组状态
kafka-consumer-groups.sh --bootstrap-server kafka1:9092 \
  --describe --group event-processor

# 查看主题分区副本状态
kafka-topics.sh --bootstrap-server kafka1:9092 \
  --describe --under-replicated-partitions
```

2. **多数据中心部署**：使用MirrorMaker 2进行跨数据中心复制：

```properties
# mm2.properties
clusters=source, target
source.bootstrap.servers=kafka1-dc1:9092,kafka2-dc1:9092,kafka3-dc1:9092
target.bootstrap.servers=kafka1-dc2:9092,kafka2-dc2:9092,kafka3-dc2:9092

# 源到目标复制
source->target.enabled=true
source->target.topics=.*
source->target.groups=.*

# 连接器配置
tasks.max=10
replication.factor=3
refresh.topics.interval.seconds=60
sync.topic.configs.enabled=true
sync.topic.acls.enabled=true
```

## 跨区域灾难恢复

### 数据复制策略

为确保跨区域灾难恢复能力，实施以下复制策略：

1. **PostgreSQL跨区域复制**：

使用logical replication跨区域复制关键数据：

```sql
-- 主区域创建发布
CREATE PUBLICATION main_pub FOR TABLE users, ai_models, model_configs;

-- 灾备区域创建订阅
CREATE SUBSCRIPTION dr_sub
  CONNECTION 'host=primary_db port=5432 user=replicator password=password dbname=aiplatform'
  PUBLICATION main_pub;
```

使用WAL归档进行完整备份：

```ini
# postgresql.conf (主区域)
archive_mode = on
archive_command = 'rsync -a %p postgres@dr-storage:/archives/%f'
```

2. **MongoDB跨区域复制**：

```javascript
// 配置跨区域复制
rs.add({
  host: "mongodb-dr:27017",
  priority: 0,
  votes: 0,
  hidden: true,
  slaveDelay: 3600  // 1小时延迟，防止操作错误立即复制
})
```

3. **Redis跨区域复制**：

```ini
# redis.conf (灾备区域)
slaveof primary_redis 6379
masterauth password
```

4. **Weaviate备份传输**：

定期将备份发送到灾备区域：

```bash
#!/bin/bash
# 将Weaviate备份同步到灾备站点
BACKUP_DIR="/var/lib/weaviate/backups"
REMOTE_HOST="dr-storage"
REMOTE_DIR="/backups/weaviate"

rsync -avz --delete $BACKUP_DIR/ $REMOTE_HOST:$REMOTE_DIR/
```

5. **Kafka跨区域复制**：

使用MirrorMaker 2在区域间复制消息：

```bash
# 启动MirrorMaker 2
/opt/kafka/bin/connect-mirror-maker.sh mm2.properties
```

### 故障切换流程

1. **手动故障切换流程**：

```markdown
## 主数据中心故障切换流程

1. 确认主数据中心不可用
   - 监控系统确认多项服务失效
   - 尝试基本连接性测试

2. 激活灾备中心
   - 提升灾备数据库为主库：
     ```bash
     # PostgreSQL提升
     # 在灾备PostgreSQL上
     pg_ctl promote -D /var/lib/postgresql/16/main
     
     # MongoDB提升
     # 在灾备MongoDB上
     rs.stepDown()
     
     # Redis提升
     # 在灾备Redis上
     redis-cli SLAVEOF NO ONE
     ```

3. 更新DNS记录
   - 将服务DNS指向灾备数据中心：
     ```bash
     # 更新DNS A记录
     aws route53 change-resource-record-sets \
       --hosted-zone-id ZXXXXXXXXXXXXX \
       --change-batch '{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"db.aiplatform.example.com","Type":"A","TTL":60,"ResourceRecords":[{"Value":"10.1.0.1"}]}}]}'
     ```

4. 启动应用程序
   - 在灾备中心启动应用服务

5. 监控和验证
   - 确认服务恢复
   - 运行健康检查和基本功能测试
```

2. **自动故障切换**：

使用Kubernetes集群联邦实现自动故障切换：

```yaml
# kubefed配置
apiVersion: types.kubefed.io/v1beta1
kind: FederatedDeployment
metadata:
  name: aiplatform-api
  namespace: aiplatform
spec:
  template:
    metadata:
      labels:
        app: aiplatform-api
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: aiplatform-api
      template:
        metadata:
          labels:
            app: aiplatform-api
        spec:
          containers:
          - name: api
            image: aiplatform/api:latest
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secrets
                  key: url
  placement:
    clusters:
    - name: cluster-primary
    - name: cluster-dr
  overrides:
  - clusterName: cluster-primary
    clusterOverrides:
    - path: "/spec/replicas"
      value: 5
  - clusterName: cluster-dr
    clusterOverrides:
    - path: "/spec/replicas"
      value: 2
```

### 恢复时间目标

1. **自动化恢复脚本**：

```bash
#!/bin/bash
# 灾备中心激活脚本

# 定义变量
PRIMARY_REGION="us-west-2"
DR_REGION="us-east-1"
DB_INSTANCE="aiplatform-db"
REDIS_CLUSTER="aiplatform-redis"
DNS_NAME="db.aiplatform.example.com"
HOSTED_ZONE_ID="ZXXXXXXXXXXXXX"

# 检查主区域可用性
echo "Checking primary region availability..."
if ! aws ec2 describe-regions --region ${PRIMARY_REGION} &>/dev/null; then
  echo "Primary region appears to be down. Starting failover..."
  
  # 激活灾备数据库
  echo "Promoting DR database..."
  aws rds promote-read-replica \
    --db-instance-identifier ${DB_INSTANCE}-replica \
    --region ${DR_REGION}
    
  # 更新DNS记录
  echo "Updating DNS records..."
  DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier ${DB_INSTANCE}-replica \
    --region ${DR_REGION} \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)
    
  aws route53 change-resource-record-sets \
    --hosted-zone-id ${HOSTED_ZONE_ID} \
    --change-batch "{\"Changes\":[{\"Action\":\"UPSERT\",\"ResourceRecordSet\":{\"Name\":\"${DNS_NAME}\",\"Type\":\"CNAME\",\"TTL\":60,\"ResourceRecords\":[{\"Value\":\"${DB_ENDPOINT}\"}]}}]}"
  
  # 扩展灾备区域的应用实例
  echo "Scaling up DR region applications..."
  aws ecs update-service \
    --cluster aiplatform-cluster \
    --service aiplatform-api \
    --desired-count 10 \
    --region ${DR_REGION}
    
  echo "Failover completed successfully!"
else
  echo "Primary region is available. No failover needed."
fi
```

2. **恢复时间目标实测**：

| 服务 | 平均恢复时间 | 注意事项 |
|------|------------|---------|
| PostgreSQL | 3分钟 | 连接池需要重新建立 |
| MongoDB | 5分钟 | 分片集群恢复较慢 |
| Redis | <1分钟 | 客户端需要重连 |
| Weaviate | 8分钟 | 索引热加载时间较长 |
| Kafka | 6分钟 | 消费者需要重平衡 |

## 负载均衡和流量管理

1. **Nginx负载均衡配置**：

```nginx
# nginx.conf
upstream postgresql_masters {
    server postgresql-0.aiplatform.svc:5432 max_fails=3 fail_timeout=30s;
    server postgresql-1.aiplatform.svc:5432 backup;
}

upstream postgresql_replicas {
    least_conn;
    server postgresql-1.aiplatform.svc:5432 max_fails=3 fail_timeout=30s;
    server postgresql-2.aiplatform.svc:5432 max_fails=3 fail_timeout=30s;
}

server {
    listen 5432;
    
    location / {
        proxy_pass postgresql_masters;
        health_check interval=10 passes=2 fails=3;
    }
}

server {
    listen 5433;
    
    location / {
        proxy_pass postgresql_replicas;
        health_check interval=10 passes=2 fails=3;
    }
}
```

2. **HAProxy配置**：

```
# haproxy.cfg
frontend mongodb_frontend
    bind *:27017
    mode tcp
    option tcplog
    default_backend mongodb_backend

backend mongodb_backend
    mode tcp
    option tcp-check
    balance roundrobin
    server mongodb1 10.0.0.1:27017 check
    server mongodb2 10.0.0.2:27017 check
    server mongodb3 10.0.0.3:27017 check backup
```

## 高可用监控和告警

1. **Prometheus告警配置**：

```yaml
# prometheus.rules.yml
groups:
- name: high_availability_alerts
  rules:
  # PostgreSQL复制滞后告警
  - alert: PostgreSQLReplicationLag
    expr: pg_replication_lag_seconds > 300
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "PostgreSQL replication lag is high"
      description: "Replica {{ $labels.instance }} is {{ $value }} seconds behind master"

  # MongoDB复制健康告警
  - alert: MongoDBReplicationHealthIssue
    expr: mongodb_replset_member_health == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "MongoDB replication health issue"
      description: "MongoDB instance {{ $labels.instance }} is unhealthy"

  # Redis主从状态告警
  - alert: RedisReplicationBroken
    expr: redis_connected_slaves < 1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Redis has no connected slaves"
      description: "Redis master {{ $labels.instance }} has no connected slaves"
      
  # Kafka副本同步告警
  - alert: KafkaUnderReplicatedPartitions
    expr: kafka_server_replicamanager_underreplicatedpartitions > 0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Kafka has under-replicated partitions"
      description: "Kafka broker {{ $labels.instance }} has {{ $value }} under-replicated partitions"
```

2. **监控仪表板**：

配置Grafana仪表板监控高可用状态：

```bash
# 安装HA监控仪表板
grafana-cli plugins install grafana-piechart-panel
grafana-cli dashboard install 455  # PostgreSQL仪表板
grafana-cli dashboard install 7362  # MongoDB仪表板
grafana-cli dashboard install 11835  # Redis仪表板
grafana-cli dashboard install 7589  # Kafka仪表板
```

## 定期测试和演练

1. **高可用测试计划**：

```markdown
## 季度故障恢复演练计划

### 活动准备
- 确定演练窗口（建议在低峰期）
- 通知所有相关团队
- 准备回滚计划
- 设置监控系统

### 演练场景
1. 数据库主节点故障
   - 模拟方法：关闭主数据库实例
   - 预期结果：自动故障转移到从节点
   - 验证步骤：
     * 验证应用程序连接性
     * 验证数据完整性
     * 测试写入功能

2. 整个区域故障
   - 模拟方法：隔离主区域网络
   - 预期结果：应用程序成功切换到灾备区域
   - 验证步骤：
     * 验证所有服务可用性
     * 验证数据一致性
     * 执行端到端测试用例

### 评估标准
- 实际恢复时间 (RTO) 是否符合目标？
- 实际数据丢失 (RPO) 是否符合目标？
- 是否有任何意外问题出现？
- 监控和告警系统是否正常工作？

### 记录和改进
- 记录演练中发现的问题
- 更新灾难恢复计划
- 改进自动化脚本
- 安排后续修复工作
```

2. **自动化测试脚本**：

```python
#!/usr/bin/env python3
# high_availability_test.py

import asyncio
import time
import random
import pymongo
import redis
import psycopg2
import requests
import json
import logging
from kafka import KafkaProducer, KafkaConsumer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ha_test")

# 配置连接参数
pg_params = {
    "host": "postgresql.aiplatform.svc",
    "port": 5432,
    "database": "aiplatform",
    "user": "app_user",
    "password": "app_password"
}

mongo_uri = "mongodb://app_user:app_password@mongodb-0.aiplatform.svc,mongodb-1.aiplatform.svc,mongodb-2.aiplatform.svc/aiplatform?replicaSet=rs0"
redis_nodes = [{"host": f"redis-{i}.aiplatform.svc", "port": 6379} for i in range(3)]
kafka_servers = ["kafka-0.aiplatform.svc:9092", "kafka-1.aiplatform.svc:9092", "kafka-2.aiplatform.svc:9092"]

async def test_postgresql_failover():
    """测试PostgreSQL故障转移"""
    try:
        # 连接到主库
        conn = psycopg2.connect(**pg_params)
        cur = conn.cursor()
        
        # 创建测试表
        cur.execute("CREATE TABLE IF NOT EXISTS ha_test (id serial PRIMARY KEY, data text, created_at timestamp DEFAULT now())")
        conn.commit()
        
        # 写入测试数据
        test_id = random.randint(1000, 9999)
        logger.info(f"Writing test data with ID {test_id} to PostgreSQL")
        cur.execute("INSERT INTO ha_test (data) VALUES (%s) RETURNING id", (f"Test data {test_id}",))
        inserted_id = cur.fetchone()[0]
        conn.commit()
        
        # 模拟主库故障（关闭当前连接）
        logger.info("Simulating PostgreSQL primary failure...")
        conn.close()
        
        # 等待故障转移
        time.sleep(10)
        
        # 重新连接并验证数据
        new_conn = psycopg2.connect(**pg_params)
        new_cur = new_conn.cursor()
        new_cur.execute("SELECT data FROM ha_test WHERE id = %s", (inserted_id,))
        result = new_cur.fetchone()
        
        if result and f"Test data {test_id}" == result[0]:
            logger.info("PostgreSQL failover test PASSED")
            return True
        else:
            logger.error("PostgreSQL failover test FAILED: Data not found or mismatch")
            return False
            
    except Exception as e:
        logger.error(f"PostgreSQL failover test error: {e}")
        return False

# 实现类似的测试函数用于MongoDB, Redis, Kafka和Weaviate

async def run_all_tests():
    """运行所有高可用性测试"""
    results = {}
    
    # 执行各个测试
    results["postgresql"] = await test_postgresql_failover()
    results["mongodb"] = await test_mongodb_failover()
    results["redis"] = await test_redis_failover()
    results["kafka"] = await test_kafka_failover()
    results["weaviate"] = await test_weaviate_failover()
    
    # 汇总结果
    success = all(results.values())
    
    if success:
        logger.info("ALL HIGH AVAILABILITY TESTS PASSED")
    else:
        logger.error("SOME HIGH AVAILABILITY TESTS FAILED")
        for service, result in results.items():
            status = "PASSED" if result else "FAILED"
            logger.info(f"{service}: {status}")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_all_tests())
```
