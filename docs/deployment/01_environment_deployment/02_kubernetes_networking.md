# AI 中台 - Kubernetes 网络配置

本文档指导如何为 AI 中台的 Kubernetes 集群配置网络，包括容器网络接口 (CNI) 和 Ingress 控制器。

## 3. 网络配置

### 3.1. SDN 网络 (CNI Plugin for Kubernetes)

**已选方案**: **Calico** (通过 Operator 部署，已在 Kubernetes 安装步骤 1.2.3 中集成)
- **Calico**: 提供了强大的网络策略功能。
  - 安装: 通常作为 Kubernetes 的 CNI 插件通过 `kubectl apply -f <manifest_url>` 安装。
  - (参考: [https://docs.projectcalico.org/getting-started/kubernetes/self-managed-onprem/onpremises](https://docs.projectcalico.org/getting-started/kubernetes/self-managed-onprem/onpremises))
- **Cilium**: 基于 eBPF，提供高性能网络和安全。
  - (参考: [https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/](https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/))
- **OVN (OVN-Kubernetes)**:
  - (参考: [https://ovn.org/en/support/distros/](https://ovn.org/en/support/distros/))

**部署建议**: Calico 是一个成熟且广泛的选择，适合大多数场景。Cilium 在性能和可观测性方面有优势，但可能配置更复杂。确保所选 CNI 插件的版本与您的 Kubernetes 版本兼容。

### 3.2. Nginx 反向代理

用于暴露服务、负载均衡和 SSL 终止。
**推荐部署方式**: 作为 Kubernetes Ingress Controller (`ingress-nginx`)。

**安装步骤 (Kubernetes Ingress Controller):**
(参考: [https://kubernetes.github.io/ingress-nginx/deploy/](https://kubernetes.github.io/ingress-nginx/deploy/))
```bash
# 确保您的 kubectl 上下文正确指向您的 Kubernetes 集群
# 使用官方推荐的部署命令，它会创建必要的命名空间、ServiceAccount、RBAC 规则等。
# 请查阅 ingress-nginx 官方文档获取与您 Kubernetes 版本 (1.28.8) 最兼容的 controller 版本。
# 以下是一个通用示例，版本号可能需要调整。
INGRESS_NGINX_VERSION="controller-v1.10.1" # 示例版本，请检查更新
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/${INGRESS_NGINX_VERSION}/deploy/static/provider/baremetal/deploy.yaml
# 注意: 上述 URL `provider/baremetal/deploy.yaml` 适用于裸金属部署。
# 如果您在云平台上 (如 AWS, GCP, Azure)，它们可能有特定的 LoadBalancer Service 类型，
# 请查阅 ingress-nginx 文档选择适合您环境的部署 manifest。

echo "等待 ingress-nginx Pods 启动..."
kubectl get pods -n ingress-nginx -w
```
(旧的独立部署方式，仅供参考，不推荐用于此 Kubernetes 集成环境)
```bash
# sudo apt-get update
# sudo apt-get install -y nginx
# sudo systemctl start nginx
# sudo systemctl enable nginx
```
