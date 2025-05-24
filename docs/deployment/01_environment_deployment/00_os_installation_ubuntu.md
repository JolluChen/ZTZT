# AI 中台 - 操作系统安装 (Ubuntu 22.04 LTS)

本文档指导如何在目标服务器上安装 Ubuntu 22.04 LTS 作为 AI 中台的基础操作系统。

## 0. 先决条件

- **服务器**: 准备一台或多台满足最低配置要求的服务器。
- **操作系统**: 在所有服务器上安装 **Ubuntu 22.04 LTS** 。
- **网络**: 确保服务器之间网络互通，并规划好 IP 地址。
- **用户权限**: 拥有 `sudo` 或 `root` 权限。


## 1. 操作系统安装 (Ubuntu 22.04 LTS)

在所有目标服务器上安装 Ubuntu 22.04 LTS。请遵循以下步骤：

1.  **下载 Ubuntu Server 22.04 LTS ISO**: 
    从 Ubuntu 官方网站下载 ISO 镜像文件: [https://ubuntu.com/download/server](https://ubuntu.com/download/server)

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
            *   **注意**: 创建 RAID 后，操作系统安装程序会将此 RAID 卷视为一个单独的磁盘进行后续分区。
        *   **分区方案选择**: 
            *   在 Ubuntu 安装程序的存储配置步骤，选择 '''Custom storage layout''' (自定义存储布局)。
            *   如果已配置 RAID，您会看到一个代表 RAID 阵列的设备 (例如 `/dev/sda` 或 `/dev/mdX`，如果使用的是 Linux 软件 RAID)。
        *   **LVM (Logical Volume Management) 配置步骤**: 
            1.  **创建物理卷 (PV)**: 
                *   选择要用于 LVM 的磁盘或分区 (例如，整个 RAID 卷 `/dev/sda`，或者如果 `/boot` 单独分区，则选择剩余空间创建的分区)。
                *   在安装程序的界面中，通常有选项将其格式化为 LVM 物理卷 (Use as LVM physical volume)。
            2.  **创建卷组 (VG)**: 
                *   将一个或多个物理卷添加到一个卷组中。例如，创建一个名为 `vg_system` 的卷组。
                *   卷组是逻辑卷的容器，可以跨越多个物理卷。
            3.  **创建逻辑卷 (LV)**: 
                *   在卷组内创建逻辑卷。这些逻辑卷将作为操作系统的分区。
                *   **`/boot` 分区**: (如果选择不放在 LVM 中) 通常建议为 `/boot` 创建一个单独的、非 LVM 的标准分区，大小约 512MB 到 1GB，文件系统为 ext4。某些系统可能要求 `/boot` 不在 LVM 上。如果安装程序支持在 LVM 内创建 `/boot` 且您的引导加载程序支持，也可以考虑。但为简单和兼容性，独立 `/boot` 分区更常见。
                *   **根分区 (`/`)**: 在 `vg_system` 卷组中创建一个逻辑卷，例如命名为 `lv_root`。分配足够的空间 (例如，至少 50GB，根据应用需求调整)，文件系统为 ext4。挂载点设置为 `/`。
                *   **Swap 分区**: 在 `vg_system` 卷组中创建一个逻辑卷，例如命名为 `lv_swap`。大小通常建议为物理内存的 0.5 到 2 倍，但对于 Kubernetes 节点，**Swap 通常需要被禁用**。如果确定不需要 Swap，可以跳过此步骤。如果创建，文件系统类型选择 `swap`。
                *   **(可选) 其他逻辑卷**: 根据需要可以创建其他逻辑卷，例如 `/home`, `/var`, `/opt`, `/srv` 等，以便更精细地管理存储空间和快照。例如：
                    *   `lv_home` 挂载到 `/home` (用户数据)
                    *   `lv_var` 挂载到 `/var` (日志、缓存等变化频繁的数据)
            4.  **格式化和挂载**: 
                *   为每个创建的逻辑卷（除了 swap）选择文件系统类型 (通常是 ext4) 并指定挂载点。
        *   **分区大小建议 (示例)** (假设总空间较大，且使用 LVM):
            *   `/boot`: 1GB (标准分区, ext4) - *如果选择不放在LVM中*
            *   LVM 卷组 `vg_system` (使用剩余全部空间):
                *   逻辑卷 `lv_root` (挂载到 `/`): 至少 50GB - 100GB (ext4)
                *   逻辑卷 `lv_swap` (用于 swap): (如果需要，但 K8s 节点禁用) 物理内存大小 (swap)
                *   逻辑卷 `lv_var` (挂载到 `/var`): 50GB - 200GB (ext4) - 根据日志和应用数据量调整
                *   逻辑卷 `lv_home` (挂载到 `/home`): (可选) 剩余空间或按需分配 (ext4)
                *   逻辑卷 `lv_data` (挂载到 `/data` 或其他应用数据目录): (可选) 剩余空间或按需分配 (ext4)
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

完成以上步骤后，您的服务器就已经准备好了 Ubuntu 22.04 LTS 操作系统，可以继续进行后续的系统层组件部署。
