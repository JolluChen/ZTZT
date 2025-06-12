# AI 中台 - 账号密码与服务端口整理

本文档整理了 AI 中台 Kubernetes 集群部署过程中涉及的所有账号密码、服务端口和访问地址，便于运维管理和故障排查。

## 1. 数据库系统账号密码

### 1.1 PostgreSQL
| 用户名    | 密码             | 数据库名      | 说明                     |
|-----------|------------------|---------------|--------------------------|
| postgres  | ai-platform-2024 | postgres      | 超级管理员账号           |
| aiuser    | aiuser-2024      | ai_platform   | 应用专用账号             |

**连接信息：**
- **Kubernetes 内部访问**: `postgresql.database.svc.cluster.local:5432`
- **端口转发访问**: `kubectl port-forward svc/postgresql 5432:5432 -n database`
- **本地连接命令**: `psql -h localhost -U aiuser -d ai_platform`

### 1.2 MongoDB
| 用户名           | 密码                     | 数据库名     | 说明                     |
|------------------|--------------------------|--------------|--------------------------|
| root             | changeThisToSecurePassword | admin        | 超级管理员账号           |
| ai_platform_user | changeThisToSecurePassword | ai_platform  | 应用专用账号             |
| readonly_user    | readOnlyPassword         | ai_platform  | 只读账号                 |

**连接信息：**
- **Docker部署访问**: `localhost:27017`
- **Kubernetes 内部访问**: `ai-mongodb.database.svc.cluster.local:27017`
- **端口转发访问**: `kubectl port-forward svc/ai-mongodb 27017:27017 -n database`
- **本地连接命令**: `mongosh mongodb://ai_platform_user:changeThisToSecurePassword@localhost:27017/ai_platform`

### 1.3 Redis
| 用户名       | 密码        | 说明           |
|--------------|-------------|----------------|
| (无用户名)   | redis-2024  | Redis 认证密码 |

**连接信息：**
- **Kubernetes 内部访问**: `redis-master.database.svc.cluster.local:6379`
- **端口转发访问**: `kubectl port-forward svc/redis-master 6379:6379 -n database`

### 1.5 SQLite 数据库 (开发环境)
| 数据库文件 | 路径 | 说明                     |
|------------|------|--------------------------|
| db.sqlite3 | 项目根目录 | Django开发环境数据库     |

**连接信息：**
- **数据库引擎**: SQLite 3
- **文件位置**: `/home/lsyzt/ZTZT/minimal-example/backend/db.sqlite3`
- **访问方式**: Django ORM 或 sqlite3 命令行
- **备份命令**: `cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)`
- **连接测试**: `python manage.py dbshell`

### 1.6 Django 数据库用户 (生产环境PostgreSQL)
| 用户名       | 密码                 | 数据库名     | 说明                     |
|--------------|----------------------|--------------|--------------------------|
| django_user  | django_password_2024 | ai_platform_django | Django应用专用账号        |
| django_readonly | readonly_pass_2024 | ai_platform_django | Django只读查询账号        |

**连接信息：**
- **生产环境数据库**: PostgreSQL 16
- **连接字符串**: `postgresql://django_user:django_password_2024@localhost:5432/ai_platform_django`
- **迁移权限**: django_user具有CREATE、ALTER、DROP权限
- **查询权限**: django_readonly仅有SELECT权限

## 2. 存储系统账号密码

### 2.1 MinIO (对象存储)
| 用户名     | 密码          | 说明           |
|------------|---------------|----------------|
| minioadmin | minioadmin123 | 管理员账号     |

**连接信息：**
- **Kubernetes 内部访问**: `minio.minio-ns.svc.cluster.local:9000`
- **端口转发访问**: `kubectl port-forward svc/minio 9000:9000 -n minio-ns`
- **Web 控制台**: `http://localhost:9000` (端口转发后)

### 2.2 OpenSearch (日志存储)
| 用户名 | 密码           | 说明           |
|--------|----------------|----------------|
| admin  | OPENsearch@123 | 管理员账号     |

**连接信息：**
- **Kubernetes 内部访问**: `opensearch-cluster-master.logging.svc.cluster.local:9200`
- **端口转发访问**: `kubectl port-forward svc/opensearch-cluster-master 9200:9200 -n logging`
- **API 访问**: `https://localhost:9200` (端口转发后，需要 HTTPS)

## 3. 监控系统账号密码

### 3.1 Grafana (可视化仪表盘)
| 用户名 | 密码                | 部署方式   | 说明           |
|--------|---------------------|------------|----------------|
| admin  | LSYgrafanaadmin2025 | 系统部署   | 管理员账号     |
| admin  | admin123            | Docker部署 | Docker容器管理员账号 |

