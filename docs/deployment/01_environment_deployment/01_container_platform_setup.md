# AI 中台 - 容器化平台部署

本文档指导如何部署和配置 AI 中台所需的容器化平台，包括 Docker 和 Kubernetes。

## 2. 容器化平台

### 2.1. Docker (Container Runtime)

**版本**: Docker Engine 25.0.6+

**注意**:
- 确保启用 BuildKit 和 Containerd。
- **重要**: 在生产环境或商业用途中，请使用 Docker Engine (通常通过 `apt` 安装的 `docker-ce` 包)，避免使用 Docker Desktop 以规避潜在的商业许可问题。

**安装步骤:**
```bash
# 1. 卸载旧版本 (如果存在)
sudo apt-get remove docker docker-engine docker.io containerd runc
# 2. 设置 Docker 的 APT 仓库
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
# 3. 安装 Docker Engine, CLI, Containerd, 和 Docker Compose
#   (确保安装的是 25.0.6 或更新版本，可以指定版本号安装，例如: sudo apt-get install docker-ce=<VERSION_STRING> docker-ce-cli=<VERSION_STRING> containerd.io ...)
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
# 4. 验证安装
sudo docker --version # 确认版本为 25.0.6+
sudo docker run hello-world
# 5. 配置 cgroup driver (对于 Kubernetes 很重要)
# 创建或修改 /etc/docker/daemon.json:
# {
#   "exec-opts": ["native.cgroupdriver=systemd"],
#   "log-driver": "json-file",
#   "log-opts": {
#     "max-size": "100m"
#   },
#   "storage-driver": "overlay2"
# }
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
EOF
sudo systemctl enable docker
sudo systemctl daemon-reload
sudo systemctl restart docker
# 6. 确保 Containerd 配置 (Kubernetes 将直接使用 Containerd)
#    Docker Engine 25.0.6+ 通常会正确配置 Containerd。
#    检查 /etc/containerd/config.toml 文件。
#    如果需要修改，例如确保 systemd cgroup driver:
#    sudo mkdir -p /etc/containerd
#    containerd config default | sudo tee /etc/containerd/config.toml
#    sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml
#    sudo systemctl restart containerd
```
(参考官方文档: [https://docs.docker.com/engine/install/ubuntu/](https://docs.docker.com/engine/install/ubuntu/))

### 2.2. Kubernetes (k8s)

**版本**: 1.28.8

**注意**: 确保 `kubeadm`, `kubelet`, `kubectl` 版本均为 1.28.8。 Kubernetes 的所有组件（包括 Master 和 Worker 节点）都将运行在 Ubuntu 22.04 LTS 服务器上。

**安装步骤 (使用 `kubeadm`):**
```bash
# 0. 准备工作 (所有将作为 Kubernetes 节点的服务器上执行)
#    - 禁用 swap:
sudo swapoff -a
#   永久禁用 swap，注释掉 /etc/fstab 文件中包含 swap 的行
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

#    - 配置内核参数 (确保 overlay 和 br_netfilter 模块加载，并设置必要的 sysctl 参数):
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter

cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sudo sysctl --system

#    - 确保 containerd 已安装并正确配置 (通过上述 Docker 安装步骤应已完成)
#      验证 containerd 服务正在运行:
sudo systemctl status containerd
#      如果 containerd 未运行或配置不正确 (特别是 cgroup driver)，请返回 Docker 安装部分检查。

# 1. 安装 kubeadm, kubelet, kubectl (所有 Kubernetes 节点上执行)
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

#   添加 Kubernetes APT 仓库的 GPG 密钥和源。
#   选项 A: 使用 Kubernetes 官方源 (如果网络允许)
#   curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
#   echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

#   选项 B: 使用国内镜像源 (例如阿里云，推荐在中国大陆环境使用)
curl -fsSL https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://mirrors.aliyun.com/kubernetes-new/core/stable/v1.28/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
#   安装指定版本的 kubelet, kubeadm, kubectl
KUBE_VERSION="1.28.8-*" # 使用通配符确保获取该补丁版本的最新修订版，例如 1.28.8-1.1 或更高
sudo apt-get install -y kubelet=${KUBE_VERSION} kubeadm=${KUBE_VERSION} kubectl=${KUBE_VERSION}
#   锁定版本，防止意外自动升级导致版本不一致
sudo apt-mark hold kubelet kubeadm kubectl

# 2. 初始化 Master 节点 (Control Plane) - 在选定的 Master 节点上执行
#    注意: --pod-network-cidr 必须与您选择安装的 CNI 插件所期望的 CIDR 一致。
#          Calico 默认通常使用 192.168.0.0/16。
#          --image-repository 用于指定拉取 Kubernetes 控制平面镜像的仓库，使用国内镜像可以加速。
#          --cri-socket 指定容器运行时的 socket 文件路径，对于 Containerd 通常是 /var/run/containerd/containerd.sock。
#          请将 <YOUR_MASTER_IP> 替换为 Master 节点的实际 IP 地址。
#          --apiserver-advertise-address=<YOUR_MASTER_IP>
echo "准备初始化 Kubernetes Master 节点..."
echo "请根据您的网络环境和CNI插件规划，确认以下参数:"
echo "Pod Network CIDR (例如 Calico: 192.168.0.0/16): "
read POD_NETWORK_CIDR
echo "Master 节点 IP 地址 (apiserver-advertise-address): "
read MASTER_IP
echo "将使用阿里云镜像仓库 (registry.aliyuncs.com/google_containers) 拉取控制平面镜像。"

sudo kubeadm init \
  --pod-network-cidr=${POD_NETWORK_CIDR:-192.168.0.0/16} \
  --kubernetes-version=v1.28.8 \
  --image-repository=registry.aliyuncs.com/google_containers \
  --cri-socket=unix:///var/run/containerd/containerd.sock \
  --apiserver-advertise-address=${MASTER_IP}

#    初始化成功后，kubeadm 会输出需要执行的命令，用于配置 kubectl 和加入 Worker 节点。
#    请务必记录这些输出。
#    通常的配置 kubectl 的命令如下 (在 Master 节点上以普通用户执行):
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 3. 安装网络插件 (CNI) - 在 Master 节点上执行
#    推荐使用 Calico Operator 进行安装和管理。
#    确保 Calico 版本与 Kubernetes 1.28.x 兼容 (例如 Calico v3.27.x 或更高)。
#    请查阅 Calico 官方文档获取最新的兼容版本和 manifest。
CALICO_OPERATOR_URL="https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml" # 示例版本，请检查更新
CALICO_CRDS_URL="https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/custom-resources.yaml" # 示例版本，请检查更新

echo "正在下载并应用 Calico Operator (版本参考: v3.27.0)..."
kubectl create -f ${CALICO_OPERATOR_URL}
echo "正在应用 Calico Custom Resource Definitions (CRDs)..."
# 下面的 custom-resources.yaml 通常定义了 IPPool 等网络配置
# 您可以下载该文件，根据需要修改 cidr (应与 kubeadm init 时 --pod-network-cidr 一致)
# 然后再 kubectl apply -f custom-resources.yaml
# 这里我们使用默认配置，它通常会尝试自动检测或使用常见的 192.168.0.0/16
# 如果 kubeadm init 时使用了不同的 CIDR，请务必修改此处的 Calico 配置以匹配。
# 确保下面的 CIDR 与 kubeadm init --pod-network-cidr 一致
cat <<EOF | kubectl apply -f -
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
    - blockSize: 26
      cidr: ${POD_NETWORK_CIDR:-192.168.0.0/16} # 确保此 CIDR 与 kubeadm init 一致
      encapsulation: VXLANCrossSubnet # 或者 IPIP, 根据网络环境选择
      natOutgoing: Enabled
      nodeSelector: all()
EOF

echo "等待 Calico Pods 启动..."
kubectl get pods -n calico-system -w

# 4. Worker 节点加入集群 - 在每个 Worker 节点上执行
#    使用 Master 节点 `kubeadm init` 成功后输出的 `kubeadm join` 命令。
#    该命令包含 token 和 CA 证书哈希。
#    例如:
#    sudo kubeadm join <master-ip>:<master-port> --token <token> \
#        --discovery-token-ca-cert-hash sha256:<hash> \
#        --cri-socket=unix:///var/run/containerd/containerd.sock
#    请将占位符替换为实际值。

# 5. (可选) 移除 Master 节点的 Taint (如果希望 Master 节点也运行 Pods，不推荐用于生产环境的 Master)
#    kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```
(参考官方文档: [https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/) 和 [https://kubernetes.io/docs/setup/production-environment/container-runtimes/](https://kubernetes.io/docs/setup/production-environment/container-runtimes/))

### 2.3. CRI-Dockerd
**不再需要**: 由于您选择了 Docker Engine 25.0.6+ 并将 Kubernetes 配置为直接使用 Containerd (通过 `--cri-socket=unix:///var/run/containerd/containerd.sock`)，因此不再需要 `cri-dockerd`。Kubernetes 1.24+ 已移除 dockershim，推荐直接使用符合 CRI 规范的运行时，如 Containerd。
