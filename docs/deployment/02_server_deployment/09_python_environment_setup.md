# ⭐ AI中台 - Python开发环境完整部署指南 (Ubuntu 24.04 LTS)

## 📋 文档概述

本文档提供在**Ubuntu 24.04 LTS**系统上为AI中台项目配置完整Python开发环境的详细指南，包括Python 3.10安装、虚拟环境配置、依赖管理以及AI框架的安装。

> **⚠️ 重要提示**: 本文档已针对Ubuntu 24.04 LTS进行优化，确保所有命令和配置与最新系统版本兼容。

## ⏱️ 预计部署时间
- **Python环境安装**: 30-45分钟
- **虚拟环境配置**: 15-20分钟  
- **AI框架安装**: 45-60分钟
- **总计**: 1.5-2小时

## 🎯 部署目标
✅ Python 3.10 运行环境  
✅ 虚拟环境管理系统  
✅ AI中台项目依赖包  
✅ Django开发环境  
✅ 机器学习框架支持

## 1. 系统准备

### 1.1 确认系统版本
```bash
# 检查系统版本
lsb_release -a

# 确认架构
uname -m

# 检查可用空间
df -h
```

### 1.2 安装系统依赖
```bash
# 更新软件包列表
sudo apt update && sudo apt upgrade -y

# 安装编译工具链
sudo apt install -y build-essential cmake

# 安装Python编译依赖
sudo apt install -y \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenblas-dev \
    liblapack-dev \
    gfortran

# 安装数据库开发库
sudo apt install -y \
    libpq-dev \
    libsqlite3-dev \
    default-libmysqlclient-dev

# 安装系统工具
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    unzip \
    software-properties-common
```

## 2. 🐍 Python 3.10 安装 (Ubuntu 24.04 LTS 优化)

> **💡 提示**: Ubuntu 24.04 LTS 默认Python版本为3.12，我们需要安装Python 3.10来确保最佳兼容性。

### 2.1 检查系统Python环境
```bash
# 检查当前Python版本
python3 --version
which python3

# 检查可用的Python版本
ls /usr/bin/python*

# 检查是否已安装Python 3.10
python3.10 --version 2>/dev/null || echo "Python 3.10 未安装"
```

### 2.2 添加Python仓库源 (Ubuntu 24.04 LTS)
```bash
# 更新包列表
sudo apt update

# 安装必要的依赖包
sudo apt install -y software-properties-common

# 添加deadsnakes PPA仓库 (提供多版本Python)
sudo add-apt-repository ppa:deadsnakes/ppa -y

# 更新包列表
sudo apt update

# 验证仓库添加成功
apt-cache policy python3.10
```

### 2.3 安装Python 3.10完整环境
```bash
# 安装Python 3.10及相关组件
sudo apt install -y \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    python3.10-distutils \
    python3.10-lib2to3 \
    python3.10-gdbm \
    python3.10-tk \
    python3.10-full

# 验证安装
python3.10 --version
python3.10 -c "import sys; print(sys.version)"

# 检查Python 3.10模块
python3.10 -c "import sqlite3, ssl, hashlib; print('Core modules OK')"
```

### 2.4 配置Python环境 (不影响系统默认)
```bash
# 创建用户级别的Python链接 (推荐方式)
mkdir -p ~/.local/bin

# 创建Python 3.10的用户链接
ln -sf /usr/bin/python3.10 ~/.local/bin/python
ln -sf /usr/bin/python3.10 ~/.local/bin/python3.10

# 添加到PATH (如果尚未添加)
if ! grep -q "~/.local/bin" ~/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
fi

# 验证配置
which python
python --version

# 确认系统Python未受影响
/usr/bin/python3 --version
```

