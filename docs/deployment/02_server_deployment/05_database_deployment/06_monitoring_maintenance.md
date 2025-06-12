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

#### 基于本地Docker镜像的离线部署

**重要说明**：AI中台监控系统已准备了离线Docker镜像，位于项目根目录下，支持Ubuntu服务器完全离线部署。

##### 1. 加载本地Docker镜像

**Ubuntu服务器部署**：

```bash
# 进入项目根目录
cd /home/lsyzt/ZTZT

# 加载所有监控相关的Docker镜像
docker load < prometheus.tar
docker load < grafana.tar
docker load < redis-exporter.tar
docker load < node-exporter.tar
docker load < mongodb-exporter.tar
docker load < postgres-exporter.tar
docker load < alertmanager.tar

# 验证镜像加载成功
docker images | grep -E "(prometheus|grafana|redis-exporter|node-exporter|mongodb-exporter|postgres-exporter|alertmanager)"
```

##### 2. 创建监控系统目录结构

```bash
# 创建监控系统目录结构
sudo mkdir -p /home/lsyzt/ZTZT/monitoring/{prometheus/{data,rules},grafana,alertmanager}

# 设置正确的目录权限（解决容器权限问题）
sudo chown -R 472:472 /home/lsyzt/ZTZT/monitoring/grafana      # Grafana容器用户ID
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus  # Prometheus容器用户ID  
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/data       # Prometheus数据目录权限
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/alertmanager # AlertManager权限

# 设置文件夹权限，确保容器可以读写
sudo chmod -R 755 /home/lsyzt/ZTZT/monitoring/
```

##### 3. 部署监控组件

**MongoDB Exporter（基于实际部署验证）**：

```bash
# MongoDB Exporter - 使用本地加载的镜像
docker run -d --name mongodb_exporter \
  --network host \
  --restart unless-stopped \
  prom/mongodb-exporter:latest \
  --mongodb.uri=mongodb://localhost:27017 \
  --web.listen-address=:9216 \
  --collect-all
```

**PostgreSQL Exporter**：

```bash
# PostgreSQL Exporter - 根据实际数据库配置调整连接字符串
docker run -d --name postgres_exporter \
  --network host \
  --restart unless-stopped \
  -e DATA_SOURCE_NAME="postgresql://postgres:your_password@localhost:5432/postgres?sslmode=disable" \
  prom/postgres-exporter:latest \
  --web.listen-address=:9187
```

**Redis Exporter（已验证配置）**：

```bash
# Redis Exporter - 基于成功部署验证的配置
docker run -d --name redis_exporter \
  --network host \
  --restart unless-stopped \
  -e REDIS_ADDR="localhost:6379" \
  oliver006/redis_exporter:latest \
  --web.listen-address=:9121
```

**Node Exporter（系统指标，已验证）**：

```bash
# Node Exporter - 监控Ubuntu服务器系统指标
docker run -d --name node_exporter \
  --network host \
  --restart unless-stopped \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter:latest \
  --path.rootfs=/host \
  --web.listen-address=:9100
```

**Prometheus监控服务**：

```bash
# Prometheus 主服务 - 使用实际部署路径
docker run -d --name prometheus \
  --network host \
  --restart unless-stopped \
  -v /home/lsyzt/ZTZT/monitoring/prometheus:/etc/prometheus \
  -v /home/lsyzt/ZTZT/monitoring/data:/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.console.templates=/etc/prometheus/consoles \
  --storage.tsdb.retention.time=200h \
  --web.enable-lifecycle \
  --web.listen-address=:9090
```

**Grafana可视化服务**：

```bash
# Grafana 可视化平台
docker run -d --name grafana \
  --network host \
  --restart unless-stopped \
  -v /home/lsyzt/ZTZT/monitoring/grafana:/var/lib/grafana \
  -e "GF_SECURITY_ADMIN_PASSWORD=LSYgrafanaadmin2025" \
  -e "GF_USERS_ALLOW_SIGN_UP=false" \
  grafana/grafana:latest \  --web.listen-address=:3000
```

**AlertManager告警管理**：

```bash
# AlertManager 告警处理
docker run -d --name alertmanager \
  --network host \
  --restart unless-stopped \
  -v /home/lsyzt/ZTZT/monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager:latest \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/alertmanager \
  --web.external-url=http://localhost:9093 \  --web.listen-address=:9093
```

##### 4. 一键部署脚本

**完整监控系统部署脚本**：

