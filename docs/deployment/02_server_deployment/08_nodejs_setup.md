# 🟢 AI中台 - Node.js环境配置 (Ubuntu 24.04 LTS)

## 📋 文档概述

本文档指导如何在Ubuntu 24.04 LTS环境中配置Node.js 20 LTS环境，用于AI中台前端开发和相关服务。

> **⏱️ 预计配置时间**: 1-2小时  
> **🎯 部署目标**: Node.js 20 LTS + 现代前端开发环境

## 🎯 技术栈规划

根据 `docs/Outline.md` 和Ubuntu 24.04 LTS优化，我们的技术栈包括：

- **Node.js 20.x LTS**：现代JavaScript运行时环境
- **前端框架**：React 18.x
- **构建工具**：Vite 5.x (替代Webpack，更快的构建)
- **UI组件库**：Ant Design 5.x
- **包管理器**：npm (Node.js自带) / yarn / pnpm

### 🔧 Node.js应用场景
- 前端应用（React）的开发和构建
- 前端服务API的开发（Express.js）
- 开发工具和脚本的运行
- 用户交互层应用的部署
- AI中台管理界面
- API测试和文档工具

## 🚀 Node.js 20 LTS 安装

### 方法一：使用 NVM 安装（推荐方式）

NVM (Node Version Manager) 允许在同一系统中安装和管理多个 Node.js 版本，特别适合开发环境。

#### Ubuntu 24.04 LTS 安装步骤：

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装必要的依赖
sudo apt install -y curl wget build-essential

# 安装最新版本的 NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# 或使用 wget
# wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# 重新加载 shell 配置
source ~/.bashrc

# 或者手动加载 NVM
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 安装 Node.js 20.x LTS
nvm install --lts  # 安装最新的LTS版本 (Node.js 20.x)

# 或者指定版本
nvm install 20

# 设置为默认版本
nvm alias default 20
nvm use default

# 验证安装
node --version  # 应显示 v20.x.x
npm --version   # 应显示 npm 10.x.x
```

### 方法二：NodeSource仓库安装（生产环境推荐）

适用于生产服务器环境，提供稳定的包管理。

```bash
# 添加 NodeSource APT 仓库 (Node.js 20.x)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# 安装 Node.js 20.x
sudo apt-get install -y nodejs

```

## ⚙️ 环境配置与优化

### 全局包管理器配置

```bash
# 配置 npm 国内镜像 (提升下载速度)
npm config set registry https://registry.npmmirror.com/

# 或配置为官方源
# npm config set registry https://registry.npmjs.org/

# 查看当前配置
npm config get registry

# 升级 npm 到最新版本
npm install -g npm@latest

# 安装常用的全局工具包
npm install -g \
  yarn \
  pnpm \
  @vue/cli \
  create-react-app \
  vite \
  typescript \
  ts-node \
  nodemon \
  pm2

# 验证全局包安装
npm list -g --depth=0
```

### 开发环境优化

```bash
# 创建 AI 中台前端项目目录
sudo mkdir -p /opt/ai_platform_frontend
sudo chown $USER:$USER /opt/ai_platform_frontend
cd /opt/ai_platform_frontend

# 设置项目级 Node.js 版本 (如果使用 NVM)
echo "20" > .nvmrc

# 创建基础 package.json
cat > package.json << 'EOF'
{
  "name": "ai-platform-frontend",
  "version": "1.0.0",
  "description": "AI中台前端应用",
  "main": "index.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix"
  },
  "keywords": ["ai", "platform", "react", "vite"],
  "author": "AI Platform Team",
  "license": "MIT",
  "engines": {
    "node": ">=20.0.0",
    "npm": ">=10.0.0"
  }
}
EOF
```

## 🛠️ 前端开发环境搭建

### React + Vite 项目创建

```bash
# 使用 Vite 创建 React TypeScript 项目
npm create vite@latest ai-platform-ui -- --template react-ts

# 进入项目目录
cd ai-platform-ui

# 安装依赖
npm install

# 安装 AI 中台常用依赖
npm install \
  antd \
  @ant-design/icons \
  axios \
  react-router-dom \
  @reduxjs/toolkit \
  react-redux \
  @types/react \
  @types/react-dom

# 安装开发依赖
npm install -D \
  @types/node \
  @typescript-eslint/eslint-plugin \
  @typescript-eslint/parser \
  eslint \
  eslint-plugin-react \
  eslint-plugin-react-hooks \
  prettier \
  @vitejs/plugin-react

# 启动开发服务器测试
npm run dev
```

### Ant Design 配置

```bash
# 创建 Ant Design 配置文件
cat > src/App.css << 'EOF'
/* AI 中台主题配置 */
.ai-platform-layout {
  min-height: 100vh;
}