### 2.5 系统集成验证
```bash
# 创建验证脚本
cat > /tmp/python_verification.py << 'EOF'
#!/usr/bin/env python3.10
import sys
import platform
import sysconfig

print("Python环境验证报告")
print("=" * 40)
print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")
print(f"平台信息: {platform.platform()}")
print(f"架构: {platform.architecture()}")
print(f"安装前缀: {sys.prefix}")
print(f"站点包目录: {sysconfig.get_path('purelib')}")

# 测试基本模块
modules_to_test = ['os', 'sys', 'json', 'sqlite3', 'ssl', 'urllib']
print(f"\n基本模块测试:")
for module in modules_to_test:
    try:
        __import__(module)
        print(f"  ✓ {module}")
    except ImportError as e:
        print(f"  ✗ {module}: {e}")
EOF

# 运行验证
python3.10 /tmp/python_verification.py

# 清理验证文件
rm /tmp/python_verification.py
```

## 3. 📦 pip和包管理工具安装 (Ubuntu 24.04 LTS)

### 3.1 安装pip for Python 3.10
```bash
# 方法1: 使用apt安装（推荐）
sudo apt install -y python3.10-pip

# 验证pip安装
python3.10 -m pip --version

# 如果apt方法失败，使用get-pip.py方法
if ! python3.10 -m pip --version >/dev/null 2>&1; then
    echo "使用get-pip.py安装pip..."
    
    # 下载get-pip.py
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    
    # 使用Python 3.10安装pip
    python3.10 get-pip.py --user
    
    # 清理下载文件
    rm get-pip.py
fi

# 升级pip到最新版本
python3.10 -m pip install --user --upgrade pip

# 验证最终安装
python3.10 -m pip --version
```

### 3.2 配置pip镜像源 (加速下载)
```bash
# 创建pip配置目录
mkdir -p ~/.pip

# 配置清华镜像源
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

# 验证镜像源配置
python3.10 -m pip config list

# 测试下载速度
echo "测试pip下载速度..."
time python3.10 -m pip install --user --no-deps setuptools
```

### 3.3 安装核心包管理工具
```bash
# 安装虚拟环境和开发工具
python3.10 -m pip install --user \
    virtualenv==20.24.6 \
    pipenv==2023.10.24 \
    wheel==0.41.3 \
    setuptools==68.2.2

# 安装开发和测试工具
python3.10 -m pip install --user \
    black==23.11.0 \
    flake8==6.1.0 \
    isort==5.12.0 \
    pytest==7.4.3 \
    pytest-cov==4.1.0

# 安装构建工具
python3.10 -m pip install --user \
    build==1.0.3 \
    twine==4.0.2

# 验证所有工具安装
echo "验证包管理工具安装:"
python3.10 -m pip list | grep -E "(virtualenv|pipenv|wheel|setuptools|black|flake8|pytest)"
```

### 3.4 配置包管理环境变量
```bash
# 添加用户级Python包路径到环境变量
cat >> ~/.bashrc << 'EOF'

# Python 3.10 User Packages
PYTHON310_USER_BASE=$(python3.10 -m site --user-base)
export PATH="$PYTHON310_USER_BASE/bin:$PATH"
export PYTHONPATH="$PYTHON310_USER_BASE/lib/python3.10/site-packages:$PYTHONPATH"

# pip配置
export PIP_USER=1
export PIP_REQUIRE_VIRTUALENV=false
EOF

# 重新加载环境变量
source ~/.bashrc

# 验证路径配置
echo "用户Python包目录:"
python3.10 -m site --user-base
python3.10 -m site --user-site

# 验证工具可用性
echo "验证命令行工具:"
which virtualenv 2>/dev/null && echo "✓ virtualenv" || echo "✗ virtualenv"
which black 2>/dev/null && echo "✓ black" || echo "✗ black"
which flake8 2>/dev/null && echo "✓ flake8" || echo "✗ flake8"
```

## 4. 🔧 虚拟环境配置 (AI平台专用环境)

### 4.1 创建AI平台项目结构
```bash
# 创建AI平台根目录
sudo mkdir -p /opt/ai-platform
sudo chown $USER:$USER /opt/ai-platform

# 创建项目子目录结构
mkdir -p /opt/ai-platform/{logs,data,config,backup,scripts}

# 进入项目目录
cd /opt/ai-platform

# 验证目录结构
tree /opt/ai-platform 2>/dev/null || ls -la /opt/ai-platform
```

