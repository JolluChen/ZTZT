# 数据库备份与恢复方案

本文档详细说明 AI 中台项目各类数据库的备份与恢复方案，包括 PostgreSQL、MongoDB、Weaviate、Redis 和 Kafka 数据的保护策略。

## 1. 备份策略概述

### 1.1 分层备份策略

AI 中台采用三层备份策略，确保数据安全：

- **日常增量备份**：每天进行增量备份，捕获当日变化
- **周备份**：每周进行一次完整备份
- **月度归档备份**：每月进行一次完整备份并归档长期存储

### 1.2 备份存储位置

- **本地备份**：存储在本地备份服务器上，用于快速恢复
- **远程备份**：复制到远程站点或云存储，防止本地灾难
- **离线备份**：关键数据定期创建离线备份，防止网络安全事件

### 1.3 备份保留策略

| 备份类型 | 保留期限 | 存储位置 |
|---------|---------|---------|
| 日常增量备份 | 14 天 | 本地 + 远程 |
| 周备份 | 2 个月 | 本地 + 远程 |
| 月度归档备份 | 1 年 | 本地 + 远程 + 离线 |

## 2. PostgreSQL 备份与恢复

### 2.1 使用 pg_dump 进行逻辑备份

```bash
# 单个数据库备份
pg_dump -h <host> -p 5432 -U postgres -d ai_platform -F c > /backup/postgres/ai_platform_$(date +%Y%m%d).dump

# 备份特定模式
pg_dump -h <host> -p 5432 -U postgres -d ai_platform -n model_platform -F c > /backup/postgres/model_platform_$(date +%Y%m%d).dump

# 全部数据库备份
pg_dumpall -h <host> -p 5432 -U postgres > /backup/postgres/all_databases_$(date +%Y%m%d).sql
```

### 2.2 使用 pg_basebackup 进行物理备份

```bash
# 物理备份（推荐用于生产环境）
pg_basebackup -h <host> -p 5432 -U postgres -D /backup/postgres/basebackup_$(date +%Y%m%d) -Ft -z -P
```

### 2.3 PostgreSQL 还原方法

```bash
# 还原自定义格式备份
pg_restore -h <host> -p 5432 -U postgres -d ai_platform /backup/postgres/ai_platform_20230101.dump

# 还原 SQL 文件
psql -h <host> -p 5432 -U postgres -d ai_platform -f /backup/postgres/all_databases_20230101.sql

# 从物理备份还原
# 1. 停止 PostgreSQL 服务
# 2. 清空数据目录
# 3. 复制备份到数据目录
# 4. 设置正确的权限
# 5. 重启服务
```

### 2.4 使用 WAL 归档进行时间点恢复 (PITR)

```bash
# 在 postgresql.conf 中启用 WAL 归档
wal_level = replica
archive_mode = on
archive_command = 'cp %p /archive/pg_wal/%f'

# 时间点恢复步骤
# 1. 创建 recovery.conf 或 recovery.signal 文件（取决于 PostgreSQL 版本）
# 2. 指定要恢复的时间点或事务 ID
# 3. 启动服务器进行恢复
```

## 3. MongoDB 备份与恢复

### 3.1 使用 mongodump 进行备份

```bash
# 备份整个数据库
mongodump --host <host> --port 27017 --username <user> --password <password> --authenticationDatabase admin --out /backup/mongo/$(date +%Y%m%d)

# 备份特定集合
mongodump --host <host> --port 27017 --username <user> --password <password> --authenticationDatabase admin --db ai_platform --collection system_logs --out /backup/mongo/logs_$(date +%Y%m%d)
```

### 3.2 使用 oplog 进行时间点备份

```bash
# 备份 oplog
mongodump --host <host> --port 27017 --username <user> --password <password> --authenticationDatabase admin --db local --collection oplog.rs --out /backup/mongo/oplog_$(date +%Y%m%d)
```

### 3.3 MongoDB 数据还原

```bash
# 全量还原
mongorestore --host <host> --port 27017 --username <user> --password <password> --authenticationDatabase admin /backup/mongo/20230101/

# 还原特定数据库
mongorestore --host <host> --port 27017 --username <user> --password <password> --authenticationDatabase admin --db ai_platform /backup/mongo/20230101/ai_platform/
```