.ai-platform-header {
  background: #001529;
  padding: 0;
}

.ai-platform-content {
  margin: 24px 16px;
  padding: 24px;
  background: #fff;
  min-height: 280px;
}

.ai-platform-footer {
  text-align: center;
}
EOF

# 更新 src/App.tsx 为 AI 中台布局
cat > src/App.tsx << 'EOF'
import React from 'react';
import { Layout, Menu, theme } from 'antd';
import {
  DesktopOutlined,
  PieChartOutlined,
  FileOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons';
import './App.css';

const { Header, Content, Footer, Sider } = Layout;

function getItem(label: React.ReactNode, key: React.Key, icon?: React.ReactNode, children?: any[]) {
  return {
    key,
    icon,
    children,
    label,
  };
}

const items = [
  getItem('数据平台', '1', <PieChartOutlined />),
  getItem('算法平台', '2', <DesktopOutlined />),
  getItem('模型平台', 'sub1', <UserOutlined />, [
    getItem('模型训练', '3'),
    getItem('模型部署', '4'),
    getItem('模型监控', '5'),
  ]),
  getItem('服务平台', 'sub2', <TeamOutlined />, [
    getItem('API管理', '6'),
    getItem('服务监控', '8'),
  ]),
  getItem('系统管理', '9', <FileOutlined />),
];

const App: React.FC = () => {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout className="ai-platform-layout">
      <Sider collapsible>
        <div className="demo-logo-vertical" />
        <Menu theme="dark" defaultSelectedKeys={['1']} mode="inline" items={items} />
      </Sider>
      <Layout>
        <Header className="ai-platform-header" style={{ background: colorBgContainer }}>
          <h1 style={{ margin: 0, padding: '0 24px', lineHeight: '64px', color: '#fff' }}>
            AI 中台管理系统
          </h1>
        </Header>
        <Content className="ai-platform-content">
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            欢迎使用 AI 中台管理系统
          </div>
        </Content>
        <Footer className="ai-platform-footer">
          AI Platform ©{new Date().getFullYear()} Created by AI Platform Team
        </Footer>
      </Layout>
    </Layout>
  );
};

export default App;
EOF
```

```

## 🔧 生产环境配置

### Nginx 反向代理配置

```bash
# 创建 Node.js 应用的 Nginx 配置
sudo tee /etc/nginx/sites-available/ai-platform-frontend << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    # React 应用静态文件
    location / {
        root /opt/ai_platform_frontend/ai-platform-ui/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }
    
    # API 代理到 Django 后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss;
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/ai-platform-frontend /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### PM2 进程管理

```bash
# 安装 PM2
npm install -g pm2

# 创建 PM2 配置文件
cat > /opt/ai_platform_frontend/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'ai-platform-frontend',
    script: 'serve',
    args: '-s dist -l 3000',
    cwd: '/opt/ai_platform_frontend/ai-platform-ui',
    instances: 'max',
    exec_mode: 'cluster',
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    error_file: '/var/log/pm2/ai-platform-frontend-error.log',
    out_file: '/var/log/pm2/ai-platform-frontend-out.log',
    log_file: '/var/log/pm2/ai-platform-frontend.log',
    time: true
  }]
};
EOF

# 创建日志目录
sudo mkdir -p /var/log/pm2
sudo chown $USER:$USER /var/log/pm2

# 启动应用
pm2 start ecosystem.config.js

# 保存 PM2 配置
pm2 save

# 设置开机自启
pm2 startup
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp /home/$USER
```

## 🔗 与 Django 后端集成

### API 调用配置

```bash
# 创建 API 配置文件
mkdir -p /opt/ai_platform_frontend/ai-platform-ui/src/config
cat > /opt/ai_platform_frontend/ai-platform-ui/src/config/api.ts << 'EOF'
// AI 中台 API 配置
export const API_CONFIG = {
  BASE_URL: process.env.NODE_ENV === 'production' 
    ? 'http://localhost:8000' 
    : 'http://localhost:8000',
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/api/auth/token/',
      REFRESH: '/api/auth/token/refresh/',
      USER: '/api/auth/user/'
    },
    ALGORITHM: '/api/algorithm/',
    DATA: '/api/data/',
    MODEL: '/api/model/',
    SERVICE: '/api/service/'
  },
  TIMEOUT: 10000
};

// Axios 实例配置
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理认证错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
EOF
```

### 构建与部署脚本

```bash
# 创建构建脚本
cat > /opt/ai_platform_frontend/build.sh << 'EOF'
#!/bin/bash
# AI 中台前端构建脚本

set -e

echo "🏗️ 开始构建 AI 中台前端..."

# 进入项目目录
cd /opt/ai_platform_frontend/ai-platform-ui