### 4.2 创建Python 3.10虚拟环境
```bash
# 创建虚拟环境 (使用Python 3.10)
python3.10 -m venv ai-platform-env

# 验证虚拟环境创建成功
ls -la ai-platform-env/

# 检查虚拟环境Python版本
ai-platform-env/bin/python --version

# 激活虚拟环境
source ai-platform-env/bin/activate

# 确认虚拟环境激活成功
echo "虚拟环境信息:"
echo "Python路径: $(which python)"
echo "Python版本: $(python --version)"
echo "Pip路径: $(which pip)"
echo "虚拟环境: $VIRTUAL_ENV"
```

### 4.3 升级虚拟环境基础包
```bash
# 确保在虚拟环境中
source /opt/ai-platform/ai-platform-env/bin/activate

# 升级pip到最新版本
pip install --upgrade pip

# 安装基础构建工具
pip install --upgrade \
    setuptools==69.0.2 \
    wheel==0.42.0 \
    build==1.0.3

# 验证升级结果
echo "基础包版本信息:"
pip --version
python -c "import setuptools; print(f'setuptools: {setuptools.__version__}')"
python -c "import wheel; print(f'wheel: {wheel.__version__}')"
```

### 4.4 配置虚拟环境快速访问
```bash
# 创建环境激活脚本
cat > /opt/ai-platform/activate.sh << 'EOF'
#!/bin/bash
# AI Platform Environment Activation Script

echo "🚀 激活AI平台开发环境..."

# 进入项目目录
cd /opt/ai-platform

# 激活虚拟环境
source ai-platform-env/bin/activate

# 显示环境信息
echo "✅ 环境已激活!"
echo "📍 当前目录: $(pwd)"
echo "🐍 Python版本: $(python --version)"
echo "📦 Pip版本: $(pip --version)"
echo "🌐 虚拟环境: $VIRTUAL_ENV"

# 显示可用的管理命令
echo ""
echo "📋 可用命令:"
echo "  python manage.py runserver    - 启动开发服务器"
echo "  python manage.py migrate      - 运行数据库迁移"
echo "  python manage.py test         - 运行测试"
echo "  python manage.py shell        - 进入Django shell"
echo "  deactivate                    - 退出虚拟环境"
EOF

chmod +x /opt/ai-platform/activate.sh

# 创建全局快速命令
sudo ln -sf /opt/ai-platform/activate.sh /usr/local/bin/ai-platform

# 创建bash别名
echo "alias ai-platform='source /opt/ai-platform/ai-platform-env/bin/activate && cd /opt/ai-platform'" >> ~/.bashrc
```

### 4.5 环境变量配置
```bash
# 创建环境变量配置文件
cat > /opt/ai-platform/.env << 'EOF'
# AI Platform Environment Variables

# Django设置
DJANGO_SETTINGS_MODULE=config.settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# 数据库设置
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0

# AI平台设置
AI_PLATFORM_HOME=/opt/ai-platform
AI_PLATFORM_DATA_DIR=/opt/ai-platform/data
AI_PLATFORM_LOG_DIR=/opt/ai-platform/logs

# Python设置
PYTHONPATH=/opt/ai-platform
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1

# 开发工具设置
PIP_REQUIRE_VIRTUALENV=true
PIP_RESPECT_VIRTUALENV=true
EOF

# 加载环境变量到激活脚本
cat >> /opt/ai-platform/activate.sh << 'EOF'

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "🔧 环境变量已加载"
fi
EOF

# 创建环境变量加载器
cat > /opt/ai-platform/load_env.py << 'EOF'
#!/usr/bin/env python3
"""
加载.env文件中的环境变量
"""
import os
from pathlib import Path

def load_env(env_file='.env'):
    """加载环境变量文件"""
    env_path = Path(__file__).parent / env_file
    
    if not env_path.exists():
        print(f"⚠️  环境文件 {env_file} 不存在")
        return
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value
                print(f"✅ 设置环境变量: {key}")

if __name__ == '__main__':
    load_env()
EOF

chmod +x /opt/ai-platform/load_env.py
```
python --version
pip --version
```

### 4.2 配置环境变量
```bash
# 创建环境配置文件
cat >> ~/.bashrc << 'EOF'

