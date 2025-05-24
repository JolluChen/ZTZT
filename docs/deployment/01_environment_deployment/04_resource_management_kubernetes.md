# AI 中台 - Kubernetes 资源管理

本文档指导如何为 AI 中台的 Kubernetes 集群配置资源管理和可视化工具，包括监控、仪表盘和 GPU 资源分配。

## 5. 资源管理

### 5.1. 资源可视化

#### 5.1.1. Prometheus (已在 4.2.1 提及)

Prometheus 不仅用于日志相关指标，也是核心的监控系统，用于收集各种系统和应用指标。请参考存储系统文档中 Prometheus 的部署部分。

#### 5.1.2. Grafana (可视化仪表盘)

用于将 Prometheus (及其他数据源) 的数据可视化。

**许可证提醒**: Grafana 使用 AGPL v3.0 许可证。内部使用通常没问题。如果计划将包含 Grafana 的系统进行商业分发或作为 SaaS 服务提供，则需要遵守 AGPL 或考虑 Grafana Enterprise。

**安装步骤 (二进制、Docker、APT/YUM):**
```bash
# 使用 APT 安装 (示例)
sudo apt-get install -y apt-transport-https software-properties-common wget
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl enable grafana-server.service
```
(参考官方文档: [https://grafana.com/docs/grafana/latest/installation/debian/](https://grafana.com/docs/grafana/latest/installation/debian/))

### 5.2. GPU 资源池化

#### 5.2.1. NVIDIA Device Plugin for Kubernetes

用于在 Kubernetes 中动态分配 GPU 资源。

**前提**:
- NVIDIA 驱动已在具有 GPU 的节点上正确安装。
- `nvidia-container-toolkit` (或 `nvidia-docker2`) 已安装和配置。

**安装步骤 (Kubernetes):**
```bash
# 确保已添加 NVIDIA Helm 仓库 (如果使用 Helm)
# helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
# helm repo update
# helm install --generate-name nvidia/gpu-operator # GPU Operator 包含 device plugin 等组件

# 或者单独安装 Device Plugin (较旧或特定场景):
# kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.15.1/nvidia-device-plugin.yml
# (版本号可能需要更新，请查阅官方 GitHub 仓库获取最新稳定版 manifest)
# 例如，对于较新版本，可能使用 Helm chart:
# helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
# helm repo update
# helm install \
#  --generate-name \
#  nvdp/nvidia-device-plugin
```