**连接信息：**
- **直接访问**: `http://<服务器IP>:3000 | http://192.168.110.88:3000` 
- **端口**: 3000
- **Docker部署**: 通过 docker compose 启动的 Grafana 实例
- **推荐仪表板**:
  - MongoDB: 7353
  - Node Exporter: 1860  
  - Prometheus: 3662

> **📋 部署说明**: 
> - 系统部署：通过包管理器安装的 Grafana 服务
> - Docker部署：用于审计监控的容器化 Grafana 实例

### 3.2 Prometheus (监控数据源)
| 用户名 | 密码 | 说明                     |
|--------|------|--------------------------|
| 无     | 无   | 无认证，仅内网访问       |

**连接信息：**
- **直接访问**: `http://<服务器IP>:9090`
- **端口**: 9090

### 3.3 AlertManager (告警管理)
| 用户名 | 密码 | 说明                     |
|--------|------|--------------------------|
| 无     | 无   | 无认证，仅内网访问       |

**连接信息：**
- **直接访问**: `http://<服务器IP>:9093`
- **端口**: 9093

### 3.4 监控Exporters
| 服务组件        | 端口 | 说明                       |
|-----------------|------|----------------------------|
| MongoDB Exporter| 9216 | MongoDB数据库指标导出      |
| Node Exporter   | 9100 | Linux系统指标导出          |
| Redis Exporter  | 9121 | Redis缓存指标导出          |
| PostgreSQL Exporter | 9187 | PostgreSQL数据库指标导出 |

## 4. 应用系统账号密码

### 4.1 Django 后端管理系统
| 用户名 | 密码    | 邮箱                  | 数据库 | 状态 | 说明                     |
|--------|---------|----------------------|--------|------|--------------------------|
| admin  | admin123| admin@aiplatform.com | SQLite (开发) | ⚠️ 待创建 | Django超级用户账号       |
| admin  | admin123| admin@aiplatform.com | PostgreSQL (生产) | ⚠️ 待创建 | Django超级用户账号（生产环境） |

**连接信息：**
- **开发环境管理后台**: `http://192.168.110.88:8000/admin/` 
- **生产环境管理后台**: `http://<服务器IP>:8000/admin/` 或 `https://your-domain.com/admin/`
- **API基础路径**: `http://192.168.110.88:8000/api/v1/`
- **权限级别**: Django超级用户（全部权限）
- **用户模型**: `authentication.User` (自定义用户模型)

**⚠️ 当前状态**: 
- ✅ Django服务已成功启动运行在端口8000
- ✅ 数据库迁移已完成，自定义用户模型已应用
- ⚠️ **超级用户尚未创建**，当前数据库中仅有AnonymousUser
- 🔧 **需要执行**: 使用下方超级用户创建命令完成账号设置
- 📊 API端点已验证可正常访问，ViewSet配置完整

**超级用户创建方式**:
1. **方式一：Django管理命令 (推荐)**
   ```bash
   cd /home/lsyzt/ZTZT/minimal-example/backend
   source venv/bin/activate
   python manage.py createsuperuser
   # 按提示输入：
   # 用户名: admin
   # 邮箱: admin@aiplatform.com  
   # 密码: admin123 (输入时不显示)
   # 确认密码: admin123
   ```

2. **方式二：Django shell创建**
   ```bash
   cd /home/lsyzt/ZTZT/minimal-example/backend
   source venv/bin/activate
   python manage.py shell
   # 在Python shell中执行:
   from authentication.models import User
   User.objects.create_superuser(username='admin', email='admin@aiplatform.com', password='admin123')
   exit()
   ```

3. **创建完成后验证**
   ```bash
   # 启动Django开发服务器
   python manage.py runserver 0.0.0.0:8000
   
   # 在浏览器访问管理后台
   # http://192.168.110.88:8000/admin/
   # 使用账号 admin / admin123 登录
   ```

**API端点（已验证）：**
- **健康检查**: `http://127.0.0.1:8000/api/v1/health/` ✅
- **数据平台API**: `http://127.0.0.1:8000/api/v1/data/` ✅
  - 数据源管理: `/datasources/` ✅
  - 数据集管理: `/datasets/` ✅ 
  - 处理任务: `/tasks/` ✅
- **算法平台API**: `http://127.0.0.1:8000/api/v1/algorithm/` ✅
- **模型平台API**: `http://127.0.0.1:8000/api/v1/model/` ✅
- **服务平台API**: `http://127.0.0.1:8000/api/v1/service/` ✅
- **Django管理后台**: `http://127.0.0.1:8000/admin/` ✅

