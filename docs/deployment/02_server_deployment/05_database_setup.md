<!-- filepath: d:\Study\StudyFiles\PyFiles\LSY\ZTZT\docs\deployment\05_database_setup_new.md -->
# AI 中台 - 数据库系统概览

## 详细部署与运维文档

本文档的详细部署指南、配置说明以及运维管理方案分别位于 `database_deployment` 目录下的专题文档中。请参考以下链接获取具体信息：

- **数据库部署与配置：**
    - [PostgreSQL 部署指南](./database_deployment/01_postgresql_deployment.md)
    - [MongoDB 部署指南](./database_deployment/02_mongodb_deployment.md)
    - [Weaviate 部署指南](./database_deployment/03_weaviate_deployment.md)
    - [Redis 部署指南](./database_deployment/04_redis_deployment.md)
    - [Kafka 部署指南](./database_deployment/05_kafka_deployment.md)
- **数据库运维管理：**
    - [监控与日常维护](./database_deployment/06_monitoring_maintenance.md)
    - [高可用性与容灾](./database_deployment/07_high_availability.md)
    - [备份与恢复策略](./database_deployment/08_backup_restore.md)

## 概述

本文档提供 AI 中台项目所用数据库系统的概览与架构设计。所有详细的部署指南和配置说明均位于 `database_deployment` 目录下的专题文档中。

## 数据库技术栈

AI 中台采用多数据库架构，以满足不同类型数据的存储和处理需求：

| 数据库 | 版本 | 主要用途 | 详细文档 |
|-------|------|---------|----------|
| PostgreSQL | 16 | 结构化数据 | [部署指南](./database_deployment/01_postgresql_deployment.md) |
| MongoDB | 6.0 | 半结构化数据 | [部署指南](./database_deployment/02_mongodb_deployment.md) |
| Weaviate | 1.22 | 向量数据 | [部署指南](./database_deployment/03_weaviate_deployment.md) |
| Redis | 7.0 | 缓存系统 | [部署指南](./database_deployment/04_redis_deployment.md) |
| Kafka | 3.6 | 消息队列 | [部署指南](./database_deployment/05_kafka_deployment.md) |

## 数据分布

每种数据库存储特定类型的数据：

-   **PostgreSQL**: 结构化数据，采用模式(Schema)分区
    - 主要模式：`public`, `auth`, `data_platform`, `algo_platform`, `model_platform`, `service_platform`
-   **MongoDB**: 半结构化或非结构化数据
    - 主要集合：`system_logs`, `configurations`, `task_status_cache`
-   **Weaviate**: 向量数据
    - 主要类：`Document`, `Image`, `ModelData`
-   **Redis**: 缓存和临时数据
    - 键空间前缀：`session:`, `token:`, `cache:`, `rate:api:`, `lock:`, `queue:`, `pubsub:`, `stats:`
-   **Kafka**: 消息和事件流
    - 主要主题：`data-ingestion`, `model-events`, `system-logs`

## 表结构和关系

本节概述了各个数据库中主要的表、集合和类及其关键属性。详细的建表语句或更具体的字段定义（如数据类型、约束等）应参考各自数据库在 `database_deployment` 文件夹下的详细部署文档。

数据库的整体关系图已在本文件的 `数据库关系图` 部分通过 Mermaid 图表展示。

### PostgreSQL 表结构

PostgreSQL 用于存储结构化数据，以下是主要模式中的核心表示例：

