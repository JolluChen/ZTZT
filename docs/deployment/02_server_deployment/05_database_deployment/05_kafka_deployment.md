# Kafka 3.6 消息队列部署指南

本文档提供了Kafka 3.6消息队列的详细部署和配置指南，作为AI中台的消息处理和事件流组件。

## 目录
- [概述](#概述)
- [快速开始](#快速开始)
- [系统要求](#系统要求)
- [部署选项](#部署选项)
  - [Docker部署](#docker部署)
  - [Docker Compose部署](#docker-compose部署)
  - [Kubernetes部署](#kubernetes部署)
  - [直接安装](#直接安装)
  - [离线部署方式](#离线部署方式)
  - [离线部署替代方案](#离线部署替代方案)
- [部署验证](#部署验证)
- [常见部署问题](#常见部署问题)
- [基本配置](#基本配置)
- [主题管理](#主题管理)
- [生产者和消费者示例](#生产者和消费者示例)
- [集群配置](#集群配置)
- [安全配置](#安全配置)
- [性能优化](#性能优化)
- [监控与管理](#监控与管理)
- [常见问题排查](#常见问题排查)
- [与AI中台项目集成](#与ai中台项目集成)
- [生产环境部署注意事项](#生产环境部署注意事项)
- [数据备份和恢复](#数据备份和恢复)
- [总结](#总结)

## 概述

Apache Kafka是一个分布式流处理平台，用于构建实时数据管道和流式应用程序。在AI中台中，Kafka主要用于以下场景：

- 系统组件间的异步通信
- 事件驱动架构的基础设施
- AI任务队列管理
- 实时数据处理和分析流水线
- 日志聚合和转发

## 快速开始

基于项目已有的Docker镜像文件（zookeeper-7.4.0.tar, kafka-7.4.0.tar, kafka-ui-latest.tar），以下是快速部署步骤：

### 加载镜像

```bash
# 加载Docker镜像
docker load -i zookeeper-7.4.0.tar
docker load -i kafka-7.4.0.tar
docker load -i kafka-ui-latest.tar

# 验证镜像已加载
docker images | grep -E "zookeeper|kafka"
```

### 创建docker-compose-kafka.yml

项目中已提供了完整的配置文件模板：`docker-compose-kafka.yml`，包含生产级别的配置优化。

基本配置示例：

```yaml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    container_name: ai_platform_zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
    networks:
      - kafka-network

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    container_name: ai_platform_kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'false'
      KAFKA_DELETE_TOPIC_ENABLE: 'true'
    volumes:
      - kafka-data:/var/lib/kafka/data
    depends_on:
      - zookeeper
    networks:
      - kafka-network

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: ai_platform_kafka_ui
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: ai-platform
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      - kafka
    networks:
      - kafka-network

volumes:
  zookeeper-data:
  kafka-data:

networks:
  kafka-network:
    driver: bridge
```

> **注意**: 使用项目目录中的 `docker-compose-kafka.yml` 文件可获得更完整的生产级配置，包括健康检查、性能优化和监控设置。

### 启动服务

```bash
# 启动Kafka服务
docker compose -f docker-compose-kafka.yml up -d

# 查看服务状态
docker compose -f docker-compose-kafka.yml ps

# 验证服务正常运行
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

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

根据项目结构，创建`docker-compose-kafka.yml`文件用于部署Kafka和ZooKeeper（与现有的mongodb和weaviate配置文件保持一致的命名规范）：

```yaml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
      - zookeeper-log:/var/lib/zookeeper/log
    networks:
      - kafka-network

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    container_name: kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'false'
      KAFKA_DELETE_TOPIC_ENABLE: 'true'
      KAFKA_NUM_PARTITIONS: 8
    volumes:
      - kafka-data:/var/lib/kafka/data
    depends_on:
      - zookeeper
    networks:
      - kafka-network

  # Kafka管理界面
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: ai-platform
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181
    depends_on:
      - kafka
    networks:
      - kafka-network

volumes:
  zookeeper-data:
    driver: local
  zookeeper-log:
    driver: local
  kafka-data:
    driver: local

networks:
  kafka-network:
    driver: bridge
```

使用以下命令启动：

```bash
# 启动Kafka服务
docker compose -f docker-compose-kafka.yml up -d

# 查看服务状态
docker compose -f docker-compose-kafka.yml ps

# 查看日志
docker compose -f docker-compose-kafka.yml logs -f kafka

# 停止服务
docker compose -f docker-compose-kafka.yml down

# 完全清理（包括数据卷）
docker compose -f docker-compose-kafka.yml down -v
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

### 离线部署方式

当服务器无法直接访问互联网时，可以使用离线部署方式：

#### Windows下载镜像

```powershell
# 在Windows环境下载Docker镜像
docker pull confluentinc/cp-zookeeper:7.4.0
docker pull confluentinc/cp-kafka:7.4.0
docker pull provectuslabs/kafka-ui:latest

# 保存镜像为tar文件
docker save confluentinc/cp-zookeeper:7.4.0 -o zookeeper-7.4.0.tar
docker save confluentinc/cp-kafka:7.4.0 -o kafka-7.4.0.tar
docker save provectuslabs/kafka-ui:latest -o kafka-ui-latest.tar

# 验证文件已创建
dir *.tar
```

#### 镜像下载问题解决

如果遇到网络连接问题，可以配置Docker镜像加速器：

```powershell
# 创建Docker配置文件
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.docker"

@"
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://hub-mirror.c.163.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
"@ | Out-File -FilePath "$env:USERPROFILE\.docker\daemon.json" -Encoding utf8
```

#### 上传到服务器

```powershell
# 使用SCP上传镜像文件
scp *.tar username@server_ip:/tmp/
```

#### 服务器端加载镜像

```bash
# 进入上传目录
cd /tmp

# 加载Docker镜像
docker load -i zookeeper-7.4.0.tar
docker load -i kafka-7.4.0.tar
docker load -i kafka-ui-latest.tar

# 验证镜像已加载
docker images | grep -E "zookeeper|kafka"

# 清理tar文件（可选）
rm -f *.tar
```

### 离线部署替代方案

如果`provectuslabs/kafka-ui`镜像下载失败，可以使用替代的管理界面：

#### 使用Kafdrop替代Kafka UI

```yaml
# 在docker-compose-kafka.yml中替换kafka-ui服务
  kafdrop:
    image: obsidiandynamics/kafdrop:latest
    container_name: kafdrop
    ports:
      - "9000:9000"
    environment:
      KAFKA_BROKERCONNECT: kafka:9092
      JVM_OPTS: "-Xms32M -Xmx64M"
      SERVER_SERVLET_CONTEXTPATH: "/"
    depends_on:
      - kafka
    networks:
      - kafka-network
```

```powershell
# Windows下载替代镜像
docker pull obsidiandynamics/kafdrop:latest
docker save obsidiandynamics/kafdrop:latest -o kafdrop-latest.tar
```

#### 最小化配置（仅Kafka和ZooKeeper）

如果管理界面不是必需的，可以使用最小化配置：

```yaml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    container_name: kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    volumes:
      - kafka-data:/var/lib/kafka/data
    depends_on:
      - zookeeper

volumes:
  zookeeper-data:
  kafka-data:
```

## 部署验证

### 验证服务启动

```bash
# 检查容器状态
docker compose -f docker-compose-kafka.yml ps

# 验证端口监听
netstat -tlnp | grep -E ":(2181|9092|8080)"

# 查看服务日志
docker compose -f docker-compose-kafka.yml logs kafka
docker compose -f docker-compose-kafka.yml logs zookeeper
```

### 测试Kafka功能

```bash
# 创建测试主题
docker exec -it kafka kafka-topics --create --topic test-topic \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1

# 列出所有主题
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# 发送测试消息
echo "Hello Kafka" | docker exec -i kafka kafka-console-producer \
  --topic test-topic --bootstrap-server localhost:9092

# 消费测试消息
docker exec -it kafka kafka-console-consumer \
  --topic test-topic --from-beginning \
  --bootstrap-server localhost:9092 --timeout-ms 10000
```

### 访问管理界面

```bash
# 访问Kafka UI（如果配置了）
# 浏览器访问: http://server_ip:8080
```

## 常见部署问题

### 1. 容器名称冲突

**问题描述：** 
```
Error response from daemon: Conflict. The container name "/zookeeper" is already in use
```

**解决方案：**
```bash
# 删除现有容器
docker rm -f zookeeper kafka kafka-ui

# 或者停止并删除所有相关容器
docker compose -f docker-compose-kafka.yml down
```

### 2. 端口占用

**问题描述：** 端口2181、9092或8080被占用

**解决方案：**
```bash
# 检查端口占用
sudo netstat -tlnp | grep -E ":(2181|9092|8080)"

# 停止占用端口的服务
sudo systemctl stop kafka
sudo systemctl stop zookeeper

# 或者修改docker-compose-kafka.yml中的端口映射
```

### 3. 网络连接问题

**问题描述：** 客户端无法连接到Kafka

**解决方案：**
```bash
# 检查防火墙设置（Ubuntu）
sudo ufw status
sudo ufw allow 2181
sudo ufw allow 9092
sudo ufw allow 8080

# 检查Docker网络
docker network ls
docker network inspect docker-compose-kafka_kafka-network
```

### 4. 镜像下载失败

**问题描述：** 
```
Error response from daemon: Head "https://registry-1.docker.io/v2/provectuslabs/kafka-ui/manifests/latest": net/http: TLS handshake timeout
```

**解决方案：**
```bash
# 使用国内镜像源
docker pull registry.cn-hangzhou.aliyuncs.com/library/kafka-ui:latest

# 或使用替代的管理界面
docker pull obsidiandynamics/kafdrop:latest
```

### 5. 权限问题

**问题描述：** 容器启动失败，权限被拒绝

**解决方案：**
```bash
# 检查Docker权限
sudo usermod -aG docker $USER
newgrp docker

# 检查数据卷权限
docker volume ls
docker volume inspect docker-compose-kafka_kafka-data
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

### 1. 连接问题

**问题描述：** 客户端无法连接到Kafka或连接频繁断开

**解决方案：**
```bash
# 检查防火墙设置
sudo ufw status
sudo ufw allow 2181
sudo ufw allow 9092

# 验证advertised.listeners配置
docker exec -it kafka cat /etc/kafka/server.properties | grep advertised.listeners

# 测试网络连通性
telnet server_ip 9092
```

### 2. 消费者组重平衡频繁

**问题描述：** 消费者组频繁发生重平衡，影响消费性能

**解决方案：**
```properties
# 在消费者配置中增加超时时间
session.timeout.ms=30000
heartbeat.interval.ms=10000
max.poll.interval.ms=300000
```

### 3. 磁盘空间不足

**问题描述：** Kafka日志占用过多磁盘空间

**解决方案：**
```bash
# 调整日志保留策略
docker exec -it kafka kafka-configs --bootstrap-server localhost:9092 \
  --alter --entity-type topics --entity-name your-topic \
  --add-config retention.ms=172800000  # 2天

# 或修改全局配置
log.retention.hours=48
log.retention.bytes=1073741824
log.segment.bytes=536870912
```

### 4. 性能下降

**问题描述：** Kafka处理性能明显下降

**解决方案：**
```bash
# 检查JVM堆内存使用
docker exec -it kafka jstat -gc $(docker exec kafka pgrep java)

# 调整JVM参数（在docker-compose中设置）
environment:
  KAFKA_HEAP_OPTS: "-Xms4g -Xmx4g -XX:MetaspaceSize=96m -XX:+UseG1GC"
  KAFKA_JVM_PERFORMANCE_OPTS: "-XX:+UnlockExperimentalVMOptions -XX:+UseContainerSupport"
```

### 5. 高延迟问题

**问题描述：** 消息处理延迟过高

**解决方案：**
```properties
# 优化Broker配置
num.network.threads=8
num.io.threads=16
socket.send.buffer.bytes=1048576
socket.receive.buffer.bytes=1048576

# 优化Producer配置
linger.ms=5
batch.size=32768
buffer.memory=67108864
```

### 6. ZooKeeper连接问题

**问题描述：** Kafka无法连接到ZooKeeper

**解决方案：**
```bash
# 检查ZooKeeper状态
docker exec -it zookeeper zkServer.sh status

# 验证ZooKeeper连接
echo "ruok" | nc localhost 2181

# 重启ZooKeeper服务
docker compose -f docker-compose-kafka.yml restart zookeeper
```

## 与AI中台项目集成

### 集成到现有Docker Compose

如果需要将Kafka集成到现有的AI中台项目中，可以将Kafka服务添加到主`docker-compose.yml`文件：

```yaml
# 在现有的docker-compose.yml中添加Kafka服务
version: '3.8'

services:
  # ...existing services (postgres, redis, backend)...

  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    container_name: ai_platform_zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
    networks:
      - ai_platform_network

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    container_name: ai_platform_kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'false'
    volumes:
      - kafka_data:/var/lib/kafka/data
    depends_on:
      - zookeeper
    networks:
      - ai_platform_network

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: ai_platform_kafka_ui
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: ai-platform
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      - kafka
    networks:
      - ai_platform_network

volumes:
  # ...existing volumes...
  zookeeper_data:
  kafka_data:

networks:
  ai_platform_network:
    driver: bridge
```

### Django集成示例

在Django后端中集成Kafka：

```python
# requirements.txt中添加
kafka-python==2.0.2

# settings.py中添加Kafka配置
KAFKA_SETTINGS = {
    'BOOTSTRAP_SERVERS': ['kafka:9092'],
    'TOPICS': {
        'AI_TASKS': 'ai-task-queue',
        'MODEL_EVENTS': 'model-events',
        'USER_ACTIVITIES': 'user-activities',
    }
}

# utils/kafka_client.py
from kafka import KafkaProducer, KafkaConsumer
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

class KafkaManager:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_SETTINGS['BOOTSTRAP_SERVERS'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all'
        )
    
    def send_task(self, task_data):
        topic = settings.KAFKA_SETTINGS['TOPICS']['AI_TASKS']
        try:
            future = self.producer.send(topic, task_data)
            record_metadata = future.get(timeout=10)
            logger.info(f"Task sent to {topic}: {record_metadata.offset}")
            return True
        except Exception as e:
            logger.error(f"Failed to send task: {e}")
            return False
```

## 生产环境部署注意事项

### 硬件要求

**推荐配置（生产环境）：**
- **CPU**: 16核心以上
- **内存**: 32GB以上
- **存储**: NVMe SSD，每个Broker至少500GB
- **网络**: 10Gbps网络连接

### 高可用配置

```yaml
# 生产环境3节点Kafka集群配置
version: '3.8'
services:
  zookeeper-1:
    image: confluentinc/cp-zookeeper:7.4.0
    hostname: zookeeper-1
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
      ZOOKEEPER_SERVER_ID: 1
      ZOOKEEPER_SERVERS: zookeeper-1:2888:3888;zookeeper-2:2888:3888;zookeeper-3:2888:3888

  kafka-1:
    image: confluentinc/cp-kafka:7.4.0
    hostname: kafka-1
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper-1:2181,zookeeper-2:2181,zookeeper-3:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka-1:9092
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_MIN_INSYNC_REPLICAS: 2
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3

  # 类似配置kafka-2和kafka-3...
```

### 安全加固

```properties
# 启用SASL/SCRAM认证
listeners=SASL_SSL://0.0.0.0:9092
advertised.listeners=SASL_SSL://your-domain:9092
security.inter.broker.protocol=SASL_SSL
sasl.mechanism.inter.broker.protocol=SCRAM-SHA-256
sasl.enabled.mechanisms=SCRAM-SHA-256

# SSL配置
ssl.keystore.location=/opt/kafka/config/kafka.server.keystore.jks
ssl.keystore.password=keystore-password
ssl.key.password=key-password
ssl.truststore.location=/opt/kafka/config/kafka.server.truststore.jks
ssl.truststore.password=truststore-password
```

### 监控和日志

```yaml
# 添加日志收集和监控
  kafka-exporter:
    image: danielqsj/kafka-exporter:latest
    ports:
      - "9308:9308"
    command: --kafka.server=kafka:9092

  filebeat:
    image: elastic/filebeat:8.5.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
      - kafka_logs:/var/log/kafka
```

## 数据备份和恢复

### 主题数据备份

```bash
# 使用MirrorMaker进行跨集群复制
kafka-mirror-maker.sh --consumer.config consumer.properties \
  --producer.config producer.properties \
  --whitelist="ai-.*"

# 导出主题配置
kafka-topics.sh --bootstrap-server kafka:9092 --describe \
  --topics-with-overrides > topics-config-backup.txt
```

### 恢复流程

```bash
# 重新创建主题
kafka-topics.sh --create --topic ai-task-queue \
  --partitions 16 --replication-factor 3 \
  --bootstrap-server kafka:9092

# 恢复消费者组偏移量
kafka-consumer-groups.sh --bootstrap-server kafka:9092 \
  --group ai-task-processor --reset-offsets \
  --to-offset 12345 --topic ai-task-queue --execute
```

## 总结

本文档提供了Kafka在AI中台项目中的完整部署指南，包括：

1. **快速部署**：使用现有Docker镜像的快速启动流程
2. **多种部署方式**：Docker、Docker Compose、Kubernetes和直接安装
3. **离线部署**：适用于无网络环境的部署方案
4. **问题排查**：常见部署和运行问题的解决方案
5. **项目集成**：与现有AI中台项目的集成示例
6. **生产部署**：生产环境的配置和安全考虑

通过遵循本指南，您可以在不同环境中成功部署和管理Kafka消息队列系统，为AI中台提供可靠的消息处理能力。