### 4.2 Django 环境配置
| 配置项 | 开发环境值 | 生产环境值 | 说明 |
|--------|------------|------------|------|
| SECRET_KEY | dev-secret-key-change-in-production-please | 复杂随机密钥 | Django加密密钥 |
| DEBUG | True | False | 调试模式 |
| ALLOWED_HOSTS | localhost,127.0.0.1,0.0.0.0 | 实际域名 | 允许的主机 |
| DATABASE_URL | sqlite:///db.sqlite3 | postgresql://... | 数据库连接 |

**部署路径：**
- **开发环境**: `/home/lsyzt/ZTZT/minimal-example/backend/`
- **生产环境**: `/opt/ai-platform/backend/`
- **虚拟环境**: `venv/` (项目目录内)
- **日志目录**: `logs/` (生产环境)

### 4.3 Django REST Framework 配置
| 组件 | 版本 | 配置文件 | 说明 |
|------|------|----------|------|
| Django | 4.2.16 | config/settings.py | 主框架 |
| DRF | 3.15.2 | config/settings.py | REST API框架 |
| CORS Headers | 4.3.1 | config/settings.py | 跨域请求支持 |
| Gunicorn | 21.2.0 | gunicorn.conf.py | WSGI服务器（生产） |

**重要修复记录：**
- ✅ **Django服务启动**: Django 4.2.16 已成功启动运行
- ✅ **ViewSet basename 配置**: 所有ViewSet注册都已添加basename参数
- ✅ **路由配置修复**: `router.register(r'datasources', views.DataSourceViewSet, basename='datasource')`
- ✅ **依赖兼容性**: 核心依赖优先，pandas为可选依赖
- ✅ **系统检查通过**: 所有Django应用配置验证无错误
- ✅ **数据库迁移完成**: 自定义用户模型已正确应用
- ⚠️ **超级用户创建**: 等待管理员执行创建命令
- 📊 **API端点验证**: 所有REST API端点响应正常
> - 定期审查管理员账号权限

### 4.2 Flower Celery 监控管理
| 用户名 | 密码         | 说明                     |
|--------|--------------|--------------------------|
| admin  | Monitor@2024 | Flower监控管理账号       |

**连接信息：**
- **监控界面**: `http://localhost:5555` (本地部署)
- **生产环境**: `http://<服务器IP>:5555`
- **权限级别**: Celery任务队列全部监控权限
- **功能说明**: 
  - 监控Celery Worker状态
  - 查看任务执行历史
  - 实时监控任务队列
  - 查看任务执行统计
- **启动方式**: `flower -A config --port=5555 --basic_auth=admin:Monitor@2024`

> **📊 监控功能**: 
> - 实时查看Worker节点状态
> - 监控任务执行成功率和失败率
> - 查看任务执行时间分布
> - 支持任务重试和撤销操作

### 4.3 审计监控系统管理
| 用户名        | 密码         | 说明                     |
|---------------|--------------|--------------------------|
| monitor_admin | Monitor@2024 | 审计监控系统管理员账号   |

**连接信息：**
- **Web管理后台**: `http://127.0.0.1:8000/admin/` (本地开发)
- **生产环境**: `http://<服务器IP>:8000/admin/`
- **权限级别**: Django超级用户（监控系统全部权限）
- **创建方式**: 通过审计监控部署脚本自动创建
- **专用功能**:
  - 访问审计监控仪表板
  - 管理审计日志和合规报告
  - 配置安全告警策略
  - 查看系统性能指标

> **🔐 专用账号**: 
> - 专门用于审计监控系统管理
> - 与Flower监控使用相同密码便于管理
> - 邮箱: monitor@ai-platform.com

## 5. Kubernetes系统信息

### 5.1 集群基本信息
- **Kubernetes 版本**: 1.28.8
- **CNI**: Flannel
- **Ingress Controller**: NGINX Ingress
- **容器运行时**: containerd
- **主节点**: lsyzt

### 5.2 命名空间列表
| 命名空间     | 说明                       |
|--------------|----------------------------|
| default      | 默认命名空间               |
| kube-system  | Kubernetes 系统组件        |
| database     | 数据库服务 (PostgreSQL, Redis) |
| minio-ns     | MinIO 对象存储             |
| logging      | OpenSearch 日志系统        |
| monitoring   | Prometheus/Grafana 监控    |

## 6. 监控系统端口映射

### 6.1 Docker部署监控服务端口
| 服务组件         | 直接访问端口 | 说明                       |
|------------------|--------------|----------------------------|
| Grafana          | 3000         | 可视化仪表盘               |
| Prometheus       | 9090         | 监控数据收集与查询         |
| AlertManager     | 9093         | 告警管理                   |
| MongoDB Exporter | 9216         | MongoDB指标导出            |
| Node Exporter    | 9100         | 系统指标导出               |
| Redis Exporter   | 9121         | Redis指标导出              |
| PostgreSQL Exporter | 9187      | PostgreSQL指标导出         |

