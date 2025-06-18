#!/bin/bash

# =============================================================================
# 配置国内镜像源脚本
# 用于加速 Docker 构建和依赖下载
# =============================================================================

# 设置环境变量
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
export PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
export NPM_CONFIG_REGISTRY=https://registry.npmmirror.com/
export NPMRC_CONFIG="registry=https://registry.npmmirror.com/"

# Docker 构建参数
export DOCKER_BUILD_ARGS="--build-arg PIP_INDEX_URL=${PIP_INDEX_URL} --build-arg PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST} --build-arg NPM_REGISTRY=${NPM_CONFIG_REGISTRY}"

echo "✅ 已设置国内镜像源环境变量："
echo "   PIP_INDEX_URL: ${PIP_INDEX_URL}"
echo "   NPM_REGISTRY: ${NPM_CONFIG_REGISTRY}"
echo "   DOCKER_BUILD_ARGS: ${DOCKER_BUILD_ARGS}"

# 配置 pip
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = ${PIP_INDEX_URL}
trusted-host = ${PIP_TRUSTED_HOST}
timeout = 120
EOF

# 配置 npm 全局设置
npm config set registry ${NPM_CONFIG_REGISTRY}

# 检查 npm 版本并配置兼容的选项
NPM_VERSION=$(npm --version)
echo "   当前 npm 版本: ${NPM_VERSION}"

# 只设置基本的 npm 配置，避免版本兼容问题
# npm config set disturl https://npmmirror.com/dist
# npm config set sass_binary_site https://npmmirror.com/mirrors/node-sass
# npm config set phantomjs_cdnurl https://npmmirror.com/mirrors/phantomjs
# npm config set electron_mirror https://npmmirror.com/mirrors/electron/

echo "✅ 已配置 pip 和 npm 基础镜像源"
