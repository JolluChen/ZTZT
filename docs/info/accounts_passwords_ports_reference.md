# AI 中台项目 - 账号密码与端口| 8085 | GPUStack 管理 | HTTP | 🟢 运行中 | `http://localhost:18085` | GPU管理平台 |
| 40002 | GPUStack vLLM | HTTP | 🟢 运行中 | `http://localhost:40002` | vLLM模型API |用汇总表

> **文档说明**: 本文档汇总了整个 AI 中台项目中所有服务的账号密码、端口使用情况，便于运维管理和故障排查。  
> **安全提醒**: 生产环境部署时请务必修改所有默认密码！  
> **更新日期**: 2025年6月21日

---

## 🚀 快速参考汇总表

### 📋 所有端口汇总表
| 端口 | 服务名称 | 协议 | 状态 | 访问地址 | 说明 |
|------|----------|------|------|----------|------|
| 5432 | PostgreSQL 主数据库 | TCP | 🟢 运行中 | `localhost:5432` | 数据库服务 |
| 5433 | PostgreSQL Dify | TCP | 🟢 运行中 | `localhost:5433` | Dify专用数据库 |
| 6379 | Redis 主缓存 | TCP | 🟢 运行中 | `localhost:6379` | 缓存服务 |
| 6380 | Redis Dify | TCP | 🟢 运行中 | `localhost:6380` | Dify专用缓存 |
| 8000 | Django 后端 | HTTP | 🟢 运行中 | `http://192.168.110.88:8000` | 应用服务 |
| 8001 | Dify Web | HTTP | 🟢 运行中 | `http://localhost:8001` | Dify Web界面 |
| 18085 | GPUStack 管理 | HTTP | 🟢 运行中 | `http://localhost:18085` | GPU管理平台 |
| 8081 | Weaviate | HTTP | 🟢 运行中 | `http://localhost:8081` | 向量数据库 |
| 8100 | Triton HTTP | HTTP | 🟢 运行中 | `http://localhost:8100` | 推理服务 |
| 8101 | Triton GRPC | GRPC | 🟢 运行中 | `localhost:8101` | 推理服务 |
| 8102 | Triton Metrics | HTTP | 🟢 运行中 | `http://localhost:8102` | 推理服务指标 |
| 9000 | MinIO API | HTTP | 🟢 运行中 | `http://localhost:9000` | 对象存储API |
| 9001 | MinIO Console | HTTP | 🟢 运行中 | `http://localhost:9001` | 对象存储控制台 |
| 9090 | Prometheus 主监控 | HTTP | 🟢 运行中 | `http://localhost:9090` | 监控数据收集 |
| 9091 | Prometheus GPU | HTTP | 🟢 运行中 | `http://localhost:9091` | GPU监控数据 |
| 9093 | AlertManager | HTTP | 🟢 运行中 | `http://localhost:9093` | 告警管理 |
| 9100 | Node Exporter | HTTP | 🟢 运行中 | `http://localhost:9100` | 系统指标 |
| 9121 | Redis Exporter | HTTP | 🟢 运行中 | `http://localhost:9121` | Redis指标 |
| 9187 | PostgreSQL Exporter | HTTP | 🟢 运行中 | `http://localhost:9187` | PostgreSQL指标 |
| 9200 | OpenSearch | HTTPS | 🟢 运行中 | `https://localhost:9200` | 日志搜索 |
| 9216 | MongoDB Exporter | HTTP | 🟢 运行中 | `http://localhost:9216` | MongoDB指标 |
| 9400 | DCGM Exporter | HTTP | 🟢 运行中 | `http://localhost:9400` | GPU指标 |
| 3000 | Grafana 主监控 | HTTP | 🟢 运行中 | `http://192.168.110.88:3000` | 监控仪表盘 |
| 3001 | OpenWebUI | HTTP | 🟢 运行中 | `http://localhost:3001` | AI Web界面 |
| 3003 | Grafana GPU | HTTP | 🟢 运行中 | `http://localhost:3003` | GPU监控仪表盘 |
| 5001 | Dify API | HTTP | 🟢 运行中 | `http://localhost:5001` | Dify API服务 |
| 5555 | Flower Celery | HTTP | 🟢 运行中 | `http://localhost:5555` | 任务监控 |
| 11434 | Ollama | HTTP | 🟢 运行中 | `http://localhost:11434` | LLM服务 |
| 27017 | MongoDB | TCP | 🟢 运行中 | `localhost:27017` | 文档数据库 |