### 6.2 Kubernetes系统信息

#### 集群基本信息
- **Kubernetes 版本**: 1.28.8
- **CNI**: Flannel
- **Ingress Controller**: NGINX Ingress
- **容器运行时**: containerd
- **主节点**: lsyzt

#### 命名空间列表
| 命名空间     | 说明                       |
|--------------|----------------------------|
| default      | 默认命名空间               |
| kube-system  | Kubernetes 系统组件        |
| database     | 数据库服务 (PostgreSQL, Redis) |
| minio-ns     | MinIO 对象存储             |
| logging      | OpenSearch 日志系统        |
| monitoring   | Prometheus/Grafana 监控    |

## 7. Kubernetes服务端口映射

### 7.1 集群内部服务端口
| 服务        | 命名空间   | 内部端口 | 服务名                    |
|-------------|------------|----------|---------------------------|
| PostgreSQL  | database   | 5432     | postgresql                |
| Redis       | database   | 6379     | redis-master              |
| MinIO       | minio-ns   | 9000     | minio                     |
| OpenSearch  | logging    | 9200     | opensearch-cluster-master |
| Grafana     | monitoring | 80       | prometheus-grafana        |
| Prometheus  | monitoring | 9090     | prometheus-kube-prometheus-prometheus |

### 7.2 本地端口转发映射
| 服务        | 本地端口 | 转发命令                                                |
|-------------|----------|---------------------------------------------------------|
| PostgreSQL  | 5432     | `kubectl port-forward svc/postgresql 5432:5432 -n database` |
| Redis       | 6379     | `kubectl port-forward svc/redis-master 6379:6379 -n database` |
| MinIO       | 9000     | `kubectl port-forward svc/minio 9000:9000 -n minio-ns` |
| OpenSearch  | 9200     | `kubectl port-forward svc/opensearch-cluster-master 9200:9200 -n logging` |
| Grafana     | 3000     | `kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring` |
| Prometheus  | 9090     | `kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring` |

## 8. 存储路径映射

### 8.1 本地存储路径
| 服务        | 本地路径                          | PV 名称       | 容量 |
|-------------|-----------------------------------|---------------|------|
| PostgreSQL  | `/data/k8s-local-storage/postgres` | postgres-pv   | 10Gi |
| Redis       | `/data/k8s-local-storage/redis`    | redis-pv      | 5Gi  |
| MinIO       | `/data/k8s-local-storage/minio`    | minio-pv      | 20Gi |
| OpenSearch  | `/data/k8s-local-storage/opensearch` | opensearch-pv | 20Gi |
| Prometheus  | `/data/k8s-local-storage/prometheus` | prometheus-pv | 50Gi |

## 9. 常用管理命令

### 9.1 服务状态检查
```bash
# 检查所有 Pod 状态
kubectl get pods --all-namespaces

# 检查 PVC 状态
kubectl get pvc --all-namespaces

# 检查 PV 状态
kubectl get pv

# 检查服务状态
kubectl get svc --all-namespaces
```

### 9.2 日志查看
```bash
# 查看 Pod 日志
kubectl logs <pod-name> -n <namespace>

# 查看 Pod 详细信息
kubectl describe pod <pod-name> -n <namespace>

# 查看系统级服务状态（如 Grafana）
sudo systemctl status grafana-server
```

### 9.3 监控服务管理命令

```bash
# 检查Docker监控服务状态
docker ps | grep -E "(prometheus|grafana|mongodb_exporter|node_exporter|redis_exporter|alertmanager)"

# 重启监控服务
docker restart grafana prometheus alertmanager mongodb_exporter node_exporter

# 查看监控服务日志
docker logs grafana
docker logs prometheus
docker logs mongodb_exporter

# 验证各Exporter响应
curl http://localhost:9216/metrics  # MongoDB Exporter
curl http://localhost:9100/metrics  # Node Exporter  
curl http://localhost:9121/metrics  # Redis Exporter
curl http://localhost:9090/targets  # Prometheus targets状态
```

### 9.4 密码修改建议
> **⚠️ 安全提醒**: 
> - 生产环境务必修改所有默认密码
> - 定期轮换密码，特别是管理员账号
> - 使用强密码策略（大小写字母 + 数字 + 特殊字符）
> - 考虑使用密钥管理系统（如 Kubernetes Secrets）

## 10. 故障排查快速参考

