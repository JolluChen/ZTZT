#!/bin/bash

# ==========================================
# AI中台 RAID 0 自动配置脚本
# 目标: sdb + sdc → RAID 0 数据存储阵列
# 作者: AI中台部署脚本
# 版本: v1.0
# ==========================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查root权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限，请使用 sudo 运行"
        exit 1
    fi
}

# 磁盘安全检查
check_disks() {
    log_info "检查目标磁盘..."
    
    # 检查磁盘是否存在
    if [[ ! -b /dev/sdb ]]; then
        log_error "/dev/sdb 不存在"
        exit 1
    fi
    
    if [[ ! -b /dev/sdc ]]; then
        log_error "/dev/sdc 不存在"
        exit 1
    fi
    
    # 显示当前磁盘信息
    log_info "当前磁盘配置:"
    lsblk /dev/sdb /dev/sdc
    echo
    
    # 检查是否已挂载
    if mount | grep -q "/dev/sdb"; then
        log_error "/dev/sdb 或其分区当前已挂载，请先卸载"
        mount | grep "/dev/sdb"
        exit 1
    fi
    
    if mount | grep -q "/dev/sdc"; then
        log_error "/dev/sdc 或其分区当前已挂载，请先卸载"
        mount | grep "/dev/sdc"
        exit 1
    fi
    
    log_success "磁盘检查通过"
}

# 用户确认
confirm_operation() {
    echo -e "${YELLOW}警告: 此操作将完全清除 /dev/sdb 和 /dev/sdc 上的所有数据!${NC}"
    echo "目标配置:"
    echo "  - /dev/sdb ($(lsblk -d -n -o SIZE /dev/sdb)) → RAID 0 成员 1"
    echo "  - /dev/sdc ($(lsblk -d -n -o SIZE /dev/sdc)) → RAID 0 成员 2"
    echo "  - 创建 RAID 0 阵列 /dev/md0"
    echo "  - 挂载到 /data 目录"
    echo
    
    read -p "确认继续? (输入 'YES' 确认): " confirm
    if [[ "$confirm" != "YES" ]]; then
        log_info "操作已取消"
        exit 0
    fi
}

# 安装必要工具
install_tools() {
    log_info "安装 mdadm 工具..."
    apt update >/dev/null 2>&1
    apt install -y mdadm
    log_success "mdadm 安装完成"
}

# 清理磁盘
clear_disks() {
    log_info "清理目标磁盘..."
    
    # 卸载可能的挂载点
    for dev in sdb sdc; do
        for part in $(lsblk -ln -o NAME /dev/$dev 2>/dev/null | grep -v "^$dev$" || true); do
            if mount | grep -q "/dev/$part"; then
                log_warning "卸载 /dev/$part"
                umount "/dev/$part" 2>/dev/null || true
            fi
        done
    done
    
    # 停止可能存在的RAID阵列
    mdadm --stop /dev/md0 2>/dev/null || true
    mdadm --stop /dev/md127 2>/dev/null || true
    
    # 清除超级块
    mdadm --zero-superblock /dev/sdb 2>/dev/null || true
    mdadm --zero-superblock /dev/sdc 2>/dev/null || true
    
    # 清除分区表
    wipefs -a /dev/sdb >/dev/null 2>&1 || true
    wipefs -a /dev/sdc >/dev/null 2>&1 || true
    
    # 创建新的分区表
    parted -s /dev/sdb mklabel gpt
    parted -s /dev/sdc mklabel gpt
    
    log_success "磁盘清理完成"
}

# 创建RAID分区
create_partitions() {
    log_info "创建RAID分区..."
    
    # sdb分区 - 整个磁盘用于RAID
    parted -s /dev/sdb mkpart primary 0% 100%
    parted -s /dev/sdb set 1 raid on
    
    # sdc分区 - 整个磁盘用于RAID  
    parted -s /dev/sdc mkpart primary 0% 100%
    parted -s /dev/sdc set 1 raid on
    
    # 等待设备节点创建
    sleep 2
    
    log_success "RAID分区创建完成"
}

# 创建RAID 0阵列
create_raid() {
    log_info "创建RAID 0阵列..."
    
    # 创建RAID 0
    mdadm --create /dev/md0 \
        --level=0 \
        --raid-devices=2 \
        --chunk=64 \
        /dev/sdb1 /dev/sdc1
    
    # 等待阵列初始化
    sleep 3
    
    # 检查阵列状态
    mdadm --detail /dev/md0
    
    log_success "RAID 0阵列创建完成"
}

# 创建文件系统
create_filesystem() {
    log_info "创建ext4文件系统..."
    
    # 创建ext4文件系统，优化AI工作负载
    mkfs.ext4 -F \
        -b 4096 \
        -E stride=16,stripe-width=32 \
        -L "ZT-DATA-RAID0" \
        /dev/md0
    
    log_success "文件系统创建完成"
}