### 🔐 所有账号密码汇总表
| 系统/服务 | 用户名 | 密码 | 角色/权限 | 访问地址 | 状态 |
|----------|--------|------|-----------|----------|------|
| PostgreSQL 主数据库 | postgres | ai-platform-2024 | 超级管理员 | `localhost:5432` | ✅ 活跃 |
| PostgreSQL 主数据库 | aiuser | aiuser-2024 | 应用用户 | `localhost:5432` | ✅ 活跃 |
| PostgreSQL Django | django_user | django_password_2024 | 应用专用 | `localhost:5432` | ✅ 活跃 |
| PostgreSQL Django | django_readonly | readonly_pass_2024 | 只读用户 | `localhost:5432` | ✅ 活跃 |
| PostgreSQL Dify | dify_user | dify_password | 应用专用 | `localhost:5433` | ✅ 活跃 |
| MongoDB | root | changeThisToSecurePassword | 超级管理员 | `localhost:27017` | ✅ 活跃 |
| MongoDB | ai_platform_user | changeThisToSecurePassword | 应用用户 | `localhost:27017` | ✅ 活跃 |
| MongoDB | readonly_user | readOnlyPassword | 只读用户 | `localhost:27017` | ✅ 活跃 |
| Redis 主缓存 | (无) | redis-2024 | 全部权限 | `localhost:6379` | ✅ 活跃 |
| MinIO | minioadmin | minioadmin | 管理员 | `http://localhost:9001` | ✅ 活跃 |
| MinIO K8s | minioadmin | minioadmin123 | 管理员 | K8s内部 | ✅ 活跃 |
| OpenSearch | admin | OPENsearch@123 | 管理员 | `https://localhost:9200` | ✅ 活跃 |
| Grafana 主监控 | admin | LSYgrafanaadmin2025 | 管理员 | `http://192.168.110.88:3000` | ✅ 活跃 |
| Grafana Docker | admin | admin123 | 管理员 | `http://localhost:3000` | ✅ 活跃 |
| Grafana GPU | admin | gpu_monitor_2025 | 管理员 | `http://localhost:3003` | ✅ 活跃 |
| Django 开发环境 | admin | admin123 | 超级用户 | `http://192.168.110.88:8000/admin/` | ⚠️ 待创建 |
| Django 生产环境 | admin | admin123 | 超级用户 | `http://<IP>:8000/admin/` | ⚠️ 待创建 |
| GPUStack | admin | $w3d9uKKrVGz | 管理员 | `http://localhost:18085` | ✅ 活跃 |
| 审计监控系统 | monitor_admin | Monitor@2024 | 超级用户 | `http://localhost:8000/admin/` | ✅ 活跃 |
| Flower Celery | admin | Monitor@2024 | 管理员 | `http://localhost:5555` | ✅ 活跃 |
| OpenWebUI | (首次设置) | (首次设置) | 管理员 | `http://localhost:3001` | ⚠️ 待设置 |

---

## 📊 1. 数据库系统

### 1.1 PostgreSQL
| 服务实例 | 用户名 | 密码 | 数据库名 | 端口 | 访问地址 | 说明 |
|---------|--------|------|----------|------|----------|------|
| 主数据库 | postgres | ai-platform-2024 | postgres | 5432 | `postgresql.database.svc.cluster.local:5432` | K8s内部访问 |
| 主数据库 | aiuser | aiuser-2024 | ai_platform | 5432 | `localhost:5432` | 端口转发访问 |
| Django生产环境 | django_user | django_password_2024 | ai_platform_django | 5432 | `localhost:5432` | Django专用账号 |
| Django只读 | django_readonly | readonly_pass_2024 | ai_platform_django | 5432 | `localhost:5432` | 只读查询账号 |
| Dify数据库 | dify_user | dify_password | dify | 5433 | `localhost:5433` | Dify专用数据库 |

### 1.2 MongoDB
| 用户名 | 密码 | 数据库名 | 端口 | 访问地址 | 说明 |
|--------|------|----------|------|----------|------|
| root | changeThisToSecurePassword | admin | 27017 | `localhost:27017` | 超级管理员 |
| ai_platform_user | changeThisToSecurePassword | ai_platform | 27017 | `localhost:27017` | 应用专用账号 |
| readonly_user | readOnlyPassword | ai_platform | 27017 | `localhost:27017` | 只读账号 |

### 1.3 Redis
| 实例 | 用户名 | 密码 | 端口 | 访问地址 | 说明 |
|------|--------|------|------|----------|------|
| 主Redis | (无) | redis-2024 | 6379 | `redis-master.database.svc.cluster.local:6379` | K8s内部访问 |
| 主Redis | (无) | redis-2024 | 6379 | `localhost:6379` | 端口转发访问 |
| Dify Redis | (无) | (无密码) | 6380 | `localhost:6380` | Dify专用缓存 |