### 10.1 常见问题检查命令
```bash
# Pod 无法启动
kubectl describe pod <pod-name> -n <namespace>

# PVC 无法绑定
kubectl describe pvc <pvc-name> -n <namespace>

# 镜像拉取失败
kubectl describe pod <pod-name> -n <namespace> | grep -i image

# 服务无法访问
kubectl get svc -n <namespace>
kubectl get endpoints -n <namespace>
```

### 10.2 应急联系信息
- **集群管理员**: lsyzt
- **主节点**: lsyzt (Ubuntu 24.04 LTS)
- **部署文档**: `/path/to/docs/deployment/`

---

> **📝 更新说明**: 本文档会随着系统部署进展持续更新，请以最新版本为准。如发现信息不准确，请及时反馈给集群管理员。

## 11. 当前部署状态与下一步行动

### 11.1 Django REST API 部署状态 ✅
- ✅ **Ubuntu服务器**: 192.168.110.88 连接正常
- ✅ **Django服务**: 4.2.16 版本运行在端口8000
- ✅ **数据库**: SQLite开发环境配置完成
- ✅ **API端点**: 所有REST API路由正常响应
- ✅ **ViewSet配置**: basename问题已修复
- ✅ **系统检查**: Django应用配置验证通过
- ⚠️ **超级用户**: 等待创建Django管理员账号

### 11.2 需要完成的任务
1. **🔧 立即执行 - 创建Django超级用户**
   ```bash
   ssh lsyzt@192.168.110.88
   cd /home/lsyzt/ZTZT/minimal-example/backend
   source venv/bin/activate
   python manage.py createsuperuser
   # 输入: admin / admin@aiplatform.com / admin123
   ```

2. **🧪 验证部署完整性**
   ```bash
   # 测试Django管理后台登录
   # 访问: http://192.168.110.88:8000/admin/
   # 使用账号: admin / admin123
   
   # 验证API端点响应
   curl -X GET http://192.168.110.88:8000/api/v1/health/
   ```

3. **📊 下一阶段部署计划**
   - [ ] 配置生产环境PostgreSQL数据库
   - [ ] 设置Gunicorn和Systemd服务
   - [ ] 配置Nginx反向代理
   - [ ] 配置SSL证书和HTTPS
   - [ ] 集成监控和日志系统

### 11.3 Windows用户快速行动指南

**一键连接Django服务器：**
```powershell
# 打开Windows Terminal或PowerShell
ssh lsyzt@192.168.110.88

# 或者使用VSCode Remote SSH
# 1. 安装Remote-SSH扩展
# 2. Ctrl+Shift+P -> Remote-SSH: Connect to Host
# 3. 输入: lsyzt@192.168.110.88
# 4. 打开文件夹: /home/lsyzt/ZTZT/minimal-example/backend
```

**常用维护命令：**
```bash
# 进入项目并激活环境
cd /home/lsyzt/ZTZT/minimal-example/backend && source venv/bin/activate

# 查看Django服务状态
python manage.py check && python manage.py showmigrations

# 启动开发服务器
python manage.py runserver 0.0.0.0:8000

# 查看实时日志（新开终端）
tail -f logs/django.log
```

## 8. Windows 用户 SSH 连接信息

### 8.1 SSH 连接配置

**Ubuntu 服务器连接信息：**
| 参数      | 值                              | 说明                        |
|-----------|--------------------------------|-----------------------------|
| 服务器IP  | `192.168.110.88`              | 实际部署服务器IP地址        |
| 用户名    | `lsyzt`                        | Ubuntu用户名                |
| SSH端口   | `22`                           | 默认SSH端口                 |
| 密钥认证  | 推荐使用SSH密钥                | 比密码认证更安全            |

**Windows SSH 客户端推荐：**
| 工具名称           | 优势                           | 下载地址/安装方式          |
|-------------------|--------------------------------|---------------------------|
| Windows Terminal   | 现代化终端，支持多标签         | Microsoft Store           |
| VSCode Remote SSH  | 代码编辑和终端一体化          | VSCode插件市场            |
| MobaXterm         | 图形化工具，内置SFTP           | https://mobaxterm.mobatek.net |
| PuTTY             | 轻量级经典工具                 | https://putty.org         |

### 8.2 SSH 连接命令

**基础连接：**
```powershell
# 使用密码认证
ssh lsyzt@192.168.110.88

# 使用指定端口
ssh -p 22 lsyzt@192.168.110.88

# 使用SSH密钥认证（推荐）
ssh -i "path\to\private\key" lsyzt@192.168.110.88
```

**保持连接配置：**
```bash
# 在Windows用户目录创建SSH配置文件
# 文件位置: C:\Users\Administrator\.ssh\config

Host ubuntu-server
    HostName 192.168.110.88
    User lsyzt
    Port 22
    ServerAliveInterval 60
    ServerAliveCountMax 3
    IdentityFile "C:\Users\Administrator\.ssh\id_rsa"
```