# 配置挂载
setup_mount() {
    log_info "配置挂载点..."
    
    # 创建挂载目录
    mkdir -p /data
    
    # 获取UUID
    UUID=$(blkid -s UUID -o value /dev/md0)
    
    # 备份fstab
    cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)
    
    # 添加到fstab
    echo "# AI中台数据存储 RAID 0" >> /etc/fstab
    echo "UUID=$UUID /data ext4 defaults,noatime,data=writeback 0 2" >> /etc/fstab
    
    # 挂载
    mount /data
    
    # 设置权限
    chown -R $SUDO_USER:$SUDO_USER /data 2>/dev/null || true
    chmod 755 /data
    
    log_success "挂载配置完成"
}

# 保存RAID配置
save_raid_config() {
    log_info "保存RAID配置..."
    
    # 更新mdadm配置
    mdadm --detail --scan >> /etc/mdadm/mdadm.conf
    
    # 更新initramfs
    update-initramfs -u
    
    log_success "RAID配置已保存"
}

# 性能优化
optimize_performance() {
    log_info "应用性能优化..."
    
    # 设置I/O调度器为mq-deadline (适合RAID 0)
    echo 'ACTION=="add|change", KERNEL=="md0", ATTR{queue/scheduler}="mq-deadline"' > /etc/udev/rules.d/60-raid-scheduler.udev
    
    # 当前会话设置
    echo mq-deadline > /sys/block/md0/queue/scheduler 2>/dev/null || true
    
    # 设置预读值
    blockdev --setra 8192 /dev/md0 2>/dev/null || true
    
    log_success "性能优化完成"
}

# 验证配置
verify_setup() {
    log_info "验证RAID配置..."
    
    echo "=== RAID状态 ==="
    cat /proc/mdstat
    echo
    
    echo "=== 磁盘使用情况 ==="
    df -h /data
    echo
    
    echo "=== 挂载信息 ==="
    mount | grep /data
    echo
    
    echo "=== RAID详细信息 ==="
    mdadm --detail /dev/md0
    echo
    
    # 简单性能测试
    log_info "执行简单性能测试..."
    sync && echo 3 > /proc/sys/vm/drop_caches
    
    echo "写入测试:"
    dd if=/dev/zero of=/data/test_write bs=1M count=1024 2>&1 | grep -E 'copied|MB/s|GB/s'
    
    echo "读取测试:"
    dd if=/data/test_write of=/dev/null bs=1M 2>&1 | grep -E 'copied|MB/s|GB/s'
    
    # 清理测试文件
    rm -f /data/test_write
    
    log_success "RAID 0配置验证完成!"
}

# 创建使用指南
create_usage_guide() {
    log_info "创建使用指南..."
    
    cat > /data/README_RAID_USAGE.md << 'EOF'
# AI中台 RAID 0 数据存储使用指南

## 配置信息
- **RAID类型**: RAID 0 (条带化)
- **设备**: /dev/md0 (/dev/sdb1 + /dev/sdc1)
- **容量**: ~1.9TB
- **文件系统**: ext4
- **挂载点**: /data
- **条带大小**: 64KB
- **预期性能**: 4000-6000 MB/s

## 推荐用途
- AI模型文件存储 (/data/models/)
- 数据集缓存 (/data/datasets/)  
- Docker镜像存储 (/data/docker/)
- 编译缓存 (/data/build-cache/)
- 日志存储 (/data/logs/)

## 重要提醒
⚠️ RAID 0 没有冗余，任何一块磁盘故障都会导致数据丢失
✅ 请定期备份重要数据到其他存储
✅ 建议配合备份策略使用

## 常用命令
```bash
# 查看RAID状态
cat /proc/mdstat
mdadm --detail /dev/md0

# 查看磁盘使用
df -h /data

# 性能测试
hdparm -tT /dev/md0
```

## 目录结构建议
```
/data/
├── models/          # AI模型文件
├── datasets/        # 数据集
├── docker/          # Docker存储
├── build-cache/     # 构建缓存
├── logs/           # 应用日志
└── backup/         # 临时备份
```
EOF

    log_success "使用指南创建完成: /data/README_RAID_USAGE.md"
}

# 主函数
main() {
    echo "=========================================="
    echo "🚀 AI中台 RAID 0 自动配置脚本"
    echo "=========================================="
    echo
    
    check_root
    check_disks
    confirm_operation
    
    log_info "开始RAID 0配置..."
    
    install_tools
    clear_disks
    create_partitions
    create_raid
    create_filesystem
    setup_mount
    save_raid_config
    optimize_performance
    verify_setup
    create_usage_guide
    
    echo
    echo "=========================================="
    log_success "🎉 RAID 0配置完成!"
    echo "=========================================="
    echo
    echo "配置摘要:"
    echo "  ✅ RAID 0阵列: /dev/md0"
    echo "  ✅ 挂载点: /data"
    echo "  ✅ 容量: $(df -h /data | tail -1 | awk '{print $2}')"
    echo "  ✅ 可用空间: $(df -h /data | tail -1 | awk '{print $4}')"
    echo
    echo "下一步建议:"
    echo "  1. 查看使用指南: cat /data/README_RAID_USAGE.md"
    echo "  2. 创建应用目录: mkdir -p /data/{models,datasets,docker,logs}"
    echo "  3. 配置Docker存储: 编辑 /etc/docker/daemon.json"
    echo "  4. 设置定期备份策略"
    echo
}

# 执行主函数
main "$@"
