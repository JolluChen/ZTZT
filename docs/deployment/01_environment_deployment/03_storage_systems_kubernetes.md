# AI 中台 - Kubernetes 存储系统部署

本文档指导如何为 AI 中台的 Kubernetes 集群部署和配置各类存储系统，包括镜像仓库、日志存储、持久化数据存储等。

---

## 1. 基础本地存储配置（推荐单节点/小规模集群，生产环境可选用分布式存储）

### 1.1 创建本地存储目录
在每个需要本地存储的节点上执行（以主节点 lsyzt 为例）：
```bash
sudo mkdir -p /data/k8s-local-storage/postgres /data/k8s-local-storage/redis
sudo chown -R 1001:1001 /data/k8s-local-storage/postgres /data/k8s-local-storage/redis
```

### 1.2 创建 StorageClass 和 PersistentVolume

#### StorageClass（local-storage）
`local-storage-sc.yaml`：
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

#### PersistentVolume（以 PostgreSQL、Redis 为例）
`postgres-pv.yaml`：
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: postgres-pv
spec:
  capacity:
    storage: 20Gi
  accessModes:
    - ReadWriteOnce
  storageClassName: local-storage
  local:
    path: /data/k8s-local-storage/postgres
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - lsyzt
```

`redis-pv.yaml`：
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: redis-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  storageClassName: local-storage
  local:
    path: /data/k8s-local-storage/redis
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - lsyzt
```

#### 应用配置
```bash
kubectl apply -f local-storage-sc.yaml
kubectl apply -f postgres-pv.yaml
kubectl apply -f redis-pv.yaml
```

#### 验证
```bash
kubectl get storageclass
kubectl get pv
```

---

## 2. 安装 Helm

```bash
# 安装 Helm（如未安装）
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > $null
sudo apt-get install apt-transport-https --yes
"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

---

## 3. 部署核心数据库服务（PostgreSQL、Redis）

### 3.1 PostgreSQL 部署

1. 创建本地存储目录（如未创建） :
   ```bash
   sudo mkdir -p /data/k8s-local-storage/postgres
   sudo chown -R 1001:1001 /data/k8s-local-storage/postgres
   ```
2. 创建 PV（postgres-pv.yaml） :
   ```yaml
   apiVersion: v1
   kind: PersistentVolume
   metadata:
     name: postgres-pv
   spec:
     capacity:
       storage: 10Gi
     accessModes:
       - ReadWriteOnce
     persistentVolumeReclaimPolicy: Retain
     storageClassName: local-storage
     local:
       path: /data/k8s-local-storage/postgres
     nodeAffinity:
       required:
         nodeSelectorTerms:
           - matchExpressions:
               - key: kubernetes.io/hostname
                 operator: In
                 values:
                   - lsyzt
   ```
   ```bash
   kubectl apply -f postgres-pv.yaml
   ```
3. 创建 postgresql-values.yaml :
   ```yaml
global:
  storageClass: "local-storage"
primary:
  persistence:
    size: 10Gi
auth:
  postgresPassword: "ai-platform-2024"
  username: "aiuser"
  password: "aiuser-2024"
  database: "ai_platform"
   ```
4. 离线安装 Chart 包（如无网络） :
   - 在 Windows下载 postgresql-15.5.2.tgz 并上传到服务器。
5. 安装 PostgreSQL :
   ```bash
   kubectl create namespace database
   helm install postgresql ./postgresql-15.5.2.tgz -f postgresql-values.yaml -n database --create-namespace
   ```
6. 镜像拉取失败时，需在服务器用 Docker Desktop/WSL2 离线下载镜像并导入 containerd :
   ```bash
   sudo ctr -n k8s.io images import postgresql-16.3.0-debian-12-r12.tar
   kubectl delete pod postgresql-0 -n database
   ```
7. 验证 :
   ```bash
   kubectl get pods -n database
   kubectl get pvc -n database
   kubectl get pv
   ```

### 3.2 Redis 部署

1. 创建本地存储目录（如未创建） :
   ```bash
   sudo mkdir -p /data/k8s-local-storage/redis
   sudo chown -R 1001:1001 /data/k8s-local-storage/redis
   ```
2. 创建 PV（redis-pv.yaml） :
   ```yaml
   apiVersion: v1
   kind: PersistentVolume
   metadata:
     name: redis-pv
   spec:
     capacity:
       storage: 5Gi
     accessModes:
       - ReadWriteOnce
     persistentVolumeReclaimPolicy: Retain
     storageClassName: local-storage
     local:
       path: /data/k8s-local-storage/redis
     nodeAffinity:
       required:
         nodeSelectorTerms:
           - matchExpressions:
               - key: kubernetes.io/hostname
                 operator: In
                 values:
                   - lsyzt
   ```
   ```bash
   kubectl apply -f redis-pv.yaml
   ```
3. 创建 redis-values.yaml :
   ```yaml