### 8.3 文件传输配置

**SCP 文件传输：**
```powershell
# 从Windows传输到Ubuntu
scp "C:\path\to\local\file.txt" lsyzt@192.168.110.88:/home/lsyzt/

# 从Ubuntu传输到Windows
scp lsyzt@192.168.110.88:/home/lsyzt/file.txt "C:\path\to\local\"
```

**VSCode Remote SSH 配置：**
1. 安装 Remote-SSH 扩展
2. 按 `Ctrl+Shift+P` 打开命令面板
3. 选择 "Remote-SSH: Connect to Host"
4. 输入 `lsyzt@192.168.110.88`
5. 选择Linux平台
6. 打开远程文件夹: `/home/lsyzt/ZTZT/minimal-example/backend`

### 8.4 部署过程中的重要路径

**Ubuntu服务器路径映射：**
| 用途                    | Ubuntu路径                                    | Windows访问方式                |
|------------------------|-----------------------------------------------|-------------------------------|
| Django项目根目录        | `/home/lsyzt/ZTZT/minimal-example/backend`    | VSCode Remote SSH             |
| 虚拟环境目录           | `/home/lsyzt/ZTZT/minimal-example/backend/venv` | SSH终端访问                   |
| 日志目录              | `/home/lsyzt/ZTZT/minimal-example/backend/logs` | SCP下载或VSCode查看           |
| 配置文件              | `/home/lsyzt/ZTZT/minimal-example/backend/.env` | VSCode编辑                    |
| 数据库文件            | `/home/lsyzt/ZTZT/minimal-example/backend/db.sqlite3` | SCP备份到Windows              |

### 8.5 Windows-Ubuntu 工作流程建议

**推荐工作流程：**
1. **代码编辑**: 使用VSCode Remote SSH直接在Ubuntu上编辑
2. **命令执行**: 使用VSCode集成终端或Windows Terminal SSH
3. **文件监控**: 使用`tail -f logs/file.log`实时查看日志
4. **会话保持**: 使用`screen`或`tmux`避免SSH断开影响
5. **文件备份**: 定期使用SCP将重要文件备份到Windows

**注意事项：**
- 🚨 避免在Windows记事本中编辑Linux文件（换行符问题）
- 🚨 使用Linux路径格式 `/home/user/` 而不是Windows格式 `C:\Users\`
- 🚨 注意文件权限，`.sh`脚本需要执行权限 `chmod +x`

## 9. Node.js 环境信息

### 9.1 Node.js 安装状态 ✅

**当前环境配置：**
| 组件     | 版本        | 安装路径        | 安装方式         | 状态 |
|----------|-------------|----------------|------------------|------|
| Node.js  | v22.16.0    | /usr/bin/node  | 系统包管理器     | ✅ 已安装 |
| npm      | v10.9.2     | /usr/bin/npm   | 随Node.js安装    | ✅ 已安装 |
| yarn     | 待安装      | 待确定         | npm全局安装      | ⚠️ 待安装 |
| PM2      | 待安装      | 待确定         | npm全局安装      | ⚠️ 待安装 |

### 9.2 验证命令记录

**环境验证结果：**
```bash
# Node.js版本确认
(venv) lsyzt@lsyzt:~/ZTZT/minimal-example$ node --version
v22.16.0

# npm版本确认
(venv) lsyzt@lsyzt:~/ZTZT/minimal-example$ npm --version
10.9.2

# 安装路径确认 - 系统级安装
(venv) lsyzt@lsyzt:~/ZTZT/minimal-example$ which node
/usr/bin/node

(venv) lsyzt@lsyzt:~/ZTZT/minimal-example$ which npm
/usr/bin/npm
```

### 9.3 Node.js 环境优势

**系统包管理器安装的优势：**
- ✅ **稳定性**: 与Ubuntu 24.04 LTS系统深度集成
- ✅ **安全性**: 通过官方仓库验证，及时安全更新
- ✅ **维护性**: 系统级统一管理，`apt upgrade`统一更新
- ✅ **性能**: 原生编译优化，比NVM安装性能更好
- ✅ **兼容性**: 与系统服务和守护进程兼容性更佳

### 9.4 前端开发环境规划

**技术栈配置：**
| 技术组件           | 推荐版本    | 当前状态      | 安装方式               |
|-------------------|-------------|---------------|------------------------|
| Node.js Runtime   | v22.16.0    | ✅ 已安装     | 系统包管理器           |
| React Framework   | 18.x        | ⚠️ 待安装     | npm create vite       |
| Vite Build Tool   | 5.x         | ⚠️ 待安装     | npm全局/项目依赖       |
| Ant Design UI     | 5.x         | ⚠️ 待安装     | npm项目依赖            |
| TypeScript        | 5.x         | ⚠️ 待安装     | npm项目依赖            |

### 9.5 立即可执行的验证命令

**Node.js环境测试：**
```bash
# 1. SSH连接到Ubuntu服务器
ssh lsyzt@192.168.110.88

