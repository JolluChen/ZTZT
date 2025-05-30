# ⭐ AI中台 - 操作系统安装与基础配置 (Ubuntu 24.04 LTS)

本文档指导在目标服务器上安装和配置 **Ubuntu 24.04 LTS** 操作系统，为AI中台提供稳定的基础环境。

> **🎯 一体化配置指南**: 
> 本文档包含完整的系统安装、RAID配置、GPU环境和AI框架配置
> - ✅ **操作系统安装**: Ubuntu 24.04 LTS安装流程
> - ✅ **RAID 0配置**: 2TB高速数据存储配置 (一键自动化+手动配置)
> - ✅ **AI环境配置**: GPU驱动、CUDA、PyTorch/TensorFlow安装
> - ✅ **系统优化**: AI工作负载性能优化

## 📋 文档概述

### 🎯 部署目标
- ✅ Ubuntu 24.04 LTS Server 基础系统
- ✅ 系统安全配置和加固
- ✅ 网络和防火墙设置
- ✅ Python 3.10 开发环境
- ✅ GPU驱动和CUDA环境 (RTX 2080Ti × 5)
- ✅ 系统监控和日志配置

### ⏱️ 预计部署时间
- **系统安装**: 30-45分钟
- **基础配置**: 30-45分钟
- **安全加固**: 20-30分钟
- **GPU配置**: 20-30分钟
- **总计**: 1.5-2.5小时

### 🖥️ 目标硬件配置
- **CPU**: 高性能多核处理器
- **内存**: 128GB DDR4/DDR5
- **显卡**: 5×RTX 2080Ti (55GB总显存)
- **存储**: 3×1TB SATA SSD (系统盘+RAID0数据存储)
- **网络**: 千兆以上网络接口

#### 存储架构设计
```
┌─────────────────┬─────────────────┬─────────────────┐
│  /dev/sda (1TB) │ /dev/sdb (1TB)  │ /dev/sdc (1TB)  │
│   系统盘        │                 │                 │
│  Ubuntu 24.04   │    RAID 0       │    RAID 0       │
│   /boot: 1GB    │   数据存储       │   数据存储       │
│   /: ~999GB     │   /data: ~2TB   │   /data: ~2TB   │
└─────────────────┴─────────────────┴─────────────────┘
```

#### AI计算性能预期
- **深度学习训练**: 5块RTX 2080Ti并行计算
- **大模型推理**: 55GB显存支持大型AI模型
- **数据处理**: 2TB RAID 0高速数据存储
- **系统响应**: NVMe SSD确保极快的I/O性能


## 1. 操作系统安装 (Ubuntu 24.04 LTS)

在所有目标服务器上安装 Ubuntu 24.04 LTS。请遵循以下步骤：