# AI Platform Environment
export AI_PLATFORM_HOME="/opt/ai-platform"
export AI_PLATFORM_VENV="$AI_PLATFORM_HOME/ai-platform-env"
alias ai-platform-env="source $AI_PLATFORM_VENV/bin/activate"

# Python环境变量
export PYTHONPATH="$AI_PLATFORM_HOME:$PYTHONPATH"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
EOF

# 重新加载配置
source ~/.bashrc

# 创建快速激活脚本
sudo tee /usr/local/bin/ai-platform << 'EOF'
#!/bin/bash
cd /opt/ai-platform
source ai-platform-env/bin/activate
echo "AI Platform environment activated!"
echo "Python: $(python --version)"
echo "Pip: $(pip --version)"
echo "Working directory: $(pwd)"
EOF

sudo chmod +x /usr/local/bin/ai-platform
```

## 5. 📦 AI平台依赖安装 (基于实际项目)

### 5.1 创建生产环境requirements文件
```bash
# 激活虚拟环境
source /opt/ai-platform/ai-platform-env/bin/activate

# 创建生产环境依赖文件
cat > /opt/ai-platform/requirements.txt << 'EOF'
# Django框架和核心依赖
Django==4.2.16
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.0

# 数据库驱动
psycopg2-binary==2.9.9

# API功能增强
django-filter==23.5
django-cors-headers==4.4.0

# 数据处理
pandas==2.1.4
numpy==1.24.4

# API文档
drf-yasg==1.21.7

# 时区支持
pytz==2024.1

# 环境变量管理
python-decouple==3.8

# 文件上传和处理
Pillow==10.1.0

# 缓存系统
redis==5.0.1
django-redis==5.4.0

# 任务队列
celery==5.3.4

# 测试框架
pytest==7.4.3
pytest-django==4.7.0

# HTTP客户端
requests==2.31.0
EOF

# 创建开发环境依赖文件
cat > /opt/ai-platform/requirements-dev.txt << 'EOF'
# 包含生产环境依赖
-r requirements.txt

# 开发工具
django-debug-toolbar==4.2.0
dj-database-url==2.1.0

# 代码质量工具
black==23.11.0
flake8==6.1.0
isort==5.12.0

# 调试工具
ipython==8.18.1
jupyter==1.0.0
jupyter-lab==4.0.8

# 性能分析
django-extensions==3.2.3
memory-profiler==0.61.0
EOF
```

### 5.2 安装基础依赖包
```bash
# 确保在虚拟环境中
source /opt/ai-platform/ai-platform-env/bin/activate

# 升级pip和基础工具
pip install --upgrade pip setuptools wheel

# 安装生产环境依赖
echo "🔄 安装AI平台生产环境依赖..."
pip install -r /opt/ai-platform/requirements.txt

# 验证关键包安装状态
echo "📋 验证关键包安装状态:"
python -c "import django; print(f'✅ Django: {django.get_version()}')"
python -c "import rest_framework; print(f'✅ DRF: {rest_framework.VERSION}')"  
python -c "import pandas; print(f'✅ Pandas: {pandas.__version__}')"
python -c "import numpy; print(f'✅ NumPy: {numpy.__version__}')"
python -c "import psycopg2; print(f'✅ PostgreSQL: {psycopg2.__version__}')"
python -c "import redis; print(f'✅ Redis: {redis.__version__}')"

# 检查依赖冲突
pip check
```

### 5.3 安装开发环境依赖 (可选)
```bash
# 安装开发工具（如果是开发环境）
echo "🛠️ 安装开发环境依赖..."
pip install -r /opt/ai-platform/requirements-dev.txt