# 2. 验证Node.js环境
node --version && npm --version

# 3. 检查npm全局配置
npm config list

# 4. 测试npm包管理功能
npm help

# 5. 创建简单测试项目
mkdir -p /tmp/nodejs-test && cd /tmp/nodejs-test
npm init -y
npm install express
node -e "console.log('Node.js v22.16.0 环境工作正常！')"

# 6. 清理测试环境
cd ~ && rm -rf /tmp/nodejs-test
```

### 9.6 前端项目初始化规划

**AI中台前端开发环境创建：**
```bash
# 1. 创建前端项目目录
sudo mkdir -p /opt/ai_platform_frontend
sudo chown $USER:$USER /opt/ai_platform_frontend
cd /opt/ai_platform_frontend

# 2. 使用Vite创建React+TypeScript项目
npm create vite@latest ai-platform-ui -- --template react-ts
cd ai-platform-ui
npm install

# 3. 安装AI中台相关依赖
npm install antd @ant-design/icons axios react-router-dom

# 4. 启动开发服务器
npm run dev
# 访问: http://192.168.110.88:5173
```

## 10. 部署状态总览

### 10.1 当前环境部署状态

**基础环境状态：**
| 组件类型      | 组件名称       | 版本/状态        | 部署状态     | 验证方式                    |
|---------------|---------------|------------------|-------------|----------------------------|
| 操作系统      | Ubuntu Linux  | 24.04 LTS        | ✅ 运行中   | `uname -a`                 |
| Python环境    | Python        | 3.12.x           | ✅ 已配置   | `python --version`         |
| Web框架       | Django        | 5.1.3            | ✅ 已部署   | `curl http://192.168.110.88:8000/api/` |
| 数据库        | SQLite        | 3.x              | ✅ 运行中   | Django数据库连接正常        |
| JavaScript环境 | Node.js       | v22.16.0         | ✅ 已安装   | `node --version`           |
| 包管理器      | npm           | v10.9.2          | ✅ 已安装   | `npm --version`            |

**Django应用部署状态：**
| 功能模块      | 部署状态      | API端点           | 测试命令                              |
|---------------|---------------|-------------------|--------------------------------------|
| 基础API       | ✅ 已部署     | `/api/v1/health/` | `curl http://192.168.110.88:8000/api/v1/health/` |
| 用户认证      | ✅ 已配置     | `/api/auth/`      | Django用户系统已激活                  |
| 管理后台      | ⚠️ 待配置     | `/admin/`         | 需要创建超级用户                      |
| 算法服务      | ✅ 已部署     | `/api/algorithm/` | ViewSet配置已修复                     |
| 数据服务      | ✅ 已部署     | `/api/data/`      | 数据模型和API已配置                   |

### 10.2 立即需要执行的任务

**优先级1 - 必须完成：**
1. **🔧 创建Django超级用户** *(预计5分钟)*
   ```bash
   ssh lsyzt@192.168.110.88
   cd /home/lsyzt/ZTZT/minimal-example/backend
   source venv/bin/activate
   python manage.py createsuperuser
   ```

2. **🧪 验证Django管理后台** *(预计5分钟)*
   ```bash
   # 访问管理后台
   # URL: http://192.168.110.88:8000/admin/
   # 账号: admin / admin123
   ```

**优先级2 - 建议完成：**
3. **📦 配置Node.js开发环境** *(预计15分钟)*
   ```bash
   # 安装全局开发工具
   npm install -g yarn pm2 typescript
   
   # 创建前端项目框架
   mkdir -p /opt/ai_platform_frontend
   cd /opt/ai_platform_frontend
   npm create vite@latest ai-platform-ui -- --template react-ts
   ```

### 10.3 下一阶段部署规划

**阶段2 - 前端开发环境：**
- [ ] React + TypeScript + Vite项目初始化
- [ ] Ant Design UI框架集成
- [ ] API客户端配置和Django后端集成
- [ ] 开发服务器配置和热重载

**阶段3 - 生产环境优化：**
- [ ] Nginx反向代理配置
- [ ] PM2进程管理配置
- [ ] 生产数据库迁移 (PostgreSQL)
- [ ] SSL证书和HTTPS配置
- [ ] 系统监控和日志管理

### 10.4 Windows用户操作指引