```bash
#!/bin/bash
# 保存为 /home/lsyzt/ZTZT/monitoring/deploy_monitoring.sh

set -e

echo "=== AI中台监控系统一键部署脚本 ==="

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "错误: Docker服务未运行，请先启动Docker"
    exit 1
fi

# 进入项目根目录
cd /home/lsyzt/ZTZT

echo "1. 加载Docker镜像..."
docker load < prometheus.tar
docker load < grafana.tar
docker load < redis-exporter.tar
docker load < node-exporter.tar
docker load < mongodb-exporter.tar
docker load < postgres-exporter.tar
docker load < alertmanager.tar

echo "2. 创建目录结构..."
sudo mkdir -p /home/lsyzt/ZTZT/monitoring/{prometheus/{data,rules},grafana,alertmanager}

echo "3. 设置目录权限..."
sudo chown -R 472:472 /home/lsyzt/ZTZT/monitoring/grafana
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/data
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/alertmanager
sudo chmod -R 755 /home/lsyzt/ZTZT/monitoring/

echo "4. 停止并清理现有容器（如果存在）..."
containers=("prometheus" "grafana" "alertmanager" "mongodb_exporter" "node_exporter" "redis_exporter" "postgres_exporter")
for container in "${containers[@]}"; do
    if docker ps -q -f name="$container" | grep -q .; then
        echo "停止容器: $container"
        docker stop "$container" && docker rm "$container"
    fi
done

echo "5. 部署监控组件..."

# 检查Redis服务是否运行，如果运行则部署Redis Exporter
if systemctl is-active --quiet redis-server 2>/dev/null || netstat -tlnp | grep ":6379 " >/dev/null 2>&1; then
    echo "部署 Redis Exporter..."
    docker run -d --name redis_exporter \
      --network host \
      --restart unless-stopped \
      -e REDIS_ADDR="localhost:6379" \
      oliver006/redis_exporter:latest \
      --web.listen-address=:9121
else
    echo "Redis服务未运行，跳过Redis Exporter部署"
fi

# 检查MongoDB服务是否运行
if systemctl is-active --quiet mongod 2>/dev/null || netstat -tlnp | grep ":27017 " >/dev/null 2>&1; then
    echo "部署 MongoDB Exporter..."
    docker run -d --name mongodb_exporter \
      --network host \
      --restart unless-stopped \
      prom/mongodb-exporter:latest \
      --mongodb.uri=mongodb://localhost:27017 \
      --web.listen-address=:9216 \
      --collect-all
else
    echo "MongoDB服务未运行，跳过MongoDB Exporter部署"
fi

# 检查PostgreSQL服务是否运行
if systemctl is-active --quiet postgresql 2>/dev/null || netstat -tlnp | grep ":5432 " >/dev/null 2>&1; then
    echo "部署 PostgreSQL Exporter..."
    # 注意：需要根据实际PostgreSQL配置调整连接字符串
    docker run -d --name postgres_exporter \
      --network host \
      --restart unless-stopped \
      -e DATA_SOURCE_NAME="postgresql://postgres:your_password@localhost:5432/postgres?sslmode=disable" \
      prom/postgres-exporter:latest \
      --web.listen-address=:9187
else
    echo "PostgreSQL服务未运行，跳过PostgreSQL Exporter部署"
fi

# Node Exporter（系统监控，总是部署）
echo "部署 Node Exporter..."
docker run -d --name node_exporter \
  --network host \
  --restart unless-stopped \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter:latest \
  --path.rootfs=/host \
  --web.listen-address=:9100

# 等待Exporters启动
echo "等待Exporters启动..."
sleep 10

# Prometheus（总是部署）
echo "部署 Prometheus..."
docker run -d --name prometheus \
  --network host \
  --restart unless-stopped \
  -v /home/lsyzt/ZTZT/monitoring/prometheus:/etc/prometheus \
  -v /home/lsyzt/ZTZT/monitoring/data:/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.console.templates=/etc/prometheus/consoles \
  --storage.tsdb.retention.time=200h \
  --web.enable-lifecycle \
  --web.listen-address=:9090

# Grafana（总是部署）
echo "部署 Grafana..."
docker run -d --name grafana \
  --network host \
  --restart unless-stopped \
  -v /home/lsyzt/ZTZT/monitoring/grafana:/var/lib/grafana \
  -e "GF_SECURITY_ADMIN_PASSWORD=LSYgrafanaadmin2025" \
  -e "GF_USERS_ALLOW_SIGN_UP=false" \
  grafana/grafana:latest

# AlertManager（总是部署）
echo "部署 AlertManager..."
docker run -d --name alertmanager \
  --network host \
  --restart unless-stopped \
  -v /home/lsyzt/ZTZT/monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager:latest \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/alertmanager \
  --web.external-url=http://localhost:9093 \
  --web.listen-address=:9093

echo "6. 等待服务启动..."
sleep 30

echo "7. 验证部署状态..."
echo "检查容器状态..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(prometheus|grafana|exporter|alertmanager)"

echo "检查端口监听..."
ports=(9090 3000 9093 9100)
redis_running=false
mongo_running=false
postgres_running=false

if docker ps | grep -q redis_exporter; then
    ports+=(9121)
    redis_running=true
fi

if docker ps | grep -q mongodb_exporter; then
    ports+=(9216)
    mongo_running=true
fi

if docker ps | grep -q postgres_exporter; then
    ports+=(9187)
    postgres_running=true
fi

for port in "${ports[@]}"; do
    if netstat -tlnp | grep ":$port " >/dev/null; then
        echo "✓ 端口 $port 正在监听"
    else
        echo "✗ 端口 $port 未监听"
    fi
done

echo "=== 部署完成 ==="
echo "访问地址："
echo "- Prometheus: http://localhost:9090 或 http://$(hostname -I | awk '{print $1}'):9090"
echo "- Grafana: http://localhost:3000 或 http://$(hostname -I | awk '{print $1}'):3000"
echo "  用户名: admin"
echo "  密码: LSYgrafanaadmin2025"
echo "- AlertManager: http://localhost:9093 或 http://$(hostname -I | awk '{print $1}'):9093"

if [ "$redis_running" = true ]; then
    echo "- Redis监控: http://localhost:9121/metrics"
fi

if [ "$mongo_running" = true ]; then
    echo "- MongoDB监控: http://localhost:9216/metrics"
fi

if [ "$postgres_running" = true ]; then
    echo "- PostgreSQL监控: http://localhost:9187/metrics"
fi

echo "- 系统监控: http://localhost:9100/metrics"

echo ""
echo "下一步："
echo "1. 配置Prometheus配置文件: /home/lsyzt/ZTZT/monitoring/prometheus/prometheus.yml"
echo "2. 配置告警规则: /home/lsyzt/ZTZT/monitoring/prometheus/rules/database_alerts.yml"
echo "3. 配置AlertManager: /home/lsyzt/ZTZT/monitoring/alertmanager/alertmanager.yml"
echo "4. 在Grafana中导入监控仪表板"
```

##### 5. 验证监控服务状态

```bash
# 检查各服务的运行状态
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(prometheus|grafana|mongodb_exporter|node_exporter|redis_exporter|alertmanager)"

# 验证各Exporter是否正常响应
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health, lastScrape: .lastScrape}'

# 快速健康检查
endpoints=(
    "http://localhost:9090/-/healthy"      # Prometheus健康检查
    "http://localhost:3000/api/health"     # Grafana健康检查  
    "http://localhost:9093/-/healthy"      # AlertManager健康检查
    "http://localhost:9100/metrics"        # Node Exporter
)

# 检查Redis Exporter（如果部署了）
if docker ps | grep -q redis_exporter; then
    endpoints+=("http://localhost:9121/metrics")
fi

# 检查MongoDB Exporter（如果部署了）  
if docker ps | grep -q mongodb_exporter; then
    endpoints+=("http://localhost:9216/metrics")
fi

# 检查PostgreSQL Exporter（如果部署了）
if docker ps | grep -q postgres_exporter; then
    endpoints+=("http://localhost:9187/metrics")
fi

for endpoint in "${endpoints[@]}"; do
    if curl -s --max-time 5 "$endpoint" >/dev/null; then
        echo "✓ $endpoint 可访问"
    else
        echo "✗ $endpoint 不可访问"
    fi
done
```

##### 6. 访问监控服务

**Ubuntu服务器访问地址**：
- **Prometheus**: http://服务器IP:9090 | http://192.168.110.88:9090
- **Grafana**: http://服务器IP:3000  | http://192.168.110.88:3000 (admin/LSYgrafanaadmin2025)
- **AlertManager**: http://服务器IP:9093 | http://192.168.110.88:9093

##### 7. Prometheus配置文件

**Ubuntu环境配置**（保存为 `/home/lsyzt/ZTZT/monitoring/prometheus/prometheus.yml`）：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - localhost:9093

rule_files:
  - "rules/database_alerts.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'mongodb'
    static_configs:
      - targets: ['localhost:9216']
        labels:
          instance: 'mongodb_server'
    scrape_interval: 30s

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']
        labels:
          instance: 'postgresql_server'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
        labels:
          instance: 'redis_server'
    scrape_interval: 15s

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']
        labels:
          instance: 'linux_server'
    scrape_interval: 15s

  - job_name: 'alertmanager'
    static_configs:
      - targets: ['localhost:9093']
```

**Windows环境配置**（保存为 `C:\Users\Administrator\Desktop\ZT\code\ZTZT\monitoring\prometheus\prometheus.yml`）：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - localhost:9093

rule_files:
  - "rules/database_alerts.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'mongodb'
    static_configs:
      - targets: ['localhost:9216']
        labels:
          instance: 'mongodb_server'
    scrape_interval: 30s

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']
        labels:
          instance: 'postgresql_server'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
        labels:
          instance: 'redis_server'    scrape_interval: 15s

  - job_name: 'alertmanager'
    static_configs:
      - targets: ['localhost:9093']
```

##### 8. 优化的配置文件创建命令

**Linux环境配置文件创建**：

```bash
# 创建Prometheus配置文件
cat > /home/lsyzt/ZTZT/monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - localhost:9093

rule_files:
  - "rules/database_alerts.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'mongodb'
    static_configs:
      - targets: ['localhost:9216']
        labels:
          instance: 'mongodb_server'
    scrape_interval: 30s

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']
        labels:
          instance: 'postgresql_server'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
        labels:
          instance: 'redis_server'
    scrape_interval: 15s

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']
        labels:
          instance: 'linux_server'
    scrape_interval: 15s

  - job_name: 'alertmanager'
    static_configs:
      - targets: ['localhost:9093']
EOF

# 设置配置文件权限
sudo chown 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus/prometheus.yml
sudo chmod 644 /home/lsyzt/ZTZT/monitoring/prometheus/prometheus.yml
```

