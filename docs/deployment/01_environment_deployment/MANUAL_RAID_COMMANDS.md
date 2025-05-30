# 🛠️ RAID 0手动配置命令参考

## 📋 适用场景
- 系统已安装Ubuntu 24.04 LTS
- 需要手动配置RAID 0
- 自动脚本出现问题时的备用方案

## ⚡ 快速命令序列

### 1. 基础准备
```bash
# 安装必要工具
sudo apt update
sudo apt install -y mdadm parted gdisk smartmontools nvme-cli hdparm

# 检查磁盘
sudo fdisk -l | grep nvme
sudo lsblk -f
```

### 2. 磁盘清理
```bash
# 清除新磁盘数据 (⚠️ 注意：将清除所有数据)
sudo wipefs -a /dev/nvme1n1 /dev/nvme2n1
sudo sgdisk --zap-all /dev/nvme1n1 /dev/nvme2n1

# 创建GPT分区表和分区
sudo parted /dev/nvme1n1 mklabel gpt
sudo parted /dev/nvme1n1 mkpart primary 0% 100%
sudo parted /dev/nvme1n1 set 1 raid on

sudo parted /dev/nvme2n1 mklabel gpt
sudo parted /dev/nvme2n1 mkpart primary 0% 100%
sudo parted /dev/nvme2n1 set 1 raid on

# 刷新分区表
sudo partprobe
```

### 3. 创建RAID 0
```bash
# 创建RAID 0阵列
sudo mdadm --create --verbose /dev/md0 \
    --level=0 \
    --raid-devices=2 \
    --chunk=64 \
    --metadata=1.2 \
    /dev/nvme1n1p1 /dev/nvme2n1p1

# 等待创建完成
while [ ! -e /dev/md0 ]; do echo "等待中..."; sleep 2; done
```

### 4. 创建文件系统
```bash
# 创建优化的ext4文件系统
sudo mkfs.ext4 -F \
    -E stride=16,stripe-width=32 \
    -b 4096 \
    -O ^has_journal,extent,flex_bg,uninit_bg,64bit \
    -m 1 \
    -L "ai-data-raid0" \
    /dev/md0
```

### 5. 挂载配置
```bash
# 创建挂载点
sudo mkdir -p /data

# 临时挂载
sudo mount -o noatime,data=writeback,barrier=0 /dev/md0 /data

# 获取UUID并配置自动挂载
RAID_UUID=$(sudo blkid -s UUID -o value /dev/md0)
echo "UUID=$RAID_UUID /data ext4 defaults,noatime,data=writeback,barrier=0 0 2" | sudo tee -a /etc/fstab

# 验证自动挂载
sudo umount /data
sudo mount -a
df -h /data
```

### 6. 目录结构
```bash
# 设置权限
sudo chown -R $USER:$USER /data

# 创建AI平台目录
mkdir -p /data/{models,datasets,outputs,cache,logs,workspace,temp}
mkdir -p /data/models/{pytorch,tensorflow,huggingface,custom}
mkdir -p /data/datasets/{training,validation,test,raw}
mkdir -p /data/outputs/{checkpoints,results,exports}
mkdir -p /data/cache/{pip,conda,docker,torch,huggingface,tensorflow}
mkdir -p /data/logs/{training,inference,system}
mkdir -p /data/workspace/{projects,notebooks,experiments}
```

### 7. RAID持久化
```bash
# 保存RAID配置
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf

# 更新initramfs
sudo update-initramfs -u
```

### 8. 性能优化
```bash
# I/O调度器优化
echo 'ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="mq-deadline"' | sudo tee /etc/udev/rules.d/60-nvme-scheduler.rules

# 内核参数优化
sudo tee /etc/sysctl.d/60-nvme-performance.conf << 'EOF'
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.dirty_expire_centisecs = 1000
vm.dirty_writeback_centisecs = 100
dev.raid.speed_limit_min = 50000
dev.raid.speed_limit_max = 200000
EOF

sudo sysctl -p /etc/sysctl.d/60-nvme-performance.conf
```

