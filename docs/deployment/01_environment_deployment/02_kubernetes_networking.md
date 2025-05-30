# ⭐ AI中台 - Kubernetes集群部署

本文档指导如何基于已配置的Docker环境部署Kubernetes集群，包括集群初始化、网络配置和基础服务。

> **📋 前置条件**: 在开始Kubernetes集群部署之前，请确保已完成：
> - ✅ [操作系统安装与基础配置](./00_os_installation_ubuntu.md)
> - ✅ [容器化平台部署](./01_container_platform_setup.md) - Docker Engine已就绪
> - ✅ 所有节点网络互通且满足Kubernetes硬件要求

## ⏱️ 预计部署时间
- **Kubernetes组件安装**: 20-30分钟  
- **集群初始化**: 15-25分钟
- **网络插件配置**: 10-20分钟
- **基础服务部署**: 15-30分钟
- **总计**: 1-1.5小时

## 🎯 部署目标
✅ Kubernetes 1.28.8 集群环境  
✅ CNI网络插件 (Calico)  
✅ Ingress控制器 (NGINX)  
✅ 基础监控和管理工具  
✅ 集群健康验证

## 1. 集群准备工作

### 1.1 所有节点基础配置

在所有将要加入集群的节点上执行以下操作：

```bash
# 禁用swap (Kubernetes要求)
sudo swapoff -a
# 永久禁用swap
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# 配置内核模块
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# 配置内核参数
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system

# 验证containerd已正确配置
sudo systemctl status containerd
```

### 1.2 配置Containerd for Kubernetes

```bash
# 生成containerd默认配置
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# 配置systemd cgroup driver (重要!)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml

# 重启containerd服务
sudo systemctl restart containerd
sudo systemctl enable containerd

# 验证配置
sudo systemctl status containerd
```

## 2. Kubernetes组件安装

### 2.1 安装kubeadm、kubelet、kubectl

```bash
# 安装必要的依赖
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# 添加Kubernetes官方GPG密钥
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# 添加Kubernetes APT源
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# 更新包索引
sudo apt-get update

# 安装指定版本的Kubernetes组件
KUBE_VERSION="1.28.8-1.1"
sudo apt-get install -y kubelet=${KUBE_VERSION} kubeadm=${KUBE_VERSION} kubectl=${KUBE_VERSION}

# 锁定版本防止自动升级
sudo apt-mark hold kubelet kubeadm kubectl

# 验证安装
kubeadm version
kubelet --version
kubectl version --client
```

### 2.2 国内镜像源配置 (可选)

如果网络访问Kubernetes官方镜像有困难，可以使用阿里云镜像源：

```bash
# 使用阿里云镜像源
curl -fsSL https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.28/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubelet=${KUBE_VERSION} kubeadm=${KUBE_VERSION} kubectl=${KUBE_VERSION}
```

## 3. 集群初始化

### 3.1 Master节点初始化

**仅在主节点(Control Plane)上执行**：

```bash
# 设置集群配置变量
MASTER_IP="<YOUR_MASTER_NODE_IP>"  # 替换为实际IP
POD_NETWORK_CIDR="192.168.0.0/16"  # Calico默认网段

# 预拉取镜像 (可选，但推荐)
sudo kubeadm config images pull --kubernetes-version=v1.28.8

# 初始化集群
sudo kubeadm init \
  --pod-network-cidr=${POD_NETWORK_CIDR} \
  --kubernetes-version=v1.28.8 \
  --apiserver-advertise-address=${MASTER_IP} \
  --cri-socket=unix:///var/run/containerd/containerd.sock

# 配置kubectl (在主节点上)
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 验证集群状态
kubectl get nodes
kubectl get pods -A
```

**重要**: 保存初始化输出中的`kubeadm join`命令，用于添加工作节点。

### 3.2 Worker节点加入集群

在每个工作节点上执行初始化时输出的join命令：

```bash
# 示例命令 (实际使用kubeadm init输出的命令)
sudo kubeadm join <MASTER_IP>:6443 --token <TOKEN> \
    --discovery-token-ca-cert-hash sha256:<HASH> \
    --cri-socket=unix:///var/run/containerd/containerd.sock
```

## 4. 网络插件部署

### 4.1 Calico CNI安装

Calico是一个成熟的Kubernetes网络插件，提供网络策略功能：

```bash
# 下载Calico Operator
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml

# 创建Calico安装配置
cat <<EOF | kubectl apply -f -
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
    - blockSize: 26
      cidr: 192.168.0.0/16
      encapsulation: VXLANCrossSubnet
      natOutgoing: Enabled
      nodeSelector: all()
---
apiVersion: operator.tigera.io/v1
kind: APIServer
metadata:
  name: default
spec: {}
EOF

# 等待Calico Pods启动
echo "等待Calico Pods启动..."
kubectl wait --for=condition=ready pod -l k8s-app=calico-node -n calico-system --timeout=300s

# 验证Calico安装
kubectl get pods -n calico-system
kubectl get nodes -o wide
```

### 4.2 网络连通性测试