# 验证开发工具
python -c "import IPython; print(f'✅ IPython: {IPython.__version__}')"
which black && echo "✅ Black 代码格式化工具已安装"
which flake8 && echo "✅ Flake8 代码检查工具已安装"
```

### 5.4 AI/ML框架安装 (按需选择)

#### 5.4.1 PyTorch生态系统
```bash
# CPU版本 (轻量级，适合开发环境)
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# 验证PyTorch安装
python -c "import torch; print(f'✅ PyTorch: {torch.__version__}, CUDA可用: {torch.cuda.is_available()}')"

# 安装相关工具
pip install \
    transformers==4.35.0 \
    datasets==2.14.0 \
    tokenizers==0.15.0 \
    accelerate==0.24.0

echo "✅ PyTorch生态系统安装完成"
```

#### 5.4.2 TensorFlow生态系统 (可选)
```bash
# 安装TensorFlow
pip install tensorflow==2.14.0

# 验证TensorFlow
python -c "import tensorflow as tf; print(f'✅ TensorFlow: {tf.__version__}, GPU可用: {tf.config.list_physical_devices(\"GPU\")}')"

# 安装Keras和相关工具
pip install \
    keras==2.14.0 \
    tensorboard==2.14.1

echo "✅ TensorFlow生态系统安装完成"
```

#### 5.4.3 科学计算和可视化
```bash
# 数据科学核心包
pip install \
    scikit-learn==1.3.2 \
    scipy==1.11.4 \
    matplotlib==3.8.2 \
    seaborn==0.13.0 \
    plotly==5.17.0

# NLP工具
pip install \
    spacy==3.7.2 \
    nltk==3.8.1 \
    jieba==0.42.1

# 验证安装
python -c "import sklearn; print(f'✅ Scikit-learn: {sklearn.__version__}')"
python -c "import matplotlib; print(f'✅ Matplotlib: {matplotlib.__version__}')"
python -c "import spacy; print(f'✅ spaCy: {spacy.__version__}')"

echo "✅ 科学计算包安装完成"
```

### 5.5 数据库连接测试
```bash
# 创建数据库连接测试脚本
cat > /opt/ai-platform/test_database.py << 'EOF'
#!/usr/bin/env python3
"""
数据库连接测试脚本
"""
import os
import sys

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 添加项目路径
sys.path.append('/opt/ai-platform')

try:
    import django
    django.setup()
    
    from django.db import connection
    from django.core.management import execute_from_command_line
    
    print("🔍 数据库连接测试")
    print("=" * 40)
    
    # 测试数据库连接
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ 数据库连接成功: {result}")
    
    # 显示数据库信息
    print(f"📊 数据库引擎: {connection.vendor}")
    print(f"📊 数据库名称: {connection.settings_dict['NAME']}")
    
    print("\n✅ 数据库连接测试通过!")
    
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    sys.exit(1)
EOF

chmod +x /opt/ai-platform/test_database.py

# 运行数据库测试
python /opt/ai-platform/test_database.py
```

### 5.6 创建环境信息导出
```bash
# 导出当前环境依赖列表
pip freeze > /opt/ai-platform/requirements-frozen.txt

# 创建环境信息脚本
cat > /opt/ai-platform/environment_info.py << 'EOF'
#!/usr/bin/env python3
"""
AI平台环境信息收集脚本
"""
import sys
import platform
import subprocess
import pkg_resources

def get_system_info():
    """获取系统信息"""
    info = {
        "Python版本": sys.version,
        "Python路径": sys.executable,
        "操作系统": platform.platform(),
        "架构": platform.architecture(),
        "处理器": platform.processor(),
        "内存": f"{platform.node()}",
    }
    return info

def get_package_versions():
    """获取关键包版本"""
    key_packages = [
        'django', 'djangorestframework', 'pandas', 'numpy', 
        'psycopg2', 'redis', 'celery', 'pytest'
    ]
    
    versions = {}
    for package in key_packages:
        try:
            version = pkg_resources.get_distribution(package).version
            versions[package] = version
        except pkg_resources.DistributionNotFound:
            versions[package] = "未安装"
    
    return versions