### 3.4 使用 mongoDB Cloud Manager 或 Ops Manager（企业版）

对于生产环境，建议使用 MongoDB 的官方管理工具，它们提供更丰富的备份和监控功能。

## 4. Weaviate 向量数据库备份

### 4.1 使用 Weaviate 备份 API

```bash
# 创建备份
curl -X POST "http://<weaviate-host>:8080/v1/backups" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "backup-$(date +%Y%m%d)",
    "backend": "filesystem",
    "include_classes": ["Document", "Image", "ModelData"],
    "backend_config": {
      "location": "/backup/weaviate"
    }
  }'

# 检查备份状态
curl -X GET "http://<weaviate-host>:8080/v1/backups/backup-$(date +%Y%m%d)" | jq
```

### 4.2 Weaviate 恢复流程

```bash
# 恢复备份
curl -X POST "http://<weaviate-host>:8080/v1/backups/backup-20230101/restore" \
  -H "Content-Type: application/json" \
  -d '{
    "backend": "filesystem",
    "backend_config": {
      "location": "/backup/weaviate"
    }
  }'

# 检查恢复状态
curl -X GET "http://<weaviate-host>:8080/v1/backups/backup-20230101/restore" | jq
```

## 5. Redis 缓存备份

### 5.1 使用 RDB 快照备份

```bash
# 手动触发 RDB 快照
redis-cli -h <host> -p 6379 -a <password> SAVE

# 配置自动 RDB 快照（在 redis.conf 中）
save 900 1
save 300 10
save 60 10000
```

### 5.2 使用 AOF 日志备份

```bash
# 在 redis.conf 中启用 AOF
appendonly yes
appendfsync everysec
```

### 5.3 Redis 备份文件导出

```bash
# 复制 RDB 文件
cp /var/lib/redis/dump.rdb /backup/redis/dump_$(date +%Y%m%d).rdb

# 复制 AOF 文件
cp /var/lib/redis/appendonly.aof /backup/redis/appendonly_$(date +%Y%m%d).aof
```

### 5.4 Redis 恢复流程

```bash
# 从 RDB 文件恢复
# 1. 停止 Redis 服务
# 2. 复制备份文件到 Redis 数据目录
cp /backup/redis/dump_20230101.rdb /var/lib/redis/dump.rdb
# 3. 重启 Redis 服务

# 从 AOF 文件恢复（如启用）
# 1. 停止 Redis 服务
# 2. 复制 AOF 备份到 Redis 数据目录
cp /backup/redis/appendonly_20230101.aof /var/lib/redis/appendonly.aof
# 3. 重启 Redis 服务
```

## 6. Kafka 消息队列备份

### 6.1 备份 Kafka 主题数据

```bash
# 使用 Kafka 内置工具导出数据
kafka-console-consumer.sh --bootstrap-server <kafka-host>:9092 \
  --topic data-ingestion --from-beginning \
  --max-messages <count> \
  --consumer.config /path/to/consumer.properties > /backup/kafka/data-ingestion_$(date +%Y%m%d).json
```

### 6.2 备份 Kafka 配置

```bash
# 复制 Kafka 配置文件
cp -r /etc/kafka /backup/kafka/config_$(date +%Y%m%d)

# 导出主题配置
kafka-topics.sh --bootstrap-server <kafka-host>:9092 \
  --describe --topic data-ingestion > /backup/kafka/data-ingestion_config_$(date +%Y%m%d).txt
```

### 6.3 Kafka 恢复流程

```bash
# 恢复主题数据
kafka-console-producer.sh --bootstrap-server <kafka-host>:9092 \
  --topic data-ingestion < /backup/kafka/data-ingestion_20230101.json
```

## 7. 自动化备份脚本示例

### 7.1 全系统备份脚本

