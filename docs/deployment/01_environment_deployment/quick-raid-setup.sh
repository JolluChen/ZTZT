#!/bin/bash
# AI工作站RAID 0快速配置脚本
# 适用于已安装Ubuntu系统，添加两块新NVMe SSD的场景
# 硬件配置: 128GB RAM + 5×RTX 2080Ti + 3×1TB NVMe SSD

set -e  # 遇到错误立即退出

echo "========================================"
echo "    AI工作站RAID 0快速配置脚本"
echo "========================================"
echo "配置时间: $(date)"
echo "目标: 配置两块新NVMe SSD为RAID 0数据存储"
echo

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志记录
LOG_FILE="/var/log/raid-setup-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo -e "${YELLOW}📋 日志文件: $LOG_FILE${NC}"
echo

# 1. 系统检查
echo -e "${YELLOW}1. 系统环境检查${NC}"
echo "----------------------------------------"

# 检查权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 请使用sudo运行此脚本${NC}"
    exit 1
fi

# 检查系统版本
if ! grep -q "Ubuntu 24.04" /etc/os-release 2>/dev/null; then
    echo -e "${YELLOW}⚠️ 警告: 未检测到Ubuntu 24.04，可能存在兼容性问题${NC}"
fi

# 检查现有磁盘
echo "当前磁盘配置:"
lsblk -f
echo

# 检查目标磁盘是否存在
if [ ! -e "/dev/nvme1n1" ] || [ ! -e "/dev/nvme2n1" ]; then
    echo -e "${RED}❌ 错误: 未检测到nvme1n1或nvme2n1设备${NC}"
    echo "请确认两块新NVMe SSD已正确安装"
    exit 1
fi

echo -e "${GREEN}✅ 检测到目标磁盘: /dev/nvme1n1 和 /dev/nvme2n1${NC}"

# 2. 安装必要工具
echo -e "${YELLOW}2. 安装必要工具${NC}"
echo "----------------------------------------"

apt update > /dev/null 2>&1
apt install -y mdadm parted gdisk smartmontools nvme-cli hdparm fio > /dev/null 2>&1

echo -e "${GREEN}✅ 工具安装完成${NC}"

# 3. 磁盘健康检查
echo -e "${YELLOW}3. 磁盘健康检查${NC}"
echo "----------------------------------------"

for nvme in /dev/nvme1n1 /dev/nvme2n1; do
    echo "检查磁盘: $nvme"
    
    # SMART健康检查
    HEALTH=$(smartctl -H "$nvme" 2>/dev/null | grep -E "SMART overall-health|PASSED|FAILED" || echo "检查失败")
    echo "  健康状态: $HEALTH"
    
    # 温度检查
    TEMP=$(nvme smart-log "$nvme" 2>/dev/null | grep -E "temperature" | head -1 | awk '{print $3}' || echo "N/A")
    echo "  当前温度: ${TEMP}°C"
    
    # 容量检查
    SIZE=$(lsblk -b -d -o SIZE "$nvme" | tail -1)
    SIZE_GB=$((SIZE / 1024 / 1024 / 1024))
    echo "  磁盘容量: ${SIZE_GB}GB"
    
    if [ "$SIZE_GB" -lt 900 ]; then
        echo -e "${YELLOW}⚠️ 警告: 磁盘容量小于预期 (应为~1TB)${NC}"
    fi
done

# 4. 用户确认
echo -e "${YELLOW}4. 配置确认${NC}"
echo "----------------------------------------"
echo -e "${RED}⚠️ 重要警告: 此操作将清除以下磁盘的所有数据:${NC}"
echo "  - /dev/nvme1n1"
echo "  - /dev/nvme2n1"
echo
echo "配置结果:"
echo "  - RAID级别: RAID 0 (无冗余，高性能)"
echo "  - 总容量: ~2TB"
echo "  - 挂载点: /data"
echo "  - 预期性能: 6000-7000 MB/s"
echo

read -p "确认继续配置? (输入 'YES' 继续): " confirm
if [ "$confirm" != "YES" ]; then
    echo -e "${YELLOW}❌ 操作已取消${NC}"
    exit 0
fi

# 5. 磁盘准备
echo -e "${YELLOW}5. 磁盘预处理${NC}"
echo "----------------------------------------"

for nvme in /dev/nvme1n1 /dev/nvme2n1; do
    echo "处理磁盘: $nvme"
    
    # 卸载可能的挂载
    umount "$nvme"* 2>/dev/null || true
    
    # 清除文件系统签名
    wipefs -a "$nvme" 2>/dev/null || true
    
    # 清除分区表
    sgdisk --zap-all "$nvme" >/dev/null 2>&1
    
    # 创建新的GPT分区表
    parted "$nvme" mklabel gpt >/dev/null 2>&1
    
    # 创建分区
    parted "$nvme" mkpart primary 0% 100% >/dev/null 2>&1
    
    # 设置RAID标志
    parted "$nvme" set 1 raid on >/dev/null 2>&1
    
    echo "  ✅ $nvme 预处理完成"
