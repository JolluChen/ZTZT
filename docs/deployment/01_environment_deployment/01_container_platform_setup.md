# ⭐ AI中台 - 容器化平台部署

本文档指导如何部署和配置 AI 中台所需的容器化平台，包括 Docker 和 Kubernetes。

> **📋 前置条件**: 在开始容器化平台部署之前，请确保已完成：
> - ✅ [操作系统安装与基础配置](./00_os_installation_ubuntu.md) - Ubuntu 24.04 LTS基础环境
> - ✅ 系统已完成基础工具安装和安全配置
> - ✅ Python 3.10 和 Node.js 20.x 环境已就绪

## ⏱️ 预计部署时间
- **Docker Engine 安装**: 15-30分钟  
- **Kubernetes 安装**: 30-45分钟
- **环境验证和测试**: 15-30分钟
- **总计**: 1-1.5小时

## 🎯 部署目标
✅ Docker Engine 25.0.6 容器运行时  
✅ Docker Compose 容器编排  
✅ Kubernetes 1.28.8 集群环境  
✅ 容器网络和存储配置  
✅ 容器化平台监控

## 1. 容器化平台概述

AI中台采用现代化的容器技术栈：
- **Docker Engine**: 作为容器运行时，支持应用容器化
- **Docker Compose**: 用于本地开发和简单部署场景
- **Kubernetes**: 用于生产环境的容器编排和管理

## 2. Docker Engine 部署

### 2.1 Docker Engine 安装

**目标版本**: Docker Engine 25.0.6

**重要说明**:
- 确保启用 BuildKit 和 Containerd
- 生产环境使用 Docker Engine (避免 Docker Desktop 的商业许可问题)
- 配置适合 Kubernetes 的 cgroup driver

#### 2.1.1 卸载旧版本和安装依赖

```bash
# 卸载可能存在的旧版本Docker
sudo apt-get remove docker docker-engine docker.io containerd runc

# 更新系统并安装依赖
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release
```

#### 2.1.2 配置Docker仓库

```bash
# 创建keyrings目录
sudo install -m 0755 -d /etc/apt/keyrings

# 下载并安装Docker GPG密钥 (推荐使用国内镜像源提高稳定性)
# 方案1: 官方源 (如果网络良好)
# curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 方案2: 阿里云镜像源 (推荐国内服务器使用)
echo "正在从阿里云镜像下载Docker GPG密钥..."
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 验证GPG密钥文件是否成功下载且非空
if [ -f /etc/apt/keyrings/docker.gpg ] && [ $(stat -c%s "/etc/apt/keyrings/docker.gpg") -gt 0 ]; then
    echo "✅ GPG密钥下载成功。"
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
else
    echo "❌ GPG密钥下载失败！请检查网络连接或尝试其他镜像。"
    # 如果您想在失败时停止脚本，可以取消下一行的注释
    # exit 1 
fi

# 添加Docker APT源 (使用阿里云镜像)
echo "正在配置阿里云Docker APT源..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 验证APT源文件是否创建成功
if [ -f /etc/apt/sources.list.d/docker.list ]; then
    echo "✅ APT源配置文件创建成功。"
    cat /etc/apt/sources.list.d/docker.list
else
    echo "❌ APT源配置文件创建失败！"
    # exit 1
fi

# 更新包索引
echo "正在更新APT包索引..."
sudo apt-get update
```

#### 2.1.3 安装Docker Engine

```bash
# 安装最新版本的Docker Engine, CLI, Containerd, Docker Compose
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 如果安装过程中出现下载失败或超时问题，可以尝试:
# 1. 逐个安装组件，可以避免单个失败导致全部重试:
# sudo apt-get install -y docker-ce
# sudo apt-get install -y docker-ce-cli
# sudo apt-get install -y containerd.io
# sudo apt-get install -y docker-buildx-plugin
# sudo apt-get install -y docker-compose-plugin

# 启动并启用Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到docker组 (避免每次使用sudo)
sudo usermod -aG docker $USER

# 验证安装 (注意：需要重新登录或执行 newgrp docker)
sudo docker --version
sudo docker run hello-world
```

#### 2.1.4 配置Docker for Kubernetes

```bash
# 创建Docker配置目录
sudo mkdir -p /etc/docker

# 创建Docker daemon配置文件 (重要：Kubernetes需要systemd cgroup driver + 国内镜像源)
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.tuna.tsinghua.edu.cn",
    "https://do.nark.eu.org",
    "https://dc.j8.work",
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://docker.nju.edu.cn"
  ],
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

# 重新加载daemon配置并重启Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置
sudo docker info | grep -i cgroup
sudo docker info | grep -A 10 "Registry Mirrors"

# 测试镜像拉取功能
sudo docker run hello-world
```