##### 9. 数据库告警规则配置

**基于实际监控指标的告警规则**（保存为 `/home/lsyzt/ZTZT/monitoring/prometheus/rules/database_alerts.yml`）：

```yaml
groups:
- name: database_alerts
  rules:
  # PostgreSQL 监控告警
  - alert: PostgreSQLHighConnections
    expr: sum(pg_stat_activity_count) > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "PostgreSQL高连接数告警"
      description: "PostgreSQL实例连接数超过100个，持续5分钟"

  - alert: PostgreSQLSlowQueries
    expr: rate(pg_stat_statements_mean_exec_time[5m]) > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "PostgreSQL慢查询告警"
      description: "PostgreSQL出现慢查询，平均执行时间超过1000ms"

  # MongoDB 监控告警（基于实际可用指标）
  - alert: MongoDBHighConnections
    expr: mongodb_ss_connections{state="current"} > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "MongoDB高连接数告警"
      description: "MongoDB当前连接数为 {{ $value }}，较高"

  - alert: MongoDBHighMemoryUsage
    expr: mongodb_ss_mem_resident > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "MongoDB高内存使用告警"
      description: "MongoDB正在使用 {{ $value }}MB 常驻内存"

  - alert: MongoDBSlowOperations
    expr: rate(mongodb_ss_opcounters_total[5m]) > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "MongoDB高操作频率告警"
      description: "MongoDB操作频率过高：{{ $value }} ops/sec"

  # Redis 监控告警（基于实际验证的指标）
  - alert: RedisDown
    expr: redis_up == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Redis服务不可用"
      description: "Redis服务已停止响应超过2分钟"

  - alert: RedisMemoryHigh
    expr: redis_memory_used_bytes / redis_config_maxmemory * 100 > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis内存使用率高"
      description: "Redis内存使用率超过80%，当前使用率: {{ $value }}%"

  - alert: RedisHighConnections
    expr: redis_connected_clients > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis高连接数告警"
      description: "Redis客户端连接数为 {{ $value }}，较高"

  - alert: RedisSlowLog
    expr: redis_slowlog_length > 0
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Redis慢查询告警"
      description: "Redis慢查询日志增长，当前长度: {{ $value }}"

  - alert: RedisKeyspaceHitRateLow
    expr: rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100 < 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis缓存命中率低"
      description: "Redis缓存命中率低于80%，当前命中率: {{ $value }}%"

  # 系统资源监控告警（基于Node Exporter指标）
  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "高CPU使用率告警"
      description: "{{ $labels.instance }} CPU使用率超过80%，持续5分钟，当前使用率: {{ $value }}%"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "高内存使用率告警"
      description: "{{ $labels.instance }} 内存使用率超过85%，持续5分钟，当前使用率: {{ $value }}%"

  - alert: DiskSpaceHigh
    expr: (node_filesystem_size_bytes{fstype!="tmpfs"} - node_filesystem_free_bytes{fstype!="tmpfs"}) / node_filesystem_size_bytes{fstype!="tmpfs"} * 100 > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "磁盘空间不足告警"
      description: "{{ $labels.instance }} 磁盘 {{ $labels.mountpoint }} 使用率超过85%，持续5分钟，当前使用率: {{ $value }}%"

  - alert: DiskSpaceCritical
    expr: (node_filesystem_size_bytes{fstype!="tmpfs"} - node_filesystem_free_bytes{fstype!="tmpfs"}) / node_filesystem_size_bytes{fstype!="tmpfs"} * 100 > 95
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "磁盘空间严重不足"
      description: "{{ $labels.instance }} 磁盘 {{ $labels.mountpoint }} 使用率超过95%，剩余空间不足"

  # 服务可用性监控
  - alert: MonitoringExporterDown
    expr: up == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "监控组件离线"
      description: "{{ $labels.job }} 在 {{ $labels.instance }} 上已离线超过2分钟"

  - alert: PrometheusTargetDown
    expr: up == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Prometheus目标离线"
      description: "Prometheus目标 {{ $labels.job }} ({{ $labels.instance }}) 已离线"

  # 网络和连接监控
  - alert: HighNetworkTraffic
    expr: rate(node_network_receive_bytes_total[5m]) > 100000000  # 100MB/s
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "高网络流量告警"
      description: "{{ $labels.instance }} 接口 {{ $labels.device }} 入站流量超过100MB/s"

  - alert: TooManyOpenFiles
    expr: node_filefd_allocated / node_filefd_maximum * 100 > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "打开文件数过多"
      description: "{{ $labels.instance }} 打开文件数占比超过80%: {{ $value }}%"

# Windows环境专用告警（如果使用Windows Exporter）
- name: windows_alerts
  rules:
  - alert: WindowsHighCPUUsage
    expr: 100 - windows_cpu_time_total{mode="idle"} > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Windows高CPU使用率"
      description: "Windows服务器CPU使用率超过80%"

  - alert: WindowsHighMemoryUsage
    expr: (windows_os_physical_memory_free_bytes / windows_cs_physical_memory_bytes) * 100 < 15
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Windows高内存使用率"
      description: "Windows服务器可用内存低于15%"

  - alert: WindowsDiskSpaceHigh
    expr: (windows_logical_disk_free_bytes / windows_logical_disk_size_bytes) * 100 < 15
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Windows磁盘空间不足"
      description: "Windows服务器磁盘 {{ $labels.volume }} 可用空间低于15%"
```

**创建告警规则文件的命令**：

**Linux环境**：
```bash
# 创建告警规则目录
sudo mkdir -p /home/lsyzt/ZTZT/monitoring/prometheus/rules

# 创建告警规则文件（此处会创建上述完整的告警规则）
sudo tee /home/lsyzt/ZTZT/monitoring/prometheus/rules/database_alerts.yml > /dev/null << 'EOF'
# 此处粘贴上述YAML内容
EOF

# 设置权限
sudo chown 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus/rules/database_alerts.yml
sudo chmod 644 /home/lsyzt/ZTZT/monitoring/prometheus/rules/database_alerts.yml

# 验证告警规则语法
docker exec prometheus promtool check rules /etc/prometheus/rules/database_alerts.yml
```

**Windows PowerShell**：
```powershell
# 创建告警规则目录
New-Item -ItemType Directory -Force -Path ".\monitoring\prometheus\rules"

# 注意：在Windows中，需要将上述YAML内容保存到文件
# 可以使用文本编辑器创建 .\monitoring\prometheus\rules\database_alerts.yml
Write-Host "请将告警规则YAML内容保存到: .\monitoring\prometheus\rules\database_alerts.yml" -ForegroundColor Yellow

# 验证告警规则语法（在Prometheus容器运行后）
# docker exec prometheus promtool check rules /etc/prometheus/rules/database_alerts.yml
```

  ##### 10. AlertManager配置优化

**基于实际部署的AlertManager配置**（保存为 `/home/lsyzt/ZTZT/monitoring/alertmanager/alertmanager.yml`）：