### 1.4 SQLite (开发环境)
| 数据库文件 | 路径 | 说明 |
|-----------|------|------|
| db.sqlite3 | `/home/lsyzt/ZTZT/minimal-example/backend/db.sqlite3` | Django开发环境数据库 |

---

## 🗄️ 2. 存储系统

### 2.1 MinIO 对象存储
| 用户名 | 密码 | API端口 | 控制台端口 | 访问地址 | 说明 |
|--------|------|---------|------------|----------|------|
| minioadmin | minioadmin | 9000 | 9001 | `http://localhost:9000` | API端点 |
| minioadmin | minioadmin | 9000 | 9001 | `http://localhost:9001` | Web控制台 |
| minioadmin | minioadmin123 | 9000 | 9001 | `minio.minio-ns.svc.cluster.local:9000` | K8s内部访问 |

### 2.2 OpenSearch 日志存储
| 用户名 | 密码 | 端口 | 访问地址 | 说明 |
|--------|------|------|----------|------|
| admin | OPENsearch@123 | 9200 | `https://localhost:9200` | 需要HTTPS |
| admin | OPENsearch@123 | 9200 | `opensearch-cluster-master.logging.svc.cluster.local:9200` | K8s内部访问 |

### 2.3 Weaviate 向量数据库
| 用户名 | 密码 | 端口 | 访问地址 | 说明 |
|--------|------|------|----------|------|
| (无) | (无) | 8081 | `http://localhost:8081` | 匿名访问已启用 |

---

## 📈 3. 监控系统

### 3.1 Grafana 可视化仪表盘
| 部署方式 | 用户名 | 密码 | 端口 | 访问地址 | 说明 |
|---------|--------|------|------|----------|------|
| 系统部署 | admin | LSYgrafanaadmin2025 | 3000 | `http://192.168.110.88:3000` | 主监控实例 |
| Docker部署 | admin | admin123 | 3000 | `http://localhost:3000` | 审计监控实例 |
| GPU监控 | admin | gpu_monitor_2025 | 3003 | `http://localhost:3003` | GPU专用监控 |

### 3.2 Prometheus 监控数据源
| 实例 | 用户名 | 密码 | 端口 | 访问地址 | 说明 |
|------|--------|------|------|----------|------|
| 主Prometheus | 无 | 无 | 9090 | `http://localhost:9090` | 无认证 |
| GPU Prometheus | 无 | 无 | 9091 | `http://localhost:9091` | GPU指标收集 |

### 3.3 监控 Exporters
| 组件 | 端口 | 访问地址 | 说明 |
|------|------|----------|------|
| Node Exporter | 9100 | `http://localhost:9100/metrics` | 系统指标 |
| MongoDB Exporter | 9216 | `http://localhost:9216/metrics` | MongoDB指标 |
| Redis Exporter | 9121 | `http://localhost:9121/metrics` | Redis指标 |
| PostgreSQL Exporter | 9187 | `http://localhost:9187/metrics` | PostgreSQL指标 |
| DCGM Exporter | 9400 | `http://localhost:9400/metrics` | GPU指标 |

### 3.4 AlertManager
| 用户名 | 密码 | 端口 | 访问地址 | 说明 |
|--------|------|------|----------|------|
| 无 | 无 | 9093 | `http://localhost:9093` | 告警管理 |

---

## 🤖 4. AI平台服务

### 4.1 Django 后端管理系统
| 环境 | 用户名 | 密码 | 邮箱 | 端口 | 访问地址 | 状态 |
|------|--------|------|------|------|----------|------|
| 开发环境 | admin | admin123 | admin@aiplatform.com | 8000 | `http://192.168.110.88:8000/admin/` | ⚠️ 待创建 |
| 生产环境 | admin | admin123 | admin@aiplatform.com | 8000 | `http://<服务器IP>:8000/admin/` | ⚠️ 待创建 |

### 4.2 GPUStack 管理平台
| 用户名 | 密码 | 端口 | 访问地址 | 说明 |
|--------|------|------|----------|------|
| admin | $w3d9uKKrVGz | 8080 | `http://localhost:8080` | GPU管理界面 |

### 4.3 Triton Inference Server
| 服务 | 端口 | 访问地址 | 说明 |
|------|------|----------|------|
| HTTP | 8100 | `http://localhost:8100` | HTTP推理API |
| GRPC | 8101 | `localhost:8101` | GRPC推理API |
| Metrics | 8102 | `http://localhost:8102/metrics` | 指标端点 |