### 9. 验证配置
```bash
# 检查RAID状态
sudo mdadm --detail /dev/md0
cat /proc/mdstat

# 检查挂载
df -h /data
mount | grep /data

# 性能测试
sudo hdparm -t /dev/md0

# 文件系统测试
echo "测试文件" | sudo tee /data/test.txt
cat /data/test.txt
sudo rm /data/test.txt
```

## 🔍 关键验证点

### RAID状态检查
```bash
# 应该显示类似以下信息:
sudo mdadm --detail /dev/md0
# 
# /dev/md0:
#         Version : 1.2
#   Creation Time : 2024-05-30 14:30:00
#      Raid Level : raid0
#      Array Size : 1953384448 (1862.89 GiB 2000.26 GB)
#        Devices : 2
#        State : clean
# Active Devices : 2
```

### 性能验证
```bash
# 应该达到 6000+ MB/s
sudo hdparm -t /dev/md0
# 
# /dev/md0:
#  Timing buffered disk reads: 18000 MB in  3.00 seconds = 6000.00 MB/sec
```

### 挂载验证
```bash
# 应该显示约1.8T可用空间
df -h /data
# 
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/md0        1.8T   77M  1.7T   1% /data
```

## 🔧 故障排除命令

### 检查磁盘健康
```bash
# 检查NVMe健康状态
sudo smartctl -a /dev/nvme1n1 | grep -E "(Model|Health|Temperature)"
sudo smartctl -a /dev/nvme2n1 | grep -E "(Model|Health|Temperature)"

# 检查NVMe详细信息
sudo nvme list
sudo nvme smart-log /dev/nvme1n1
sudo nvme smart-log /dev/nvme2n1
```

### RAID问题诊断
```bash
# 查看RAID事件日志
sudo dmesg | grep -E "(md0|raid)"

# 检查RAID同步状态
cat /proc/mdstat

# 强制重新扫描RAID
sudo mdadm --assemble --scan

# 检查mdadm配置
cat /etc/mdadm/mdadm.conf
```

### 文件系统问题
```bash
# 检查文件系统错误
sudo fsck.ext4 -n /dev/md0  # 只读检查

# 修复文件系统 (需要先卸载)
sudo umount /data
sudo fsck.ext4 -f /dev/md0
sudo mount /dev/md0 /data
```

### 权限问题
```bash
# 修复目录权限
sudo chown -R $USER:$USER /data
sudo chmod -R 755 /data

# 检查挂载选项
mount | grep /data
```

## 🚨 紧急恢复

### 完全重置RAID配置
```bash
# 1. 停止RAID
sudo umount /data 2>/dev/null || true
sudo mdadm --stop /dev/md0 2>/dev/null || true

# 2. 清除磁盘
sudo wipefs -a /dev/nvme1n1 /dev/nvme2n1
sudo sgdisk --zap-all /dev/nvme1n1 /dev/nvme2n1

# 3. 移除配置
sudo sed -i '/md0/d' /etc/fstab
sudo sed -i '/md0/d' /etc/mdadm/mdadm.conf

# 4. 重新开始配置
# (返回步骤2重新开始)
```

### 单盘应急使用
```bash
# 如果RAID出现问题，可以临时使用单个磁盘
sudo mkfs.ext4 /dev/nvme1n1p1
sudo mount /dev/nvme1n1p1 /data
```

## 📝 配置验证清单

- [ ] 两块NVMe SSD都被识别 (`lsblk`)
- [ ] RAID 0阵列创建成功 (`/proc/mdstat`)
- [ ] 文件系统创建完成 (`sudo blkid /dev/md0`)
- [ ] 自动挂载配置正确 (`mount -a`)
- [ ] 目录结构创建完整 (`ls -la /data/`)
- [ ] 性能达到预期 (`hdparm -t /dev/md0`)
- [ ] 权限设置正确 (`touch /data/test.txt`)
- [ ] RAID配置持久化 (`/etc/mdadm/mdadm.conf`)

---

**✅ 配置完成后建议重启系统验证所有配置生效**
