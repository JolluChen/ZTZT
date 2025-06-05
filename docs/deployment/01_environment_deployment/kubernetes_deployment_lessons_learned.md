# 🎯 Kubernetes 部署实战经验总结

本文档基于真实的Kubernetes集群部署过程，总结了实际遇到的问题、解决方案和最佳实践。

## 📊 部署概况

### 成功部署信息
- **集群版本**: Kubernetes v1.28.8
- **部署环境**: Ubuntu 24.04 LTS
- **网络环境**: 企业内网 (192.168.110.0/24)
- **主节点IP**: 192.168.110.88
- **成功网络插件**: Flannel
- **部署总耗时**: 约2小时 (包含故障排查)

### 关键成功因素
1. **正确的containerd配置** - SystemdCgroup=true
2. **一致的CIDR配置** - 集群初始化与网络插件保持一致
3. **国内镜像源配置** - 解决镜像拉取问题
4. **自定义网络插件配置** - 避免在线下载失败

## 🚨 实际遇到的问题与解决方案

### 问题1: Calico网络插件部署失败 ❌

**故障现象**:
```
pod/calico-node-xxxxx   0/1     ImagePullBackOff   0          2m
Error: failed to pull image "docker.io/calico/cni:v3.27.0": 
rpc error: code = DeadlineExceeded desc = context deadline exceeded
```

**根本原因**:
- 网络环境受限，无法稳定访问docker.io
- 镜像拉取超时 (> 5分钟)
- Calico镜像较大且依赖多个外部镜像

**解决方案**:
1. **短期解决**: 切换到Flannel网络插件
2. **长期解决**: 配置企业级镜像仓库代理

**经验教训**:
- 在受限网络环境下，优先选择轻量级网络插件
- 提前测试镜像拉取能力
- 准备多种网络插件方案

### 问题2: 网络CIDR配置不匹配 ❌

**故障现象**:
```
pod/kube-flannel-ds-xxxxx   0/1     CrashLoopBackOff   5          10m
Error: failed to find plugin "bridge" in path [/opt/cni/bin]
```

**根本原因**:
- kubeadm init使用: `--pod-network-cidr=192.168.0.0/16`
- Flannel默认配置: `"Network": "10.244.0.0/16"`
- 网络配置不一致导致CNI插件无法正确初始化

**解决方案**:
```bash
# 1. 下载Flannel默认配置
curl -o kube-flannel.yml https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# 2. 修改网络配置
sed -i 's|"Network": "10.244.0.0/16"|"Network": "192.168.0.0/16"|g' kube-flannel.yml

# 3. 应用修改后的配置
kubectl apply -f kube-flannel.yml
```

**经验教训**:
- 集群初始化和网络插件的CIDR配置必须完全一致
- 使用自定义配置文件而非默认在线配置
- 部署前仔细检查所有网络参数

### 问题3: containerd配置问题 ❌

**故障现象**:
```
kubelet: E0605 failed to run Kubelet: failed to create kubelet: 
misconfiguration: kubelet cgroup driver: "systemd" is different from docker cgroup driver: "cgroupfs"
```

**根本原因**:
- containerd默认配置中`SystemdCgroup = false`
- kubelet期望使用systemd作为cgroup驱动
- 配置不匹配导致kubelet启动失败

**解决方案**:
```bash
# 修正containerd配置
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl restart kubelet
```

**经验教训**:
- 容器运行时配置是集群正常运行的基础
- 必须确保kubelet和containerd使用相同的cgroup驱动
- 每次修改配置后都要重启相关服务

## ✅ 成功部署的关键配置

### 1. containerd最终配置

`/etc/containerd/config.toml` 关键部分:

```toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  SystemdCgroup = true  # 关键：与kubelet保持一致

# 镜像加速配置
[plugins."io.containerd.grpc.v1.cri".registry.mirrors]
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
    endpoint = ["https://registry-1.docker.io", "https://y8y5jkya.mirror.aliyuncs.com"]
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."registry.k8s.io"]
    endpoint = ["https://registry.aliyuncs.com/google_containers"]
```

### 2. 集群初始化参数

```bash
sudo kubeadm init \
  --pod-network-cidr=192.168.0.0/16 \          # 与Flannel配置一致
  --apiserver-advertise-address=192.168.110.88 \  # 实际主节点IP
  --kubernetes-version=v1.28.8 \               # 指定版本
  --cri-socket=unix:///var/run/containerd/containerd.sock  # 明确指定容器运行时
```

### 3. Flannel网络配置

核心配置部分:
```json
{
  "Network": "192.168.0.0/16",  # 必须与kubeadm init参数一致
  "Backend": {
    "Type": "vxlan"
  }
}
```

## 📈 性能优化经验

### 1. 网络性能优化