```yaml
global:
  resolve_timeout: 5m
  # SMTP邮件配置（根据实际邮件服务器配置）
  smtp_smarthost: 'smtp.163.com:587'  # 例如：使用163邮箱
  smtp_from: 'ai-platform-alert@163.com'
  smtp_auth_username: 'ai-platform-alert@163.com'
  smtp_auth_password: 'your_email_auth_code'  # 邮箱授权码
  smtp_require_tls: true
  smtp_hello: 'AI中台监控系统'

# 告警路由规则
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s      # 等待30秒收集同组告警
  group_interval: 5m   # 同组告警间隔5分钟
  repeat_interval: 12h # 重复告警间隔12小时
  receiver: 'default-receiver'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
    repeat_interval: 2h  # 严重告警2小时重复一次
  - match:
      severity: warning
    receiver: 'warning-alerts'
    repeat_interval: 12h # 警告告警12小时重复一次
  - match:
      alertname: 'RedisDown'
    receiver: 'database-critical'
    repeat_interval: 1h
  - match:
      alertname: 'MongoDBHighConnections'
    receiver: 'database-warning'
    repeat_interval: 6h

# 告警接收器配置
receivers:
- name: 'default-receiver'
  email_configs:
  - to: 'dba-team@company.com'
    subject: '[AI中台监控] {{ .GroupLabels.alertname }} 告警通知'
    headers:
      From: 'AI中台监控系统 <ai-platform-alert@163.com>'
      Reply-To: 'ops-team@company.com'
    body: |
      AI中台监控系统告警通知
      
      告警时间: {{ range .Alerts }}{{ .StartsAt.Format "2006-01-02 15:04:05" }}{{ end }}
      告警摘要: {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}
      告警详情: {{ range .Alerts }}{{ .Annotations.description }}{{ end }}
      
      告警标签:
      {{ range .Alerts }}{{ range .Labels.SortedPairs }}  {{ .Name }}: {{ .Value }}
      {{ end }}{{ end }}
      
      请及时查看和处理。
      
      监控平台: http://192.168.110.88:9090
      Grafana仪表板: http://192.168.110.88:3000
    html: |
      <h2>🔔 AI中台监控系统告警通知</h2>
      <table border="1" style="border-collapse: collapse; width: 100%;">
      {{ range .Alerts }}
      <tr><td><strong>告警名称</strong></td><td>{{ .Labels.alertname }}</td></tr>
      <tr><td><strong>告警级别</strong></td><td>{{ .Labels.severity }}</td></tr>
      <tr><td><strong>告警摘要</strong></td><td>{{ .Annotations.summary }}</td></tr>
      <tr><td><strong>告警详情</strong></td><td>{{ .Annotations.description }}</td></tr>
      <tr><td><strong>实例</strong></td><td>{{ .Labels.instance }}</td></tr>
      <tr><td><strong>开始时间</strong></td><td>{{ .StartsAt.Format "2006-01-02 15:04:05" }}</td></tr>
      <tr><td colspan="2"><hr></td></tr>
      {{ end }}
      </table>
      <p><a href="http://192.168.110.88:9090">查看监控面板</a> | <a href="http://192.168.110.88:3000">查看Grafana仪表板</a></p>

- name: 'critical-alerts'
  email_configs:
  - to: 'critical-alerts@company.com,ops-manager@company.com'
    subject: '[🚨CRITICAL🚨] AI中台严重告警 - {{ .GroupLabels.alertname }}'
    body: |
      🚨🚨🚨 AI中台严重告警 🚨🚨🚨
      
      这是一个需要立即处理的严重告警！
      
      {{ range .Alerts }}
      告警名称: {{ .Labels.alertname }}
      严重程度: {{ .Labels.severity }}
      告警摘要: {{ .Annotations.summary }}
      告警详情: {{ .Annotations.description }}
      影响实例: {{ .Labels.instance }}
      开始时间: {{ .StartsAt.Format "2006-01-02 15:04:05" }}
      
      {{ end }}
      
      请立即查看并处理此告警。
      
      监控详情: http://192.168.110.88:9090
      Grafana详情: http://192.168.110.88:3000
  # 可以添加钉钉、企业微信等webhook通知
  webhook_configs:
  - url: 'http://localhost:8080/webhook/critical'  # 自定义webhook接口
    send_resolved: true
    http_config:
      basic_auth:
        username: 'webhook_user'
        password: 'webhook_password'

- name: 'warning-alerts'
  email_configs:
  - to: 'monitoring@company.com'
    subject: '[⚠️WARNING⚠️] AI中台监控警告 - {{ .GroupLabels.alertname }}'
    body: |
      ⚠️ AI中台监控警告 ⚠️
      
      {{ range .Alerts }}
      告警名称: {{ .Labels.alertname }}
      严重程度: {{ .Labels.severity }}
      告警摘要: {{ .Annotations.summary }}
      告警详情: {{ .Annotations.description }}
      实例: {{ .Labels.instance }}
      开始时间: {{ .StartsAt.Format "2006-01-02 15:04:05" }}
      
      {{ end }}
      
      建议在方便时查看并处理。
      
      监控详情: http://192.168.110.88:9090

- name: 'database-critical'
  email_configs:
  - to: 'dba-oncall@company.com'
    subject: '[数据库严重告警] {{ .GroupLabels.alertname }}'
    body: |
      数据库服务严重告警！
      
      {{ range .Alerts }}
      数据库: {{ .Labels.job }}
      问题: {{ .Annotations.summary }}
      详情: {{ .Annotations.description }}
      时间: {{ .StartsAt.Format "2006-01-02 15:04:05" }}
      {{ end }}
      
      数据库服务可能影响业务，请立即处理！

- name: 'database-warning'
  email_configs:
  - to: 'dba-team@company.com'
    subject: '[数据库监控警告] {{ .GroupLabels.alertname }}'
    body: |
      数据库监控警告
      
      {{ range .Alerts }}
      数据库: {{ .Labels.job }}
      警告: {{ .Annotations.summary }}
      详情: {{ .Annotations.description }}
      时间: {{ .StartsAt.Format "2006-01-02 15:04:05" }}
      {{ end }}
      
      请关注数据库性能状况。

# 告警抑制规则（避免告警风暴）
inhibit_rules:
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['alertname', 'cluster', 'service']

- source_match:
    alertname: 'MonitoringExporterDown'
  target_match_re:
    alertname: '.*High.*|.*Slow.*'
  equal: ['instance']  # 如果监控组件挂了，抑制其他基于该实例的告警
```

**创建AlertManager配置文件命令**：

**Linux环境**：
```bash
# 创建AlertManager配置文件
sudo tee /home/lsyzt/ZTZT/monitoring/alertmanager/alertmanager.yml > /dev/null << 'EOF'
# 此处粘贴上述YAML配置内容
EOF

# 设置权限
sudo chown 65534:65534 /home/lsyzt/ZTZT/monitoring/alertmanager/alertmanager.yml
sudo chmod 644 /home/lsyzt/ZTZT/monitoring/alertmanager/alertmanager.yml

# 验证配置语法
docker exec alertmanager amtool config check /etc/alertmanager/alertmanager.yml
```

**Windows PowerShell**：
```powershell
# 在Windows环境中，需要手动创建AlertManager配置文件
Write-Host "请将AlertManager配置内容保存到: .\monitoring\alertmanager\alertmanager.yml" -ForegroundColor Yellow
Write-Host "配置文件路径: $PWD\monitoring\alertmanager\alertmanager.yml" -ForegroundColor Cyan
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

## 故障排查指南

基于实际部署的AI中台监控系统，以下是常见问题的诊断和解决方法：

### 监控系统故障排查

#### 1. Redis监控问题排查

**问题1：Redis Exporter无法连接Redis**

```bash
# 1. 检查Redis服务状态
sudo systemctl status redis-server
# 或检查Redis进程
ps aux | grep redis

# 2. 检查Redis是否监听正确端口
netstat -tlnp | grep 6379
sudo ss -tlnp | grep 6379

# 3. 测试Redis连接
redis-cli ping
# 期望输出：PONG

