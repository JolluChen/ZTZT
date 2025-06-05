# ⭐ AI中台 - Kubernetes集群部署

本文档指导如何基于已配置的Docker环境部署Kubernetes集群，包括集群初始化、网络配置和基础服务。

> **📋 前置条件**: 在开始Kubernetes集群部署之前，请确保已完成：
> - ✅ [操作系统安装与基础配置](./00_os_installation_ubuntu.md)
> - ✅ [容器化平台部署](./01_container_platform_setup.md) - Docker Engine已就绪
> - ✅ 所有节点网络互通且满足Kubernetes硬件要求

## 📑 文档目录

- [⏱️ 预计部署时间](#️-预计部署时间)
- [🎯 部署目标](#-部署目标)
- [🚨 实际部署经验总结](#-实际部署经验总结)
- [1. 集群准备工作](#1-集群准备工作)
  - [1.1 所有节点基础配置](#11-所有节点基础配置)
  - [1.2 配置Containerd for Kubernetes](#12-配置containerd-for-kubernetes)
  - [1.3 验证 SystemdCgroup 配置](#13-验证-systemdcgroup-配置)
- [2. Kubernetes组件安装](#2-kubernetes组件安装)
  - [2.1 安装kubeadm、kubelet、kubectl](#21-安装kubeadmkubeletkubectl)
  - [2.2 配置kubelet](#22-配置kubelet)
- [3. 集群初始化](#3-集群初始化)
  - [3.1 Master节点初始化](#31-master节点初始化)
  - [3.2 配置kubectl](#32-配置kubectl)
  - [3.3 Worker节点加入集群](#33-worker节点加入集群)
  - [3.4 集群初始化故障排查](#34-集群初始化故障排查)
- [4. 网络插件部署](#4-网络插件部署)
  - [4.1 选择网络插件](#41-选择网络插件)
  - [4.2 部署Flannel网络插件](#42-部署flannel网络插件)
  - [4.3 部署Calico网络插件(替代方案)](#43-部署calico网络插件替代方案)
  - [4.4 验证网络插件](#44-验证网络插件)
  - [4.5 网络连通性测试](#45-网络连通性测试)
  - [4.6 网络插件故障排查](#46-网络插件故障排查)
  - [4.7 完整网络验证](#47-完整网络验证)
  - [4.8 生产环境网络优化配置](#48-生产环境网络优化配置)
- [5. Ingress控制器部署](#5-ingress控制器部署)
  - [5.1 NGINX Ingress Controller部署](#51-nginx-ingress-controller部署)
  - [5.2 Ingress Controller故障排查](#52-ingress-controller故障排查)
  - [5.3 验证Ingress Controller](#53-验证ingress-controller)
  - [5.4 Ingress测试应用](#54-ingress测试应用)
- [6. 🔒 集群安全配置](#6--集群安全配置)
  - [6.1 网络安全策略](#61-网络安全策略)
  - [6.2 RBAC安全加固](#62-rbac安全加固)
  - [6.3 Pod安全标准](#63-pod安全标准)
  - [6.4 集群访问安全](#64-集群访问安全)
  - [6.5 定期安全检查脚本](#65-定期安全检查脚本)
- [7. 集群验证与测试](#7-集群验证与测试)
  - [7.1 集群基础功能验证](#71-集群基础功能验证)
  - [7.2 完整功能测试](#72-完整功能测试)
- [8. 部署总结](#8-部署总结)
  - [8.1 部署完成检查清单](#81-部署完成检查清单)
  - [8.2 实际部署时间统计](#82-实际部署时间统计)
  - [8.3 集群状态监控](#83-集群状态监控)
- [故障排查联系方式](#故障排查联系方式)
- [部署成功标志](#部署成功标志)

## ⏱️ 预计部署时间
- **Kubernetes组件安装**: 20-30分钟  
- **集群初始化**: 15-25分钟
- **网络插件配置**: 10-20分钟
- **基础服务部署**: 15-30分钟
- **总计**: 1-1.5小时

## 🎯 部署目标
✅ Kubernetes 1.28.8 集群环境  
✅ CNI网络插件 (Flannel/Calico - 基于网络环境选择)  
✅ Ingress控制器 (NGINX)  
✅ 基础监控和管理工具  
✅ 集群健康验证

## 📋 版本兼容性矩阵

| 组件 | 推荐版本 | 兼容版本范围 | 备注 |
|------|---------|-------------|------|
| **Ubuntu** | 24.04 LTS | 22.04+ | 本文档基于24.04验证 |
| **Kubernetes** | 1.28.8 | 1.28.x | 生产稳定版本 |
| **containerd** | 1.7.x | 1.6.x+ | 包含在Docker安装中 |
| **Flannel** | v0.24.x | v0.22.x+ | 推荐用于受限网络 |
| **Calico** | v3.27.x | v3.25.x+ | 推荐用于生产环境 |
| **NGINX Ingress** | v1.9.x | v1.8.x+ | 官方维护版本 |

> **⚠️ 版本升级提醒**: 
> - Kubernetes组件版本应保持一致性
> - 跨大版本升级前请先在测试环境验证
> - CNI插件版本需与Kubernetes版本兼容

## 🚨 实际部署经验总结
> **基于实际部署过程的关键发现 (Ubuntu 24.04 LTS + Kubernetes 1.28.8)**:
> - **网络插件选择**: 在受限网络环境下，Flannel比Calico更稳定可靠
> - **CIDR配置一致性**: 确保kubeadm init的--pod-network-cidr与网络插件配置完全匹配
> - **镜像拉取**: 配置国内镜像源可显著提升部署成功率，建议预拉取pause容器
> - **自定义配置**: 使用本地配置文件比在线下载更可靠
> - **RBAC权限**: Ingress Controller部署可能需要额外的ClusterRole权限修复
> - **Admission Webhook**: 建议在受限环境中删除validatingwebhookconfiguration
> - **部署时长**: 实际部署时间约2-3小时，包含问题排查和解决

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

**关键配置**: 以下配置基于实际部署经验，可有效解决镜像拉取和pause容器问题。

```bash
# 生成containerd默认配置
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# 配置containerd国内镜像源 (解决镜像拉取超时问题)
sudo tee -a /etc/containerd/config.toml <<EOF

# 配置国内镜像源以提升拉取速度和成功率
[plugins."io.containerd.grpc.v1.cri".registry]
  config_path = ""

  [plugins."io.containerd.grpc.v1.cri".registry.auths]

  [plugins."io.containerd.grpc.v1.cri".registry.configs]

  [plugins."io.containerd.grpc.v1.cri".registry.headers]

  [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
      endpoint = ["https://registry-1.docker.io", "https://y8y5jkya.mirror.aliyuncs.com"]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."k8s.gcr.io"]
      endpoint = ["https://registry.aliyuncs.com/google_containers"]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."registry.k8s.io"]
      endpoint = ["https://registry.aliyuncs.com/google_containers"]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."quay.io"]
      endpoint = ["https://quay.mirrors.ustc.edu.cn"]
EOF

# 重启containerd服务
sudo systemctl restart containerd
sudo systemctl enable containerd

# 验证配置
sudo systemctl status containerd

# ⭐ 重要：预拉取pause容器 (解决pause容器问题)
echo "预拉取pause容器..."
sudo crictl pull registry.aliyuncs.com/google_containers/pause:3.9
sudo ctr -n k8s.io image tag registry.aliyuncs.com/google_containers/pause:3.9 registry.k8s.io/pause:3.9
```

### 1.3 验证 SystemdCgroup 配置

在配置完 Containerd 后，验证 SystemdCgroup 设置：

```bash
# 验证 SystemdCgroup 配置
grep -A 5 -B 5 "SystemdCgroup.*true" /etc/containerd/config.toml

# 应该看到类似输出:
# [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
#   BinaryName = ""
#   ...
#   SystemdCgroup = true
```

如果配置正确，继续下一步。如果没有找到或值为 false，重新执行：

```bash
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml
sudo systemctl restart containerd
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
# ⚠️ 注意：如果官方源可以正常访问，建议优先使用官方源
# 使用阿里云镜像源作为备选方案

# 清理现有配置
sudo rm -f /etc/apt/keyrings/kubernetes-apt-keyring.gpg
sudo rm -f /etc/apt/sources.list.d/kubernetes.list

# 重新添加阿里云镜像源
curl -fsSL https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.28/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list

# 更新包索引
sudo apt-get update

# 验证包是否可用
apt-cache madison kubelet kubeadm kubectl

# 安装Kubernetes组件
KUBE_VERSION="1.28.8-1.1"
sudo apt-get install -y kubelet=${KUBE_VERSION} kubeadm=${KUBE_VERSION} kubectl=${KUBE_VERSION}
```

### 2.3 故障排查指南

如果遇到包安装问题：

```bash
# 问题1: 无法定位包 (Unable to locate package)
# 解决方案: 重新配置APT源
sudo rm -f /etc/apt/keyrings/kubernetes-apt-keyring.gpg
sudo rm -f /etc/apt/sources.list.d/kubernetes.list

# 重新添加官方源
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
apt-cache search kubelet  # 骜证包是否可用

# 问题2: GPG密钥验证失败
# 解决方案: 清理并重新添加密钥
sudo apt-key del $(sudo apt-key list | grep -B1 Kubernetes | head -1 | awk '{print $2}' | tr -d '/')
# 然后重新执行密钥添加步骤

# 问题3: 网络连接问题
# 解决方案: 检查网络连接
curl -I https://pkgs.k8s.io  # 测试官方源连通性
curl -I https://mirrors.aliyun.com  # 测试阿里云源连通性
```

## 3. 集群初始化

### 3.1 Master节点初始化

**仅在主节点(Control Plane)上执行**：

```bash
# 获取主节点IP地址 (选择合适的网络接口)
# 方法1: 查看所有网络接口
ip addr show
# 示例输出:
# eno1: inet 192.168.110.88/24  (主网络接口)
# eno2: inet 192.168.110.89/24  (备用网络接口)

# 方法2: 自动获取主IP
MASTER_IP=$(ip route get 1 | awk '{print $7; exit}')
# 或手动设置 (根据实际网络环境调整)
MASTER_IP="192.168.110.88"  # 使用实际的主节点IP

# 设置集群配置变量 (⭐ 重要：此处使用Flannel默认网段)
POD_NETWORK_CIDR="192.168.0.0/16"  # Flannel默认网段，与网络插件配置保持一致

echo "Master节点IP: $MASTER_IP"
echo "Pod网络CIDR: $POD_NETWORK_CIDR"

# 预拉取镜像 (强烈推荐：避免初始化时拉取失败)
sudo kubeadm config images pull --kubernetes-version=v1.28.8

# ⭐ 关键配置：初始化集群
sudo kubeadm init \
  --pod-network-cidr=${POD_NETWORK_CIDR} \
  --kubernetes-version=v1.28.8 \
  --apiserver-advertise-address=${MASTER_IP} \
  --cri-socket=unix:///var/run/containerd/containerd.sock \
  --ignore-preflight-errors=NumCPU,Mem

# 配置kubectl (在主节点上)
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 验证集群状态
kubectl get nodes
kubectl get pods -A

# ⭐ 实际部署经验：此时节点状态为NotReady是正常的，需要安装网络插件后才会变为Ready
echo "注意：节点状态为NotReady是正常的，安装网络插件后会变为Ready"
```

**重要**: 保存初始化输出中的`kubeadm join`命令，用于添加工作节点。

### 🚨 集群初始化常见问题及解决方案

基于实际部署经验，以下是常见问题和解决方案：

```bash
# 问题1: pause容器拉取失败
# 错误信息: failed to pull image "registry.k8s.io/pause:3.9"
# 解决方案: 预拉取并标记pause容器
sudo crictl pull registry.aliyuncs.com/google_containers/pause:3.9
sudo ctr -n k8s.io image tag registry.aliyuncs.com/google_containers/pause:3.9 registry.k8s.io/pause:3.9

# 问题2: kubeadm init 超时
# 解决方案: 增加超时时间并忽略预检查
sudo kubeadm init \
  --pod-network-cidr=${POD_NETWORK_CIDR} \
  --kubernetes-version=v1.28.8 \
  --apiserver-advertise-address=${MASTER_IP} \
  --cri-socket=unix:///var/run/containerd/containerd.sock \
  --ignore-preflight-errors=NumCPU,Mem \
  --v=5  # 增加日志详细程度

# 问题3: 初始化失败后重试
# 解决方案: 重置集群状态
sudo kubeadm reset --cri-socket=unix:///var/run/containerd/containerd.sock
sudo systemctl restart containerd
sudo systemctl restart kubelet
# 然后重新执行kubeadm init

# 问题4: 验证初始化是否成功
# 检查关键组件是否启动
kubectl get pods -n kube-system
# 应该看到: kube-apiserver, etcd, kube-controller-manager, kube-scheduler, coredns
```

### 3.2 Worker节点加入集群

在每个工作节点上执行初始化时输出的join命令：

```bash
# 示例命令 (实际使用kubeadm init输出的命令)
sudo kubeadm join <MASTER_IP>:6443 --token <TOKEN> \
    --discovery-token-ca-cert-hash sha256:<HASH> \
    --cri-socket=unix:///var/run/containerd/containerd.sock
```

## 4. 网络插件部署 - 生产环境最佳实践

### 4.1 网络插件选择指南

基于实际部署经验，不同网络环境的推荐方案：

| 网络环境 | 推荐插件 | 原因 | 适用场景 |
|---------|---------|------|---------|
| **受限网络/内网** | Flannel | 配置简单、稳定性高、资源占用少 | 企业内网、开发测试环境 |
| **公有云/开放网络** | Calico | 功能丰富、网络策略支持 | 生产环境、需要网络隔离 |
| **高性能需求** | Cilium | 基于eBPF、性能优异 | 大规模生产环境 |

### 4.2 Flannel CNI安装 (推荐：受限网络环境)

基于实际部署成功经验，Flannel在受限网络环境下表现最佳：

```bash
# 方案A: 在线安装 (网络环境良好时)
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# 方案B: 离线安装 (推荐：避免网络问题)
# 1. 下载并自定义Flannel配置
curl -o kube-flannel.yml https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# 2. 修改网络配置以匹配集群CIDR
# 重要：确保与kubeadm init时的--pod-network-cidr参数一致
sed -i 's|"Network": "10.244.0.0/16"|"Network": "192.168.0.0/16"|g' kube-flannel.yml

# 3. 应用配置
kubectl apply -f kube-flannel.yml

# 4. 验证部署
kubectl get pods -n kube-flannel
kubectl get nodes  # 节点状态应该变为Ready
```

### 4.3 自定义Flannel配置文件 (生产环境推荐)

创建完全自定义的Flannel配置，避免网络下载问题：

```bash
# 创建自定义Flannel配置
cat <<EOF | kubectl apply -f -
---
apiVersion: v1
kind: Namespace
metadata:
  labels:
    k8s-app: flannel
    pod-security.kubernetes.io/enforce: privileged
  name: kube-flannel
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-app: flannel
  name: flannel
  namespace: kube-flannel
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    k8s-app: flannel
  name: flannel
rules:
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
- apiGroups:
  - ""
  resources:
  - nodes
  verbs:
  - get
  - list
  - watch
- apiGroups:
  - ""
  resources:
  - nodes/status
  verbs:
  - patch
- apiGroups:
  - networking.k8s.io
  resources:
  - clustercidrs
  verbs:
  - list
  - watch
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  labels:
    k8s-app: flannel
  name: flannel
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flannel
subjects:
- kind: ServiceAccount
  name: flannel
  namespace: kube-flannel
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-flannel-cfg
  namespace: kube-flannel
  labels:
    tier: node
    k8s-app: flannel
    app: flannel
data:
  cni-conf.json: |
    {
      "name": "cbr0",
      "cniVersion": "0.3.1",
      "plugins": [
        {
          "type": "flannel",
          "delegate": {
            "hairpinMode": true,
            "isDefaultGateway": true
          }
        },
        {
          "type": "portmap",
          "capabilities": {
            "portMappings": true
          }
        }
      ]
    }
  net-conf.json: |
    {
      "Network": "192.168.0.0/16",
      "Backend": {
        "Type": "vxlan"
      }
    }
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: kube-flannel-ds
  namespace: kube-flannel
  labels:
    tier: node
    app: flannel
    k8s-app: flannel
spec:
  selector:
    matchLabels:
      app: flannel
  template:
    metadata:
      labels:
        tier: node
        app: flannel
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/os
                operator: In
                values:
                - linux
      hostNetwork: true
      priorityClassName: system-node-critical
      tolerations:
      - operator: Exists
        effect: NoSchedule
      serviceAccountName: flannel
      initContainers:
      - name: install-cni-plugin
        image: docker.io/flannel/flannel-cni-plugin:v1.2.0
        command:
        - cp
        args:
        - -f
        - /flannel
        - /opt/cni/bin/flannel
        volumeMounts:
        - name: cni-plugin
          mountPath: /opt/cni/bin
      - name: install-cni
        image: docker.io/flannel/flannel:v0.22.3
        command:
        - cp
        args:
        - -f
        - /etc/kube-flannel/cni-conf.json
        - /etc/cni/net.d/10-flannel.conflist
        volumeMounts:
        - name: cni
          mountPath: /etc/cni/net.d
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      containers:
      - name: kube-flannel
        image: docker.io/flannel/flannel:v0.22.3
        command:
        - /opt/bin/flanneld
        args:
        - --ip-masq
        - --kube-subnet-mgr
        resources:
          requests:
            cpu: "100m"
            memory: "50Mi"
        securityContext:
          privileged: false
          capabilities:
            add: ["NET_ADMIN", "NET_RAW"]
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: EVENT_QUEUE_DEPTH
          value: "5000"
        volumeMounts:
        - name: run
          mountPath: /run/flannel
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
        - name: xtables-lock
          mountPath: /run/xtables.lock
      volumes:
      - name: run
        hostPath:
          path: /run/flannel
      - name: cni-plugin
        hostPath:
          path: /opt/cni/bin
      - name: cni
        hostPath:
          path: /etc/cni/net.d
      - name: flannel-cfg
        configMap:
          name: kube-flannel-cfg
      - name: xtables-lock
        hostPath:
          path: /run/xtables.lock
          type: FileOrCreate
EOF

# 等待Flannel Pod启动
echo "等待Flannel Pod启动..."
kubectl wait --for=condition=ready pod -l app=flannel -n kube-flannel --timeout=300s

# 验证安装
kubectl get pods -n kube-flannel -o wide
kubectl get nodes -o wide
```

### 4.4 Calico CNI安装 (备选方案)

如果网络环境允许且需要网络策略功能：

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
      cidr: 192.168.0.0/16  # 注意：必须与kubeadm init的--pod-network-cidr一致
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

### 4.5 网络插件故障排查

基于实际部署经验的故障排查方法：

```bash
# 问题1: 网络插件Pod处于CrashLoopBackOff状态
# 检查Pod日志
kubectl logs -n kube-flannel -l app=flannel
kubectl logs -n calico-system -l k8s-app=calico-node

# 常见原因1: CIDR配置不匹配
# 检查集群CIDR配置
kubectl cluster-info dump | grep -i cluster-cidr
kubectl get nodes -o yaml | grep podCIDR

# 常见原因2: 网络插件配置错误
# 检查ConfigMap配置
kubectl get configmap -n kube-flannel kube-flannel-cfg -o yaml
kubectl describe configmap -n kube-flannel kube-flannel-cfg

# 问题2: 节点状态一直是NotReady
# 检查kubelet日志
sudo journalctl -u kubelet -f --no-pager

# 检查容器运行时状态
sudo systemctl status containerd
sudo crictl pods

# 问题3: Pod间网络不通
# 检查iptables规则
sudo iptables -t nat -L | grep KUBE
sudo iptables -L | grep KUBE

# 检查网络接口
ip route show
ip addr show flannel.1  # Flannel网络接口
```

### 4.6 网络插件切换指南

如果需要从一种网络插件切换到另一种：

```bash
# 切换网络插件的安全步骤
# 1. 备份现有配置
kubectl get all -A > cluster-backup-$(date +%Y%m%d).yaml

# 2. 卸载当前网络插件
# 卸载Calico
kubectl delete -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml

# 卸载Flannel
kubectl delete -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
# 或使用自定义配置文件卸载
kubectl delete -f kube-flannel.yml

# 3. 清理网络配置
sudo ip link delete flannel.1  # 删除Flannel接口
sudo ip link delete cali+  # 删除Calico接口（如果存在）

# 4. 重置网络配置
sudo systemctl restart containerd
sudo systemctl restart kubelet

# 5. 重新部署新的网络插件
# 参考上述相应插件的部署步骤

# 6. 验证切换结果
kubectl get nodes
kubectl get pods -A
```

### 4.7 网络连通性测试

部署网络插件后的完整验证流程：

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

# 获取Pod IP地址
POD_IP_1=$(kubectl get pod network-test-1 -o jsonpath='{.status.podIP}')
POD_IP_2=$(kubectl get pod network-test-2 -o jsonpath='{.status.podIP}')

echo "Pod 1 IP: $POD_IP_1"
echo "Pod 2 IP: $POD_IP_2"

# 测试Pod间网络连通性
echo "测试Pod间网络连通性..."
kubectl exec network-test-1 -- ping -c 3 $POD_IP_2
kubectl exec network-test-2 -- ping -c 3 $POD_IP_1

# 测试DNS解析
echo "测试DNS解析..."
kubectl exec network-test-1 -- nslookup kubernetes.default
kubectl exec network-test-1 -- nslookup network-test-2.default.svc.cluster.local

# 测试外网连通性
echo "测试外网连通性..."
kubectl exec network-test-1 -- ping -c 3 8.8.8.8
kubectl exec network-test-1 -- nslookup www.baidu.com

# 清理测试资源
kubectl delete pod network-test-1 network-test-2
```

### 4.8 生产环境网络优化配置

基于实际部署经验的性能优化建议：

```bash
# 1. 优化Flannel性能配置
# 修改kube-flannel配置，增加性能参数
kubectl patch configmap kube-flannel-cfg -n kube-flannel --patch='
data:
  net-conf.json: |
    {
      "Network": "192.168.0.0/16",
      "Backend": {
        "Type": "vxlan",
        "VNI": 1,
        "Port": 8472,
        "GBP": true,
        "Learning": false
      }
    }'

# 2. 配置Pod网络资源限制
kubectl patch daemonset kube-flannel-ds -n kube-flannel --patch='
spec:
  template:
    spec:
      containers:
      - name: kube-flannel
        resources:
          limits:
            cpu: "500m"
            memory: "200Mi"
          requests:
            cpu: "100m"
            memory: "100Mi"'

# 3. 优化内核网络参数
sudo tee /etc/sysctl.d/k8s-network.conf <<EOF
# 增加网络连接数
net.core.somaxconn = 32768
net.core.netdev_max_backlog = 5000

# 优化TCP性能
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_congestion_control = bbr

# 调整iptables性能
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 86400
EOF

sudo sysctl -p /etc/sysctl.d/k8s-network.conf
```

## 5. Ingress控制器部署

### 5.1 NGINX Ingress Controller

**基于实际部署经验的完整解决方案**：

```bash
# 方法1: 标准部署 (推荐先尝试)
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

### 🚨 Ingress Controller部署问题解决方案

基于实际部署经验，NGINX Ingress Controller可能遇到以下问题：

#### 问题1: RBAC权限不足

```bash
# 症状: Ingress Controller Pod处于CrashLoopBackOff状态
# 错误日志: forbidden: User "system:serviceaccount:ingress-nginx:ingress-nginx" cannot...

# 解决方案: 修复ClusterRole权限
kubectl patch clusterrole ingress-nginx --type='merge' -p='
{
  "rules": [
    {
      "apiGroups": [""],
      "resources": ["configmaps", "endpoints", "nodes", "pods", "secrets", "namespaces"],
      "verbs": ["list", "watch"]
    },
    {
      "apiGroups": ["coordination.k8s.io"],
      "resources": ["leases"],
      "verbs": ["list", "watch"]
    },
    {
      "apiGroups": [""],
      "resources": ["nodes"],
      "verbs": ["get"]
    },
    {
      "apiGroups": [""],
      "resources": ["services"],
      "verbs": ["get", "list", "watch"]
    },
    {
      "apiGroups": ["networking.k8s.io"],
      "resources": ["ingresses"],
      "verbs": ["get", "list", "watch"]
    },
    {
      "apiGroups": [""],
      "resources": ["events"],
      "verbs": ["create", "patch"]
    },
    {
      "apiGroups": ["networking.k8s.io"],
      "resources": ["ingresses/status"],
      "verbs": ["update"]
    },
    {
      "apiGroups": ["networking.k8s.io"],
      "resources": ["ingressclasses"],
      "verbs": ["get", "list", "watch"]
    },
    {
      "apiGroups": ["discovery.k8s.io"],
      "resources": ["endpointslices"],
      "verbs": ["list", "watch", "get"]
    }
  ]
}'

# 重启Ingress Controller
kubectl rollout restart deployment ingress-nginx-controller -n ingress-nginx
```

#### 问题2: Admission Webhook配置问题

```bash
# 症状: Ingress资源创建失败
# 错误信息: Internal error occurred: failed calling webhook "validate.nginx.ingress.kubernetes.io"

# 解决方案: 删除有问题的ValidatingWebhookConfiguration
kubectl delete validatingwebhookconfiguration ingress-nginx-admission

# 验证删除结果
kubectl get validatingwebhookconfiguration | grep ingress

# 如果需要，也可以删除MutatingWebhookConfiguration
kubectl delete mutatingwebhookconfiguration ingress-nginx-admission 2>/dev/null || true
```

#### 问题3: 简化版Ingress Controller部署

如果标准部署遇到问题，可以使用简化版配置：

```bash
# 创建简化版Ingress Controller配置
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: ingress-nginx
---
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: ingress-nginx
    app.kubernetes.io/component: controller
  name: ingress-nginx
  namespace: ingress-nginx
automountServiceAccountToken: true
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: ingress-nginx
  name: ingress-nginx
rules:
  - apiGroups:
      - ""
    resources:
      - configmaps
      - endpoints
      - nodes
      - pods
      - secrets
      - namespaces
    verbs:
      - list
      - watch
  - apiGroups:
      - coordination.k8s.io
    resources:
      - leases
    verbs:
      - list
      - watch
  - apiGroups:
      - ""
    resources:
      - nodes
    verbs:
      - get
  - apiGroups:
      - ""
    resources:
      - services
    verbs:
      - get
      - list
      - watch
  - apiGroups:
      - networking.k8s.io
    resources:
      - ingresses
    verbs:
      - get
      - list
      - watch
  - apiGroups:
      - ""
    resources:
      - events
    verbs:
      - create
      - patch
  - apiGroups:
      - networking.k8s.io
    resources:
      - ingresses/status
    verbs:
      - update
  - apiGroups:
      - networking.k8s.io
    resources:
      - ingressclasses
    verbs:
      - get
      - list
      - watch
  - apiGroups:
      - discovery.k8s.io
    resources:
      - endpointslices
    verbs:
      - list
      - watch
      - get
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: ingress-nginx
  name: ingress-nginx
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: ingress-nginx
subjects:
  - kind: ServiceAccount
    name: ingress-nginx
    namespace: ingress-nginx
---
apiVersion: v1
kind: ConfigMap
metadata:
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: ingress-nginx
    app.kubernetes.io/component: controller
  name: ingress-nginx-controller
  namespace: ingress-nginx
data:
  allow-snippet-annotations: "true"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: ingress-nginx
    app.kubernetes.io/component: controller
  name: ingress-nginx-controller
  namespace: ingress-nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
      app.kubernetes.io/instance: ingress-nginx
      app.kubernetes.io/component: controller
  template:
    metadata:
      labels:
        app.kubernetes.io/name: ingress-nginx
        app.kubernetes.io/instance: ingress-nginx
        app.kubernetes.io/component: controller
    spec:
      dnsPolicy: ClusterFirst
      containers:
        - name: controller
          image: registry.k8s.io/ingress-nginx/controller:v1.8.4
          imagePullPolicy: IfNotPresent
          args:
            - /nginx-ingress-controller
            - --election-id=ingress-controller-leader
            - --controller-class=k8s.io/ingress-nginx
            - --ingress-class=nginx
            - --configmap=$(POD_NAMESPACE)/ingress-nginx-controller
            - --validating-webhook=:8443
            - --validating-webhook-certificate=/usr/local/certificates/cert
            - --validating-webhook-key=/usr/local/certificates/key
            - --watch-ingress-without-class=true
          securityContext:
            capabilities:
              drop:
                - ALL
              add:
                - NET_BIND_SERVICE
            runAsUser: 101
            allowPrivilegeEscalation: true
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            - name: LD_PRELOAD
              value: /usr/local/lib/libmimalloc.so
          livenessProbe:
            failureThreshold: 5
            httpGet:
              path: /healthz
              port: 10254
              scheme: HTTP
            initialDelaySeconds: 10
            periodSeconds: 10
            successThreshold: 1
            timeoutSeconds: 1
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /healthz
              port: 10254
              scheme: HTTP
            initialDelaySeconds: 10
            periodSeconds: 10
            successThreshold: 1
            timeoutSeconds: 1
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
            - name: https
              containerPort: 443
              protocol: TCP
            - name: webhook
              containerPort: 8443
              protocol: TCP
          resources:
            requests:
              cpu: 100m
              memory: 90Mi
      nodeSelector:
        kubernetes.io/os: linux
      serviceAccountName: ingress-nginx
      terminationGracePeriodSeconds: 300
---
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: ingress-nginx
    app.kubernetes.io/component: controller
  name: nginx
spec:
  controller: k8s.io/ingress-nginx
---
apiVersion: v1
kind: Service
metadata:
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: ingress-nginx
    app.kubernetes.io/component: controller
  name: ingress-nginx-controller
  namespace: ingress-nginx
spec:
  type: NodePort
  ports:
    - name: http
      port: 80
      protocol: TCP
      targetPort: http
    - name: https
      port: 443
      protocol: TCP
      targetPort: https
  selector:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/instance: ingress-nginx
    app.kubernetes.io/component: controller
EOF

# 等待部署完成
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s
```

### 5.2 配置Ingress服务和端口信息

```bash
# 验证Ingress Controller部署状态
kubectl get pods -n ingress-nginx -o wide
kubectl get svc -n ingress-nginx

# 获取Ingress Controller的NodePort端口
INGRESS_HTTP_PORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}')
INGRESS_HTTPS_PORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')

echo "NGINX Ingress访问信息:"
echo "HTTP端口: $INGRESS_HTTP_PORT"
echo "HTTPS端口: $INGRESS_HTTPS_PORT"
echo "访问地址: http://192.168.110.88:$INGRESS_HTTP_PORT"
echo "HTTPS地址: https://192.168.110.88:$INGRESS_HTTPS_PORT"

# 测试Ingress Controller响应
echo "测试Ingress Controller响应..."
curl -I http://192.168.110.88:$INGRESS_HTTP_PORT || echo "Ingress Controller尚未完全启动，请稍等..."
```

### 5.3 Ingress Controller状态验证

```bash
# 完整验证脚本
cat <<'EOF' > verify-ingress.sh
#!/bin/bash
echo "=== NGINX Ingress Controller 状态验证 ==="

# 1. 检查Pod状态
echo "1. Ingress Controller Pod状态:"
kubectl get pods -n ingress-nginx -o wide

# 2. 检查Service状态
echo -e "\n2. Ingress Controller Service状态:"
kubectl get svc -n ingress-nginx -o wide

# 3. 检查端口信息
echo -e "\n3. 访问端口信息:"
HTTP_PORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}')
HTTPS_PORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
echo "HTTP端口: $HTTP_PORT"
echo "HTTPS端口: $HTTPS_PORT"

# 4. 检查IngressClass
echo -e "\n4. IngressClass状态:"
kubectl get ingressclass

# 5. 测试连通性
echo -e "\n5. 连通性测试:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:$HTTP_PORT --connect-timeout 5; then
    echo "✅ Ingress Controller响应正常"
else
    echo "❌ Ingress Controller无响应，请检查配置"
fi

echo -e "\n=== 验证完成 ==="
EOF

chmod +x verify-ingress.sh
./verify-ingress.sh
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
  - 192.168.110.200-192.168.110.250  # 基于我们的实际网段 192.168.110.0/24
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

**基于实际部署经验的简化测试方案**：

```bash
# 部署简化测试应用 (避免复杂的Ingress配置问题)
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
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
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
    nodePort: 30080  # 固定NodePort端口
  type: NodePort
EOF

# 等待测试应用启动
echo "等待测试应用启动..."
kubectl wait --for=condition=ready pod -l app=nginx-test --timeout=120s

# 验证测试应用
kubectl get pods -l app=nginx-test -o wide
kubectl get svc nginx-test-service

# 测试应用访问
echo "=== 测试应用访问方式 ==="
echo "方式1 - NodePort直接访问:"
echo "  访问地址: http://192.168.110.88:30080"

echo "方式2 - ClusterIP内部访问:"
CLUSTER_IP=$(kubectl get svc nginx-test-service -o jsonpath='{.spec.clusterIP}')
echo "  内部地址: http://$CLUSTER_IP"

# 简单的连通性测试
echo "方式3 - 连通性测试:"
if curl -s -o /dev/null -w "%{http_code}" http://192.168.110.88:30080 --connect-timeout 5; then
    echo "✅ 测试应用访问正常"
else
    echo "❌ 测试应用无法访问，请检查配置"
fi
```

### 📋 高级测试：Ingress资源部署 (可选)

如果Ingress Controller配置正常，可以测试Ingress功能：

```bash
# 创建Ingress资源 (仅在Ingress Controller正常工作时使用)
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-test-ingress
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
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
  - http:  # 默认规则，不需要特定host
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx-test-service
            port:
              number: 80
EOF

# 验证Ingress资源
kubectl get ingress nginx-test-ingress -o wide

# 获取Ingress访问端口
INGRESS_HTTP_PORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}')

echo "=== Ingress访问测试 ==="
echo "方式1 - 通过默认规则访问:"
echo "  访问地址: http://192.168.110.88:$INGRESS_HTTP_PORT"

echo "方式2 - 通过域名访问 (需要配置hosts):"
echo "  添加到hosts: 192.168.110.88 test.ai-platform.local"
echo "  访问地址: http://test.ai-platform.local:$INGRESS_HTTP_PORT"

# 测试Ingress访问
if curl -s -o /dev/null -w "%{http_code}" http://192.168.110.88:$INGRESS_HTTP_PORT --connect-timeout 5; then
    echo "✅ Ingress访问正常"
else
    echo "❌ Ingress访问异常，建议使用NodePort方式"
fi
```

### 🔧 测试应用故障排查

```bash
# 测试应用故障排查脚本
cat <<'EOF' > debug-test-app.sh
#!/bin/bash
echo "=== 测试应用故障排查 ==="

# 1. 检查Pod状态
echo "1. Pod状态检查:"
kubectl get pods -l app=nginx-test -o wide

# 2. 检查Pod详细信息
echo -e "\n2. Pod详细信息:"
for pod in $(kubectl get pods -l app=nginx-test -o name); do
    echo "检查 $pod:"
    kubectl describe $pod | grep -A 10 "Events:"
done

# 3. 检查Service状态
echo -e "\n3. Service状态:"
kubectl get svc nginx-test-service -o wide
kubectl describe svc nginx-test-service

# 4. 检查Endpoint
echo -e "\n4. Endpoint状态:"
kubectl get endpoints nginx-test-service

# 5. 网络连通性测试
echo -e "\n5. 网络连通性测试:"
NODE_PORT=$(kubectl get svc nginx-test-service -o jsonpath='{.spec.ports[0].nodePort}')
echo "NodePort: $NODE_PORT"

# 测试内部连通性
if kubectl get pods | grep -q nginx-test; then
    TEST_POD=$(kubectl get pods -l app=nginx-test -o jsonpath='{.items[0].metadata.name}')
    echo "内部Pod连通性测试:"
    kubectl exec $TEST_POD -- curl -s -o /dev/null -w "%{http_code}" http://nginx-test-service || echo "内部连通失败"
fi

# 测试外部连通性
echo "外部NodePort连通性测试:"
curl -s -o /dev/null -w "%{http_code}" http://192.168.110.88:$NODE_PORT --connect-timeout 5 || echo "外部连通失败"

echo -e "\n=== 故障排查完成 ==="
EOF

chmod +x debug-test-app.sh
./debug-test-app.sh
```

---

## 6. 🔒 集群安全配置

基于生产环境最佳实践的安全配置指南：

### 6.1 网络安全策略

```bash
# 1. 配置基础网络策略
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: default
EOF

# 2. 保护kube-system命名空间
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: kube-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF
```

### 6.2 RBAC安全加固

```bash
# 1. 创建受限的服务账户
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: restricted-user
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: ServiceAccount
  name: restricted-user
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
EOF

# 2. 审计现有权限
kubectl auth can-i --list --as=system:serviceaccount:default:restricted-user
```

### 6.3 Pod安全标准

```bash
# 1. 应用Pod安全策略
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: secure-namespace
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
EOF

# 2. 创建安全上下文示例
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-app
  namespace: secure-namespace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: secure-app
  template:
    metadata:
      labels:
        app: secure-app
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: nginx:1.25-alpine
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            cpu: "200m"
            memory: "256Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
      - name: run
        emptyDir: {}
EOF
```

### 6.4 集群访问安全

```bash
# 1. 配置kubectl访问权限
# 创建只读用户
openssl genrsa -out readonly-user.key 2048
openssl req -new -key readonly-user.key -out readonly-user.csr -subj "/CN=readonly-user/O=viewers"

# 生成证书 (需要CA证书)
sudo openssl x509 -req -in readonly-user.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out readonly-user.crt -days 365

# 配置kubectl context
kubectl config set-credentials readonly-user --client-certificate=readonly-user.crt --client-key=readonly-user.key
kubectl config set-context readonly-context --cluster=kubernetes --user=readonly-user

# 2. 创建只读ClusterRole
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: readonly-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "nodes", "namespaces"]
  verbs: ["get", "watch", "list"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "watch", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: readonly-binding
subjects:
- kind: User
  name: readonly-user
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: readonly-role
  apiGroup: rbac.authorization.k8s.io
EOF
```

### 6.5 定期安全检查脚本

```bash
# 创建定期安全检查脚本
cat > security-check.sh << 'EOF'
#!/bin/bash
echo "=== Kubernetes集群安全检查 ==="
echo "检查时间: $(date)"
echo

# 1. 检查特权Pod
echo "1. 检查特权Pod:"
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.securityContext.privileged}{"\n"}{end}' | grep true || echo "无特权Pod"
echo

# 2. 检查网络策略
echo "2. 检查网络策略:"
kubectl get networkpolicies --all-namespaces
echo

# 3. 检查服务账户权限
echo "3. 检查危险的ClusterRoleBinding:"
kubectl get clusterrolebinding -o json | jq -r '.items[] | select(.roleRef.name=="cluster-admin") | .metadata.name + " -> " + (.subjects[]?.name // "N/A")'
echo

# 4. 检查未加密的Secret
echo "4. 检查Secret数量:"
kubectl get secrets --all-namespaces --no-headers | wc -l
echo

# 5. 检查Pod安全上下文
echo "5. 检查运行为root的Pod:"
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.securityContext.runAsUser}{"\n"}{end}' | grep -E '\t0$|\t$' || echo "无root Pod"
echo

echo "=== 安全检查完成 ==="
EOF

chmod +x security-check.sh
```

---

### 🗑️ 清理测试资源

```bash
# 清理测试应用资源
echo "清理测试应用资源..."
kubectl delete deployment nginx-test
kubectl delete service nginx-test-service
kubectl delete ingress nginx-test-ingress 2>/dev/null || true

echo "✅ 测试资源清理完成"
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
*文档更新时间: 2025年1月7日 - Kubernetes 1.28.8集群部署*  
*基于实际环境配置: Ubuntu 24.04 LTS, IP: 192.168.110.88*  
*实际部署时间: 2-3小时 (包含问题排查)*  
*部署经验总结: Flannel成功部署，Ingress Controller RBAC权限修复，admission webhook问题解决*

## 🏆 部署成功验证清单

### ✅ 集群基础组件验证

```bash
# 运行完整验证脚本
cat <<'EOF' > final-verification.sh
#!/bin/bash
echo "=== Kubernetes 集群部署成功验证 ==="
echo "验证时间: $(date)"
echo

# 1. 节点状态验证
echo "✅ 1. 节点状态验证:"
kubectl get nodes -o wide
NODE_STATUS=$(kubectl get nodes --no-headers | awk '{print $2}')
if [[ "$NODE_STATUS" == "Ready" ]]; then
    echo "✅ 节点状态: Ready"
else
    echo "❌ 节点状态: $NODE_STATUS"
fi
echo

# 2. 系统Pod状态验证
echo "✅ 2. 系统Pod状态验证:"
kubectl get pods -n kube-system -o wide
SYSTEM_PODS_RUNNING=$(kubectl get pods -n kube-system --no-headers | grep -c "Running")
TOTAL_SYSTEM_PODS=$(kubectl get pods -n kube-system --no-headers | wc -l)
echo "运行中的系统Pod: $SYSTEM_PODS_RUNNING/$TOTAL_SYSTEM_PODS"
echo

# 3. 网络插件验证
echo "✅ 3. 网络插件验证:"
kubectl get pods -n kube-flannel -o wide 2>/dev/null || echo "Flannel未安装"
FLANNEL_PODS_RUNNING=$(kubectl get pods -n kube-flannel --no-headers 2>/dev/null | grep -c "Running" || echo "0")
echo "Flannel Pod运行状态: $FLANNEL_PODS_RUNNING"
echo

# 4. Ingress Controller验证
echo "✅ 4. Ingress Controller验证:"
kubectl get pods -n ingress-nginx -o wide
INGRESS_PODS_RUNNING=$(kubectl get pods -n ingress-nginx --no-headers 2>/dev/null | grep -c "Running" || echo "0")
echo "Ingress Controller运行状态: $INGRESS_PODS_RUNNING"

# 获取Ingress端口信息
HTTP_PORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}' 2>/dev/null || echo "未配置")
HTTPS_PORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}' 2>/dev/null || echo "未配置")
echo "HTTP端口: $HTTP_PORT"
echo "HTTPS端口: $HTTPS_PORT"
echo

# 5. DNS服务验证
echo "✅ 5. DNS服务验证:"
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
COREDNS_PODS_RUNNING=$(kubectl get pods -n kube-system -l k8s-app=kube-dns --no-headers | grep -c "Running")
echo "CoreDNS Pod运行状态: $COREDNS_PODS_RUNNING"
echo

# 6. 网络连通性验证
echo "✅ 6. 网络连通性验证:"
# 创建临时测试Pod
kubectl run test-pod --image=busybox:1.35 --rm -i --restart=Never --command -- /bin/sh -c "nslookup kubernetes.default" 2>/dev/null && echo "✅ DNS解析正常" || echo "❌ DNS解析失败"
echo

# 7. 最终总结
echo "=== 部署成功标志检查 ==="
SUCCESS_COUNT=0
TOTAL_CHECKS=6

if [[ "$NODE_STATUS" == "Ready" ]]; then
    echo "✅ 节点状态正常"
    ((SUCCESS_COUNT++))
else
    echo "❌ 节点状态异常"
fi

if [[ $SYSTEM_PODS_RUNNING -ge 5 ]]; then
    echo "✅ 系统Pod运行正常"
    ((SUCCESS_COUNT++))
else
    echo "❌ 系统Pod运行异常"
fi

if [[ $FLANNEL_PODS_RUNNING -ge 1 ]]; then
    echo "✅ 网络插件运行正常"
    ((SUCCESS_COUNT++))
else
    echo "❌ 网络插件运行异常"
fi

if [[ $COREDNS_PODS_RUNNING -ge 1 ]]; then
    echo "✅ DNS服务运行正常"
    ((SUCCESS_COUNT++))
else
    echo "❌ DNS服务运行异常"
fi

if [[ $INGRESS_PODS_RUNNING -ge 1 ]]; then
    echo "✅ Ingress Controller运行正常"
    ((SUCCESS_COUNT++))
else
    echo "❌ Ingress Controller运行异常"
fi

if [[ "$HTTP_PORT" != "未配置" && "$HTTP_PORT" != "" ]]; then
    echo "✅ Ingress端口配置正常"
    ((SUCCESS_COUNT++))
else
    echo "❌ Ingress端口配置异常"
fi

echo
echo "=== 最终部署结果 ==="
echo "成功项目: $SUCCESS_COUNT/$TOTAL_CHECKS"

if [[ $SUCCESS_COUNT -eq $TOTAL_CHECKS ]]; then
    echo "🎉 Kubernetes集群部署完全成功！"
    echo "📋 访问信息:"
    echo "   集群地址: https://192.168.110.88:6443"
    echo "   HTTP访问: http://192.168.110.88:$HTTP_PORT"
    echo "   HTTPS访问: https://192.168.110.88:$HTTPS_PORT"
    echo "✅ 可以进行下一阶段部署"
elif [[ $SUCCESS_COUNT -ge 4 ]]; then
    echo "⚠️  Kubernetes集群基本可用，存在部分问题"
    echo "🔧 建议解决后续问题后再进行下一阶段部署"
else
    echo "❌ Kubernetes集群部署存在重大问题"
    echo "🚨 需要排查和解决问题后才能继续"
fi
echo
EOF

chmod +x final-verification.sh
./final-verification.sh
```

### 📊 实际部署时间统计

基于真实部署经验的时间分配：

| 阶段 | 预计时间 | 实际时间 | 主要任务 |
|------|---------|---------|----------|
| **基础环境准备** | 20-30分钟 | 15分钟 | containerd配置、镜像源设置 |
| **Kubernetes组件安装** | 20-30分钟 | 25分钟 | kubeadm、kubelet、kubectl安装 |
| **集群初始化** | 15-25分钟 | 30分钟 | 包含pause容器问题解决 |
| **网络插件部署** | 10-20分钟 | 45分钟 | Flannel部署和配置验证 |
| **Ingress Controller部署** | 15-30分钟 | 60分钟 | 包含RBAC权限和webhook问题解决 |
| **测试和验证** | 10-20分钟 | 30分钟 | 完整功能验证 |
| **问题排查和文档** | - | 45分钟 | 实际问题解决和经验总结 |
| **总计** | 1-1.5小时 | **3.5小时** | 包含完整问题解决过程 |

### 🎯 关键成功因素

1. **镜像拉取优化**: 使用国内镜像源，预拉取关键镜像
2. **网络配置一致性**: Pod CIDR配置必须在所有组件中保持一致
3. **权限配置完整性**: Ingress Controller需要完整的RBAC权限
4. **Webhook简化**: 在受限环境中删除admission webhook
5. **分步验证**: 每个阶段完成后进行验证，避免后续问题积累

## 🔗 相关文档链接

- [容器化平台部署](./01_container_platform_setup.md) - Docker和containerd配置
- [Kubernetes存储系统](./03_storage_systems_kubernetes.md) - 持久化存储配置  
- [Kubernetes资源管理](./04_resource_management_kubernetes.md) - 资源配额和监控
- [数据库部署指南](../02_server_deployment/05_database_deployment/) - PostgreSQL、MongoDB等数据库
- [应用部署概览](../03_application_deployment/00_application_overview.md) - 完整应用堆栈部署

## 📞 技术支持与故障排查

### 常见问题快速诊断

```bash
# 快速集群健康检查脚本
cat > check-cluster-health.sh << 'EOF'
#!/bin/bash
echo "=== Kubernetes 集群快速健康检查 ==="
echo "检查时间: $(date)"
echo

# 1. 节点状态
echo "1. 节点状态:"
kubectl get nodes -o wide
echo

# 2. 关键系统Pod状态
echo "2. 系统Pod状态:"
kubectl get pods -n kube-system -o wide
echo

# 3. 网络插件状态
echo "3. 网络插件状态:"
kubectl get pods -n kube-flannel -o wide 2>/dev/null || echo "Flannel未安装"
kubectl get pods -n calico-system -o wide 2>/dev/null || echo "Calico未安装"
echo

# 4. DNS服务状态
echo "4. DNS服务状态:"
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
echo

# 5. 最近事件
echo "5. 最近集群事件:"
kubectl get events --sort-by=.metadata.creationTimestamp | tail -10
echo

# 6. 资源使用概览
echo "6. 资源使用概览:"
kubectl top nodes 2>/dev/null || echo "Metrics Server未安装，无法显示资源使用情况"

echo "=== 健康检查完成 ==="
EOF

chmod +x check-cluster-health.sh
./check-cluster-health.sh
```

### 故障排查联系方式

如果在部署过程中遇到无法解决的问题，请参考：

1. **文档内故障排查**: 查看本文档"实际部署问题与解决方案"章节
2. **官方文档**: 
   - [Kubernetes官方文档](https://kubernetes.io/docs/)
   - [Flannel项目文档](https://github.com/flannel-io/flannel)
   - [Calico项目文档](https://docs.projectcalico.org/)
3. **日志收集**: 使用上述健康检查脚本收集详细信息
4. **社区支持**: Kubernetes社区和相关项目的GitHub Issues

### 部署成功标志

集群部署成功的验证标准：

- ✅ 所有节点状态为`Ready`
- ✅ 所有kube-system Pod状态为`Running`
- ✅ 网络插件Pod状态为`Running`
- ✅ CoreDNS Pod正常运行
- ✅ Pod间网络通信正常
- ✅ DNS解析功能正常

当所有标志都满足时，即可进行下一阶段的部署工作。

---

## 🚨 常见错误速查表

基于实际部署经验整理的快速问题解决指南：

### 🔥 超高频错误 (90%+遇到)

| 错误现象 | 可能原因 | 快速解决方案 | 验证方法 |
|---------|---------|-------------|---------|
| **节点NotReady** | 网络插件未就绪 | `kubectl apply -f kube-flannel.yml` | `kubectl get nodes` |
| **镜像拉取超时** | 网络问题/墙 | 配置国内镜像源 | `crictl images` |
| **pause:3.9拉取失败** | pause容器问题 | 预拉取并重标记 | `crictl images \| grep pause` |
| **kubeadm init超时** | swap未关闭 | `swapoff -a` | `free -h` |
| **Ingress Webhook错误** | 准入控制器问题 | 删除validatingwebhook | `kubectl get validatingwebhook` |

### 📋 网络相关错误

| 错误现象 | 症状 | 解决方案 |
|---------|------|---------|
| **Pod间无法通信** | ping失败 | 检查网络插件、CIDR配置 |
| **DNS解析失败** | nslookup失败 | 重启CoreDNS：`kubectl rollout restart deployment coredns -n kube-system` |
| **Service访问异常** | 服务不可达 | 检查kube-proxy、防火墙规则 |
| **NodePort无法访问** | 外部访问失败 | 检查防火墙端口开放 |

### 🛠️ 容器运行时错误

| 错误现象 | 常见原因 | 解决命令 |
|---------|---------|---------|
| **containerd连接失败** | socket路径错误 | `--cri-socket=unix:///var/run/containerd/containerd.sock` |
| **SystemdCgroup错误** | cgroup配置不当 | 修改`/etc/containerd/config.toml` |
| **运行时响应超时** | containerd性能问题 | `systemctl restart containerd` |

### ⚡ 一键修复脚本

```bash
# 创建应急修复脚本
cat > emergency-fix.sh << 'EOF'
#!/bin/bash
echo "=== Kubernetes 应急修复脚本 ==="

# 1. 重启关键服务
echo "重启containerd..."
sudo systemctl restart containerd

echo "重启kubelet..."
sudo systemctl restart kubelet

# 2. 清理有问题的Pod
echo "清理Evicted Pod..."
kubectl get pods --all-namespaces | grep Evicted | awk '{print $2 " -n " $1}' | xargs -r kubectl delete pod

# 3. 检查网络插件
echo "检查网络插件状态..."
kubectl get pods -n kube-flannel 2>/dev/null || echo "Flannel未安装"
kubectl get pods -n calico-system 2>/dev/null || echo "Calico未安装"

# 4. 重启CoreDNS
echo "重启CoreDNS..."
kubectl rollout restart deployment coredns -n kube-system

# 5. 显示集群状态
echo "=== 修复后状态 ==="
kubectl get nodes
kubectl get pods -n kube-system

echo "=== 修复完成 ==="
EOF

chmod +x emergency-fix.sh
```

### 📞 技术支持

**部署遇到问题时的建议流程：**

1. **🔍 检查错误类型**: 对照上述速查表快速定位
2. **📋 收集信息**: 运行健康检查脚本
3. **🛠️ 尝试修复**: 使用对应的解决方案
4. **🚨 应急处理**: 运行一键修复脚本
5. **📖 查阅文档**: 参考具体章节的详细说明

**📄 文档版本信息**
- 文档版本: v2.1
- 最后更新: 2025年6月5日
- 基于实际部署: Ubuntu 24.04 LTS + Kubernetes 1.28.8
- 部署环境: 生产级企业环境
- 验证状态: ✅ 完全验证通过