# 安装依赖
echo "📦 安装依赖..."
npm ci

# 执行代码检查
echo "🔍 执行代码检查..."
npm run lint

# 构建生产版本
echo "🔨 构建生产版本..."
npm run build

# 检查构建结果
if [ -d "dist" ]; then
    echo "✅ 构建成功！输出目录: dist/"
    ls -la dist/
else
    echo "❌ 构建失败！"
    exit 1
fi

echo "🎉 前端构建完成！"
EOF

chmod +x /opt/ai_platform_frontend/build.sh

# 创建部署脚本
cat > /opt/ai_platform_frontend/deploy.sh << 'EOF'
#!/bin/bash
# AI 中台前端部署脚本

set -e

echo "🚀 开始部署 AI 中台前端..."

# 执行构建
./build.sh

# 重启 PM2 应用
echo "🔄 重启前端服务..."
pm2 restart ai-platform-frontend

# 重新加载 Nginx
echo "🔄 重新加载 Nginx..."
sudo nginx -t && sudo systemctl reload nginx

echo "✅ 前端部署完成！"
echo "🌐 访问地址: http://localhost"
EOF

chmod +x /opt/ai_platform_frontend/deploy.sh
```

## 📊 性能监控与优化

### 性能监控配置

```bash
# 安装性能监控工具
npm install -g clinic autocannon

# 创建性能测试脚本
cat > /opt/ai_platform_frontend/performance-test.js << 'EOF'
const autocannon = require('autocannon');

// 性能测试配置
const testConfig = {
  url: 'http://localhost:3000',
  connections: 10,
  duration: 30,
  pipelining: 1
};

console.log('🔥 开始前端性能测试...');

autocannon(testConfig, (err, result) => {
  if (err) {
    console.error('测试失败:', err);
    return;
  }
  
  console.log('📊 性能测试结果:');
  console.log(`平均延迟: ${result.latency.average}ms`);
  console.log(`请求/秒: ${result.requests.average}`);
  console.log(`总请求数: ${result.requests.total}`);
  console.log(`错误数: ${result.non2xx}`);
});
EOF

# 运行性能测试
node /opt/ai_platform_frontend/performance-test.js
```

### 构建优化配置

```bash
# 更新 vite.config.ts 添加优化配置
cat > /opt/ai_platform_frontend/ai-platform-ui/vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    // 生产环境构建优化
    target: 'es2015',
    outDir: 'dist',
    assetsDir: 'assets',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        // 手动分块
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd', '@ant-design/icons'],
          utils: ['axios', 'react-router-dom']
        }
      }
    },
    // 启用 gzip 压缩提示
    reportCompressedSize: true,
    chunkSizeWarningLimit: 500
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
EOF
```

## ✅ 环境验证

### 验证脚本

```bash
# 创建环境验证脚本
cat > /opt/ai_platform_frontend/verify.sh << 'EOF'
#!/bin/bash
# Node.js 环境验证脚本

echo "🔍 验证 Node.js 环境..."

# 检查 Node.js 版本
echo "Node.js 版本:"
node --version

# 检查 npm 版本
echo "npm 版本:"
npm --version

# 检查全局包
echo "全局包列表:"
npm list -g --depth=0

# 检查项目依赖
if [ -f "ai-platform-ui/package.json" ]; then
    echo "项目依赖检查:"
    cd ai-platform-ui
    npm ls
    cd ..
fi

# 检查服务状态
echo "PM2 服务状态:"
pm2 status

# 检查端口占用
echo "端口占用检查:"
netstat -tlnp | grep -E ":(3000|80|8000)"

echo "✅ 环境验证完成！"
EOF

chmod +x /opt/ai_platform_frontend/verify.sh

# 运行验证
./verify.sh
```

## 📚 相关文档

- [Python环境配置](09_python_environment_setup.md)
- [Django REST配置](06_django_rest_setup.md)
- [前端应用部署](../03_application_deployment/02_frontend_deployment.md)
- [API集成测试](../03_application_deployment/03_api_integration.md)

## 🔧 故障排除

### 常见问题解决

1. **npm 安装失败**
   ```bash
   # 清理缓存
   npm cache clean --force
   
   # 删除 node_modules 重新安装
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **构建内存不足**
   ```bash
   # 增加 Node.js 内存限制
   export NODE_OPTIONS="--max-old-space-size=4096"
   npm run build
   ```

3. **PM2 服务无法启动**
   ```bash
   # 查看详细错误日志
   pm2 logs ai-platform-frontend
   
   # 重置 PM2
   pm2 kill
   pm2 start ecosystem.config.js
   ```

---

> **📝 注意**: 本文档基于Ubuntu 24.04 LTS和Node.js 20 LTS编写，确保环境兼容性。