# 4. 检查Redis配置
redis-cli config get bind
redis-cli config get port

# 5. 如果Redis未安装，安装Redis
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 6. 验证Redis Exporter连接
curl http://localhost:9121/metrics | grep redis_up
# 期望看到：redis_up 1
```

**问题2：Redis Exporter指标缺失**

```bash
# 检查Redis Exporter日志
docker logs redis_exporter

# 重新部署Redis Exporter（使用正确的连接字符串）
docker stop redis_exporter
docker rm redis_exporter

# 根据实际验证的配置重新部署
docker run -d --name redis_exporter \
  --network host \
  --restart unless-stopped \
  -e REDIS_ADDR="localhost:6379" \
  oliver006/redis_exporter:latest \
  --web.listen-address=:9121

# 验证指标输出
curl http://localhost:9121/metrics | head -20
```

#### 2. Prometheus配置问题

**问题1：Prometheus容器启动失败**

```bash
# 检查Prometheus容器日志
docker logs prometheus

# 常见错误和解决方法：

# 错误1：权限拒绝
# level=error msg="Error opening query logger file" err="permission denied"
# 解决：修复目录权限
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/data
sudo chmod -R 755 /home/lsyzt/ZTZT/monitoring/

# 错误2：配置文件语法错误
# 解决：验证配置文件语法
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml

# 错误3：端口被占用
# 解决：检查端口使用情况
sudo netstat -tlnp | grep 9090
# 如果有其他进程占用，停止该进程或更改Prometheus端口

# 重启Prometheus容器
docker restart prometheus
```

**问题2：Prometheus无法抓取目标数据**

```bash
# 1. 检查Prometheus目标状态
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health, lastError: .lastError}'

# 2. 检查各个Exporter是否运行
docker ps | grep exporter

# 3. 手动测试Exporter端点
endpoints=(
    "http://localhost:9100/metrics"   # Node Exporter
    "http://localhost:9121/metrics"   # Redis Exporter
    "http://localhost:9216/metrics"   # MongoDB Exporter
    "http://localhost:9187/metrics"   # PostgreSQL Exporter
)

for endpoint in "${endpoints[@]}"; do
    echo "测试 $endpoint"
    if curl -s --max-time 5 "$endpoint" | head -5; then
        echo "✓ $endpoint 正常"
    else
        echo "✗ $endpoint 失败"
    fi
done

# 4. 检查网络连接
sudo ss -tlnp | grep -E ':(9090|9100|9121|9216|9187)'

# 5. 重新加载Prometheus配置（无需重启）
curl -X POST http://localhost:9090/-/reload
```

#### 3. MongoDB Exporter问题

**问题1：MongoDB Exporter版本兼容性**

```bash
# 检查当前MongoDB版本
mongosh --eval "db.version()"

# 检查MongoDB Exporter日志
docker logs mongodb_exporter

# 如果出现连接问题，使用验证过的版本和配置
docker stop mongodb_exporter
docker rm mongodb_exporter

# 使用经过验证的配置重新部署
docker run -d --name mongodb_exporter \
  --network host \
  --restart unless-stopped \
  prom/mongodb-exporter:latest \
  --mongodb.uri=mongodb://localhost:27017 \
  --web.listen-address=:9216 \
  --collect-all \
  --log.level=debug  # 临时启用调试日志

# 检查连接状态
curl http://localhost:9216/metrics | grep mongodb_up
```

**问题2：MongoDB认证问题**

```bash
# 如果MongoDB启用了认证，需要创建监控用户
mongosh admin --eval "
db.createUser({
  user: 'mongodb_exporter',
  pwd: 'monitoring_password',
  roles: [
    { role: 'clusterMonitor', db: 'admin' },
    { role: 'read', db: 'local' }
  ]
})
"

# 更新MongoDB Exporter连接字符串
docker stop mongodb_exporter
docker rm mongodb_exporter

docker run -d --name mongodb_exporter \
  --network host \
  --restart unless-stopped \
  prom/mongodb-exporter:latest \
  --mongodb.uri="mongodb://mongodb_exporter:monitoring_password@localhost:27017/admin" \
  --web.listen-address=:9216 \
  --collect-all
```

#### 4. Grafana访问问题

**问题1：Grafana无法访问**

```bash
# 检查Grafana容器状态
docker logs grafana

# 检查Grafana端口
sudo netstat -tlnp | grep 3000

# 常见错误解决：

# 错误1：权限问题
sudo chown -R 472:472 /home/lsyzt/ZTZT/monitoring/grafana
sudo chmod -R 755 /home/lsyzt/ZTZT/monitoring/grafana

# 错误2：端口冲突
# 如果3000端口被占用，修改Grafana端口
docker stop grafana
docker rm grafana

docker run -d --name grafana \
  --restart unless-stopped \
  -p 3001:3000 \  # 使用不同端口
  -v /home/lsyzt/ZTZT/monitoring/grafana:/var/lib/grafana \
  -e "GF_SECURITY_ADMIN_PASSWORD=LSYgrafanaadmin2025" \
  grafana/grafana:latest

# 重置Grafana密码（如果忘记）
docker exec -it grafana grafana-cli admin reset-admin-password newpassword
```

**问题2：Grafana无法连接Prometheus数据源**

```bash
# 1. 测试Prometheus API连接
curl http://localhost:9090/api/v1/query?query=up

# 2. 在Grafana中配置数据源
# 访问 http://localhost:3000
# 用户名: admin
# 密码: LSYgrafanaadmin2025
# 配置Prometheus数据源:
#   - Name: Prometheus
#   - Type: Prometheus  
#   - URL: http://localhost:9090
#   - Access: Server (default)

# 3. 测试数据源连接
# 在Grafana数据源配置页面点击 "Save & Test"
```

#### 5. AlertManager告警问题

**问题1：告警未发送**

```bash
# 1. 检查AlertManager状态
curl http://localhost:9093/-/healthy

# 2. 检查AlertManager配置
docker exec alertmanager amtool config check /etc/alertmanager/alertmanager.yml

# 3. 查看当前告警
curl http://localhost:9093/api/v1/alerts

# 4. 检查告警路由
docker exec alertmanager amtool config routes show

# 5. 测试邮件配置
docker exec alertmanager amtool config check /etc/alertmanager/alertmanager.yml

# 6. 查看AlertManager日志
docker logs alertmanager

# 7. 手动触发测试告警
curl -XPOST http://localhost:9093/api/v1/alerts -H "Content-Type: application/json" -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "Test alert for verification"
    }
  }
]'
```

#### 6. 完整系统验证脚本

**综合诊断脚本** (`/home/lsyzt/ZTZT/monitoring/diagnose_monitoring.sh`)：

```bash
#!/bin/bash
# AI中台监控系统综合诊断脚本

echo "=== AI中台监控系统诊断脚本 ==="

# 1. 检查Docker服务
echo "1. 检查Docker服务..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker服务未运行"
    exit 1
else
    echo "✅ Docker服务正常"
fi

# 2. 检查容器状态
echo -e "\n2. 检查容器状态..."
containers=("prometheus" "grafana" "alertmanager" "node_exporter" "redis_exporter" "mongodb_exporter")
for container in "${containers[@]}"; do
    if docker ps -q -f name="$container" | grep -q .; then
        status=$(docker inspect -f '{{.State.Status}}' "$container")
        if [ "$status" = "running" ]; then
            echo "✅ $container: 运行中"
        else
            echo "⚠️ $container: $status"
        fi
    else
        echo "❌ $container: 未运行"
    fi
done