global:
  storageClass: "local-storage"
master:
  persistence:
    size: 5Gi
auth:
  enabled: true
  password: "redis-2024"
replica:
  replicaCount: 0
   ```
4. 离线安装 Chart 包（如无网络） :
   - 在 Windows下载 redis-18.1.2.tgz 并上传到服务器。
5. 安装 Redis :
   ```bash
   helm install redis ./redis-18.1.2.tgz -f redis-values.yaml -n database
   ```
6. 镜像拉取失败时，需在服务器用 Docker Desktop/WSL2 离线下载镜像并导入 containerd :
   ```bash
   sudo ctr -n k8s.io images import redis-7.2.1-debian-11-r0.tar
   kubectl delete pod redis-master-0 -n database
   ```
7. 验证 :
   ```bash
   kubectl get pods -n database
   kubectl get pvc -n database
   kubectl get pv
   ```

> 说明：如需 Redis 副本，请为每个副本单独创建 PV，并将 replicaCount 设置为对应数量。

---

## 4. 高级存储系统与监控（可选/后续）

> 以下为 Harbor、MinIO、OpenSearch、Prometheus 等高级组件部署，建议在核心数据库服务部署并验证无误后再逐步实施。

### 4.1 Harbor (容器镜像仓库)

**推荐部署方式**: 使用 Helm Chart 在 Kubernetes 中部署 Harbor。

**前提**:
- Kubernetes 集群已运行。
- Helm 3 已安装并配置。
  ```bash
  # 安装 Helm (如果尚未安装)
  # curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
  # sudo apt-get install apt-transport-https --yes
  # echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
  # sudo apt-get update
  # sudo apt-get install helm
  ```
- 持久化存储已配置 (例如，通过 StorageClass 和 PersistentVolumeClaims，MinIO 也可以作为 Harbor 的后端存储)。

**安装步骤 (使用 Helm Chart):**
1.  添加 Harbor Helm 仓库:
    ```bash
    helm repo add harbor https://helm.goharbor.io
    helm repo update
    ```
2.  准备 Harbor 的 `values.yaml` 配置文件。
    创建一个 `harbor-values.yaml` 文件，并根据您的需求进行配置。关键配置项包括：
    - `expose.type`: 通常设置为 `ingress` 或 `loadBalancer`。如果使用 `ingress`，确保 Ingress Controller (如 ingress-nginx) 已部署。
    - `expose.ingress.hosts.core`: Harbor 的访问域名。
    - `externalURL`: Harbor 的外部访问 URL。
    - `persistence.enabled`: `true`，并配置存储类。
    - `harborAdminPassword`: 管理员密码。
    - 其他如数据库、Redis、存储后端（如 MinIO）的配置。

    一个简化的 `harbor-values.yaml` 示例 (用于演示，生产环境需要更详细配置):
    ```yaml
    # harbor-values.yaml
    expose:
      type: ingress # 或者 LoadBalancer, NodePort
      ingress:
        hosts:
          core: harbor.yourdomain.com # 替换为您的域名
        # className: "nginx" # 如果您有多个 Ingress Controller 或需要指定
    externalURL: https://harbor.yourdomain.com # 替换为您的域名

    harborAdminPassword: "YourStrongPassword" # 务必修改

    # 内部 PostgreSQL (用于演示，生产环境可考虑外部 PostgreSQL)
    database:
      type: internal
    # 内部 Redis (用于演示)
    redis:
      type: internal

    # 存储配置 (示例: 使用 PVC，您需要有可用的 StorageClass)
    persistence:
      enabled: true
      resourcePolicy: "keep"
      persistentVolumeClaim:
        registry:
          storageClass: "your-storage-class" # 替换为您的 StorageClass
          accessMode: ReadWriteOnce
          size: 100Gi
        chartmuseum:
          storageClass: "your-storage-class"
          accessMode: ReadWriteOnce
          size: 5Gi
        jobservice:
          storageClass: "your-storage-class"
          accessMode: ReadWriteOnce
          size: 1Gi
        database:
          storageClass: "your-storage-class"
          accessMode: ReadWriteOnce
          size: 10Gi
        redis:
          storageClass: "your-storage-class"
          accessMode: ReadWriteOnce
          size: 1Gi
        trivy:
          storageClass: "your-storage-class"
          accessMode: ReadWriteOnce
          size: 5Gi
    ```

3.  部署 Harbor:
    ```bash
    # 创建命名空间 (推荐)
    kubectl create namespace harbor
    # 安装 Harbor
    helm install harbor harbor/harbor -f harbor-values.yaml -n harbor --create-namespace
    ```
4.  验证部署:
    等待所有 Harbor Pods 启动并运行正常。通过配置的域名访问 Harbor UI。

(旧的独立安装方式，仅供参考)
```bash
# 1.  从 https://github.com/goharbor/harbor/releases 下载 Harbor 安装包。
# 2.  解压并配置 harbor.yml 文件 (HTTPS, 存储等)。
# 3.  运行 ./install.sh。
```
(参考官方文档: [https://goharbor.io/docs/latest/install-config/install-harbor-by-helm-chart/](https://goharbor.io/docs/latest/install-config/install-harbor-by-helm-chart/))

### 4.2. 日志与监控系统部署（Prometheus/Grafana 本地离线部署，OpenSearch 仅模板）

本节聚焦 Prometheus/Grafana 监控栈的本地/离线部署与实际问题排查，所有步骤与实际部署完全一致，便于复现和维护。OpenSearch 仅保留标准模板，后续如需实际部署请补充详细步骤。

##### 4.2.1 Prometheus/Grafana 监控栈（本地/离线部署最佳实践）

**推荐方式**：使用 kube-prometheus-stack Helm Chart，结合本地 PV、本地离线包和镜像导入，确保离线环境可用。

**实际部署流程**：
1. **准备本地存储目录与 PV**（以主节点 lsyzt 为例，路径与主机名请按实际情况调整）：
   ```bash
   sudo mkdir -p /data/k8s-local-storage/prometheus /data/k8s-local-storage/alertmanager /data/k8s-local-storage/grafana
   sudo chown -R 1000:1000 /data/k8s-local-storage/prometheus /data/k8s-local-storage/alertmanager /data/k8s-local-storage/grafana
   ```
   分别创建 PV（示例）：
   - `prometheus-pv.yaml`：
     ```yaml
     apiVersion: v1
     kind: PersistentVolume
     metadata:
       name: prometheus-pv
     spec:
       capacity:
         storage: 50Gi
       accessModes:
         - ReadWriteOnce
       storageClassName: local-storage
       local:
         path: /data/k8s-local-storage/prometheus
       nodeAffinity:
         required:
           nodeSelectorTerms:
             - matchExpressions:
                 - key: kubernetes.io/hostname
                   operator: In
                   values:
                     - lsyzt
     ```
   - `alertmanager-pv.yaml`、`grafana-pv.yaml` 类似，路径和容量按需调整。
   
   应用 PV：
   ```bash
   kubectl apply -f prometheus-pv.yaml
   kubectl apply -f alertmanager-pv.yaml
   kubectl apply -f grafana-pv.yaml
   ```

2. **准备 StorageClass**（如未创建） :
   ```yaml
   # local-storage-sc.yaml
   apiVersion: storage.k8s.io/v1
   kind: StorageClass
   metadata:
     name: local-storage
   provisioner: kubernetes.io/no-provisioner
   volumeBindingMode: WaitForFirstConsumer
   ```
   ```bash
   kubectl apply -f local-storage-sc.yaml
   ```

3. **准备 prometheus-values.yaml**（与实际一致，示例） :
   ```yaml
   grafana:
     enabled: true
     adminPassword: "minioadmin123" # 示例密码，实际以文档整理为准
     persistence:
       enabled: true
       storageClassName: local-storage
       size: 10Gi
     ingress:
       enabled: false # 如需 Ingress 按需开启
   prometheus:
     prometheusSpec:
       storageSpec:
         volumeClaimTemplate:
           spec:
             storageClassName: local-storage
             accessModes: ["ReadWriteOnce"]
             resources:
               requests:
                 storage: 50Gi
   alertmanager:
     alertmanagerSpec:
       storage:
         volumeClaimTemplate:
           spec:
             storageClassName: local-storage
             accessModes: ["ReadWriteOnce"]
             resources:
               requests:
                 storage: 10Gi
   ```

4. **离线包与镜像导入** :
   - 上传 `kube-prometheus-stack-73.2.0.tgz` 到服务器。
   - 镜像拉取失败时，需在本地下载相关镜像（如 `quay.io/prometheus/prometheus`、`grafana/grafana` 等），导出为 tar 包后上传服务器并导入 containerd：
     ```bash
     sudo ctr -n k8s.io images import prometheus-v2.51.2.tar
     sudo ctr -n k8s.io images import grafana-10.2.3.tar
     # 依次导入所有所需镜像
     # 镜像导入后，重启拉取失败的 Pod
     kubectl delete pod <pod-name> -n monitoring
     ```

5. **安装 kube-prometheus-stack** :
   ```bash
   kubectl create namespace monitoring
   helm install prometheus ./kube-prometheus-stack-73.2.0.tgz -f prometheus-values.yaml -n monitoring --create-namespace
   ```

6. **常见问题排查** :
   - Pod 卡在 `ImagePullBackOff`：确认镜像已导入 containerd，重启 Pod。
   - PVC 卡在 `Pending`：检查 PV 是否与 PVC 匹配（storageClass、容量、主机名等），`kubectl describe pvc/pv` 查看详细原因。
   - 端口转发访问 Grafana：
     ```bash
     kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
     # 浏览器访问 http://localhost:3000
     ```
   - 账号密码见文档整理表。

7. **验证** :
   ```bash
   kubectl get pods -n monitoring
   kubectl get pvc -n monitoring
   kubectl get pv
   ```

> 详细部署与排查流程已在本节覆盖，所有配置与实际部署保持一致。

##### 4.2.2 OpenSearch 日志系统（本地/离线部署实操）

本节以实际离线部署为例，详细说明 OpenSearch 在本地 Kubernetes 集群的完整部署流程，包括本地存储、离线镜像导入、PV/PVC 配置与常见问题排查。

**部署步骤如下：**

1. **准备本地存储目录与 PV**
   ```bash
   sudo mkdir -p /data/k8s-local-storage/opensearch
   sudo chown -R 1000:1000 /data/k8s-local-storage/opensearch
   ```
   新建 `opensearch-pv.yaml`：
   ```yaml
   apiVersion: v1
   kind: PersistentVolume
   metadata:
     name: opensearch-pv
   spec:
     capacity:
       storage: 20Gi
     accessModes:
       - ReadWriteOnce
     storageClassName: local-storage
     local:
       path: /data/k8s-local-storage/opensearch
     nodeAffinity:
       required:
         nodeSelectorTerms:
           - matchExpressions:
               - key: kubernetes.io/hostname
                 operator: In
                 values:
                   - lsyzt
   ```
   应用 PV：
   ```bash
   kubectl apply -f opensearch-pv.yaml
   ```

2. **准备 opensearch-values.yaml**（示例）
   ```yaml
   clusterName: "opensearch-cluster"
   nodeGroup: "master"
   replicas: 1
   persistence:
     enabled: true
     storageClass: "local-storage"
     size: "20Gi"
   extraEnvs:
     - name: OPENSEARCH_INITIAL_ADMIN_PASSWORD
       value: "OPENsearch@123"
   # 如需 Dashboards、账号密码等可补充
   ```

3. **离线下载并导入镜像**
   - 在有网络的主机（如 Windows）拉取并导出主镜像和 Init 容器镜像：
     ```powershell
     docker pull opensearchproject/opensearch:3.0.0
     docker save opensearchproject/opensearch:3.0.0 -o opensearch-3.0.0.tar
     docker pull busybox:latest
     docker save busybox:latest -o busybox-latest.tar
     ```
   - 上传 `opensearch-3.0.0.tar` 和 `busybox-latest.tar` 到服务器。
   - 在服务器导入镜像：
     ```bash
     sudo ctr -n k8s.io images import opensearch-3.0.0.tar
     sudo ctr -n k8s.io images import busybox-latest.tar
     ```

4. **安装 OpenSearch**
   ```bash
   kubectl create namespace logging
   helm install opensearch ./opensearch-3.0.0.tgz -f opensearch-values.yaml -n logging --create-namespace
   ```

5. **验证与排查**
   - 查看 Pod、PVC、PV 状态：
     ```bash
     kubectl get pods -n logging
     kubectl get pvc -n logging
     kubectl get pv
     ```
   - 如 Pod 卡在 `Init:ErrImagePull` 或 `ImagePullBackOff`，请用如下命令定位缺失镜像：
     ```bash
     kubectl describe pod -n logging opensearch-cluster-master-0
     ```
     按需补充导入所有报错的镜像，导入后删除 Pod 让其自动重建。
   - 如 PVC 卡在 Pending，检查 PV 与 PVC 的 storageClass、容量、主机名等是否一致。

> 说明：OpenSearch 离线部署时，所有用到的镜像（主容器和 Init 容器）都需提前导入。遇到镜像拉取失败，务必先用 `kubectl describe pod` 查明缺失镜像并补齐。

> OpenSearch 3.0.0 及以上版本必须设置强密码，建议将 admin 密码记录到“账号与密码整理”表格中，便于后续管理。

---

### 4.3. 容器持久化数据

#### 4.3.1 MinIO (对象存储，离线/本地部署实操)

本节以实际离线部署为例，详细说明 MinIO 在本地 Kubernetes 集群的完整部署流程，确保所有步骤与实际操作一致，便于复现和排查。

**部署流程如下：**

1. **准备本地存储目录与 PV**
   ```bash
   sudo mkdir -p /data/k8s-local-storage/minio
   sudo chown -R 1000:1000 /data/k8s-local-storage/minio
   ```
   新建 `minio-pv.yaml`：
   ```yaml
   apiVersion: v1
   kind: PersistentVolume
   metadata:
     name: minio-pv
   spec:
     capacity:
       storage: 20Gi
     accessModes:
       - ReadWriteOnce
     storageClassName: local-storage
     local:
       path: /data/k8s-local-storage/minio
     nodeAffinity:
       required:
         nodeSelectorTerms:
           - matchExpressions:
               - key: kubernetes.io/hostname
                 operator: In
                 values:
                   - lsyzt
   ```
   应用 PV：
   ```bash
   kubectl apply -f minio-pv.yaml
   ```

2. **准备 minio-values.yaml**（与实际一致，示例）
   ```yaml
   mode: standalone
   accessKey: "minioadmin"
   secretKey: "minioadmin123"
   persistence:
     enabled: true
     storageClass: "local-storage"
     size: 20Gi
   ingress:
     enabled: false # 如需 Ingress 按需开启
   resources:
     requests:
       memory: 512Mi
       cpu: 250m
   ```

3. **离线下载并导入镜像**
   - 在有网络的主机（如 Windows）拉取并导出 MinIO 镜像：
     ```powershell
     docker pull bitnami/minio:2024.6.4-debian-12-r0
     docker save bitnami/minio:2024.6.4-debian-12-r0 -o minio-2024.6.4-debian-12-r0.tar
     ```
   - 上传 `minio-2024.6.4-debian-12-r0.tar` 到服务器。
   - 在服务器导入镜像：
     ```bash
     sudo ctr -n k8s.io images import minio-2024.6.4-debian-12-r0.tar
     ```

4. **安装 MinIO**
   - 上传 `minio-14.6.5.tgz` Chart 包到服务器。
   - 安装 MinIO：
     ```bash
     kubectl create namespace minio-ns
     helm install minio ./minio-14.6.5.tgz -f minio-values.yaml -n minio-ns --create-namespace
     ```

5. **验证与排查**
   - 查看 Pod、PVC、PV 状态：
     ```bash
     kubectl get pods -n minio-ns
     kubectl get pvc -n minio-ns
     kubectl get pv
     ```
   - 如 Pod 卡在 `ImagePullBackOff`，请确认镜像已导入 containerd，导入后删除 Pod 让其自动重建。
   - 如 PVC 卡在 Pending，检查 PV 与 PVC 的 storageClass、容量、主机名等是否一致。
   - 端口转发访问 MinIO 控制台：
     ```bash
     kubectl port-forward svc/minio 9000:9000 -n minio-ns
     # 浏览器访问 http://localhost:9000
     # 默认账号密码见下表
     ```

> 说明：所有用到的镜像需提前导入，遇到镜像拉取失败，务必先用 `kubectl describe pod` 查明缺失镜像并补齐。账号密码建议同步到“账号与密码整理”表格，便于后续管理。

#### 4.3.2. PostgreSQL (关系型数据库)
**版本**: 16
**推荐部署方式**: 使用 PostgreSQL Operator (如 Crunchy Data, Zalando) 或 Bitnami PostgreSQL HA Helm Chart 在 Kubernetes 中部署。

**安装步骤 (使用 Bitnami PostgreSQL HA Helm Chart 示例):**
1.  添加 Bitnami Helm 仓库 (如果尚未添加):
    ```bash
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo update
    ```
2.  准备 `postgresql-values.yaml`。
    ```yaml
    # postgresql-values.yaml (HA 简化示例)
    global:
      storageClass: "your-storage-class" # 替换
    # postgresqlUsername: your_user
    # postgresqlPassword: "YourStrongPassword" # 修改
    # postgresqlDatabase: your_db
    primary:
      persistence:
        size: 20Gi
    readReplicas:
      replicas: 1 # 可选的读副本
      persistence:
        size: 20Gi
    ```
3.  部署 PostgreSQL HA:
    ```bash
    # 创建命名空间
    kubectl create namespace database
    # 安装
    helm install postgresql-ha bitnami/postgresql-ha -f postgresql-values.yaml -n database --create-namespace
    ```
(旧的独立安装方式，仅供参考)
```bash
# sudo apt update
# sudo apt install -y postgresql postgresql-contrib
# sudo systemctl start postgresql
# sudo systemctl enable postgresql
```
(参考: Bitnami PostgreSQL HA Chart 文档)

### 4.4. 网络数据存储

- **Calico/Cilium 自带存储机制**:
  - Calico 通常使用 Kubernetes etcd 或其自带的 etcd 作为数据存储。
  - Cilium 也可以使用 Kubernetes etcd 或其他键值存储。
  - 这些通常作为 CNI 插件安装和配置的一部分进行处理，不需要单独部署存储系统。
---

## 账号与密码整理（部署默认/示例配置）

| 组件         | 用户名         | 密码              | 说明                  |
|--------------|----------------|-------------------|-----------------------|
| PostgreSQL   | postgres       | ai-platform-2024  | 管理员，Helm values   |
| PostgreSQL   | aiuser         | aiuser-2024       | 普通用户，Helm values |
| Redis        | (无用户名)     | redis-2024        | Helm values           |
| MinIO        | minioadmin     | minioadmin123     | minio-values.yaml     |
| OpenSearch   | admin          | OPENsearch@123     | opensearch-values.yaml |

> 说明：如有自定义 values.yaml，请以实际配置为准。生产环境建议修改所有默认密码！
