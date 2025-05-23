# AI 中台 - Kubernetes 存储系统部署

本文档指导如何为 AI 中台的 Kubernetes 集群部署和配置各类存储系统，包括镜像仓库、日志存储、持久化数据存储等。

## 4. 存储系统

### 4.1. Harbor (容器镜像仓库)

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

### 4.2. 日志数据存储与分析

#### 4.2.1. Prometheus (监控与告警)
**推荐部署方式**: 使用 `kube-prometheus-stack` Helm Chart 在 Kubernetes 中部署。

**前提**:
- Kubernetes 集群已运行。
- Helm 3 已安装。

**安装步骤 (使用 `kube-prometheus-stack` Helm Chart):**
1.  添加 Prometheus Community Helm 仓库:
    ```bash
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    ```
2.  准备 `prometheus-values.yaml` (可选，用于自定义配置)。
    例如，配置 Grafana 的 Ingress、持久化存储等。
    ```yaml
    # prometheus-values.yaml (示例)
    grafana:
      enabled: true
      adminPassword: "YourGrafanaPassword" # 修改密码
      ingress:
        enabled: true
        hosts:
          - grafana.yourdomain.com # 替换为您的域名
        # ingressClassName: nginx # 如果需要
    prometheus:
      prometheusSpec:
        storageSpec:
          volumeClaimTemplate:
            spec:
              storageClassName: your-storage-class # 替换为您的 StorageClass
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: 50Gi
    alertmanager:
      alertmanagerSpec:
        storage:
          volumeClaimTemplate:
            spec:
              storageClassName: your-storage-class # 替换为您的 StorageClass
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: 10Gi
    ```
3.  部署 `kube-prometheus-stack`:
    ```bash
    # 创建命名空间 (推荐)
    kubectl create namespace monitoring
    # 安装
    helm install prometheus prometheus-community/kube-prometheus-stack -f prometheus-values.yaml -n monitoring --create-namespace
    ```
(参考官方文档: [https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack))

#### 4.2.2. OpenSearch 和 OpenSearch Dashboards (替代 ELK Stack)
**推荐部署方式**: 使用 Helm Chart 在 Kubernetes 中部署。

**许可证提醒**: OpenSearch (Apache 2.0 许可证) 是推荐的替代方案。

**安装步骤 (使用 OpenSearch Helm Chart):**
1.  添加 OpenSearch Helm 仓库:
    ```bash
    helm repo add opensearch https://opensearch-project.github.io/helm-charts/
    helm repo update
    ```
2.  准备 `opensearch-values.yaml` (可选，用于自定义配置)。
    关键配置包括持久化、副本数、资源限制等。
    ```yaml
    # opensearch-values.yaml (简化示例)
    clusterName: "opensearch-cluster"
    nodeGroup: "master" # 示例，可以配置多个节点组 (master, data, client)
    replicas: 1 # 用于演示，生产环境至少3个 master, 多个 data 节点
    persistence:
      enabled: true
      storageClass: "your-storage-class" # 替换
      size: "20Gi"
    # opensearchDashboards.enabled: true (通常 Helm chart 会包含 Dashboards)
    # opensearchDashboards.replicas: 1
    # opensearchDashboards.persistence.enabled: true
    # opensearchDashboards.persistence.storageClass: "your-storage-class"
    # opensearchDashboards.ingress.enabled: true
    # opensearchDashboards.ingress.hosts[0].host: opensearch.yourdomain.com
    # opensearchDashboards.ingress.hosts[0].path: /
    ```
3.  部署 OpenSearch (通常包含 OpenSearch Dashboards):
    ```bash
    # 创建命名空间
    kubectl create namespace logging
    # 安装 (通常一个 chart 会同时部署 OpenSearch 和 OpenSearch Dashboards)
    helm install opensearch opensearch/opensearch -f opensearch-values.yaml -n logging --create-namespace
    # 如果 Dashboards 是分开的 chart:
    # helm install opensearch-dashboards opensearch/opensearch-dashboards -f dashboards-values.yaml -n logging
    ```
(参考官方文档: [https://opensearch.org/docs/latest/opensearch/install/helm/](https://opensearch.org/docs/latest/opensearch/install/helm/))

### 4.3. 容器持久化数据

#### 4.3.1. MinIO (对象存储)
**推荐部署方式**: 使用 MinIO Kubernetes Operator 或 Helm Chart 在 Kubernetes 中部署。

**许可证提醒**: MinIO 使用 AGPL v3.0。

**安装步骤 (使用 MinIO Helm Chart - Standalone Mode 示例):**
1.  添加 MinIO Helm 仓库:
    ```bash
    helm repo add minio https://operator.min.io/
    helm repo update
    ```
2.  准备 `minio-values.yaml` (可选)。
    ```yaml
    # minio-values.yaml (Standalone 简化示例)
    mode: standalone
    accessKey: "YOURACCESSKEY" # 修改
    secretKey: "YOURSECRETKEY" # 修改
    persistence:
      enabled: true
      storageClass: "your-storage-class" # 替换
      size: 100Gi
    ingress:
      enabled: true
      hosts:
        - minio.yourdomain.com # 替换
      # className: "nginx"
    ```
3.  部署 MinIO:
    ```bash
    # 创建命名空间
    kubectl create namespace minio-ns
    # 安装 (使用旧的 stable/minio chart，官方推荐 Operator，但 Helm chart 仍可用)
    # helm install minio minio/minio -f minio-values.yaml -n minio-ns --create-namespace
    # 或者使用新的 MinIO Operator 提供的 Helm Chart (如果适用)
    # helm install minio-operator minio/operator -n minio-operator --create-namespace
    # kubectl apply -f tenant.yaml # (需要定义 Tenant CRD)
    # 对于简单部署，可以直接使用 Bitnami MinIO chart
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm install minio bitnami/minio -f minio-values.yaml -n minio-ns --create-namespace
    ```
(参考: [https://min.io/docs/minio/kubernetes/upstream/index.html](https://min.io/docs/minio/kubernetes/upstream/index.html) 和 Bitnami MinIO Chart 文档)

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