def main():
    print("🔍 AI平台环境信息报告")
    print("=" * 50)
    
    # 系统信息
    print("\n🖥️ 系统信息:")
    for key, value in get_system_info().items():
        print(f"  {key}: {value}")
    
    # 包版本信息
    print("\n📦 关键包版本:")
    for package, version in get_package_versions().items():
        status = "✅" if version != "未安装" else "❌"
        print(f"  {status} {package}: {version}")
    
    # 虚拟环境信息
    print(f"\n🌐 虚拟环境: {sys.prefix}")
    print(f"📁 工作目录: {subprocess.getoutput('pwd')}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
EOF

chmod +x /opt/ai-platform/environment_info.py

# 运行环境信息收集
python /opt/ai-platform/environment_info.py
```

### 5.2 安装基础依赖
```bash
# 确保在虚拟环境中
source /opt/ai-platform/ai-platform-env/bin/activate

# 安装基础依赖
pip install -r /opt/ai-platform/requirements.txt

# 验证关键包安装
python -c "import django; print(f'Django: {django.get_version()}')"
python -c "import pandas; print(f'Pandas: {pandas.__version__}')"
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
```

### 5.3 AI框架安装 (可选)

#### PyTorch安装
```bash
# CPU版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 或者GPU版本 (如果有CUDA)
# pip install torch torchvision torchaudio

# 验证PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
```

#### TensorFlow安装
```bash
# 安装TensorFlow
pip install tensorflow==2.14.0

# 验证TensorFlow
python -c "import tensorflow as tf; print(f'TensorFlow: {tf.__version__}')"
```

#### Transformers和NLP工具
```bash
# 安装Transformers库
pip install transformers==4.35.0

# 安装NLP相关工具
pip install \
    spacy==3.7.2 \
    nltk==3.8.1 \
    jieba==0.42.1

# 验证安装
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
```

## 6. 数据科学工具安装

### 6.1 Jupyter环境
```bash
# 安装Jupyter
pip install \
    jupyter==1.0.0 \
    jupyterlab==4.0.8 \
    notebook==7.0.6

# 配置Jupyter
jupyter lab --generate-config

# 创建Jupyter启动脚本
cat > /opt/ai-platform/start-jupyter.sh << 'EOF'
#!/bin/bash
source /opt/ai-platform/ai-platform-env/bin/activate
cd /opt/ai-platform
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
EOF

chmod +x /opt/ai-platform/start-jupyter.sh
```

### 6.2 数据可视化工具
```bash
# 安装可视化库
pip install \
    matplotlib==3.8.2 \
    seaborn==0.13.0 \
    plotly==5.17.0 \
    bokeh==3.3.2

# 验证安装
python -c "import matplotlib; print(f'Matplotlib: {matplotlib.__version__}')"
```

## 7. 开发工具配置

### 7.1 代码质量工具
```bash
# 创建.flake8配置
cat > /opt/ai-platform/.flake8 << 'EOF'
[flake8]
max-line-length = 88
exclude = .git,__pycache__,migrations,venv,env
ignore = E203,W503
EOF

# 创建pyproject.toml (Black配置)
cat > /opt/ai-platform/pyproject.toml << 'EOF'
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | venv
  | \.env
  | env
  | _build
  | buck-out
  | build
  | dist
  | migrations
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
EOF
```

### 7.2 Git配置
```bash
# 创建.gitignore
cat > /opt/ai-platform/.gitignore << 'EOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
ai-platform-env/
venv/
env/
ENV/

# Django
*.log
local_settings.py
db.sqlite3
media/
staticfiles/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment variables
.env
.env.local
.env.production

# Jupyter
.ipynb_checkpoints/

# Cache
.cache/
.pytest_cache/

# Coverage
htmlcov/
.coverage
.coverage.*
EOF
```

## 8. 环境验证

### 8.1 创建验证脚本
```bash
cat > /opt/ai-platform/validate-environment.py << 'EOF'
#!/usr/bin/env python3
"""
AI Platform Environment Validation Script
验证AI平台Python环境是否正确配置
"""

import sys
import platform
import subprocess

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    return version.major == 3 and version.minor == 10

def check_packages():
    """检查关键包安装"""
    packages = [
        'django',
        'djangorestframework', 
        'pandas',
        'numpy',
        'psycopg2',
        'redis',
        'celery',
        'gunicorn',
        'pytest'
    ]
    
    results = {}
    for package in packages:
        try:
            __import__(package)
            results[package] = "✓ 已安装"
        except ImportError:
            results[package] = "✗ 未安装"
    
    return results

def check_system_info():
    """检查系统信息"""
    info = {
        "操作系统": platform.system(),
        "版本": platform.release(),
        "架构": platform.machine(),
        "处理器": platform.processor(),
        "Python实现": platform.python_implementation(),
        "Python版本": platform.python_version()
    }
    return info

def main():
    print("=" * 60)
    print("AI平台Python环境验证")
    print("=" * 60)
    
    # 系统信息
    print("\n🖥️  系统信息:")
    for key, value in check_system_info().items():
        print(f"  {key}: {value}")
    
    # Python版本检查
    print("\n🐍 Python版本检查:")
    if check_python_version():
        print("  ✓ Python 3.10 - 正确")
    else:
        print("  ✗ Python版本不正确，需要Python 3.10")
    
    # 包安装检查
    print("\n📦 关键包安装检查:")
    packages = check_packages()
    for package, status in packages.items():
        print(f"  {package}: {status}")
    
    # 环境路径检查
    print("\n📁 环境路径:")
    print(f"  Python可执行文件: {sys.executable}")
    print(f"  工作目录: {subprocess.getoutput('pwd')}")
    
    # 总结
    missing_packages = [pkg for pkg, status in packages.items() if "未安装" in status]
    
    print("\n" + "=" * 60)
    if not missing_packages and check_python_version():
        print("🎉 环境验证通过！AI平台Python环境配置正确。")
    else:
        print("⚠️  环境验证失败，请检查以下问题：")
        if not check_python_version():
            print("  - Python版本不正确")
        if missing_packages:
            print("  - 缺少以下包：", ", ".join(missing_packages))
    print("=" * 60)

if __name__ == "__main__":
    main()
EOF

chmod +x /opt/ai-platform/validate-environment.py
```

### 8.2 运行验证
```bash
# 激活环境并运行验证
source /opt/ai-platform/ai-platform-env/bin/activate
cd /opt/ai-platform
python validate-environment.py
```

## 9. 性能优化配置

### 9.1 Python性能调优
```bash
# 创建Python性能配置
cat >> ~/.bashrc << 'EOF'

# Python性能优化
export PYTHONHASHSEED=random
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# 多线程优化
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
EOF

source ~/.bashrc
```

### 9.2 内存优化
```bash
# 创建Python内存配置文件
cat > /opt/ai-platform/python-memory.conf << 'EOF'
# Python内存优化配置
# 设置Python内存分配器
export PYTHONMALLOC=malloc

# 设置垃圾回收阈值
export PYTHONGC=1

# 设置内存映射阈值
export PYTHONMALLOCSTATS=1
EOF
```

## 10. 服务化配置

### 10.1 创建systemd服务
```bash
# 创建AI平台服务文件
sudo tee /etc/systemd/system/ai-platform.service << 'EOF'
[Unit]
Description=AI Platform Service
After=network.target

[Service]
Type=forking
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/ai-platform
Environment=PATH=/opt/ai-platform/ai-platform-env/bin
ExecStart=/opt/ai-platform/ai-platform-env/bin/gunicorn --daemon --workers 4 --bind 0.0.0.0:8000 config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务（部署时使用）
# sudo systemctl enable ai-platform
# sudo systemctl start ai-platform
```

## 11. 备份和恢复

### 11.1 创建环境备份脚本
```bash
cat > /opt/ai-platform/backup-environment.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/backup/ai-platform"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
sudo mkdir -p $BACKUP_DIR

# 激活环境
source /opt/ai-platform/ai-platform-env/bin/activate

# 导出已安装的包列表
pip freeze > $BACKUP_DIR/requirements_$TIMESTAMP.txt

# 备份配置文件
cp /opt/ai-platform/.flake8 $BACKUP_DIR/
cp /opt/ai-platform/pyproject.toml $BACKUP_DIR/
cp /opt/ai-platform/.gitignore $BACKUP_DIR/

# 压缩整个虚拟环境（可选，占用空间较大）
# tar -czf $BACKUP_DIR/ai-platform-env_$TIMESTAMP.tar.gz /opt/ai-platform/ai-platform-env

echo "环境备份完成: $BACKUP_DIR"
echo "requirements文件: requirements_$TIMESTAMP.txt"
EOF

chmod +x /opt/ai-platform/backup-environment.sh
```

### 11.2 创建环境恢复脚本
```bash
cat > /opt/ai-platform/restore-environment.sh << 'EOF'
#!/bin/bash

if [ $# -eq 0 ]; then
    echo "用法: $0 <requirements_file>"
    echo "例如: $0 requirements_20250529_143000.txt"
    exit 1
fi

REQUIREMENTS_FILE=$1

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "错误: 文件 $REQUIREMENTS_FILE 不存在"
    exit 1
fi

# 激活环境
source /opt/ai-platform/ai-platform-env/bin/activate

# 安装依赖
echo "正在从 $REQUIREMENTS_FILE 恢复环境..."
pip install -r $REQUIREMENTS_FILE

echo "环境恢复完成！"
EOF

chmod +x /opt/ai-platform/restore-environment.sh
```

## 12. 故障排除

### 12.1 常见问题解决

#### Python编译错误
```bash
# 如果遇到编译错误，安装完整的构建工具
sudo apt install -y python3.10-dev python3-dev
sudo apt install -y gcc g++ make cmake
```

#### SSL证书问题
```bash
# 更新证书
sudo apt update && sudo apt install -y ca-certificates

# 重新安装requests和urllib3
pip install --upgrade --force-reinstall requests urllib3
```

#### 权限问题
```bash
# 修复权限
sudo chown -R $USER:$USER /opt/ai-platform
chmod -R 755 /opt/ai-platform
```

#### 内存不足
```bash
# 创建临时swap空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 安装完成后可以删除
# sudo swapoff /swapfile
# sudo rm /swapfile
```

### 12.2 诊断脚本
```bash
cat > /opt/ai-platform/diagnose.sh << 'EOF'
#!/bin/bash

echo "=== AI平台环境诊断 ==="

echo "1. Python环境："
which python3
python3 --version
which pip3
pip3 --version

echo -e "\n2. 虚拟环境："
echo "AI Platform Env: /opt/ai-platform/ai-platform-env"
ls -la /opt/ai-platform/ai-platform-env/bin/python* 2>/dev/null || echo "虚拟环境不存在"

echo -e "\n3. 关键目录权限："
ls -la /opt/ai-platform/ | head -5

echo -e "\n4. 磁盘空间："
df -h /opt

echo -e "\n5. 内存使用："
free -h

echo -e "\n6. 网络连接："
ping -c 1 pypi.org >/dev/null 2>&1 && echo "PyPI连接正常" || echo "PyPI连接失败"

echo -e "\n=== 诊断完成 ==="
EOF

chmod +x /opt/ai-platform/diagnose.sh
```

## 总结

完成以上步骤后，您将拥有一个完整配置的AI平台Python开发环境：

- ✅ Python 3.10 安装并配置
- ✅ 虚拟环境创建和激活
- ✅ Django和AI框架依赖安装
- ✅ 开发工具和代码质量工具配置
- ✅ 环境验证和诊断工具
- ✅ 备份恢复机制
- ✅ 服务化配置

### 快速使用命令：
```bash
# 激活AI平台环境
ai-platform

# 或手动激活
source /opt/ai-platform/ai-platform-env/bin/activate

# 验证环境
python /opt/ai-platform/validate-environment.py

# 诊断问题
/opt/ai-platform/diagnose.sh
```

---
*文档创建时间: 2025年5月29日*
*适用系统: Ubuntu 24.04 LTS*
*Python版本: 3.10*