**参考文档**: [Docker Engine Installation Guide](https://docs.docker.com/engine/install/ubuntu/)

### 2.2 Docker Compose 配置

为了支持本地开发和简单的多容器应用部署，需要配置Docker Compose：

```bash
# 验证Docker Compose Plugin安装
docker compose version

# 创建基础的compose配置目录
sudo mkdir -p /opt/docker-compose
sudo chown $USER:$USER /opt/docker-compose

# 测试Docker Compose
cat > /tmp/test-compose.yml << 'EOF'
version: '3.8'
services:
  test:
    image: hello-world
EOF

docker compose -f /tmp/test-compose.yml up
docker compose -f /tmp/test-compose.yml down
rm /tmp/test-compose.yml
```

## 3. 容器运行时验证

### 3.1 Docker环境验证

创建验证脚本确保Docker环境正常：

```bash
# 创建Docker环境检查脚本
sudo tee /usr/local/bin/check-docker.sh << 'EOF'
#!/bin/bash

echo "=== Docker 环境检查 ==="
echo

echo "Docker版本信息:"
docker --version
docker compose version
echo

echo "Docker服务状态:"
systemctl is-active docker
systemctl is-enabled docker
echo

echo "Docker配置信息:"
docker info | grep -E "Cgroup Driver|Storage Driver|Logging Driver"
echo

echo "Docker权限测试:"
if docker run --rm hello-world >/dev/null 2>&1; then
    echo "✅ Docker权限配置正确"
else
    echo "❌ Docker权限配置有问题，可能需要重新登录"
fi
echo

echo "容器运行时测试:"
if docker run --rm ubuntu:22.04 echo "容器测试成功" 2>/dev/null; then
    echo "✅ 容器运行时正常"
else
    echo "❌ 容器运行时异常"
fi

echo
echo "=== Docker 环境检查完成 ==="
EOF

chmod +x /usr/local/bin/check-docker.sh

# 运行检查
/usr/local/bin/check-docker.sh
```

### 3.2 容器网络测试

```bash
# 测试Docker网络功能
echo "测试Docker网络..."

# 创建测试网络
docker network create test-network

# 启动两个容器测试网络连通性
docker run -d --name test-container1 --network test-network nginx:alpine
docker run -d --name test-container2 --network test-network alpine sleep 60

# 测试容器间网络连通性
if docker exec test-container2 ping -c 2 test-container1 >/dev/null 2>&1; then
    echo "✅ 容器网络连通性正常"
else
    echo "❌ 容器网络连通性异常"
fi

# 清理测试资源
docker stop test-container1 test-container2
docker rm test-container1 test-container2
docker network rm test-network
```

## 4. 下一步部署指引

容器平台基础环境部署完成后，根据部署场景选择下一步：

### 4.1 生产环境路径
如果是生产环境部署，继续进行Kubernetes集群配置：

> 📋 **生产环境下一步**: [Kubernetes网络配置](./02_kubernetes_networking.md)
> 
> 该文档包含：
> - ✅ Kubernetes集群初始化
> - ✅ CNI网络插件配置  
> - ✅ Ingress控制器部署
> - ✅ 网络策略配置

### 4.2 开发环境路径  
如果是开发环境，可以直接进入中间件部署：

> 📋 **开发环境下一步**: [数据库部署](../02_server_deployment/05_database_setup.md)
>
> 使用Docker Compose进行：
> - ✅ PostgreSQL数据库
> - ✅ Redis缓存
> - ✅ MongoDB文档存储

## 📝 重要说明

### 容器化平台选择建议

- **开发环境**: 使用Docker + Docker Compose，部署简单，资源消耗低
- **测试环境**: 可选择Docker Compose或单节点Kubernetes
- **生产环境**: 推荐使用Kubernetes集群，提供高可用性和扩展性

### 🛠️ 常见问题解决

#### 问题1: Docker 启动失败 - overlay2 选项错误
**错误信息**: 
```
failed to start daemon: error initializing graphdriver: overlay2: unknown option overlay2.override_kernel_check: overlay2
```

**原因**: `overlay2.override_kernel_check=true` 选项在新版本 Docker 中已被废弃

**解决方案**: 
```bash
# 移除已废弃的 storage-opts 配置
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "storage-driver": "overlay2"
}
EOF
```

#### 问题2: 镜像拉取超时或连接重置
**错误信息**: 
```
Error response from daemon: Get "https://registry-1.docker.io/v2/": context deadline exceeded
connection reset by peer
```

**原因**: 无法直接访问 Docker Hub 官方仓库

**解决方案**: 配置国内镜像源加速器
```bash
# 使用经过验证的国内镜像源
"registry-mirrors": [
  "https://docker.mirrors.tuna.tsinghua.edu.cn",
  "https://do.nark.eu.org", 
  "https://dc.j8.work",
  "https://docker.m.daocloud.io",
  "https://dockerproxy.com",
  "https://docker.mirrors.ustc.edu.cn",
  "https://docker.nju.edu.cn"
]
```

#### 问题3: JSON 配置语法错误
**错误信息**: Docker 服务启动失败，无明确错误

**解决方案**: 验证 JSON 语法
```bash
# 验证配置文件语法
python3 -m json.tool /etc/docker/daemon.json

# 常见语法错误：
# - 数组最后元素后多余的逗号
# - 缺少引号或括号不匹配
```

### 安全配置提醒

```bash
# 定期更新Docker
sudo apt update && sudo apt upgrade docker-ce docker-ce-cli containerd.io

# 清理未使用的容器和镜像
docker system prune -f

# 监控磁盘使用情况
docker system df
```

---
*文档更新时间: 2025年6月4日 - 修复Docker配置问题并优化镜像源配置*