**立即可执行的验证命令：**
```powershell
# 1. 连接Ubuntu服务器
ssh lsyzt@192.168.110.88

# 2. 验证Django环境
cd /home/lsyzt/ZTZT/minimal-example/backend
source venv/bin/activate
python manage.py check

# 3. 验证Node.js环境
node --version && npm --version

# 4. 测试API响应
curl -X GET http://192.168.110.88:8000/api/v1/health/
```

**从Windows浏览器测试：**
- Django API: `http://192.168.110.88:8000/api/`
- Django管理后台: `http://192.168.110.88:8000/admin/` *(需要先创建超级用户)*
- API健康检查: `http://192.168.110.88:8000/api/v1/health/`

---

> **📝 更新日期**: 2025年6月9日  
> **✅ 文档状态**: 基于实际部署状态优化完成  
> **🎯 下一步**: 创建Django超级用户并验证前端开发环境
- 💡 建议使用UTF-8编码保存所有文件
- 💡 可以在Windows中安装Git Bash获得更好的Linux命令支持

### 8.6 Windows用户常见问题解决

**SSH连接问题：**
```powershell
# 如果SSH连接超时或拒绝
ssh -v lsyzt@192.168.110.88  # 使用详细模式查看连接过程

# 如果提示密钥问题
ssh-keygen -R 192.168.110.88  # 清除已知主机记录

# 如果需要强制密码认证
ssh -o PreferredAuthentications=password lsyzt@192.168.110.88
```

**文件编码问题：**
```bash
# 检查文件编码
file -i filename.py
ls -la | grep filename

# 转换文件编码（在Ubuntu服务器上）
iconv -f gbk -t utf-8 file.txt > file_utf8.txt

# 修复Windows换行符问题
dos2unix filename.py
```

**VSCode Remote SSH 问题：**
- 🔧 **连接断开**: 检查ServerAliveInterval配置
- 🔧 **权限错误**: 确保SSH密钥权限正确（600）
- 🔧 **插件冲突**: 禁用其他Remote相关插件
- 🔧 **平台选择**: 首次连接选择Linux平台

## 9. Django 部署维护命令

**Django 开发环境：**
```bash
# 进入项目目录
cd /home/lsyzt/ZTZT/minimal-example/backend

# 激活虚拟环境
source venv/bin/activate

# Django 管理命令
python manage.py runserver 0.0.0.0:8000  # 启动开发服务器
python manage.py check                    # 检查项目配置
python manage.py migrate                  # 执行数据库迁移
python manage.py createsuperuser          # 创建超级用户
python manage.py collectstatic --noinput  # 收集静态文件
python manage.py dbshell                  # 进入数据库命令行
```

**Django 生产环境服务管理：**
```bash
# Systemd 服务管理
sudo systemctl start ai-platform-django      # 启动Django服务
sudo systemctl stop ai-platform-django       # 停止Django服务
sudo systemctl restart ai-platform-django    # 重启Django服务
sudo systemctl status ai-platform-django     # 查看服务状态
sudo systemctl enable ai-platform-django     # 设置开机启动

# 查看服务日志
sudo journalctl -u ai-platform-django -f     # 实时查看系统日志
tail -f /home/lsyzt/ZTZT/minimal-example/backend/logs/gunicorn_error.log  # 查看应用错误日志
tail -f /home/lsyzt/ZTZT/minimal-example/backend/logs/gunicorn_access.log # 查看访问日志
```

**Django 维护脚本：**
```bash
# 部署和维护脚本（需要先cd到项目目录）
./quick_deploy.sh          # 一键部署脚本
./test_deployment.sh       # 部署测试脚本
./monitor_django.sh        # 系统监控脚本
./backup_django.sh         # 数据备份脚本
./emergency_recovery.sh    # 紧急恢复脚本
./verify_deployment.sh     # 部署验证脚本
```

**Django API 状态检查：**
```bash
# API 健康检查
curl -X GET http://localhost:8000/api/v1/health/
curl -X GET http://localhost:8000/admin/

# 检查API端点
curl -X GET http://localhost:8000/api/v1/data/
curl -X GET http://localhost:8000/api/v1/algorithm/
curl -X GET http://localhost:8000/api/v1/model/
curl -X GET http://localhost:8000/api/v1/service/

# 压力测试（需要先安装apache2-utils）
ab -n 100 -c 10 http://localhost:8000/
```

**Django 数据库维护：**
```bash
# SQLite 数据库操作
sqlite3 db.sqlite3 ".tables"              # 查看数据表
sqlite3 db.sqlite3 "SELECT * FROM django_migrations;" # 查看迁移记录

# 数据库备份
cp db.sqlite3 "db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)"

# 重置数据库（谨慎操作）
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```
