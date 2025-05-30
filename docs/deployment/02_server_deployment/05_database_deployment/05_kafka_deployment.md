# Kafka 3.6 消息队列部署指南

本文档提供了Kafka 3.6消息队列的详细部署和配置指南，作为AI中台的消息处理和事件流组件。

## 目录
- [概述](#概述)
- [系统要求](#系统要求)
- [部署选项](#部署选项)
  - [Docker部署](#docker部署)
  - [Docker Compose部署](#docker-compose部署)
  - [Kubernetes部署](#kubernetes部署)
  - [直接安装](#直接安装)
- [基本配置](#基本配置)
- [主题管理](#主题管理)
- [生产者和消费者示例](#生产者和消费者示例)
- [集群配置](#集群配置)
- [安全配置](#安全配置)
- [性能优化](#性能优化)
- [监控与管理](#监控与管理)
- [常见问题排查](#常见问题排查)

## 概述

Apache Kafka是一个分布式流处理平台，用于构建实时数据管道和流式应用程序。在AI中台中，Kafka主要用于以下场景：

- 系统组件间的异步通信
- 事件驱动架构的基础设施
- AI任务队列管理
- 实时数据处理和分析流水线
- 日志聚合和转发

## 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| 磁盘 | 100GB SSD | 500GB+ SSD |
| 网络 | 千兆网络 | 万兆网络 |
| JVM | Java 11 | Java 17 |
| 操作系统 | Ubuntu 20.04 | Ubuntu 22.04 |

## 部署选项

### Docker部署

使用官方Docker镜像部署单节点Kafka服务：

```bash
# 先启动ZooKeeper（Kafka 3.6支持KRaft模式但此处使用传统ZooKeeper模式）
docker run -d --name zookeeper -p 2181:2181 -e ZOOKEEPER_CLIENT_PORT=2181 confluentinc/cp-zookeeper:7.4.0

# 启动Kafka
docker run -d --name kafka \
  -p 9092:9092 \
  -e KAFKA_BROKER_ID=1 \
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  --link zookeeper:zookeeper \
  confluentinc/cp-kafka:7.4.0
```

### Docker Compose部署

创建`docker-compose.yml`文件用于部署Kafka和ZooKeeper：

```yaml
version: '3'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
      - zookeeper-log:/var/lib/zookeeper/log

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
    volumes:
      - kafka-data:/var/lib/kafka/data
    depends_on:
      - zookeeper

  # Kafka管理界面（可选）
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: ai-platform
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181
    depends_on:
      - kafka

volumes:
  zookeeper-data:
  zookeeper-log:
  kafka-data:
```

使用以下命令启动：

```bash
docker-compose up -d
```

### Kubernetes部署

使用Helm部署Kafka到Kubernetes集群：

```bash
# 添加Bitnami仓库
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 创建自定义values.yaml文件
cat > kafka-values.yaml << EOF
replicaCount: 3
heapOpts: "-Xmx1024m -Xms1024m"
resources:
  requests:
    memory: 2Gi
    cpu: 500m
  limits:
    memory: 4Gi
    cpu: 2000m
persistence:
  enabled: true
  size: 100Gi
  storageClass: "managed-premium"
metrics:
  kafka:
    enabled: true
zookeeper:
  enabled: true
  replicaCount: 3
  persistence:
    enabled: true
    size: 20Gi
EOF

# 安装Kafka
helm install kafka bitnami/kafka -f kafka-values.yaml -n middleware
```

### 直接安装

在Ubuntu服务器上直接安装Kafka：

```bash
# 安装Java
sudo apt update
sudo apt install -y openjdk-17-jdk

# 下载Kafka
wget https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz
tar -xzf kafka_2.13-3.6.0.tgz
sudo mv kafka_2.13-3.6.0 /opt/kafka

# 创建数据目录
sudo mkdir -p /var/lib/kafka/data

# 配置Kafka
sudo cat > /opt/kafka/config/server.properties << EOF
broker.id=1
listeners=PLAINTEXT://0.0.0.0:9092
advertised.listeners=PLAINTEXT://YOUR_SERVER_IP:9092
log.dirs=/var/lib/kafka/data
num.partitions=8
default.replication.factor=1
log.retention.hours=168
zookeeper.connect=localhost:2181
EOF

# 创建systemd服务文件
sudo cat > /etc/systemd/system/zookeeper.service << EOF
[Unit]
Description=Apache Zookeeper server
Documentation=http://zookeeper.apache.org
Requires=network.target remote-fs.target
After=network.target remote-fs.target

[Service]
Type=simple
User=kafka
ExecStart=/opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties
ExecStop=/opt/kafka/bin/zookeeper-server-stop.sh
Restart=on-abnormal

[Install]
WantedBy=multi-user.target
EOF

sudo cat > /etc/systemd/system/kafka.service << EOF
[Unit]
Description=Apache Kafka Server
Documentation=http://kafka.apache.org/documentation.html
Requires=zookeeper.service
After=zookeeper.service

[Service]
Type=simple
User=kafka
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties
ExecStop=/opt/kafka/bin/kafka-server-stop.sh
Restart=on-abnormal

[Install]
WantedBy=multi-user.target
EOF

# 创建kafka用户
sudo useradd -r -d /opt/kafka kafka
sudo chown -R kafka:kafka /opt/kafka
sudo chown -R kafka:kafka /var/lib/kafka

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable zookeeper
sudo systemctl enable kafka
sudo systemctl start zookeeper
sudo systemctl start kafka
```

## 基本配置

Kafka的关键配置参数说明：

| 参数 | 描述 | 推荐值 |
|------|------|--------|
| broker.id | Broker唯一标识符 | 集群中唯一 |
| listeners | 监听地址和端口 | PLAINTEXT://0.0.0.0:9092 |
| advertised.listeners | 公布给客户端的地址 | PLAINTEXT://SERVER_IP:9092 |
| num.partitions | 主题默认分区数 | 8-16 |
| default.replication.factor | 默认复制因子 | 3 (生产) |
| log.retention.hours | 日志保留时间 | 168 (7天) |
| log.segment.bytes | 日志段大小 | 1073741824 (1GB) |
| zookeeper.connect | ZooKeeper连接字符串 | zk1:2181,zk2:2181,zk3:2181 |
| auto.create.topics.enable | 是否自动创建主题 | false (生产) |
| delete.topic.enable | 是否允许删除主题 | true |

## 主题管理

创建主题：

```bash
# 创建主题
kafka-topics.sh --create --topic ai-task-queue \
  --partitions 8 \
  --replication-factor 3 \
  --bootstrap-server kafka:9092

# 列出所有主题
kafka-topics.sh --list --bootstrap-server kafka:9092

# 描述主题
kafka-topics.sh --describe --topic ai-task-queue \
  --bootstrap-server kafka:9092

# 修改主题配置
kafka-configs.sh --alter --entity-type topics --entity-name ai-task-queue \
  --add-config retention.ms=604800000 \
  --bootstrap-server kafka:9092
```

AI中台推荐的主题设计：

| 主题名称 | 分区数 | 复制因子 | 用途 |
|---------|-------|----------|------|
| ai-task-queue | 16 | 3 | AI任务队列 |
| model-events | 8 | 3 | 模型相关事件 |
| user-activities | 16 | 3 | 用户活动日志 |
| system-metrics | 4 | 3 | 系统指标数据 |
| data-pipeline | 8 | 3 | 数据处理管道 |

## 生产者和消费者示例

Python生产者示例：

```python
from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all'
)

task = {
    'task_id': '12345',
    'model': 'gpt-4',
    'input': 'Generate a summary of the document',
    'timestamp': time.time()
}

future = producer.send('ai-task-queue', task)
try:
    record_metadata = future.get(timeout=10)
    print(f"Topic: {record_metadata.topic}")
    print(f"Partition: {record_metadata.partition}")
    print(f"Offset: {record_metadata.offset}")
except Exception as e:
    print(f"Failed to send message: {e}")
finally:
    producer.close()
```

Python消费者示例：

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'ai-task-queue',
    bootstrap_servers=['kafka:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='ai-task-processor',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for message in consumer:
    task = message.value
    print(f"Received task: {task['task_id']}")
    print(f"Model: {task['model']}")
    print(f"Input: {task['input']}")
    # 处理任务...
```

## 集群配置

多节点Kafka集群配置：

1. 每个节点的`server.properties`文件中设置唯一的`broker.id`
2. 所有节点使用相同的ZooKeeper连接字符串
3. 配置不同的监听地址

示例3节点配置（节点1）：

```properties
broker.id=1
listeners=PLAINTEXT://0.0.0.0:9092
advertised.listeners=PLAINTEXT://kafka1:9092
log.dirs=/var/lib/kafka/data
zookeeper.connect=zk1:2181,zk2:2181,zk3:2181
default.replication.factor=3
min.insync.replicas=2
```

## 安全配置

启用SASL/SCRAM认证：

1. 创建JAAS配置文件：

```
KafkaServer {
   org.apache.kafka.common.security.scram.ScramLoginModule required
   username="admin"
   password="admin-secret";
};
```

2. 更新`server.properties`：

```properties
listeners=SASL_PLAINTEXT://0.0.0.0:9092
advertised.listeners=SASL_PLAINTEXT://kafka:9092
security.inter.broker.protocol=SASL_PLAINTEXT
sasl.mechanism.inter.broker.protocol=SCRAM-SHA-256
sasl.enabled.mechanisms=SCRAM-SHA-256
```

3. 创建用户：

```bash
kafka-configs.sh --bootstrap-server kafka:9092 \
  --alter --add-config 'SCRAM-SHA-256=[password=client-secret],SCRAM-SHA-512=[password=client-secret]' \
  --entity-type users --entity-name client
```

## 性能优化

生产环境性能调优建议：

1. 服务器配置：
   - 使用SSD存储
   - 分离操作系统和Kafka数据目录
   - 分配足够的堆内存（-Xms和-Xmx设置为相同值）

2. Broker配置：
   ```properties
   # 增加网络线程数
   num.network.threads=8
   
   # 增加I/O线程数
   num.io.threads=16
   
   # 增加发送缓冲区大小
   socket.send.buffer.bytes=1048576
   
   # 增加接收缓冲区大小
   socket.receive.buffer.bytes=1048576
   
   # 最大消息大小（10MB）
   message.max.bytes=10485760
   
   # 文件刷盘策略（增加性能，降低可靠性）
   log.flush.interval.messages=10000
   log.flush.interval.ms=1000
   ```

3. 主题级别配置：
   ```
   # 对于高吞吐量场景增加分区数
   kafka-topics.sh --alter --topic high-throughput-topic \
     --partitions 32 --bootstrap-server kafka:9092
   ```

## 监控与管理

1. JMX指标收集

在启动Kafka时启用JMX：

```bash
export JMX_PORT=9999
bin/kafka-server-start.sh config/server.properties
```

2. 与Prometheus集成

使用Prometheus JMX Exporter收集Kafka指标。配置文件示例：

```yaml
lowercaseOutputName: true
rules:
  - pattern: "kafka.server<type=(.+), name=(.+)><>Value"
    name: kafka_server_$1_$2
  - pattern: "kafka.server<type=(.+), name=(.+), topic=(.+)><>Value"
    name: kafka_server_$1_$2
    labels:
      topic: "$3"
```

3. Grafana仪表板

推荐使用Grafana仪表板ID：7589或11963监控Kafka集群。

4. 监控关键指标

- BytesInPerSec/BytesOutPerSec: 流量
- RequestsPerSec: 请求率
- UnderReplicatedPartitions: 复制状态
- ActiveControllerCount: 控制器状态
- OfflinePartitionsCount: 分区健康状态
- LogFlushRateAndTimeMs: 刷盘性能

## 常见问题排查

1. 连接问题

   检查防火墙设置和`advertised.listeners`配置是否正确。

2. 消费者组重平衡频繁

   增加会话超时和心跳间隔配置：
   ```
   session.timeout.ms=30000
   heartbeat.interval.ms=10000
   ```

3. 磁盘空间不足

   调整日志保留策略：
   ```
   log.retention.hours=48
   log.retention.bytes=1073741824
   ```

4. 性能下降

   检查JVM GC日志，考虑增加堆大小或调整GC参数：
   ```
   export KAFKA_HEAP_OPTS="-Xms4g -Xmx4g -XX:MetaspaceSize=96m -XX:+UseG1GC"
   ```

5. 高延迟

   检查网络配置和磁盘I/O，考虑增加网络线程数和I/O线程数。
