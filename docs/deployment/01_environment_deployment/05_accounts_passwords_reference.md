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

### 1.2 Redis
| 用户名       | 密码        | 说明           |
|--------------|-------------|----------------|
| (无用户名)   | redis-2024  | Redis 认证密码 |

**连接信息：**
- **Kubernetes 内部访问**: `redis-master.database.svc.cluster.local:6379`
- **端口转发访问**: `kubectl port-forward svc/redis-master 6379:6379 -n database`

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
| 用户名 | 密码                | 说明           |
|--------|---------------------|----------------|
| admin  | LSYgrafanaadmin2025 | 管理员账号     |

**连接信息：**
- **直接访问**: `http://<服务器IP>:3000 | http://192.168.110.88:3000` 
- **Kubernetes 内部访问**: `prometheus-grafana.monitoring.svc.cluster.local:80`
- **端口转发访问**: `kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring`

### 3.2 Prometheus (监控数据源)
| 用户名 | 密码 | 说明                     |
|--------|------|--------------------------|
| 无     | 无   | 通常无认证或集成 Grafana |

**连接信息：**
- **Kubernetes 内部访问**: `prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090`
- **端口转发访问**: `kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring`
- **Web 界面**: `http://localhost:9090` (端口转发后)

## 4. Kubernetes 系统信息

### 4.1 集群基本信息
- **Kubernetes 版本**: 1.28.8
- **CNI**: Flannel
- **Ingress Controller**: NGINX Ingress
- **容器运行时**: containerd
- **主节点**: lsyzt

### 4.2 命名空间列表
| 命名空间     | 说明                       |
|--------------|----------------------------|
| default      | 默认命名空间               |
| kube-system  | Kubernetes 系统组件        |
| database     | 数据库服务 (PostgreSQL, Redis) |
| minio-ns     | MinIO 对象存储             |
| logging      | OpenSearch 日志系统        |
| monitoring   | Prometheus/Grafana 监控    |

## 5. 常用端口映射

### 5.1 集群内部服务端口
| 服务        | 命名空间   | 内部端口 | 服务名                    |
|-------------|------------|----------|---------------------------|
| PostgreSQL  | database   | 5432     | postgresql                |
| Redis       | database   | 6379     | redis-master              |
| MinIO       | minio-ns   | 9000     | minio                     |
| OpenSearch  | logging    | 9200     | opensearch-cluster-master |
| Grafana     | monitoring | 80       | prometheus-grafana        |
| Prometheus  | monitoring | 9090     | prometheus-kube-prometheus-prometheus |

### 5.2 本地端口转发映射
| 服务        | 本地端口 | 转发命令                                                |
|-------------|----------|---------------------------------------------------------|
| PostgreSQL  | 5432     | `kubectl port-forward svc/postgresql 5432:5432 -n database` |
| Redis       | 6379     | `kubectl port-forward svc/redis-master 6379:6379 -n database` |
| MinIO       | 9000     | `kubectl port-forward svc/minio 9000:9000 -n minio-ns` |
| OpenSearch  | 9200     | `kubectl port-forward svc/opensearch-cluster-master 9200:9200 -n logging` |
| Grafana     | 3000     | `kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring` |
| Prometheus  | 9090     | `kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring` |

## 6. 存储路径映射

### 6.1 本地存储路径
| 服务        | 本地路径                          | PV 名称       | 容量 |
|-------------|-----------------------------------|---------------|------|
| PostgreSQL  | `/data/k8s-local-storage/postgres` | postgres-pv   | 10Gi |
| Redis       | `/data/k8s-local-storage/redis`    | redis-pv      | 5Gi  |
| MinIO       | `/data/k8s-local-storage/minio`    | minio-pv      | 20Gi |
| OpenSearch  | `/data/k8s-local-storage/opensearch` | opensearch-pv | 20Gi |
| Prometheus  | `/data/k8s-local-storage/prometheus` | prometheus-pv | 50Gi |

## 7. 常用管理命令

### 7.1 服务状态检查
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

### 7.2 日志查看
```bash
# 查看 Pod 日志
kubectl logs <pod-name> -n <namespace>

# 查看 Pod 详细信息
kubectl describe pod <pod-name> -n <namespace>

# 查看系统级服务状态（如 Grafana）
sudo systemctl status grafana-server
```

### 7.3 密码修改建议
> **⚠️ 安全提醒**: 
> - 生产环境务必修改所有默认密码
> - 定期轮换密码，特别是管理员账号
> - 使用强密码策略（大小写字母 + 数字 + 特殊字符）
> - 考虑使用密钥管理系统（如 Kubernetes Secrets）

## 8. 故障排查快速参考

### 8.1 常见问题检查命令
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

### 8.2 应急联系信息
- **集群管理员**: lsyzt
- **主节点**: lsyzt (Ubuntu 24.04 LTS)
- **部署文档**: `/path/to/docs/deployment/`

---

> **📝 更新说明**: 本文档会随着系统部署进展持续更新，请以最新版本为准。如发现信息不准确，请及时反馈给集群管理员。