### 4.4 Ollama LLM服务
| 服务 | 端口 | 访问地址 | 说明 |
|------|------|----------|------|
| API | 11434 | `http://localhost:11434` | LLM API |

### 4.5 OpenWebUI
| 用户名 | 密码 | 端口 | 访问地址 | 说明 |
|--------|------|------|----------|------|
| (首次设置) | (首次设置) | 3001 | `http://localhost:3001` | Web界面 |

---

## 📦 5. Dify 平台服务

### 5.1 Dify API & Web
| 服务 | 端口 | 访问地址 | 说明 |
|------|------|----------|------|
| API | 5001 | `http://localhost:5001` | Dify API |
| Web | 8001 | `http://localhost:8001` | Dify Web界面 |

---

## 🔧 6. 审计监控系统

### 6.1 专用账号
| 用户名 | 密码 | 用途 | 端口 | 说明 |
|--------|------|------|------|------|
| monitor_admin | Monitor@2024 | 审计监控系统管理 | 8000 | Django超级用户 |

### 6.2 Flower Celery监控
| 用户名 | 密码 | 端口 | 访问地址 | 说明 |
|--------|------|------|----------|------|
| admin | Monitor@2024 | 5555 | `http://localhost:5555` | Celery任务监控 |

---

## 🌐 7. 网络端口使用总览

### 7.1 主要服务端口分配
| 端口范围 | 服务类型 | 具体服务 |
|---------|----------|----------|
| 5432-5433 | 数据库 | PostgreSQL (主/Dify) |
| 6379-6380 | 缓存 | Redis (主/Dify) |
| 8000-8102 | 应用服务 | Django, Dify, Triton |
| 9000-9400 | 存储/监控 | MinIO, Prometheus, 各种Exporter |
| 3000-3003 | 监控界面 | Grafana实例 |
| 11434 | AI服务 | Ollama |
| 27017 | 文档数据库 | MongoDB |

### 7.2 端口冲突避免策略
| 原始端口 | 重映射端口 | 服务 | 原因 |
|---------|------------|------|------|
| 5432 | 5433 | Dify PostgreSQL | 避免与主数据库冲突 |
| 6379 | 6380 | Dify Redis | 避免与主缓存冲突 |
| 3000 | 3003 | GPU Grafana | 避免与主监控冲突 |
| 9090 | 9091 | GPU Prometheus | 避免与主监控冲突 |

---

## 🔒 8. 安全配置建议

### 8.1 密码策略
- ✅ **生产环境**: 必须修改所有默认密码
- ✅ **密码复杂度**: 大小写字母 + 数字 + 特殊字符
- ✅ **定期轮换**: 建议每90天更换关键账号密码
- ✅ **密钥管理**: 使用 Kubernetes Secrets 管理敏感信息

### 8.2 网络安全
- 🔒 **内网访问**: 生产环境仅允许内网访问管理接口
- 🔒 **防火墙**: 配置适当的防火墙规则
- 🔒 **SSL/TLS**: 生产环境启用HTTPS
- 🔒 **访问控制**: 实施基于角色的访问控制

---

## 📝 9. 故障排查快速参考

### 9.1 服务状态检查命令
```bash
# 检查Docker服务状态
docker ps | grep -E "(postgres|redis|minio|grafana|prometheus)"

# 检查端口占用
netstat -tlnp | grep -E "(5432|6379|8000|9000|3000)"

# 测试数据库连接
psql -h localhost -U aiuser -d ai_platform
mongosh mongodb://ai_platform_user:changeThisToSecurePassword@localhost:27017/ai_platform
redis-cli -h localhost -p 6379 -a redis-2024
```

### 9.2 服务重启命令
```bash
# Docker Compose服务重启
cd /home/lsyzt/ZTZT/minimal-example/docker
docker compose -f docker-compose.yml restart
docker compose -f docker-compose.gpu.yml restart

# Django开发服务器
cd /home/lsyzt/ZTZT/minimal-example/backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

---

## 📞 10. 应急联系信息

| 角色 | 联系方式 | 负责范围 |
|------|----------|----------|
| 集群管理员 | lsyzt | 整体系统架构、K8s集群 |
| 服务器地址 | 192.168.110.88 | Ubuntu 24.04 LTS |
| 文档位置 | `/home/lsyzt/ZTZT/docs/` | 完整部署文档 |

---

> **📋 维护说明**: 
> - 本文档随系统部署进展持续更新
> - 如发现信息不准确，请及时反馈给集群管理员
> - 生产环境部署前务必进行完整的安全审查
> - 建议定期备份重要配置文件和数据库