# 3. 检查端口监听
echo -e "\n3. 检查端口监听..."
declare -A ports=(
    ["9090"]="Prometheus"
    ["3000"]="Grafana"
    ["9093"]="AlertManager"
    ["9100"]="Node Exporter"
    ["9121"]="Redis Exporter"
    ["9216"]="MongoDB Exporter"
)

for port in "${!ports[@]}"; do
    if ss -tlnp | grep ":$port " >/dev/null; then
        echo "✅ ${ports[$port]} (端口 $port): 正在监听"
    else
        echo "❌ ${ports[$port]} (端口 $port): 未监听"
    fi
done

# 4. 检查服务健康状态
echo -e "\n4. 检查服务健康状态..."
endpoints=(
    "http://localhost:9090/-/healthy:Prometheus健康检查"
    "http://localhost:3000/api/health:Grafana健康检查"
    "http://localhost:9093/-/healthy:AlertManager健康检查"
    "http://localhost:9100/metrics:Node Exporter指标"
)

# 动态检查已部署的Exporter
if docker ps | grep -q redis_exporter; then
    endpoints+=("http://localhost:9121/metrics:Redis Exporter指标")
fi

if docker ps | grep -q mongodb_exporter; then
    endpoints+=("http://localhost:9216/metrics:MongoDB Exporter指标")
fi

for endpoint_info in "${endpoints[@]}"; do
    IFS=':' read -r endpoint description <<< "$endpoint_info"
    if timeout 5 curl -s "$endpoint" >/dev/null 2>&1; then
        echo "✅ $description: 可访问"
    else
        echo "❌ $description: 不可访问"
    fi
done

# 5. 检查Prometheus目标状态
echo -e "\n5. 检查Prometheus目标状态..."
if command -v jq >/dev/null; then
    targets=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "$targets" | jq -r '.data.activeTargets[]? | "\(.labels.job): \(.health)"' 2>/dev/null || echo "无法解析Prometheus目标数据"
    else
        echo "❌ 无法获取Prometheus目标状态"
    fi
else
    echo "⚠️ 未安装jq，跳过详细目标检查"
fi