| 模式 (Schema)      | 表名 (Table)          | 主要属性 (Key Attributes)                                                                 | 备注                               |
|--------------------|-----------------------|-------------------------------------------------------------------------------------------|------------------------------------|
| `auth`             | `users`               | `id`, `username`, `email`, `password_hash`, `is_active`, `date_joined`, `organization_id` | 用户账户信息                       |
| `auth`             | `groups`              | `id`, `name`, `description`                                                               | 用户组                             |
| `auth`             | `permissions`         | `id`, `name`, `codename`                                                                  | 操作权限                           |
| `data_platform`    | `datasets`            | `id`, `name`, `description`, `source_type`, `created_by`, `created_at`, `is_active`        | 数据集信息                         |
| `data_platform`    | `data_items`          | `id`, `dataset_id`, `content_reference`, `metadata`, `created_at`                         | 单条数据记录                       |
| `data_platform`    | `text_embeddings`     | `id`, `dataset_id`, `record_id`, `text_content`, `embedding` (vector)                     | 文本向量数据 (示例)                |
| `algo_platform`    | `algorithms`          | `id`, `name`, `version`, `description`, `entry_point`, `created_at`                       | 算法信息                           |
| `model_platform`   | `models`              | `id`, `name`, `version`, `description`, `artifact_path`, `algorithm_id`, `created_at`     | 模型信息                           |
| `model_platform`   | `model_versions`      | `id`, `model_id`, `version_tag`, `artifact_url`, `metrics`, `created_at`                  | 模型版本                           |
| `service_platform` | `deployed_services`   | `id`, `name`, `endpoint_url`, `model_version_id`, `status`, `created_at`                  | 已部署的模型服务                   |

### MongoDB 集合结构

MongoDB 用于存储半结构化或非结构化数据，以下是主要集合示例：

| 集合 (Collection)    | 主要属性 (Key Attributes)                                                              | 备注                       |
|----------------------|----------------------------------------------------------------------------------------|----------------------------|
| `system_logs`        | `_id`, `timestamp`, `level`, `service_name`, `message`, `details` (object)             | 系统运行日志               |
| `configurations`     | `_id`, `component_name`, `environment`, `version`, `config_data` (object), `is_active` | 系统各组件的配置信息       |
| `task_status_cache`  | `_id`, `task_id`, `task_type`, `status`, `progress`, `result_summary`, `last_updated`   | 异步任务状态及缓存         |
| `audit_trails`       | `_id`, `timestamp`, `user_id`, `action`, `resource_type`, `resource_id`, `details`      | 用户操作审计日志 (示例)    |

### Weaviate 类结构

Weaviate 用于存储向量数据，以下是主要类示例：

| 类 (Class)   | 主要属性 (Key Properties)                                                                    | 向量化模块 (Vectorizer) | 备注                         |
|--------------|----------------------------------------------------------------------------------------------|-------------------------|------------------------------|
| `Document`   | `title`, `content`, `source`, `category`, `creationDate`, `author`, `tags`                   | `text2vec-transformers` | 文档及其向量表示             |
| `Image`      | `filename`, `caption`, `mimeType`, `imageUrl`, `resolution`, `tags`, `uploadDate`            | `img2vec-neural`        | 图片及其向量表示             |
| `ModelData`  | `modelName`, `modelDescription`, `framework`, `metrics` (text), `useCase`, `version`, `createdBy` | `text2vec-transformers` | 机器学习模型元数据及描述向量 |

## 运维管理

| 管理方面 | 详细文档 |
|---------|----------|
| 监控与日常维护 | [监控与维护](./database_deployment/06_monitoring_maintenance.md) |
| 高可用性配置 | [高可用性与容灾](./database_deployment/07_high_availability.md) |
| 备份与恢复策略 | [备份与恢复](./database_deployment/08_backup_restore.md) |

## 资源规划参考

以下是各数据库系统的基本资源需求建议，实际配置应根据业务负载进行调整：

| 数据库 | CPU | 内存 | 存储 | 网络 |
|-------|-----|------|------|------|
| PostgreSQL | 4核+ | 8GB+ | SSD, 50GB+ | 1Gbps |
| MongoDB | 2核+ | 4GB+ | SSD, 20GB+ | 1Gbps |
| Weaviate | 4核+ | 8GB+ | SSD, 20GB+ | 1Gbps |
| Redis | 2核+ | 4GB+ | SSD, 10GB+ | 1Gbps |
| Kafka | 4核+ | 8GB+ | SSD, 50GB+ | 1Gbps |


## 后续部署步骤

完成数据库部署后，建议按以下顺序继续：

1. 部署权限管理系统 ([07_permission_management.md](./07_permission_management.md))
2. 部署 Django REST 后端 ([06_django_rest_setup.md](./06_django_rest_setup.md))
3. 部署 NodeJS 前端 ([08_nodejs_setup.md](./08_nodejs_setup.md))

更多数据库设计详情，请参考 [数据库设计文档](../development/database_design.md)