done

# 刷新分区表
partprobe >/dev/null 2>&1
sleep 2

echo -e "${GREEN}✅ 磁盘预处理完成${NC}"

# 6. 创建RAID 0阵列
echo -e "${YELLOW}6. 创建RAID 0阵列${NC}"
echo "----------------------------------------"

# 创建RAID 0
mdadm --create --verbose /dev/md0 \
    --level=0 \
    --raid-devices=2 \
    --chunk=64 \
    --metadata=1.2 \
    /dev/nvme1n1p1 /dev/nvme2n1p1

# 等待阵列就绪
echo "等待RAID阵列初始化..."
while [ ! -e /dev/md0 ]; do
    echo -n "."
    sleep 1
done
echo

echo -e "${GREEN}✅ RAID 0阵列创建成功${NC}"

# 7. 创建文件系统
echo -e "${YELLOW}7. 创建优化文件系统${NC}"
echo "----------------------------------------"

# 计算优化参数
CHUNK_SIZE=64  # KB
RAID_DEVICES=2
STRIDE=$((CHUNK_SIZE * 1024 / 4096))  # stride = chunk_size / block_size
STRIPE_WIDTH=$((STRIDE * RAID_DEVICES))

echo "文件系统参数:"
echo "  Chunk Size: ${CHUNK_SIZE}KB"
echo "  Stride: ${STRIDE}"
echo "  Stripe Width: ${STRIPE_WIDTH}"

# 创建ext4文件系统
mkfs.ext4 -F \
    -E stride=${STRIDE},stripe-width=${STRIPE_WIDTH} \
    -b 4096 \
    -O ^has_journal,extent,flex_bg,uninit_bg,64bit \
    -m 1 \
    -L "ai-data-raid0" \
    /dev/md0 >/dev/null 2>&1

echo -e "${GREEN}✅ 文件系统创建完成${NC}"

# 8. 配置挂载
echo -e "${YELLOW}8. 配置自动挂载${NC}"
echo "----------------------------------------"

# 创建挂载点
mkdir -p /data

# 挂载RAID设备
mount -o noatime,data=writeback,barrier=0,nobh /dev/md0 /data

# 获取UUID
RAID_UUID=$(blkid -s UUID -o value /dev/md0)
echo "RAID UUID: $RAID_UUID"

# 备份fstab
cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d)

# 添加到fstab
echo "# AI数据存储 RAID 0阵列 - 配置于 $(date)" >> /etc/fstab
echo "UUID=$RAID_UUID /data ext4 defaults,noatime,data=writeback,barrier=0 0 2" >> /etc/fstab

# 验证挂载配置
mount -a
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 自动挂载配置成功${NC}"
else
    echo -e "${RED}❌ 自动挂载配置失败${NC}"
    exit 1
fi

# 9. 创建目录结构
echo -e "${YELLOW}9. 创建AI平台目录结构${NC}"
echo "----------------------------------------"

# 设置权限
USER_NAME=$(logname 2>/dev/null || echo "$SUDO_USER")
chown -R $USER_NAME:$USER_NAME /data 2>/dev/null || chown -R $USER:$USER /data
chmod 755 /data

# 创建目录结构
mkdir -p /data/{models,datasets,outputs,cache,logs,workspace,temp}
mkdir -p /data/models/{pytorch,tensorflow,huggingface,custom}
mkdir -p /data/datasets/{training,validation,test,raw}
mkdir -p /data/outputs/{checkpoints,results,exports}
mkdir -p /data/cache/{pip,conda,docker,model-cache,torch,huggingface,tensorflow}
mkdir -p /data/logs/{training,inference,system}
mkdir -p /data/workspace/{projects,notebooks,experiments}

# 再次设置权限
chown -R $USER_NAME:$USER_NAME /data 2>/dev/null || chown -R $USER:$USER /data

echo -e "${GREEN}✅ 目录结构创建完成${NC}"

# 10. 配置RAID持久化
echo -e "${YELLOW}10. 配置RAID持久化${NC}"
echo "----------------------------------------"

# 保存mdadm配置
mdadm --detail --scan >> /etc/mdadm/mdadm.conf

# 更新initramfs
update-initramfs -u >/dev/null 2>&1

echo -e "${GREEN}✅ RAID持久化配置完成${NC}"

# 11. 性能优化
echo -e "${YELLOW}11. 应用性能优化${NC}"
echo "----------------------------------------"

# I/O调度器优化
for device in /sys/block/nvme*/queue/scheduler; do
    echo mq-deadline > "$device" 2>/dev/null || true
done