1.  **下载 Ubuntu Server 24.04 LTS ISO**: 
    从 Ubuntu 官方网站下载 ISO 镜像文件: [https://ubuntu.com/download/server](https://ubuntu.com/download/server)
    
    建议选择：**Ubuntu Server 24.04 LTS (Long Term Support)**

2.  **创建可引导 USB驱动器**: 
    使用工具如 Rufus (Windows), balenaEtcher (跨平台), 或 `dd` (Linux/macOS) 将下载的 ISO 镜像写入 USB 驱动器。
    例如，在 Linux 上使用 `dd` (请谨慎操作，确保 `/dev/sdX` 是正确的 USB 设备):
    ```bash
    sudo dd if=/path/to/ubuntu-22.04.x-live-server-amd64.iso of=/dev/sdX bs=4M status=progress conv=fdatasync
    ```

3.  **从 USB 启动服务器**: 
    - 将 USB 驱动器插入目标服务器，启动服务器。
    - 在服务器启动的初始阶段，屏幕通常会短暂显示进入 BIOS/UEFI 设置的热键提示。
    
      > 常见的按键包括 **Del, F2, F10, F12, 或 Esc**。不同品牌和型号的服务器/主板可能会使用不同的按键，请留意屏幕提示或查阅服务器/主板的说明手册以确认正确的按键。
    
    - 按下正确的按键后，您将进入 BIOS/UEFI 设置界面。
    - 在该界面中，找到“Boot”或“启动”选项卡，将 USB 驱动器设置为第一启动设备。
    - 保存更改并退出 BIOS/UEFI 设置程序，服务器将尝试从 USB 驱动器启动。

4.  **Ubuntu 安装过程**: 
    服务器将从 USB 启动并加载 Ubuntu 安装程序。
    *   **语言选择**: 选择您的语言。
    *   **键盘布局**: 选择您的键盘布局。
    *   **网络配置**: 
        *   安装程序会尝试通过 DHCP 自动配置网络。如果需要静态 IP，请在此处配置。
        *   确保服务器可以访问互联网以下载更新和软件包。
    *   **代理配置**: 如果您的网络需要代理才能访问互联网，请在此处配置。
    *   **镜像源配置**: 
        *   默认通常是 `archive.ubuntu.com`。在中国大陆，建议修改为国内镜像源以加快速度。
        *   安装程序通常会提供一个输入框让您手动编辑镜像地址。您可以将其修改为例如：
            *   阿里云: `http://mirrors.aliyun.com/ubuntu/`
            *   清华大学: `http://mirrors.tuna.tsinghua.edu.cn/ubuntu/`
            *   华为云: `https://mirrors.huaweicloud.com/ubuntu/`
            *   网易: `http://mirrors.163.com/ubuntu/`
        *   选择一个离您地理位置较近或访问速度较快的镜像源。
    *   **存储布局**: 
        *   **RAID 配置 (可选但推荐用于服务器)**:
            *   在 Ubuntu Server 安装开始之前，您通常需要在服务器的 BIOS/UEFI 或专门的 RAID 控制器配置界面中设置 RAID。此步骤因硬件而异。
            *   常见的 RAID 级别及其特性:
                *   **RAID 0 (Stripe)**: 至少需要2个磁盘。数据被分成块，交替写入所有磁盘。提供最高的性能（读写速度接近所有磁盘速度之和），但没有冗余。任何一个磁盘故障都会导致所有数据丢失。适用于对性能要求极高且数据可轻松恢复的场景。
                *   **RAID 1 (Mirror)**: 至少需要2个磁盘。数据完全相同地写入到每个磁盘（镜像）。提供良好的读取性能和写入性能（写入速度受限于最慢的磁盘）。在一个磁盘发生故障时，数据仍然可用。磁盘利用率为50%。适用于对数据可靠性要求高的场景。
                *   **RAID 5 (Stripe with Parity)**: 至少需要3个磁盘。数据和奇偶校验信息被条带化地分布在所有磁盘上。允许一个磁盘发生故障而数据不丢失。读取性能好，写入性能一般。磁盘利用率为 (N-1)/N (N为磁盘数量)。是性能、容量和可靠性的良好折中。
                *   **RAID 6 (Stripe with Dual Parity)**: 至少需要4个磁盘。与 RAID 5 类似，但使用两个独立的奇偶校验块。允许两个磁盘同时发生故障而数据不丢失。提供更高的可靠性，但写入性能较差，成本也更高。
                *   **RAID 10 (RAID 1+0)**: 至少需要4个磁盘（偶数个）。先将磁盘两两组成 RAID 1 镜像对，然后再将这些镜像对组成 RAID 0 条带。兼具 RAID 0 的高性能和 RAID 1 的高可靠性。允许每个镜像对中的一个磁盘发生故障。磁盘利用率为50%。成本较高。
            *   **选择 RAID 级别的考虑因素**: 性能需求、数据重要性、预算、可用磁盘数量。
            *   **配置方法**: 通常在服务器启动时按特定键 (如 Ctrl+R, Ctrl+M, F8 等，具体请参考服务器或 RAID 卡手册) 进入 RAID 配置工具。在该工具中，您可以选择物理磁盘来创建逻辑驱动器 (Virtual Disk) 并指定 RAID 级别、条带大小等参数。
            *   **注意**: 创建 RAID 后，操作系统安装程序会将此 RAID 卷视为一个单独的磁盘进行后续分区。        *   **AI中台生产环境分区方案 (RAID 0 + 系统盘)**: 
            *   在 Ubuntu 安装程序的存储配置步骤，选择 **Custom storage layout** (自定义存储布局)。
            *   **系统盘 (SATA SSD)**: `/dev/sda` - 1TB SATA SSD (安装系统)
            *   **数据存储 RAID 0 (SATA SSD x2)**: `/dev/sdb` + `/dev/sdc` - ~2TB 总容量
            
        *   **实际磁盘配置方案**:
            ```bash
            # 当前磁盘配置 
            # /dev/sda (1TB) - 系统盘，用于Ubuntu安装
            # /dev/sdb (1TB) - 数据存储 RAID 0 成员1 (安装后配置)
            # /dev/sdc (1TB) - 数据存储 RAID 0 成员2 (安装后配置)
            ```
            
            1.  **系统盘分区 (`/dev/sda`)** - 安装时配置:
                *   **`/boot/efi`**: 512MB (EFI系统分区, FAT32)
                *   **`/boot`**: 1GB (启动分区, ext4)
                *   **根分区 (`/`)**: ~998GB (根文件系统, ext4)
                *   **注意**: 简化分区策略，便于管理和维护
                
            2.  **RAID 0 数据存储 (系统安装后配置)**:
                *   使用软件RAID创建RAID 0阵列 (`/dev/md0`)
                *   源设备: `/dev/sdb` + `/dev/sdc`
                *   挂载点: `/data` (~2TB RAID 0阵列，用于AI模型和数据存储)
                *   配置脚本: `setup_raid0_sdb_sdc.sh` (一键自动配置)
                  *   **分区大小配置 (AI工作站 - SATA SSD)**:
            ```
            系统盘 (/dev/sda - 1TB):
            ├── /boot/efi: 512MB (FAT32, EFI系统分区)
            ├── /boot: 1GB (ext4, 启动分区)
            └── /: ~998GB (ext4, 根文件系统)
            
            数据存储 (RAID 0 - 2TB):
            └── /data: ~2TB (ext4, AI模型和数据存储)
            ```
              *   **性能优化配置**:
            *   **文件系统**: 使用ext4，启用`noatime`和`data=writeback`选项
            *   **I/O调度器**: 设置为`mq-deadline`以优化SATA SSD性能
            *   **RAID条带大小**: 128KB (优化AI工作负载的大文件读写)
            *   **文件系统块大小**: 4KB (平衡性能和空间效率)
        *   **确认并写入更改**: 在 Ubuntu 安装程序中完成分区设置后，确认更改并继续安装。
    *   **配置文件设置**: 
        *   设置服务器的主机名 (Your server's name)。
        *   设置您的用户名 (Your name) 和密码 (Pick a username, Choose a password, Confirm your password)。
    *   **SSH 设置**: 
        *   选择 '''Install OpenSSH server''' 以便远程管理服务器。
        *   可以选择从 GitHub/Launchpad 导入 SSH 密钥。
    *   **特色服务器快照 (Featured Server Snaps)**: 您可以选择安装一些推荐的 Snap 包，例如 Docker。但由于我们后续会手动安装特定版本的 Docker Engine，此处可以跳过或不选择 Docker。
    *   **安装开始**: 确认配置后，安装过程将开始。这可能需要一些时间。
    *   **安装完成与重启**: 安装完成后，移除 USB 驱动器并重启服务器。

5.  **首次登录和系统更新**: 
    使用您在安装过程中创建的用户名和密码通过 SSH 或直接登录服务器。
    登录后，立即更新系统软件包：
    ```bash
    sudo apt update
    sudo apt upgrade -y
    sudo apt autoremove -y # 可选，移除不再需要的包
    sudo reboot # 如果内核有更新，建议重启
    ```

6.  **(可选) 基本配置**: 
    *   **设置时区**: `sudo timedatectl set-timezone Asia/Shanghai` (替换为您的时区)
    *   **配置 NTP 时间同步**: 确保 `systemd-timesyncd` 服务已启用并运行。
        ```bash
        sudo timedatectl set-ntp true
        timedatectl status
        ```
    *   **配置防火墙 (UFW)**: 如果需要，配置 UFW (Uncomplicated Firewall) 并打开必要的端口 (例如 SSH)。
        ```bash
        sudo ufw allow OpenSSH
        sudo ufw enable
        sudo ufw status
        ```

完成以上步骤后，您的服务器就已经准备好了 Ubuntu 24.04 LTS 操作系统，可以继续进行后续的系统层组件部署。

## 2. 系统安装后配置

### 2.0 RAID 0高速数据存储配置

> **🎯 配置目标**: 将两块1TB SATA SSD配置为RAID 0阵列，提供~2TB高速数据存储
> - **系统盘**: `/dev/sda` (1TB, 已安装Ubuntu)  
> - **数据存储**: `/dev/sdb` + `/dev/sdc` → `/dev/md0` (~2TB RAID 0)
> - **挂载点**: `/data` (AI模型和数据存储)
> - **预期性能**: 1000-1200 MB/s读写速度 (SATA限制)
> - **总配置时间**: 10-15分钟 (95%自动化)

#### ⚡ 方法一：一键自动配置 (推荐)

**选项1: 使用专用脚本**
```bash
# 运行针对sda/sdb/sdc配置的专用脚本
sudo bash docs/deployment/01_environment_deployment/setup_raid0_sdb_sdc.sh
```
```bash
# 创建并运行自动配置脚本
sudo tee /usr/local/bin/setup-raid0.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 AI工作站RAID 0配置脚本"
echo "========================================"

# 1. 检查环境
echo "检查系统环境..."
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用sudo权限运行此脚本"
    exit 1
fi

# 检查NVMe设备
NVME_COUNT=$(lsblk -d -n | grep nvme | wc -l)
if [ "$NVME_COUNT" -lt 3 ]; then
    echo "❌ 检测到${NVME_COUNT}块NVMe设备，至少需要3块"
    exit 1
fi

echo "✅ 检测到${NVME_COUNT}块NVMe设备"

# 2. 显示当前设备
echo "当前NVMe设备:"
lsblk -d -o NAME,SIZE,MODEL | grep nvme

# 3. 用户确认
echo ""
echo "⚠️  警告: 此操作将清除 /dev/nvme1n1 和 /dev/nvme2n1 上的所有数据!"
echo "确认配置RAID 0数据存储? (将占用nvme1n1和nvme2n1)"
read -p "输入 'YES' 确认: " confirm
if [ "$confirm" != "YES" ]; then
    echo "操作已取消"
    exit 0
fi

# 4. 安装必要工具
echo "安装RAID管理工具..."
apt update
apt install -y mdadm parted smartmontools nvme-cli

# 5. 磁盘健康检查
echo "检查磁盘健康状态..."
smartctl -H /dev/nvme1n1 && smartctl -H /dev/nvme2n1 || {
    echo "⚠️  磁盘健康检查警告，请检查磁盘状态"
    read -p "是否继续? (y/N): " continue_anyway
    [[ "$continue_anyway" != "y" ]] && exit 1
}

# 6. 清理目标设备
echo "清理目标设备..."
wipefs -a /dev/nvme1n1 /dev/nvme2n1
sgdisk --zap-all /dev/nvme1n1 /dev/nvme2n1

# 7. 创建RAID 0 (优化参数)
echo "创建RAID 0阵列..."
mdadm --create --verbose /dev/md0 \
    --level=0 \
    --raid-devices=2 \
    --chunk=64 \
    --metadata=1.2 \
    /dev/nvme1n1 /dev/nvme2n1

# 8. 等待RAID初始化
echo "等待RAID初始化..."
sleep 5

# 9. 创建优化的ext4文件系统
echo "创建优化的ext4文件系统..."
mkfs.ext4 -F -L "ZT-DATA" \
    -O ^has_journal,large_file,extent,flex_bg \
    -E stride=16,stripe-width=32,lazy_itable_init=0 \
    -m 1 \
    /dev/md0

# 10. 创建挂载点和配置自动挂载
mkdir -p /data
UUID=$(blkid -s UUID -o value /dev/md0)
echo "UUID=${UUID} /data ext4 defaults,noatime,data=writeback,barrier=0 0 2" >> /etc/fstab

# 11. 挂载并创建目录结构
mount /data
mkdir -p /data/{cache,tmp,models,datasets,outputs,logs}
mkdir -p /data/cache/{torch,tensorflow,huggingface,conda}

# 12. 设置权限
chown -R $SUDO_USER:$SUDO_USER /data
chmod 755 /data

# 13. 保存RAID配置
mdadm --detail --scan >> /etc/mdadm/mdadm.conf
update-initramfs -u

# 14. 创建管理脚本
tee /usr/local/bin/raid-status << 'SCRIPT_EOF'
#!/bin/bash
echo "=== AI工作站RAID 0状态 ==="
cat /proc/mdstat
echo ""
mdadm --detail /dev/md0
echo ""
echo "存储使用情况:"
df -h /data
echo ""
echo "最近性能 (如需完整测试请运行: sudo hdparm -t /dev/md0):"
hdparm -t /dev/md0 2>/dev/null | tail -1 || echo "请安装hdparm: sudo apt install hdparm"
SCRIPT_EOF
chmod +x /usr/local/bin/raid-status

# 15. 配置AI框架环境变量
tee -a /etc/environment << 'ENV_EOF'
# AI框架缓存配置
TORCH_HOME=/data/cache/torch
TF_KERAS_CACHE_DIR=/data/cache/tensorflow
TRANSFORMERS_CACHE=/data/cache/huggingface
CONDA_PKGS_DIRS=/data/cache/conda
ENV_EOF

# 16. 最终验证和报告
echo ""
echo "✅ RAID 0配置完成!"
echo "========================================"
cat /proc/mdstat
echo ""
echo "存储信息:"
df -h /data
echo ""
echo "性能测试:"
hdparm -t /dev/md0
echo ""
echo "管理命令: raid-status"
echo "========================================"

EOF

# 设置执行权限并运行
chmod +x /usr/local/bin/setup-raid0.sh
sudo /usr/local/bin/setup-raid0.sh
```

**选项2: 网络一键配置**
```bash
# 从网络直接下载并执行 (如果脚本已发布)
curl -fsSL https://raw.githubusercontent.com/your-repo/quick-raid-setup.sh | sudo bash
```

#### 🔧 方法二：手动分步配置

如果需要自定义配置或学习详细过程，可以手动执行：

```bash
# 1. 安装必要工具
sudo apt update
sudo apt install -y mdadm parted smartmontools hdparm

# 2. 检查磁盘 (确认sda为系统盘，sdb/sdc为数据盘)
sudo fdisk -l | grep -E "(sda|sdb|sdc)"
sudo lsblk -d -o NAME,SIZE,MODEL | grep -E "(sda|sdb|sdc)"

# 3. 磁盘健康检查
sudo smartctl -H /dev/sdb
sudo smartctl -H /dev/sdc

# 4. 清理数据盘 (⚠️ 会删除sdb和sdc上的所有数据)
sudo wipefs -a /dev/sdb /dev/sdc
sudo sgdisk --zap-all /dev/sdb /dev/sdc

# 5. 创建RAID 0 (sdb + sdc整盘模式)
sudo mdadm --create --verbose /dev/md0 \
    --level=0 \
    --raid-devices=2 \
    --chunk=128 \
    --metadata=1.2 \
    /dev/sdb /dev/sdc

# 6. 创建文件系统
sudo mkfs.ext4 -F -L "ZT-DATA-RAID0" \
    -O ^has_journal,large_file,extent,flex_bg \
    -E stride=32,stripe-width=64,lazy_itable_init=0 \
    -m 1 \
    /dev/md0

# 7. 挂载配置
sudo mkdir -p /data
UUID=$(sudo blkid -s UUID -o value /dev/md0)
echo "UUID=${UUID} /data ext4 defaults,noatime,data=writeback,barrier=0,stripe=64 0 2" | sudo tee -a /etc/fstab
sudo mount /data

# 8. 创建AI数据目录结构
sudo mkdir -p /data/{models,datasets,cache,tmp,outputs,logs,workspace}
sudo mkdir -p /data/cache/{torch,tensorflow,huggingface,conda,pip}
sudo chown -R $USER:$USER /data

# 9. 保存RAID配置
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf
sudo update-initramfs -u
sudo update-initramfs -u
```

#### 📊 配置验证

配置完成后，验证系统状态：

```bash
# 检查RAID状态
raid-status

# 或手动检查
cat /proc/mdstat
sudo mdadm --detail /dev/md0

# 检查挂载
df -h /data

# 性能测试
sudo hdparm -t /dev/md0

# 查看目录结构
ls -la /data/
```

#### 🔧 常用管理命令

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

#### 🚨 故障排除

**常见问题及解决方案:**

1. **磁盘未检测到**
```bash
# 检查物理连接
sudo fdisk -l | grep -E "(sda|sdb|sdc)"
lsblk | grep -E "(sda|sdb|sdc)"
# 检查BIOS/UEFI设置，确保SATA控制器已启用
```

2. **RAID创建失败**
```bash
# 检查磁盘状态
sudo smartctl -a /dev/sdb
sudo smartctl -a /dev/sdc

# 手动清除磁盘
sudo wipefs -a /dev/sdb /dev/sdc
sudo sgdisk --zap-all /dev/sdb /dev/sdc
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

**紧急恢复:**
```bash
# 停止RAID阵列
sudo mdadm --stop /dev/md0

# 移除fstab条目
sudo nano /etc/fstab  # 删除相关行

# 清除磁盘 (如果需要重新开始)
sudo wipefs -a /dev/sdb /dev/sdc
```

#### 📈 性能优化建议

**预期性能指标 (SATA SSD RAID 0):**
- **顺序读取**: 1000-1200 MB/s
- **顺序写入**: 900-1100 MB/s
- **随机4K读取**: 90,000-110,000 IOPS
- **随机4K写入**: 80,000-100,000 IOPS

**AI框架缓存优化:**
```bash
# PyTorch缓存
export TORCH_HOME="/data/cache/torch"

# TensorFlow缓存
export TF_KERAS_CACHE_DIR="/data/cache/tensorflow"

# Hugging Face缓存
export TRANSFORMERS_CACHE="/data/cache/huggingface"

# Conda包缓存
conda config --add pkgs_dirs /data/cache/conda/pkgs
```

**Docker数据目录迁移:**
```bash
# 停止Docker并迁移数据到高速存储
sudo systemctl stop docker
sudo mkdir -p /data/docker
sudo rsync -aP /var/lib/docker/ /data/docker/
sudo mv /var/lib/docker /var/lib/docker.backup
sudo ln -s /data/docker /var/lib/docker
sudo systemctl start docker
```

> **⚠️ 重要提醒**: RAID 0无数据冗余，重要数据请定期备份！

### 2.1 时区和本地化设置

```bash
# 设置时区
sudo timedatectl set-timezone Asia/Shanghai

# 启用NTP时间同步
sudo timedatectl set-ntp true

# 验证时间配置
timedatectl status
```

### 2.2 主机名和网络配置

```bash
# 设置主机名
sudo hostnamectl set-hostname ai-platform-server

# 更新hosts文件
echo "127.0.0.1 $(hostname)" | sudo tee -a /etc/hosts

# 配置静态IP (如果需要)
# 编辑网络配置文件
sudo nano /etc/netplan/00-installer-config.yaml
```

### 2.3 SSH安全配置

```bash
# 备份SSH配置
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# 创建安全配置
sudo tee /etc/ssh/sshd_config.d/99-security.conf << 'EOF'
# SSH安全配置
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication yes
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
EOF

# 重启SSH服务
sudo systemctl restart sshd
```

### 2.4 防火墙配置

```bash
# 启用UFW防火墙
sudo ufw enable

# 基础规则配置
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# AI平台端口 (可选)
sudo ufw allow 8000:8010/tcp  # Django开发服务器
sudo ufw allow 3000:3010/tcp  # Frontend服务
sudo ufw allow 5432/tcp       # PostgreSQL
sudo ufw allow 6379/tcp       # Redis

# 查看防火墙状态
sudo ufw status verbose
```

### 2.5 基础工具安装

```bash
# 更新软件包列表
sudo apt update

# 安装基础编辑器和工具
sudo apt install -y vim nano curl wget git tree htop

# 安装网络和系统工具
sudo apt install -y net-tools unzip software-properties-common

# 安装构建工具和开发库
sudo apt install -y build-essential smartmontools nvme-cli

# 验证安装
vim --version
git --version
```

## 3. Python 3.10 开发环境配置

Ubuntu 24.04 LTS默认包含Python 3.12，但AI平台需要确保Python 3.10的兼容性：

### 3.1 Python环境安装

```bash
# 检查当前Python版本
python3 --version

# 如需Python 3.10，添加deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# 安装Python 3.10及开发工具
sudo apt install -y python3.10 python3.10-venv python3.10-dev
sudo apt install -y python3-pip python3-wheel python3-setuptools

# 安装AI开发必需的系统库
sudo apt install -y libpq-dev libffi-dev libssl-dev
sudo apt install -y libjpeg-dev libpng-dev libxml2-dev libxslt1-dev

# 验证安装
python3 --version
pip3 --version
```

### 3.2 AI开发工具链

```bash
# 安装Node.js (前端开发需要)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# 安装数据库客户端
sudo apt install -y postgresql-client redis-tools

# 验证安装
node --version
npm --version
psql --version
redis-cli --version
```

## 4. GPU驱动和AI框架配置

### 4.1 NVIDIA驱动安装 (RTX 2080Ti × 5)

```bash
# 检测可用的NVIDIA驱动
sudo apt install -y ubuntu-drivers-common
ubuntu-drivers devices

# 安装推荐的NVIDIA驱动 (自动检测)
sudo ubuntu-drivers autoinstall

# 或手动安装特定版本 (RTX 2080Ti兼容)
sudo apt install -y nvidia-driver-535

# 重启系统使驱动生效
sudo reboot

# 重启后验证GPU状态
nvidia-smi
```

### 4.2 CUDA工具包配置

```bash
# 下载并安装CUDA 12.x
wget https://developer.download.nvidia.com/compute/cuda/12.3.0/local_installers/cuda_12.3.0_545.23.06_linux.run

# 运行CUDA安装程序 (不安装驱动，因为已安装)
sudo sh cuda_12.3.0_545.23.06_linux.run

# 配置CUDA环境变量
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export CUDA_HOME=/usr/local/cuda' >> ~/.bashrc
source ~/.bashrc

# 验证CUDA安装
nvcc --version
nvidia-smi
```

### 4.3 AI框架安装

```bash
# 更新pip
pip3 install --upgrade pip

# 安装PyTorch (CUDA支持)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装TensorFlow (GPU支持)
pip3 install tensorflow[and-cuda]

# 安装常用AI库
pip3 install numpy pandas scikit-learn matplotlib seaborn
pip3 install transformers datasets accelerate
pip3 install jupyter notebook

# 验证GPU可用性
python3 -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}, GPU count: {torch.cuda.device_count()}')"
python3 -c "import tensorflow as tf; print(f'TensorFlow GPU: {len(tf.config.list_physical_devices(\"GPU\"))}')"
```

### 4.4 GPU监控和管理

```bash
# 创建GPU状态检查脚本
sudo tee /usr/local/bin/gpu-status.sh << 'EOF'
#!/bin/bash
echo "=== GPU状态检查 ==="
echo "时间: $(date)"
echo "GPU硬件信息:"
nvidia-smi --query-gpu=name,memory.total,temperature.gpu,power.draw --format=csv
echo
nvidia-smi
EOF

sudo chmod +x /usr/local/bin/gpu-status.sh

# 运行GPU状态检查
/usr/local/bin/gpu-status.sh
```

## 5. 系统性能优化

### 5.1 AI工作站内核参数优化

```bash
# 创建AI工作站优化配置
sudo tee /etc/sysctl.d/99-ai-workstation.conf << 'EOF'
# ========== 网络优化 ==========
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_congestion_control = bbr

# ========== 内存优化 (128GB RAM) ==========
vm.swappiness = 1
vm.dirty_ratio = 40
vm.dirty_background_ratio = 10
vm.max_map_count = 1048576

# ========== 文件系统优化 ==========
fs.file-max = 1048576
fs.inotify.max_user_watches = 524288

# ========== AI计算优化 ==========
kernel.numa_balancing = 0
kernel.sched_autogroup_enabled = 0
EOF

# 应用配置
sudo sysctl -p /etc/sysctl.d/99-ai-workstation.conf
```

### 5.2 用户资源限制优化

```bash
# 配置资源限制
sudo tee /etc/security/limits.d/99-ai-workstation.conf << 'EOF'
# 文件描述符限制
* soft nofile 1048576
* hard nofile 1048576

# 进程数限制
* soft nproc 131072
* hard nproc 131072

# 内存锁定 (GPU计算需要)
* soft memlock unlimited
* hard memlock unlimited
EOF
```

### 5.3 AI环境变量配置

```bash
# 配置AI框架环境变量
sudo tee -a /etc/environment << 'EOF'
# CUDA环境
CUDA_HOME=/usr/local/cuda
CUDA_DEVICE_ORDER=PCI_BUS_ID

# PyTorch优化
OMP_NUM_THREADS=16
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# TensorFlow优化
TF_GPU_ALLOCATOR=cuda_malloc_async
TF_CPP_MIN_LOG_LEVEL=2

# 通用优化
MKL_NUM_THREADS=16
OPENBLAS_NUM_THREADS=16
EOF

# 创建AI数据目录 (如果已配置RAID 0)
if mountpoint -q /data; then
    sudo mkdir -p /data/{cache,tmp,models,datasets,outputs}
    sudo chown -R $USER:$USER /data/
fi
```

## 6. 验证系统就绪状态

创建系统检查脚本：

```bash
# 创建系统检查脚本
sudo tee /usr/local/bin/check-system.sh << 'EOF'
#!/bin/bash

echo "=== AI平台高性能工作站环境检查 ==="
echo "检查时间: $(date)"
echo

echo "1. 操作系统信息:"
lsb_release -a
echo "主机名: $(hostname)"
echo "内核版本: $(uname -r)"
echo

echo "2. 硬件配置:"
echo "CPU: $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)"
echo "CPU核心数: $(nproc)"
echo "内存大小: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo "内存使用: $(free -h | grep '^Mem:' | awk '{print $3"/"$2}')"
echo

echo "3. 存储配置:"
echo "系统盘 (/):"
df -h / | tail -1 | awk '{print "  空间: "$2" | 已用: "$3" | 可用: "$4" | 使用率: "$5}'
echo "数据存储 (/data):"
if mountpoint -q /data; then
    df -h /data | tail -1 | awk '{print "  空间: "$2" | 已用: "$3" | 可用: "$4" | 使用率: "$5}'
    echo "  RAID状态: $(cat /proc/mdstat | grep md0 | awk '{print $3" "$4" "$5}')"
else
    echo "  /data 未挂载或不存在"
fi
echo

echo "4. GPU配置验证"
echo "----------------------------------------"
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA驱动: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
    echo "CUDA版本: $(nvcc --version 2>/dev/null | grep release | awk '{print $6}' | cut -d, -f1 || echo '未安装')"
    echo "GPU数量: $(nvidia-smi --list-gpus | wc -l)"
    echo "GPU详情:"
    nvidia-smi --query-gpu=index,name,memory.total,temperature.gpu --format=csv | grep -v index
    echo "总显存: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | awk '{sum+=$1} END {printf "%.1fGB", sum/1024}')"
else
    echo "未检测到NVIDIA驱动或GPU"
fi
echo

echo "5. Python环境:"
python3 --version
pip3 --version
if python3 -c "import torch" 2>/dev/null; then
    echo "PyTorch: $(python3 -c "import torch; print(torch.__version__)")"
    echo "PyTorch CUDA: $(python3 -c "import torch; print('可用' if torch.cuda.is_available() else '不可用')")"
fi
if python3 -c "import tensorflow" 2>/dev/null; then
    echo "TensorFlow: $(python3 -c "import tensorflow as tf; print(tf.__version__)")"
fi
echo

echo "6. 网络配置:"
echo "活动网络接口:"
ip addr show | grep -E "^[0-9]+:" | grep -v lo | awk '{print "  "$2}' | tr -d ':'
echo "活动连接:"
ip addr show | grep -E "inet.*global" | awk '{print "  "$2}' | head -3
echo "DNS配置:"
grep nameserver /etc/resolv.conf | awk '{print "  "$2}' | head -2
echo

echo "7. 系统服务:"
echo "SSH服务: $(systemctl is-active ssh)"
echo "时间同步: $(timedatectl status | grep 'synchronized' | awk '{print $4}')"
echo "防火墙: $(sudo ufw status | head -1 | cut -d: -f2 | xargs)"
echo "系统负载: $(uptime | awk -F'load average:' '{print $2}' | xargs)"
echo

echo "8. 系统性能:"
echo "系统负载: $(uptime | awk -F'load average:' '{print $2}')"
echo "磁盘I/O:"
if command -v iostat &> /dev/null; then
    iostat -x 1 1 | grep -E "nvme|md0" | tail -3
else
    echo "  iostat未安装 (apt install sysstat)"
fi
echo

echo "9. AI平台目录结构:"
if [ -d "/data" ]; then
    echo "/data目录结构:"
    ls -la /data/ 2>/dev/null || echo "  无法访问/data目录"
else
    echo "/data目录不存在"
fi
echo

echo "========================================"
echo "验证完成时间: $(date)"
echo "========================================"
EOF

# 设置执行权限
sudo chmod +x /usr/local/bin/check-system.sh

# 运行检查
check-system.sh
```

## 7. 完整系统验证和性能测试

### 7.1 硬件配置验证

```bash
# 创建完整的硬件验证脚本
sudo tee /usr/local/bin/validate-ai-workstation.sh << 'EOF'
#!/bin/bash

echo "========================================"
echo "    AI高性能工作站完整验证测试"
echo "========================================"
echo "测试时间: $(date)"
echo

# 1. 基础硬件检测
echo "1. 硬件配置验证"
echo "----------------------------------------"
echo "CPU信息:"
echo "  型号: $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)"
echo "  核心数: $(nproc) 物理核心"
echo "  架构: $(lscpu | grep Architecture | cut -d: -f2 | xargs)"

echo "内存信息:"
echo "  总内存: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo "  可用内存: $(free -h | grep '^Mem:' | awk '{print $7}')"
echo "  内存使用率: $(free | grep '^Mem:' | awk '{printf "%.1f%%", ($3/$2)*100}')"

if [ -f /proc/meminfo ]; then
    echo "  内存详情: $(grep MemTotal /proc/meminfo | awk '{printf "%.1fGB", $2/1024/1024}')"
fi
echo

# 2. 存储系统验证
echo "2. 存储系统验证"
echo "----------------------------------------"
echo "NVMe设备:"
lsblk -d -o NAME,SIZE,MODEL | grep nvme || echo "  未检测到NVMe设备"

echo "RAID状态:"
if [ -f /proc/mdstat ]; then
    cat /proc/mdstat | grep -A3 md0 || echo "  RAID未配置"
else
    echo "  mdadm未安装"
fi

echo "文件系统:"
echo "  系统盘: $(df -h / | tail -1 | awk '{print $2" 总计, "$4" 可用, "$5" 使用率"}')"
if mountpoint -q /data; then
    echo "  数据盘: $(df -h /data | tail -1 | awk '{print $2" 总计, "$4" 可用, "$5" 使用率"}')"
else
    echo "  数据盘: 未挂载"
fi
echo

# 3. GPU配置验证
echo "3. GPU配置验证"
echo "----------------------------------------"
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA驱动: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
    echo "CUDA版本: $(nvcc --version 2>/dev/null | grep release | awk '{print $6}' | cut -d, -f1 || echo '未安装')"
    echo "GPU数量: $(nvidia-smi --list-gpus | wc -l)"
    echo "GPU详情:"
    nvidia-smi --query-gpu=index,name,memory.total,temperature.gpu --format=csv | grep -v index
    echo "总显存: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | awk '{sum+=$1} END {printf "%.1fGB", sum/1024}')"
else
    echo "未检测到NVIDIA驱动或GPU"
fi
echo

# 4. 网络配置验证
echo "4. 网络配置验证"
echo "----------------------------------------"
echo "网络接口:"
ip addr show | grep -E "^[0-9]+:" | grep -v lo | awk '{print "  "$2}' | tr -d ':'
echo "活动连接:"
ip addr show | grep -E "inet.*global" | awk '{print "  "$2}' | head -3
echo "DNS配置:"
grep nameserver /etc/resolv.conf | awk '{print "  "$2}' | head -2
echo

# 5. 系统服务验证
echo "5. 系统服务验证"
echo "----------------------------------------"
echo "SSH服务: $(systemctl is-active ssh)"
echo "时间同步: $(timedatectl status | grep 'synchronized' | awk '{print $4}')"
echo "防火墙: $(sudo ufw status | head -1 | cut -d: -f2 | xargs)"
echo "系统负载: $(uptime | awk -F'load average:' '{print $2}' | xargs)"
echo

# 6. AI框架验证
echo "6. AI框架验证"
echo "----------------------------------------"
if python3 -c "import torch" 2>/dev/null; then
    echo "PyTorch: $(python3 -c "import torch; print(torch.__version__)")"
    echo "PyTorch CUDA: $(python3 -c "import torch; print('支持' if torch.cuda.is_available() else '不支持')")"
    if python3 -c "import torch; torch.cuda.is_available()" 2>/dev/null; then
        echo "可用GPU数: $(python3 -c "import torch; print(torch.cuda.device_count())")"
    fi
else
    echo "PyTorch: 未安装"
fi

if python3 -c "import tensorflow" 2>/dev/null; then
    echo "TensorFlow: $(python3 -c "import tensorflow as tf; print(tf.__version__)")"
    echo "TF GPU支持: $(python3 -c "import tensorflow as tf; print('支持' if len(tf.config.list_physical_devices('GPU')) > 0 else '不支持')")"
else
    echo "TensorFlow: 未安装"
fi
echo

echo "========================================"
echo "验证完成时间: $(date)"
echo "========================================"
EOF

# 设置执行权限
sudo chmod +x /usr/local/bin/validate-ai-workstation.sh

# 运行完整验证
/usr/local/bin/validate-ai-workstation.sh
```

### 7.2 系统验证与性能基准

```bash
# 快速系统验证
echo "========================================"
echo "    AI工作站系统验证"
echo "========================================"

# 基础硬件检查
echo "硬件配置验证:"
echo "CPU核心数: $(nproc)"
echo "内存总量: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo "GPU数量: $(nvidia-smi -L | wc -l)"
echo "存储设备: $(lsblk | grep disk | wc -l) 块设备"

# RAID状态检查
if [ -e /dev/md0 ]; then
    echo "RAID状态: 正常"
    cat /proc/mdstat | grep md0
else
    echo "RAID状态: 未配置"
fi

# GPU状态检查
echo "GPU状态:"
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu --format=csv

# 简单性能测试
echo "快速性能测试:"
echo "- CPU: $(sysbench cpu --cpu-max-prime=10000 --threads=1 run 2>/dev/null | grep 'events per second' | awk '{print $4, $5}')"
echo "- 内存: $(sysbench memory --memory-total-size=1G run 2>/dev/null | grep 'transferred' | awk '{print $3, $4}')"
if mountpoint -q /data; then
    echo "- 数据盘: $(sudo hdparm -t /data 2>/dev/null | tail -1)"
fiecho "========================================"
echo "系统验证完成 - 准备就绪"
echo "========================================"
```

### 7.3 AI框架验证

> **🔧 详细验证**: 完整的AI框架功能验证流程请参考专门的验证脚本和测试套件

```bash
# 快速AI框架验证
echo "AI框架快速验证:"

# PyTorch验证
python3 -c "
import torch
print(f'PyTorch版本: {torch.__version__}')
print(f'CUDA可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU数量: {torch.cuda.device_count()}')
    print('✅ PyTorch GPU支持正常')
else:
    print('❌ PyTorch GPU支持异常')
"

# TensorFlow验证
python3 -c "
import tensorflow as tf
print(f'TensorFlow版本: {tf.__version__}')
gpus = tf.config.list_physical_devices('GPU')
print(f'GPU设备: {len(gpus)}个')
if len(gpus) > 0:
    print('✅ TensorFlow GPU支持正常')
else:
    print('❌ TensorFlow GPU支持异常')
"
echo "✅ AI框架验证完成"
```

## 8. 下一步：容器平台部署

### 8.1 部署流程概览

> **🚀 AI中台部署路径**:
> 1. ✅ **操作系统安装** (当前文档)
> 2. 🔄 **容器平台搭建** → [容器平台配置指南](../02_container_platform/01_container_platform_setup.md)
> 3. 🔄 **AI服务部署** → [AI服务部署指南](../03_ai_services/README.md)

### 8.2 系统状态确认

运行以下命令确认系统准备就绪：

```bash
# 系统状态检查
echo "========== 系统状态检查 =========="
echo "操作系统: $(lsb_release -d | cut -f2)"
echo "内核版本: $(uname -r)"
echo "Python版本: $(python3 --version)"
echo "GPU驱动: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
echo "CUDA版本: $(nvcc --version | grep release | awk '{print $6}' | cut -c2-)"
echo "Docker状态: $(systemctl is-active docker)"

# RAID状态检查
if [ -e /dev/md0 ]; then
    echo "RAID状态: 已配置"
    echo "数据目录: /data ($(df -h /data | tail -1 | awk '{print $2}'))"
else
    echo "RAID状态: 未配置 (可选)"
fi

echo "========== 准备就绪 ==========="
echo "✅ 基础系统配置完成"
echo "✅ AI开发环境就绪"
echo "✅ GPU加速支持可用"
echo ""
echo "下一步: 请参考容器平台配置文档"
echo "文档路径: docs/deployment/02_container_platform/"
```

### 8.3 故障排除

常见问题快速解决：

```bash
# GPU驱动问题
if ! nvidia-smi >/dev/null 2>&1; then
    echo "❌ GPU驱动异常，请重新安装NVIDIA驱动"
    echo "参考: 第4.1节 GPU驱动安装"
fi

# Docker服务问题
if ! systemctl is-active docker >/dev/null 2>&1; then
    echo "❌ Docker服务未运行"
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# Python环境问题
if ! python3 -c "import torch" >/dev/null 2>&1; then
    echo "❌ PyTorch环境异常，请重新安装"
    echo "参考: 第3.2节 AI开发工具链"
fi
```

---

**📋 文档状态**: 
- **版本**: v2.0 (优化版)
- **更新时间**: $(date '+%Y-%m-%d')
- **状态**: ✅ 基础系统配置完成

**🔗 相关文档**:
- [容器平台配置](../02_container_platform/01_container_platform_setup.md)
- [AI服务部署](../03_ai_services/README.md)
- [数据库部署](../02_server_deployment/05_database_setup.md)

**💡 技术支持**: 如遇到问题，请参考故障排除章节或查阅相关技术文档。
