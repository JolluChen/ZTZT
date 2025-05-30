# 🚀 AI工作站RAID 0快速配置指南

## 📋 概述

本指南适用于已安装Ubuntu 24.04 LTS系统，需要添加两块新NVMe SSD配置RAID 0数据存储的AI工作站。

### 🎯 目标配置
- **系统盘**: 1TB NVMe SSD (已安装Ubuntu)
- **数据存储**: 2TB RAID 0 (2×1TB NVMe SSD)
- **性能**: 6000-7000 MB/s读写速度
- **挂载点**: `/data`

## ⚡ 一键配置

### 方法1: 下载并运行脚本

```bash
# 下载配置脚本
wget https://raw.githubusercontent.com/your-repo/quick-raid-setup.sh

# 设置执行权限
chmod +x quick-raid-setup.sh

# 运行配置 (需要sudo权限)
sudo ./quick-raid-setup.sh
```

### 方法2: 直接执行 (网络安装)

```bash
# 一键配置命令
curl -fsSL https://raw.githubusercontent.com/your-repo/quick-raid-setup.sh | sudo bash
```

### 方法3: 本地脚本

如果您已有脚本文件，直接运行：

```bash
sudo bash quick-raid-setup.sh
```

## 📝 配置过程

脚本将自动执行以下步骤：

1. **系统检查** - 验证Ubuntu版本和硬件
2. **工具安装** - 安装mdadm、parted等必要工具
3. **磁盘检查** - 检查新NVMe SSD健康状态
4. **用户确认** - 确认配置参数和数据清除
5. **磁盘准备** - 清除并分区新磁盘
6. **RAID创建** - 创建RAID 0阵列
7. **文件系统** - 创建优化的ext4文件系统
8. **自动挂载** - 配置开机自动挂载
9. **目录结构** - 创建AI平台目录
10. **性能优化** - 应用I/O和内核优化
11. **工具安装** - 创建管理和监控脚本
12. **环境变量** - 配置AI框架环境变量

## ⏱️ 预计时间

- **总时间**: 10-15分钟
- **用户交互**: 2-3次确认
- **自动化程度**: 95%

## 🔍 配置验证

配置完成后，验证系统状态：

```bash
# 检查RAID状态
raid-status

# 检查挂载
df -h /data

# 性能测试
sudo hdparm -t /dev/md0

# 查看目录结构
ls -la /data/
```

## 📊 预期结果

```bash
# RAID状态示例
=== AI工作站RAID 0状态 ===
RAID Level : raid0
Array Size : 1953384448 (1.82 TiB)
State : clean
Active Devices : 2

# 存储容量示例
Filesystem      Size  Used Avail Use% Mounted on
/dev/md0        1.8T   77M  1.7T   1% /data

# 性能测试示例
/dev/md0:
 Timing buffered disk reads: 18000 MB in  3.00 seconds = 6000.00 MB/sec
```

## 🛠️ 常用管理命令

```bash
# 快速状态检查
raid-status

# 详细RAID信息
sudo mdadm --detail /dev/md0

# 查看RAID活动
cat /proc/mdstat

# 性能测试
sudo hdparm -t /dev/md0

# 文件系统检查
sudo fsck.ext4 -n /dev/md0

# 重新挂载 (如果需要)
sudo umount /data
sudo mount /dev/md0 /data
```

## 🔧 故障排除

### 常见问题

1. **磁盘未检测到**
```bash
# 检查物理连接
sudo fdisk -l | grep nvme
lsblk

# 检查BIOS/UEFI设置
# 确保NVMe控制器已启用
```

2. **RAID创建失败**
```bash
# 检查磁盘状态
sudo smartctl -a /dev/nvme1n1
sudo smartctl -a /dev/nvme2n1

# 手动清除磁盘
sudo wipefs -a /dev/nvme1n1 /dev/nvme2n1
sudo sgdisk --zap-all /dev/nvme1n1 /dev/nvme2n1
```

3. **挂载失败**
```bash
# 检查文件系统
sudo fsck.ext4 /dev/md0

# 检查fstab配置
cat /etc/fstab | grep md0

# 手动挂载测试
sudo mount -t ext4 /dev/md0 /data
```

### 紧急恢复

如果配置出现问题，可以安全停止：

```bash
# 停止RAID阵列
sudo mdadm --stop /dev/md0

# 移除fstab条目
sudo nano /etc/fstab  # 删除相关行

# 清除磁盘 (如果需要重新开始)
sudo wipefs -a /dev/nvme1n1 /dev/nvme2n1
```

## 📈 性能优化建议

配置完成后，可以进一步优化：

1. **AI框架缓存配置**
```bash
# PyTorch
export TORCH_HOME="/data/cache/torch"

# TensorFlow  
export TF_KERAS_CACHE_DIR="/data/cache/tensorflow"

# Hugging Face
export TRANSFORMERS_CACHE="/data/cache/huggingface"
```

2. **Docker数据目录**
```bash
# 修改Docker数据目录到高速存储
sudo systemctl stop docker
sudo mkdir -p /data/docker
sudo rsync -aP /var/lib/docker/ /data/docker/
sudo mv /var/lib/docker /var/lib/docker.backup
sudo ln -s /data/docker /var/lib/docker
sudo systemctl start docker
```

3. **Conda包管理**
```bash
# 设置Conda包缓存到高速存储
conda config --add pkgs_dirs /data/cache/conda/pkgs
```

## 🔗 相关文档

- [容器化平台部署](./01_container_platform_setup.md)
- [GPU驱动配置](./gpu-setup-guide.md)
- [AI框架安装](./ai-frameworks-setup.md)
- [系统监控配置](./monitoring-setup.md)

## 📞 支持

如果遇到问题：

1. 检查日志文件: `/var/log/raid-setup-*.log`
2. 运行诊断: `sudo /usr/local/bin/validate-ai-workstation.sh`
3. 查看详细状态: `raid-status`

---

**⚠️ 重要提醒**: RAID 0无数据冗余，重要数据请定期备份！