```bash
# 优化内核网络参数
sudo tee /etc/sysctl.d/k8s-network.conf <<EOF
# 增加网络连接数
net.core.somaxconn = 32768
net.core.netdev_max_backlog = 5000

# 优化TCP性能
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_congestion_control = bbr

# 调整iptables性能
net.netfilter.nf_conntrack_max = 1048576
EOF

sudo sysctl -p /etc/sysctl.d/k8s-network.conf
```

### 2. containerd性能优化

```bash
# 调整containerd并发限制
sudo tee -a /etc/containerd/config.toml <<EOF
[plugins."io.containerd.grpc.v1.cri"]
  max_concurrent_downloads = 10
  max_container_log_line_size = 16384
EOF
```

## 🔧 故障排查工具箱

### 1. 快速诊断脚本

```bash
#!/bin/bash
# Kubernetes 故障快速诊断脚本

echo "=== Kubernetes 故障诊断 ==="
echo "时间: $(date)"
echo

# 检查节点状态
echo "1. 节点状态:"
kubectl get nodes -o wide
echo

# 检查系统Pod
echo "2. 系统Pod状态:"
kubectl get pods -n kube-system | grep -v Running
echo

# 检查网络插件
echo "3. 网络插件状态:"
kubectl get pods -n kube-flannel 2>/dev/null | grep -v Running || echo "Flannel未安装或无异常"
kubectl get pods -n calico-system 2>/dev/null | grep -v Running || echo "Calico未安装或无异常"
echo

# 检查最近的错误事件
echo "4. 最近错误事件:"
kubectl get events --field-selector type=Warning --sort-by=.metadata.creationTimestamp | tail -10
echo

# 检查容器运行时
echo "5. 容器运行时状态:"
sudo systemctl status containerd | grep -E "(Active|Main PID)"
echo

# 检查kubelet状态
echo "6. kubelet状态:"
sudo systemctl status kubelet | grep -E "(Active|Main PID)"
echo

echo "=== 诊断完成 ==="
```

### 2. 日志收集命令

```bash
# 收集关键日志用于故障分析
mkdir -p ~/k8s-logs/$(date +%Y%m%d-%H%M)
cd ~/k8s-logs/$(date +%Y%m%d-%H%M)

# 收集集群状态
kubectl get all -A > cluster-status.log
kubectl describe nodes > nodes-detail.log
kubectl get events --sort-by=.metadata.creationTimestamp > events.log

# 收集系统日志
sudo journalctl -u kubelet --since "1 hour ago" > kubelet.log
sudo journalctl -u containerd --since "1 hour ago" > containerd.log

# 收集网络插件日志
kubectl logs -n kube-flannel -l app=flannel --tail=200 > flannel.log 2>/dev/null || echo "Flannel未运行"

echo "日志已收集到: $(pwd)"
```

## 📋 部署检查清单

### 前置条件检查 ✅
- [ ] 所有节点已禁用swap
- [ ] 容器运行时已正确配置
- [ ] 网络端口已开放 (6443, 10250, 10259, 10257, 2379-2380)
- [ ] 时间同步已配置
- [ ] 镜像源已配置

### 部署过程检查 ✅
- [ ] kubeadm、kubelet、kubectl版本一致
- [ ] 集群初始化成功
- [ ] kubectl配置正确
- [ ] 网络插件CIDR配置正确
- [ ] 网络插件Pod正常运行

### 部署后验证 ✅
- [ ] 所有节点状态为Ready
- [ ] 所有系统Pod状态为Running
- [ ] Pod间网络通信正常
- [ ] DNS解析正常
- [ ] 可以成功部署测试应用

## 🎓 经验总结与建议

### 网络插件选择策略

| 环境类型 | 推荐插件 | 理由 |
|---------|---------|------|
| **企业内网/受限环境** | Flannel | 轻量、稳定、配置简单 |
| **公有云环境** | Calico | 功能丰富、性能好、支持网络策略 |
| **高性能需求** | Cilium | 基于eBPF、性能最佳 |
| **混合云环境** | Antrea | VMware支持、功能全面 |

### 部署最佳实践

1. **准备阶段**:
   - 提前测试镜像拉取能力
   - 准备离线安装包作为备选
   - 确定网络CIDR规划

2. **实施阶段**:
   - 严格按照文档顺序执行
   - 每步操作后进行验证
   - 及时记录遇到的问题

3. **验证阶段**:
   - 使用自动化脚本进行全面检查
   - 部署测试应用验证功能
   - 进行网络连通性测试

### 故障预防措施

1. **配置一致性**: 确保所有配置参数在不同组件间保持一致
2. **版本兼容性**: 使用经过验证的组件版本组合
3. **网络规划**: 提前规划好各种网络CIDR，避免冲突
4. **监控告警**: 及早发现和解决潜在问题

---

*文档创建时间: 2025年6月5日*  
*基于实际部署过程总结，持续更新维护*