```bash
#!/bin/bash
# 文件名: backup_all_databases.sh

# 设置变量
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d)
POSTGRES_USER="postgres"
MONGO_USER="admin"
MONGO_PASS="password"
REDIS_HOST="localhost"
WEAVIATE_HOST="localhost"
KAFKA_HOST="localhost"

# 创建备份目录
mkdir -p $BACKUP_DIR/{postgres,mongo,weaviate,redis,kafka}/$DATE

# PostgreSQL 备份
echo "开始 PostgreSQL 备份..."
pg_dump -U $POSTGRES_USER -d ai_platform -F c > $BACKUP_DIR/postgres/$DATE/ai_platform.dump

# MongoDB 备份
echo "开始 MongoDB 备份..."
mongodump --host localhost --port 27017 --username $MONGO_USER --password $MONGO_PASS --authenticationDatabase admin --out $BACKUP_DIR/mongo/$DATE

# Weaviate 备份
echo "开始 Weaviate 备份..."
curl -X POST "http://$WEAVIATE_HOST:8080/v1/backups" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "backup-'$DATE'",
    "backend": "filesystem",
    "backend_config": {
      "location": "'$BACKUP_DIR'/weaviate/'$DATE'"
    }
  }'

# Redis 备份
echo "开始 Redis 备份..."
redis-cli -h $REDIS_HOST SAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis/$DATE/dump.rdb

# Kafka 配置备份
echo "开始 Kafka 配置备份..."
cp -r /etc/kafka $BACKUP_DIR/kafka/$DATE/config

echo "备份完成！"
```

### 7.2 设置定时备份任务

```bash
# 添加到 crontab
# 每天凌晨 2 点执行增量备份
0 2 * * * /path/to/backup_all_databases.sh

# 每周日凌晨 1 点执行周备份
0 1 * * 0 /path/to/weekly_backup.sh

# 每月 1 日凌晨 0 点执行月度归档备份
0 0 1 * * /path/to/monthly_backup.sh
```

## 8. 灾难恢复流程

### 8.1 恢复优先级

1. **关键业务数据**：首先恢复 PostgreSQL 中的核心业务数据
2. **应用状态**：恢复 MongoDB 中的应用状态数据
3. **缓存系统**：重建 Redis 缓存
4. **消息队列**：重建 Kafka 消息队列
5. **向量数据**：恢复 Weaviate 向量数据

### 8.2 完整恢复流程

1. 评估损失范围
2. 准备新的基础设施（如果需要）
3. 恢复数据库软件和配置
4. 按优先级顺序恢复数据
5. 验证数据完整性
6. 测试应用功能
7. 切换到生产环境

### 8.3 恢复时间目标 (RTO) 和恢复点目标 (RPO)

| 数据库类型 | RTO（恢复时间目标） | RPO（恢复点目标） |
|-----------|-------------------|-------------------|
| PostgreSQL | 1-2 小时 | < 15 分钟 |
| MongoDB | 2-3 小时 | < 1 小时 |
| Weaviate | 3-4 小时 | < 24 小时 |
| Redis | 30 分钟 | 可重建，非关键 |
| Kafka | 1 小时 | 可重建，消息可能丢失 |

## 9. 最佳实践

1. **定期测试恢复流程**：每季度至少进行一次恢复演练
2. **验证备份完整性**：使用校验和工具验证备份文件的完整性
3. **监控备份过程**：设置备份完成通知和备份失败警报
4. **文档化**：记录每次备份和恢复操作，包括时间、范围和结果
5. **安全存储**：备份介质加密存储，访问控制严格限制
6. **异地备份**：关键备份数据存储在不同地理位置
7. **自动化**：尽可能自动化备份和验证过程，减少人为错误

## 10. 备份工具推荐

| 数据库 | 企业级备份工具 | 开源备份工具 |
|--------|--------------|-------------|
| PostgreSQL | Barman, pgBackRest | pg_dump, WAL-G |
| MongoDB | MongoDB Cloud Manager | mongodump, mgob |
| Weaviate | 官方 Backup API | 自定义脚本 |
| Redis | Redis Enterprise | redis-cli, redis-dump |
| Kafka | Conduktor, Lenses.io | kafka-backup (开源) |

---

本文档提供了 AI 中台各数据库系统的备份与恢复方案。根据实际部署环境和业务需求，可能需要对上述方案进行适当调整。对于生产环境，强烈建议设置自动化备份流程并定期测试恢复功能。