# 内核参数优化
cat > /etc/sysctl.d/60-nvme-performance.conf << 'EOF'
# NVMe和RAID性能优化
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.dirty_expire_centisecs = 1000
vm.dirty_writeback_centisecs = 100
dev.raid.speed_limit_min = 50000
dev.raid.speed_limit_max = 200000
EOF

sysctl -p /etc/sysctl.d/60-nvme-performance.conf >/dev/null 2>&1

echo -e "${GREEN}✅ 性能优化应用完成${NC}"

# 12. 创建管理脚本
echo -e "${YELLOW}12. 创建管理工具${NC}"
echo "----------------------------------------"

# 创建状态检查脚本
cat > /usr/local/bin/raid-status << 'EOF'
#!/bin/bash
echo "=== AI工作站RAID 0状态 ==="
echo "时间: $(date)"
echo
echo "RAID阵列状态:"
mdadm --detail /dev/md0 | grep -E "(Raid Level|Array Size|State|Active Devices)"
echo
cat /proc/mdstat | grep -A3 md0
echo
echo "存储使用情况:"
df -h /data
echo
echo "性能测试:"
hdparm -t /dev/md0 | grep Timing
echo
echo "=== 状态检查完成 ==="
EOF

chmod +x /usr/local/bin/raid-status

echo -e "${GREEN}✅ 管理工具创建完成${NC}"

# 13. 配置验证和性能测试
echo -e "${YELLOW}13. 配置验证和性能测试${NC}"
echo "----------------------------------------"

echo "RAID阵列详情:"
mdadm --detail /dev/md0 | grep -E "(Raid Level|Array Size|State)"

echo "挂载验证:"
df -h /data

echo "快速性能测试:"
hdparm -t /dev/md0

echo "文件系统测试:"
time (echo "RAID 0配置测试" > /data/test-file.txt && sync)
rm -f /data/test-file.txt

# 14. 设置环境变量
echo -e "${YELLOW}14. 配置AI环境变量${NC}"
echo "----------------------------------------"

# 为当前用户配置环境变量
USER_HOME=$(eval echo ~$USER_NAME)
cat >> "$USER_HOME/.bashrc" << 'EOF'

# AI平台数据存储路径
export AI_DATA_ROOT="/data"
export AI_MODELS_PATH="/data/models"
export AI_DATASETS_PATH="/data/datasets"
export AI_OUTPUTS_PATH="/data/outputs"
export AI_CACHE_PATH="/data/cache"
export AI_WORKSPACE_PATH="/data/workspace"

# PyTorch配置
export TORCH_HOME="/data/cache/torch"
export TRANSFORMERS_CACHE="/data/cache/huggingface"

# TensorFlow配置
export TF_KERAS_CACHE_DIR="/data/cache/tensorflow"

# Conda/Pip缓存配置
export CONDA_PKGS_DIRS="/data/cache/conda/pkgs"
export PIP_CACHE_DIR="/data/cache/pip"

echo "AI平台数据存储已就绪: $AI_DATA_ROOT"
EOF

echo -e "${GREEN}✅ 环境变量配置完成${NC}"

# 15. 完成总结
echo
echo "========================================"
echo -e "${GREEN}🎉 RAID 0配置完成! ${NC}"
echo "========================================"
echo "配置摘要:"
echo "  ✅ RAID 0阵列: /dev/md0"
echo "  ✅ 存储容量: $(df -h /data | tail -1 | awk '{print $2}')"
echo "  ✅ 挂载点: /data"
echo "  ✅ 文件系统: ext4 (优化配置)"
echo "  ✅ 自动挂载: 已配置"
echo "  ✅ 目录结构: AI平台就绪"
echo "  ✅ 性能优化: 已应用"
echo
echo "性能指标:"
RAID_SPEED=$(hdparm -t /dev/md0 2>/dev/null | grep Timing | awk '{print $11" "$12}' || echo "测试中...")
echo "  📊 读取速度: $RAID_SPEED"
echo "  📊 预期性能: 6000-7000 MB/s"
echo
echo "管理命令:"
echo "  🔍 检查状态: raid-status"
echo "  📊 详细信息: sudo mdadm --detail /dev/md0"
echo "  📈 性能测试: sudo hdparm -t /dev/md0"
echo
echo "目录结构:"
echo "  📁 AI模型: /data/models/"
echo "  📁 数据集: /data/datasets/"
echo "  📁 输出: /data/outputs/"
echo "  📁 缓存: /data/cache/"
echo "  📁 工作区: /data/workspace/"
echo
echo "下一步:"
echo "  1. 重启系统验证自动挂载"
echo "  2. 安装AI框架 (PyTorch, TensorFlow)"
echo "  3. 配置GPU驱动和CUDA"
echo "  4. 部署容器化平台"
echo
echo -e "${YELLOW}📋 详细日志: $LOG_FILE${NC}"
echo "========================================"