```bash
# 创建测试Pod
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: network-test-1
  namespace: default
spec:
  containers:
  - name: test
    image: busybox:1.35
    command: ["/bin/sh", "-c", "sleep 3600"]
---
apiVersion: v1
kind: Pod
metadata:
  name: network-test-2
  namespace: default
spec:
  containers:
  - name: test
    image: busybox:1.35
    command: ["/bin/sh", "-c", "sleep 3600"]
EOF

# 等待Pod启动
kubectl wait --for=condition=ready pod network-test-1 --timeout=60s
kubectl wait --for=condition=ready pod network-test-2 --timeout=60s

# 测试Pod间网络连通性
echo "测试Pod间网络连通性..."
POD_IP_1=$(kubectl get pod network-test-1 -o jsonpath='{.status.podIP}')
POD_IP_2=$(kubectl get pod network-test-2 -o jsonpath='{.status.podIP}')

kubectl exec network-test-1 -- ping -c 3 $POD_IP_2
kubectl exec network-test-2 -- ping -c 3 $POD_IP_1

# 清理测试资源
kubectl delete pod network-test-1 network-test-2
```

## 5. Ingress控制器部署

### 5.1 NGINX Ingress Controller

```bash
# 部署NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.4/deploy/static/provider/baremetal/deploy.yaml

# 等待Ingress Controller启动
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

# 验证安装
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

### 5.2 配置Ingress服务

```bash
# 将Ingress Controller Service改为NodePort类型 (生产环境建议使用LoadBalancer)
kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec": {"type": "NodePort"}}'

# 获取Ingress Controller的NodePort
INGRESS_HTTP_PORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}')
INGRESS_HTTPS_PORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')

echo "NGINX Ingress HTTP Port: $INGRESS_HTTP_PORT"
echo "NGINX Ingress HTTPS Port: $INGRESS_HTTPS_PORT"
```

## 6. 基础服务部署

### 6.1 Kubernetes Dashboard (可选)

```bash
# 部署Kubernetes Dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# 创建管理员用户
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
EOF

# 获取Dashboard访问Token
kubectl -n kubernetes-dashboard create token admin-user
```

### 6.2 MetalLB负载均衡器 (可选)

如果在裸机环境中需要LoadBalancer服务：

```bash
# 部署MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml

# 等待MetalLB启动
kubectl wait --namespace metallb-system \
  --for=condition=ready pod \
  --selector=app=metallb \
  --timeout=300s

# 配置IP地址池 (请根据实际网络环境调整)
cat <<EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: ai-platform-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.200-192.168.1.250  # 调整为实际可用的IP范围
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: ai-platform-l2
  namespace: metallb-system
spec:
  ipAddressPools:
  - ai-platform-pool
EOF
```

## 7. 集群验证和测试

### 7.1 集群状态检查

创建集群检查脚本：

```bash
# 创建集群检查脚本
sudo tee /usr/local/bin/check-k8s-cluster.sh << 'EOF'
#!/bin/bash

echo "=== Kubernetes 集群状态检查 ==="
echo

echo "集群节点状态:"
kubectl get nodes -o wide
echo

echo "系统Pod状态:"
kubectl get pods -A | grep -E "(kube-system|calico-system|ingress-nginx)"
echo

echo "集群组件状态:"
kubectl get componentstatuses
echo

echo "集群资源使用情况:"
kubectl top nodes 2>/dev/null || echo "Metrics Server未安装"
echo

echo "网络插件状态:"
kubectl get pods -n calico-system -o wide
echo

echo "Ingress控制器状态:"
kubectl get pods -n ingress-nginx -o wide
echo

echo "=== 集群检查完成 ==="
EOF

chmod +x /usr/local/bin/check-k8s-cluster.sh

# 运行检查
/usr/local/bin/check-k8s-cluster.sh
```

### 7.2 测试应用部署

```bash
# 部署测试应用
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-test
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-test
  template:
    metadata:
      labels:
        app: nginx-test
    spec:
      containers:
      - name: nginx
        image: nginx:1.25-alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-test-service
  namespace: default
spec:
  selector:
    app: nginx-test
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-test-ingress
  namespace: default
spec:
  ingressClassName: nginx
  rules:
  - host: test.ai-platform.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx-test-service
            port:
              number: 80
EOF

# 验证测试应用
kubectl get pods -l app=nginx-test
kubectl get svc nginx-test-service
kubectl get ingress nginx-test-ingress

# 测试访问 (需要配置hosts文件)
echo "测试访问说明:"
echo "1. 添加到 /etc/hosts: <任意节点IP> test.ai-platform.local"
echo "2. 访问: http://test.ai-platform.local:$INGRESS_HTTP_PORT"
```

## 8. 下一步部署指引

Kubernetes集群部署完成后，可以继续部署存储和资源管理：

> 📋 **下一步**: [Kubernetes存储系统](./03_storage_systems_kubernetes.md)
> 
> 该文档包含：
> - ✅ 持久化存储配置
> - ✅ StorageClass设置
> - ✅ 数据备份策略

> 📋 **同时进行**: [Kubernetes资源管理](./04_resource_management_kubernetes.md)
> 
> 该文档包含：
> - ✅ 资源配额管理
> - ✅ 命名空间规划
> - ✅ 监控和日志

## 📝 重要运维说明

### 集群维护

```bash
# 定期检查集群健康状态
kubectl get nodes
kubectl get pods -A

# 查看集群事件
kubectl get events --sort-by=.metadata.creationTimestamp

# 清理完成的Pod
kubectl delete pods --field-selector=status.phase==Succeeded -A

# 更新集群证书 (证书即将过期时)
sudo kubeadm certs renew all
```

### 故障排查

```bash
# 查看Pod日志
kubectl logs <pod-name> -n <namespace>

# 查看Pod详细信息
kubectl describe pod <pod-name> -n <namespace>

# 查看节点详细信息
kubectl describe node <node-name>

# 查看集群组件日志
sudo journalctl -u kubelet -f
```

---
*文档更新时间: 2025年5月30日 - Kubernetes 1.28.8集群部署*
