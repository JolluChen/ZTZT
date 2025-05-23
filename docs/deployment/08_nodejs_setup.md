# AI 中台 - Node.js 环境配置

本文档指导如何在 AI 中台项目中安装和配置 Node.js 环境，用于支持前端开发（React）和相关服务。

## 1. 概述

根据 `docs/Outline.md`，我们的技术栈包括：

- **Node.js 18.x LTS**：用于前端开发API和工具
- **前端框架**：React 18.x
- **构建工具**：Webpack 5
- **UI组件库**：Ant Design
- **包管理器**：npm / yarn / pnpm

Node.js 将主要用于以下场景：
- 前端应用（React）的开发和构建
- 前端服务API的开发（Express.js）
- 开发工具和脚本的运行
- 用户交互层应用的部署

## 2. Node.js 安装

### 2.1 使用 NVM 安装（推荐方式）

NVM (Node Version Manager) 允许在同一系统中安装和管理多个 Node.js 版本。

#### Ubuntu 22.04 LTS 安装步骤：

```bash
# 安装 NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
# 或使用 wget
# wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash

# 加载 NVM
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 安装 Node.js 18.x LTS
nvm install --lts=hydrogen  # Node.js 18.x LTS (氢)版本

# 设置为默认版本
nvm alias default 18

# 验证安装
node --version  # 应显示 v18.x.x
npm --version   # 应显示 npm 对应版本
```

### 2.2 通过包管理器安装

如果不需要管理多个Node.js版本，可以直接使用系统包管理器安装。

```bash
# 添加 Node.js 18.x 源
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# 安装 Node.js 和 npm
sudo apt-get install -y nodejs

# 验证安装
node --version
npm --version
```

### 2.3 在 Kubernetes 中部署 Node.js 应用

对于在 Kubernetes 中部署的应用，推荐使用官方 Node.js Docker 镜像：

```Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["node", "server.js"]
```

## 3. 包管理器配置

### 3.1 npm 配置（默认）

npm 是 Node.js 的默认包管理器，配置如下：

```bash
# 配置国内镜像源（可选，国内网络环境建议配置）
npm config set registry https://registry.npmmirror.com

# 配置项目级依赖缓存
npm config set cache-min 9999999
```

### 3.2 yarn 配置（可选）

Yarn 是一个可选的包管理器，提供更快的包安装速度和确定性安装：

```bash
# 安装 yarn
npm install -g yarn

# 配置国内镜像（可选）
yarn config set registry https://registry.npmmirror.com

# 验证安装
yarn --version
```

### 3.3 pnpm 配置（可选）

pnpm 是更节省磁盘空间的包管理器，特别适合有大量项目的环境：

```bash
# 安装 pnpm
npm install -g pnpm

# 配置国内镜像（可选）
pnpm config set registry https://registry.npmmirror.com

# 验证安装
pnpm --version
```

## 4. 前端框架配置

### 4.1 React 项目

创建新的 React 18 项目：

```bash
# 使用 Create React App
npx create-react-app my-app
# 或指定模板（推荐使用TypeScript）
npx create-react-app my-app --template typescript

# 安装 Ant Design
cd my-app
npm install antd @ant-design/icons
```

### 4.2 Next.js 项目（SSR）

创建支持服务端渲染的基于React的Next.js项目：

```bash
# 创建Next.js项目
npx create-next-app@latest my-nextjs-app
# 或使用TypeScript（推荐）
npx create-next-app@latest my-nextjs-app --typescript

cd my-nextjs-app
npm install

# 安装Ant Design
npm install antd @ant-design/icons
```

## 5. Express.js API 服务配置

设置 Express.js 后端 API 服务：

```bash
# 创建项目目录
mkdir my-express-api
cd my-express-api

# 初始化项目
npm init -y

# 安装 Express 和必要依赖
npm install express cors body-parser mongoose

# 可选：安装开发依赖
npm install --save-dev nodemon typescript ts-node @types/express @types/node
```

## 6. 开发工具与最佳实践

### 6.1 代码质量工具

```bash
# ESLint 安装
npm install --save-dev eslint

# 配置 ESLint
npx eslint --init

# Prettier 安装
npm install --save-dev prettier eslint-config-prettier eslint-plugin-prettier
```

### 6.2 CI/CD 集成

在 `.gitlab-ci.yml` 或 GitHub Actions 配置中集成 Node.js 构建：

```yaml
# .gitlab-ci.yml 示例
stages:
  - build
  - test
  - deploy

frontend-build:
  stage: build
  image: node:18-alpine
  script:
    - npm install
    - npm run build
  artifacts:
    paths:
      - build/
```

### 6.3 Docker 容器化

使用多阶段构建减小镜像大小：

```Dockerfile
# 构建阶段
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 生产阶段 - React应用部署到Nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
# React路由支持
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

示例React路由支持的nginx配置文件(./nginx/nginx.conf):

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存设置
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

## 7. 性能优化建议

- 使用生产模式构建以启用优化：`NODE_ENV=production`
- 启用 Gzip/Brotli 压缩来减少传输大小
- 实现代码分割（Code Splitting）以减少初始加载时间
- 为静态资产配置适当的缓存策略
- 考虑使用服务端渲染（SSR）或静态站点生成（SSG）提升性能

## 8. 安全最佳实践

- 定期更新依赖以修补安全漏洞：`npm audit fix`
- 避免在前端代码中存储敏感信息
- 实施适当的 CSP（内容安全策略）
- 使用 Helmet.js 增强 Express.js 应用安全性
- 对 API 调用实施速率限制（Rate Limiting）

## 结论

本文档提供了在 AI 中台项目中安装和配置 Node.js 环境的指南。按照这些步骤，您可以为前端开发（React/Vue）和相关服务建立一个稳定的环境。请确保定期更新 Node.js 和相关依赖，以获取安全修复和性能改进。