# 6. 检查Redis连接（如果Redis Exporter在运行）
if docker ps | grep -q redis_exporter; then
    echo -e "\n6. 检查Redis连接..."
    if redis-cli ping >/dev/null 2>&1; then
        echo "✅ Redis连接正常"
        redis_metrics=$(curl -s http://localhost:9121/metrics 2>/dev/null | grep -c "redis_up 1")
        if [ "$redis_metrics" -gt 0 ]; then
            echo "✅ Redis Exporter指标正常"
        else
            echo "⚠️ Redis Exporter指标异常"
        fi
    else
        echo "❌ Redis连接失败"
    fi
fi

# 7. 检查MongoDB连接（如果MongoDB Exporter在运行）
if docker ps | grep -q mongodb_exporter; then
    echo -e "\n7. 检查MongoDB连接..."
    if mongosh --eval "db.runCommand('ping')" >/dev/null 2>&1; then
        echo "✅ MongoDB连接正常"
        mongo_metrics=$(curl -s http://localhost:9216/metrics 2>/dev/null | grep -c "mongodb_up")
        if [ "$mongo_metrics" -gt 0 ]; then
            echo "✅ MongoDB Exporter指标正常"
        else
            echo "⚠️ MongoDB Exporter指标异常"
        fi
    else
        echo "❌ MongoDB连接失败"
    fi
fi

# 8. 检查告警规则
echo -e "\n8. 检查告警规则..."
if [ -f "/home/lsyzt/ZTZT/monitoring/prometheus/rules/database_alerts.yml" ]; then
    echo "✅ 告警规则文件存在"
    if docker exec prometheus promtool check rules /etc/prometheus/rules/database_alerts.yml >/dev/null 2>&1; then
        echo "✅ 告警规则语法正确"
    else
        echo "❌ 告警规则语法错误"
    fi
else
    echo "⚠️ 告警规则文件不存在"
fi

# 9. 生成诊断报告
echo -e "\n=== 诊断报告 ==="
echo "时间: $(date)"
echo "主机: $(hostname)"
echo "IP地址: $(hostname -I | awk '{print $1}')"
echo ""
echo "监控服务访问地址:"
echo "- Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
echo "- Grafana: http://$(hostname -I | awk '{print $1}'):3000 (admin/LSYgrafanaadmin2025)"
echo "- AlertManager: http://$(hostname -I | awk '{print $1}'):9093"
echo ""

# 10. 提供修复建议
echo "=== 修复建议 ==="
echo "如果发现问题，请运行以下命令进行修复:"
echo "1. 修复权限: sudo /home/lsyzt/ZTZT/monitoring/fix_permissions.sh"
echo "2. 重新部署: sudo /home/lsyzt/ZTZT/monitoring/deploy_monitoring.sh"
echo "3. 查看日志: docker logs <container_name>"
echo ""
echo "=== 诊断完成 ==="
```

**权限修复脚本** (`/home/lsyzt/ZTZT/monitoring/fix_permissions.sh`)：

```bash
#!/bin/bash
# 监控系统权限修复脚本

echo "=== 修复监控系统权限 ==="

# 创建目录（如果不存在）
sudo mkdir -p /home/lsyzt/ZTZT/monitoring/{prometheus/{data,rules},grafana,alertmanager}

# 修复权限
echo "修复Grafana权限..."
sudo chown -R 472:472 /home/lsyzt/ZTZT/monitoring/grafana

echo "修复Prometheus权限..."
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/data

echo "修复AlertManager权限..."
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/alertmanager

echo "设置通用权限..."
sudo chmod -R 755 /home/lsyzt/ZTZT/monitoring/

echo "权限修复完成！"

# 验证权限
echo "验证权限设置..."
ls -la /home/lsyzt/ZTZT/monitoring/
```

使这些脚本可执行：

```bash
chmod +x /home/lsyzt/ZTZT/monitoring/diagnose_monitoring.sh
chmod +x /home/lsyzt/ZTZT/monitoring/fix_permissions.sh
```

### Grafana仪表板配置

#### 1. 数据源配置

**配置Prometheus数据源**：

1. 访问Grafana: http://服务器IP:3000 (admin/LSYgrafanaadmin2025)
2. 左侧菜单 → Configuration → Data Sources
3. Add data source → Prometheus
4. 配置参数：
   - **Name**: Prometheus
   - **URL**: http://localhost:9090 (Linux) 或 http://host.docker.internal:9090 (Windows)
   - **Access**: Server (default)
   - **Scrape interval**: 15s
5. Save & Test

#### 2. 推荐仪表板导入

**基础系统监控仪表板**：

```bash
# 下载推荐的仪表板JSON文件
wget -O /tmp/node-exporter-dashboard.json https://grafana.com/api/dashboards/1860/revisions/33/download
wget -O /tmp/redis-dashboard.json https://grafana.com/api/dashboards/763/revisions/4/download
wget -O /tmp/mongodb-dashboard.json https://grafana.com/api/dashboards/2583/revisions/2/download
wget -O /tmp/prometheus-dashboard.json https://grafana.com/api/dashboards/3662/revisions/2/download
```

**仪表板导入步骤**：

1. Grafana → Dashboards → Import
2. 上传JSON文件或输入仪表板ID
3. 选择Prometheus数据源
4. 点击Import

**推荐仪表板ID列表**：

- **Node Exporter Full**: 1860 - Linux系统全面监控
- **Redis Dashboard**: 763 - Redis性能监控
- **MongoDB Dashboard**: 2583 - MongoDB指标监控
- **Prometheus Stats**: 3662 - Prometheus自身监控
- **AlertManager Dashboard**: 9578 - 告警系统监控

#### 3. 自定义AI中台监控仪表板

**创建专用的AI中台监控仪表板JSON配置**：

```json
{
  "dashboard": {
    "id": null,
    "title": "AI中台数据库监控仪表板",
    "tags": ["ai-platform", "database", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "系统概览",
        "type": "stat",
        "targets": [
          {
            "expr": "up",
            "legendFormat": "{{job}} - {{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Redis连接数",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_connected_clients",
            "legendFormat": "当前连接数"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Redis内存使用",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_memory_used_bytes",
            "legendFormat": "已使用内存"
          },
          {
            "expr": "redis_config_maxmemory",
            "legendFormat": "最大内存"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "MongoDB连接数",
        "type": "graph",
        "targets": [
          {
            "expr": "mongodb_ss_connections",
            "legendFormat": "{{state}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      },
      {
        "id": 5,
        "title": "系统CPU使用率",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU使用率 - {{instance}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
      },
      {
        "id": 6,
        "title": "系统内存使用率",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "legendFormat": "内存使用率 - {{instance}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

#### 4. 告警仪表板配置

**配置告警状态监控面板**：

```json
{
  "dashboard": {
    "title": "AI中台告警监控",
    "panels": [
      {
        "id": 1,
        "title": "当前活跃告警",
        "type": "table",
        "targets": [
          {
            "expr": "ALERTS{alertstate=\"firing\"}",
            "format": "table"
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {
                "__name__": true,
                "job": false,
                "instance": false
              }
            }
          }
        ]
      },
      {
        "id": 2,
        "title": "告警历史趋势",
        "type": "graph",
        "targets": [
          {
            "expr": "increase(prometheus_notifications_total[1h])",
            "legendFormat": "告警发送数量"
          }
        ]
      }
    ]
  }
}
```

#### 5. 性能优化监控

**数据库性能监控面板配置**：

1. **Redis性能面板**：
   - Redis命令执行频率: `rate(redis_commands_total[5m])`
   - Redis缓存命中率: `rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))`
   - Redis慢查询: `redis_slowlog_length`

2. **MongoDB性能面板**：
   - MongoDB操作数: `rate(mongodb_ss_opcounters_total[5m])`
   - MongoDB连接数: `mongodb_ss_connections`
   - MongoDB内存使用: `mongodb_ss_mem_resident`

3. **系统资源面板**：
   - 磁盘使用率: `(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100`
   - 网络流量: `rate(node_network_receive_bytes_total[5m])`, `rate(node_network_transmit_bytes_total[5m])`
   - 磁盘I/O: `rate(node_disk_read_bytes_total[5m])`, `rate(node_disk_written_bytes_total[5m])`

#### 6. 快速导入脚本

**自动导入仪表板脚本** (`import_dashboards.sh`)：

```bash
#!/bin/bash
# Grafana仪表板自动导入脚本

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="LSYgrafanaadmin2025"

echo "=== 导入Grafana仪表板 ==="

# 检查Grafana可用性
if ! curl -s "$GRAFANA_URL/api/health" >/dev/null; then
    echo "❌ Grafana不可访问: $GRAFANA_URL"
    exit 1
fi

# 导入常用仪表板
dashboards=(
    "1860:Node Exporter Full"
    "763:Redis Dashboard" 
    "2583:MongoDB Dashboard"
    "3662:Prometheus Stats"
)

for dashboard_info in "${dashboards[@]}"; do
    IFS=':' read -r dashboard_id dashboard_name <<< "$dashboard_info"
    
    echo "导入仪表板: $dashboard_name (ID: $dashboard_id)"
    
    # 下载仪表板JSON
    dashboard_json=$(curl -s "https://grafana.com/api/dashboards/$dashboard_id/revisions/latest/download")
    
    if [ $? -eq 0 ] && [ -n "$dashboard_json" ]; then
        # 准备导入数据
        import_data=$(echo "$dashboard_json" | jq '{
          dashboard: (. + {id: null}),
          overwrite: true,
          inputs: [
            {
              name: "DS_PROMETHEUS",
              type: "datasource",
              pluginId: "prometheus",
              value: "Prometheus"
            }
          ]
        }')
        
        # 导入仪表板
        response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -d "$import_data" \
            "$GRAFANA_URL/api/dashboards/import" \
            -u "$GRAFANA_USER:$GRAFANA_PASS")
        
        if echo "$response" | jq -e '.id' >/dev/null 2>&1; then
            echo "✅ $dashboard_name 导入成功"
        else
            echo "❌ $dashboard_name 导入失败: $response"
        fi
    else
        echo "❌ 无法下载 $dashboard_name"
    fi
    
    sleep 2  # 避免请求过于频繁
done

echo "=== 仪表板导入完成 ==="
echo "访问Grafana查看仪表板: $GRAFANA_URL/dashboards"
```

**使用说明**：

```bash
# 赋予执行权限
chmod +x import_dashboards.sh

# 运行导入脚本
./import_dashboards.sh
```

### 数据库特定问题排查

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

### 监控系统故障排查

#### Prometheus容器启动问题

1. **权限拒绝错误**：

```bash
# 问题症状：Prometheus容器不断重启，日志显示权限错误
docker logs prometheus

# 典型错误信息：
# level=error ts=2024-01-01T12:00:00.000Z caller=main.go msg="Error opening query logger file" file=/prometheus/queries.active err="open /prometheus/queries.active: permission denied"

# 解决方案：修复目录权限
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/data
sudo chmod -R 755 /home/lsyzt/ZTZT/monitoring/

# 重启容器
docker restart prometheus
```

2. **配置文件语法错误**：

```bash
# 验证Prometheus配置文件语法
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml

# 验证告警规则语法
docker exec prometheus promtool check rules /etc/prometheus/rules/database_alerts.yml

# 修复配置后重新载入（无需重启）
docker exec prometheus kill -HUP 1
```

3. **目标连接失败**：

```bash
# 检查Prometheus目标状态
curl http://localhost:9090/api/v1/targets

# 手动测试各个exporter连接
curl http://localhost:9216/metrics  # MongoDB Exporter
curl http://localhost:9100/metrics  # Node Exporter
curl http://localhost:9121/metrics  # Redis Exporter

# 检查网络连接
netstat -tlnp | grep -E ':(9090|9100|9121|9216|9187|9093)'
```

#### MongoDB Exporter问题

1. **版本兼容性问题**：

```bash
# 问题：latest版本连接MongoDB失败
# 解决：使用固定版本percona/mongodb_exporter:0.40.0

# 停止并删除失效容器
docker stop mongodb_exporter
docker rm mongodb_exporter

# 重新部署固定版本
docker run -d --name mongodb_exporter \
  --network host \
  --restart unless-stopped \
  percona/mongodb_exporter:0.40.0 \
  --mongodb.uri=mongodb://localhost:27017 \
  --web.listen-address=:9216
```

2. **MongoDB连接认证问题**：

```bash
# 如果MongoDB启用了认证，更新连接URI
docker stop mongodb_exporter
docker rm mongodb_exporter

# 使用认证连接
docker run -d --name mongodb_exporter \
  --network host \
  --restart unless-stopped \
  percona/mongodb_exporter:0.40.0 \
  --mongodb.uri="mongodb://username:password@localhost:27017/admin" \
  --web.listen-address=:9216
```

#### Grafana问题

1. **数据源连接失败**：

```bash
# 问题：Grafana无法连接到Prometheus
# 检查Prometheus服务状态
docker logs prometheus
curl http://localhost:9090/api/v1/query?query=up

# 在Grafana中配置数据源时使用：
# URL: http://localhost:9090 （如果Grafana和Prometheus在同一主机）
# 或使用容器间通信：http://prometheus:9090
```

2. **仪表板导入失败**：

```bash
# 手动下载仪表板JSON文件
wget -O mongodb-dashboard.json https://grafana.com/api/dashboards/7353/revisions/5/download
wget -O node-exporter-dashboard.json https://grafana.com/api/dashboards/1860/revisions/22/download

# 通过文件导入而不是ID导入
# 登录Grafana → Import → Upload JSON file
```

#### 完整部署验证脚本

创建监控系统验证脚本：

```bash
#!/bin/bash
# 保存为 /home/lsyzt/ZTZT/monitoring/verify_monitoring.sh

echo "=== AI中台监控系统验证脚本 ==="

# 1. 检查目录和权限
echo "检查目录结构..."
directories=(
    "/home/lsyzt/ZTZT/monitoring/prometheus"
    "/home/lsyzt/ZTZT/monitoring/data"
    "/home/lsyzt/ZTZT/monitoring/grafana"
    "/home/lsyzt/ZTZT/monitoring/alertmanager"
)

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir 存在"
        ls -la "$dir"
    else
        echo "✗ $dir 不存在，正在创建..."
        sudo mkdir -p "$dir"
    fi
done

# 2. 修复权限
echo "修复权限..."
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/data
sudo chown -R 472:472 /home/lsyzt/ZTZT/monitoring/grafana
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/alertmanager
sudo chmod -R 755 /home/lsyzt/ZTZT/monitoring/

# 3. 检查容器状态
echo "检查容器状态..."
containers=("prometheus" "grafana" "alertmanager" "mongodb_exporter" "node_exporter" "redis_exporter")

for container in "${containers[@]}"; do
    if docker ps -q -f name="$container" | grep -q .; then
        status=$(docker inspect -f '{{.State.Status}}' "$container")
        echo "✓ $container: $status"
    else
        echo "✗ $container: 未运行"
    fi
done

# 4. 检查端口监听
echo "检查端口监听..."
ports=(9090 3000 9093 9216 9100 9121)

for port in "${ports[@]}"; do
    if netstat -tlnp | grep ":$port " > /dev/null; then
        echo "✓ 端口 $port 正在监听"
    else
        echo "✗ 端口 $port 未监听"
    fi
done

# 5. 测试HTTP端点
echo "测试HTTP端点..."
endpoints=(
    "http://localhost:9090/api/v1/targets"
    "http://localhost:3000/api/health"
    "http://localhost:9093/-/healthy"
    "http://localhost:9216/metrics"
    "http://localhost:9100/metrics"
)

for endpoint in "${endpoints[@]}"; do
    if curl -s -o /dev/null -w "%{http_code}" "$endpoint" | grep -q "200"; then
        echo "✓ $endpoint 可访问"
    else
        echo "✗ $endpoint 不可访问"
    fi
done

# 6. 检查Prometheus目标状态
echo "检查Prometheus目标状态..."
if command -v jq > /dev/null; then
    curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"'
else
    echo "安装jq以获得详细的目标状态：sudo apt install jq"
    curl -s http://localhost:9090/api/v1/targets
fi

echo "=== 验证完成 ==="
```

#### 监控系统重新部署脚本

如果需要完全重新部署监控系统：

```bash
#!/bin/bash
# 保存为 /home/lsyzt/ZTZT/monitoring/redeploy_monitoring.sh

echo "=== 重新部署AI中台监控系统 ==="

# 1. 停止并删除现有容器
echo "停止现有监控容器..."
containers=("prometheus" "grafana" "alertmanager" "mongodb_exporter" "node_exporter" "redis_exporter")

for container in "${containers[@]}"; do
    if docker ps -q -f name="$container" | grep -q .; then
        echo "停止容器: $container"
        docker stop "$container"
        docker rm "$container"
    fi
done

# 2. 清理和重建目录
echo "清理并重建目录..."
sudo rm -rf /home/lsyzt/ZTZT/monitoring/prometheus/data/*
sudo rm -rf /home/lsyzt/ZTZT/monitoring/grafana/*

# 重新创建目录结构
sudo mkdir -p /home/lsyzt/ZTZT/monitoring/{prometheus/{data,rules},grafana,alertmanager}

# 3. 设置正确权限
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/data
sudo chown -R 472:472 /home/lsyzt/ZTZT/monitoring/grafana
sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/alertmanager
sudo chmod -R 755 /home/lsyzt/ZTZT/monitoring/

# 4. 重新部署容器（按顺序）
echo "重新部署监控容器..."

# Node Exporter
docker run -d --name node_exporter \
  --network host \
  --restart unless-stopped \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter:latest \
  --path.rootfs=/host

# MongoDB Exporter
docker run -d --name mongodb_exporter \
  --network host \
  --restart unless-stopped \
  percona/mongodb_exporter:0.40.0 \
  --mongodb.uri=mongodb://localhost:27017 \
  --web.listen-address=:9216

# Redis Exporter (如果有Redis)
docker run -d --name redis_exporter \
  --network host \
  --restart unless-stopped \
  -e REDIS_ADDR=redis://localhost:6379 \
  oliver006/redis_exporter:latest

# Prometheus
docker run -d --name prometheus \
  --network host \
  --restart unless-stopped \
  -v /home/lsyzt/ZTZT/monitoring/prometheus:/etc/prometheus \
  -v /home/lsyzt/ZTZT/monitoring/data:/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.console.templates=/etc/prometheus/consoles \
  --storage.tsdb.retention.time=200h \
  --web.enable-lifecycle

# AlertManager
docker run -d --name alertmanager \
  --network host \
  --restart unless-stopped \
  -v /home/lsyzt/ZTZT/monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager:latest \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/alertmanager \
  --web.external-url=http://localhost:9093

# Grafana
docker run -d --name grafana \
  --network host \
  --restart unless-stopped \
  -v /home/lsyzt/ZTZT/monitoring/grafana:/var/lib/grafana \
  -e "GF_SECURITY_ADMIN_PASSWORD=LSYgrafanaadmin2025" \
  grafana/grafana:latest

echo "等待服务启动..."
sleep 30

# 5. 验证部署
echo "验证部署状态..."
./verify_monitoring.sh

echo "=== 重新部署完成 ==="
echo "访问地址："
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000 (admin/LSYgrafanaadmin2025)"
echo "- AlertManager: http://localhost:9093"
```

#### 常见问题快速解决

**问题1：Prometheus容器启动后立即退出**
```bash
# 查看错误日志
docker logs prometheus

# 常见原因和解决：
# 1. 权限问题：sudo chown -R 65534:65534 /home/lsyzt/ZTZT/monitoring/prometheus
# 2. 配置语法错误：检查prometheus.yml语法
# 3. 端口冲突：netstat -tlnp | grep 9090
```

**问题2：MongoDB Exporter连接失败**
```bash
# 测试MongoDB连接
mongosh --eval "db.adminCommand('ping')"

# 检查MongoDB是否监听正确端口
netstat -tlnp | grep 27017

# 使用正确的连接URI重新部署exporter
```

**问题3：Grafana无法访问Prometheus数据源**
```bash
# 测试Prometheus API
curl http://localhost:9090/api/v1/query?query=up

# 在Grafana数据源配置中使用HTTP URL: http://localhost:9090
# 测试连接时确保Prometheus正在运行
```

通过以上配置和故障排查步骤，可以确保AI中台监控系统的稳定运行和有效监控。
