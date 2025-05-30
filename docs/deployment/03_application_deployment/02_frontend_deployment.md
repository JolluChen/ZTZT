# ⭐ AI中台 - 前端应用部署指南 (Ubuntu 24.04 LTS)

本文档指导如何部署AI中台前端应用，包括管理后台、用户门户和监控界面的配置与部署。

> **⚠️ 重要提示**: 请确保后端应用已成功部署并正常运行。

## ⏱️ 预计部署时间
- **Node.js环境配置**: 30分钟
- **前端项目构建**: 45分钟  
- **静态文件部署**: 30分钟
- **Nginx配置**: 45分钟
- **集成测试**: 30分钟
- **总计**: 3-3.5小时

## 🎯 部署目标
✅ Node.js 20 LTS 运行环境  
✅ 管理后台前端界面  
✅ 用户门户系统  
✅ Nginx反向代理配置  
✅ 静态文件服务优化

## 📋 前置条件检查

```bash
# 1. 验证后端服务状态
curl -f http://127.0.0.1:8000/admin/ && echo "✅ 后端服务正常"

# 2. 验证Node.js环境
node --version  # 应该显示 v20.x.x
npm --version   # 应该显示 10.x.x

# 3. 验证Nginx安装
nginx -version  # 应该显示 nginx version

# 4. 验证权限设置
ls -la /opt/ai-platform/
```

## 1. 🌐 Node.js 环境验证

### 1.1 验证Node.js环境
```bash
# 激活Node.js环境 (如果使用nvm)
# source ~/.bashrc
# nvm use 20

# 验证版本
node --version
npm --version
```

### 1.2 全局包安装
```bash
# 安装常用全局包
npm install -g pm2 serve http-server

# 验证安装
pm2 --version
serve --version
```

## 2. 📦 前端项目准备

### 2.1 创建前端项目结构
```bash
# 创建前端项目目录
cd /opt/ai-platform
mkdir -p frontend/{admin,portal,monitoring,static,dist}
cd frontend

# 设置权限
sudo chown -R $USER:$USER /opt/ai-platform/frontend
chmod -R 755 /opt/ai-platform/frontend
```

### 2.2 Django管理后台定制
```bash
# 创建自定义管理后台模板
cd /opt/ai-platform/backend
mkdir -p templates/admin

# 创建基础管理后台模板
cat > templates/admin/base_site.html << 'EOF'
{% extends "admin/base.html" %}
{% load static %}

{% block title %}AI中台管理系统{% endblock %}

{% block branding %}
<h1 id="site-name">
    <img src="{% static 'admin/img/ai_logo.png' %}" alt="AI中台" style="height: 30px; margin-right: 10px;">
    AI中台管理系统
</h1>
{% endblock %}

{% block nav-global %}{% endblock %}

{% block extrahead %}
<style>
    #header {
        background: linear-gradient(to right, #667eea 0%, #764ba2 100%);
    }
    
    #site-name {
        color: white;
        font-weight: bold;
    }
    
    .module h2, .module caption, .inline-group h2 {
        background: linear-gradient(to right, #667eea 0%, #764ba2 100%);
    }
    
    .dashboard .module table th {
        background: #f8f9fa;
    }
    
    .button, input[type=submit], input[type=button] {
        background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
        border: none;
    }
    
    .button:hover, input[type=submit]:hover {
        opacity: 0.9;
    }
</style>
{% endblock %}

{% block footer %}
<div id="footer">
    <p>AI中台管理系统 v1.0 | © 2025 AI Platform Team</p>
</div>
{% endblock %}
EOF

# 创建主页模板
cat > templates/admin/index.html << 'EOF'
{% extends "admin/base_site.html" %}
{% load static admin_urls %}

{% block content %}
<div id="content-main">
    <div class="dashboard">
        <div class="module" style="margin-bottom: 20px;">
            <h2>系统概览</h2>
            <table>
                <tr>
                    <th>平台模块</th>
                    <th>状态</th>
                    <th>操作</th>
                </tr>
                <tr>
                    <td>数据平台</td>
                    <td><span style="color: green;">运行中</span></td>
                    <td><a href="{% url 'admin:data_platform_dataplatformbase_changelist' %}" class="button">管理</a></td>
                </tr>
                <tr>
                    <td>算法平台</td>
                    <td><span style="color: green;">运行中</span></td>
                    <td><a href="{% url 'admin:algorithm_platform_algorithmplatformbase_changelist' %}" class="button">管理</a></td>
                </tr>
                <tr>
                    <td>模型平台</td>
                    <td><span style="color: green;">运行中</span></td>
                    <td><a href="{% url 'admin:model_platform_modelplatformbase_changelist' %}" class="button">管理</a></td>
                </tr>
                <tr>
                    <td>服务平台</td>
                    <td><span style="color: green;">运行中</span></td>
                    <td><a href="{% url 'admin:service_platform_serviceplatformbase_changelist' %}" class="button">管理</a></td>
                </tr>
            </table>
        </div>
        
        <!-- 原有的应用列表 -->
        {% for app in app_list %}
            <div class="app-{{ app.app_label }} module">
                <table>
                    <caption>
                        <a href="{{ app.app_url }}" class="section" title="{% blocktranslate with name=app.name %}Models in the {{ name }} application{% endblocktranslate %}">{{ app.name }}</a>
                    </caption>
                    {% for model in app.models %}
                        <tr class="model-{{ model.object_name|lower }}">
                            {% if model.admin_url %}
                                <th scope="row"><a href="{{ model.admin_url }}">{{ model.name }}</a></th>
                            {% else %}
                                <th scope="row">{{ model.name }}</th>
                            {% endif %}
                            
                            {% if model.add_url %}
                                <td><a href="{{ model.add_url }}" class="addlink">新增</a></td>
                            {% else %}
                                <td>&nbsp;</td>
                            {% endif %}
                            
                            {% if model.admin_url %}
                                {% if model.view_only %}
                                    <td><a href="{{ model.admin_url }}" class="viewlink">查看</a></td>
                                {% else %}
                                    <td><a href="{{ model.admin_url }}" class="changelink">管理</a></td>
                                {% endif %}
                            {% else %}
                                <td>&nbsp;</td>
                            {% endif %}
                        </tr>
                    {% endfor %}
                </table>
            </div>
        {% empty %}
            <p>没有可用的管理模块。</p>
        {% endfor %}
    </div>
</div>
{% endblock %}
EOF

# 创建静态文件目录并添加logo
mkdir -p static/admin/img
# 注意：这里需要添加实际的logo文件
echo "请在static/admin/img/目录下添加ai_logo.png文件"
```

## 3. 🔧 用户门户前端

### 3.1 创建简单的用户门户
```bash
# 创建用户门户项目
cd /opt/ai-platform/frontend
mkdir -p portal/{src,public,build}

# 创建package.json
cat > portal/package.json << 'EOF'
{
  "name": "ai-platform-portal",
  "version": "1.0.0",
  "description": "AI中台用户门户",
  "main": "index.js",
  "scripts": {
    "start": "serve -s build -l 3000",
    "build": "npm run copy-files",
    "copy-files": "cp -r src/* build/",
    "dev": "http-server src -p 3001 -c-1"
  },
  "dependencies": {
    "serve": "^14.2.0"
  },
  "devDependencies": {
    "http-server": "^14.1.1"
  }
}
EOF

# 创建主HTML文件
cat > portal/src/index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI中台用户门户</title>
    <link rel="stylesheet" href="styles.css">
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
</head>
<body>
    <header class="header">
        <div class="container">
            <h1 class="logo">🤖 AI中台</h1>
            <nav class="nav">
                <a href="#home" class="nav-link active">首页</a>
                <a href="#platforms" class="nav-link">平台</a>
                <a href="#docs" class="nav-link">文档</a>
                <a href="#login" class="nav-link" id="loginBtn">登录</a>
            </nav>
        </div>
    </header>

    <main class="main">
        <!-- 首页部分 -->
        <section id="home" class="section active">
            <div class="container">
                <div class="hero">
                    <h2>欢迎使用AI中台系统</h2>
                    <p>一站式AI开发和部署平台</p>
                    <div class="hero-buttons">
                        <button class="btn btn-primary" onclick="showSection('platforms')">开始使用</button>
                        <button class="btn btn-secondary" onclick="window.open('/swagger/', '_blank')">API文档</button>
                    </div>
                </div>
                
                <div class="features">
                    <div class="feature-card">
                        <h3>🔧 算法平台</h3>
                        <p>机器学习算法开发和管理</p>
                    </div>
                    <div class="feature-card">
                        <h3>📊 数据平台</h3>
                        <p>数据处理和分析平台</p>
                    </div>
                    <div class="feature-card">
                        <h3>🧠 模型平台</h3>
                        <p>AI模型训练和部署</p>
                    </div>
                    <div class="feature-card">
                        <h3>⚡ 服务平台</h3>
                        <p>API服务管理和监控</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- 平台部分 -->
        <section id="platforms" class="section">
            <div class="container">
                <h2>平台服务</h2>
                <div class="platform-grid">
                    <div class="platform-card" data-platform="data">
                        <h3>数据平台</h3>
                        <p>状态: <span class="status" id="data-status">检查中...</span></p>
                        <button class="btn btn-primary" onclick="testPlatformAPI('data')">测试API</button>
                    </div>
                    <div class="platform-card" data-platform="algorithm">
                        <h3>算法平台</h3>
                        <p>状态: <span class="status" id="algorithm-status">检查中...</span></p>
                        <button class="btn btn-primary" onclick="testPlatformAPI('algorithm')">测试API</button>
                    </div>
                    <div class="platform-card" data-platform="model">
                        <h3>模型平台</h3>
                        <p>状态: <span class="status" id="model-status">检查中...</span></p>
                        <button class="btn btn-primary" onclick="testPlatformAPI('model')">测试API</button>
                    </div>
                    <div class="platform-card" data-platform="service">
                        <h3>服务平台</h3>
                        <p>状态: <span class="status" id="service-status">检查中...</span></p>
                        <button class="btn btn-primary" onclick="testPlatformAPI('service')">测试API</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- 文档部分 -->
        <section id="docs" class="section">
            <div class="container">
                <h2>API文档</h2>
                <div class="docs-grid">
                    <div class="doc-card">
                        <h3>📋 Swagger UI</h3>
                        <p>交互式API文档</p>
                        <button class="btn btn-primary" onclick="window.open('/swagger/', '_blank')">打开</button>
                    </div>
                    <div class="doc-card">
                        <h3>📖 ReDoc</h3>
                        <p>美观的API文档</p>
                        <button class="btn btn-primary" onclick="window.open('/redoc/', '_blank')">打开</button>
                    </div>
                    <div class="doc-card">
                        <h3>🔧 管理后台</h3>
                        <p>系统管理界面</p>
                        <button class="btn btn-primary" onclick="window.open('/admin/', '_blank')">打开</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- 登录部分 -->
        <section id="login" class="section">
            <div class="container">
                <div class="login-form">
                    <h2>用户登录</h2>
                    <form id="loginForm">
                        <div class="form-group">
                            <label for="username">用户名:</label>
                            <input type="text" id="username" name="username" required>
                        </div>
                        <div class="form-group">
                            <label for="password">密码:</label>
                            <input type="password" id="password" name="password" required>
                        </div>
                        <button type="submit" class="btn btn-primary">登录</button>
                    </form>
                </div>
            </div>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>&copy; 2025 AI中台系统. All rights reserved.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>
EOF

# 创建样式文件
cat > portal/src/styles.css << 'EOF'
/* 全局样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* 头部样式 */
.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 0;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
}

.nav {
    display: flex;
    gap: 2rem;
}

.nav-link {
    color: white;
    text-decoration: none;
    transition: opacity 0.3s;
    cursor: pointer;
}

.nav-link:hover,
.nav-link.active {
    opacity: 0.8;
}

/* 主体样式 */
.main {
    margin-top: 80px;
    min-height: calc(100vh - 160px);
}

.section {
    display: none;
    padding: 2rem 0;
}

.section.active {
    display: block;
}

/* 英雄区域 */
.hero {
    text-align: center;
    padding: 4rem 0;
    background: white;
    border-radius: 10px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.hero h2 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero p {
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
}

.hero-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
}

/* 功能卡片 */
.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.feature-card:hover {
    transform: translateY(-5px);
}

.feature-card h3 {
    margin-bottom: 1rem;
    font-size: 1.3rem;
}

/* 平台网格 */
.platform-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.platform-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.platform-card:hover {
    transform: translateY(-5px);
}

.platform-card h3 {
    margin-bottom: 1rem;
    color: #333;
}

.status {
    font-weight: bold;
}

.status.online {
    color: #28a745;
}

.status.offline {
    color: #dc3545;
}

/* 文档网格 */
.docs-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.doc-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.doc-card:hover {
    transform: translateY(-5px);
}

/* 登录表单 */
.login-form {
    max-width: 400px;
    margin: 2rem auto;
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
}

.form-group input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 1rem;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
}

/* 按钮样式 */
.btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1rem;
    text-decoration: none;
    display: inline-block;
    transition: all 0.3s;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover {
    opacity: 0.9;
    transform: translateY(-2px);
}

.btn-secondary {
    background: transparent;
    color: #667eea;
    border: 2px solid #667eea;
}

.btn-secondary:hover {
    background: #667eea;
    color: white;
}

/* 底部样式 */
.footer {
    background: #333;
    color: white;
    text-align: center;
    padding: 1rem 0;
    margin-top: 2rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .header .container {
        flex-direction: column;
        gap: 1rem;
    }
    
    .nav {
        gap: 1rem;
    }
    
    .hero h2 {
        font-size: 2rem;
    }
    
    .hero-buttons {
        flex-direction: column;
        align-items: center;
    }
    
    .features,
    .platform-grid,
    .docs-grid {
        grid-template-columns: 1fr;
    }
}
EOF

# 创建JavaScript文件
cat > portal/src/script.js << 'EOF'
// 全局配置
const API_BASE_URL = 'http://127.0.0.1:8000/api';
let authToken = localStorage.getItem('authToken');

// 页面导航
function showSection(sectionId) {
    // 隐藏所有section
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // 移除所有nav-link的active类
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // 显示目标section
    document.getElementById(sectionId).classList.add('active');
    
    // 添加对应nav-link的active类
    document.querySelector(`[href="#${sectionId}"]`).classList.add('active');
}

// 导航点击事件
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const href = link.getAttribute('href');
        if (href && href.startsWith('#')) {
            showSection(href.substring(1));
        }
    });
});

// 测试平台API
async function testPlatformAPI(platform) {
    const statusElement = document.getElementById(`${platform}-status`);
    statusElement.textContent = '检查中...';
    statusElement.className = 'status';
    
    try {
        const response = await axios.get(`${API_BASE_URL}/${platform}/status/`, {
            headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {}
        });
        
        if (response.status === 200) {
            statusElement.textContent = '在线';
            statusElement.className = 'status online';
        }
    } catch (error) {
        statusElement.textContent = '离线';
        statusElement.className = 'status offline';
        console.error(`${platform} platform error:`, error);
    }
}

// 检查所有平台状态
async function checkAllPlatforms() {
    const platforms = ['data', 'algorithm', 'model', 'service'];
    
    for (const platform of platforms) {
        await testPlatformAPI(platform);
    }
}

// 用户登录
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await axios.post(`${API_BASE_URL}/auth/token/`, {
            username,
            password
        });
        
        if (response.data.access) {
            authToken = response.data.access;
            localStorage.setItem('authToken', authToken);
            
            // 更新登录按钮
            document.getElementById('loginBtn').textContent = '已登录';
            document.getElementById('loginBtn').style.color = '#28a745';
            
            alert('登录成功！');
            showSection('home');
        }
    } catch (error) {
        alert('登录失败，请检查用户名和密码');
        console.error('Login error:', error);
    }
});

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 检查登录状态
    if (authToken) {
        document.getElementById('loginBtn').textContent = '已登录';
        document.getElementById('loginBtn').style.color = '#28a745';
    }
    
    // 检查平台状态
    setTimeout(() => {
        checkAllPlatforms();
    }, 1000);
});

// 定期检查平台状态
setInterval(() => {
    if (document.getElementById('platforms').classList.contains('active')) {
        checkAllPlatforms();
    }
}, 30000); // 每30秒检查一次
EOF

# 构建项目
npm install
npm run build
```

## 4. 🔧 Nginx 配置

### 4.1 安装和配置Nginx
```bash
# 安装Nginx (如果未安装)
sudo apt update
sudo apt install nginx -y

# 验证安装
nginx -version
```

### 4.2 创建AI中台Nginx配置
```bash
# 创建站点配置
sudo tee /etc/nginx/sites-available/ai-platform << 'EOF'
server {
    listen 80;
    server_name localhost ai-platform.local;
    
    # 前端静态文件
    location / {
        root /opt/ai-platform/frontend/portal/build;
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Django后端API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS头部
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # Django管理后台
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API文档
    location ~ ^/(swagger|redoc)/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Django静态文件
    location /static/ {
        alias /opt/ai-platform/backend/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Django媒体文件
    location /media/ {
        alias /opt/ai-platform/backend/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 日志配置
    access_log /var/log/nginx/ai-platform-access.log;
    error_log /var/log/nginx/ai-platform-error.log;
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/ai-platform /etc/nginx/sites-enabled/

# 移除默认站点
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重新加载Nginx
sudo systemctl reload nginx
```

## 5. 🚀 服务启动和验证

### 5.1 启动所有服务
```bash
# 创建服务启动脚本
cat > /opt/ai-platform/start_all_services.sh << 'EOF'
#!/bin/bash

echo "🚀 启动AI中台所有服务..."

# 1. 启动Django后端
echo "📱 启动Django后端服务..."
cd /opt/ai-platform/backend
source /opt/ai-platform/ai-platform-env/bin/activate
python manage.py runserver 127.0.0.1:8000 &
DJANGO_PID=$!
echo "Django PID: $DJANGO_PID"

# 等待Django启动
sleep 5

# 2. 启动前端服务 (可选，因为Nginx已配置静态文件)
echo "🌐 前端文件已通过Nginx服务"

# 3. 启动Nginx
echo "🔧 启动Nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

# 验证服务状态
echo ""
echo "🔍 服务状态检查:"
echo "================================"

# 检查Django
if curl -s http://127.0.0.1:8000/admin/ > /dev/null; then
    echo "✅ Django后端: 运行中"
else
    echo "❌ Django后端: 未运行"
fi

# 检查Nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx: 运行中"
else
    echo "❌ Nginx: 未运行"
fi

# 检查前端
if curl -s http://localhost/ > /dev/null; then
    echo "✅ 前端门户: 可访问"
else
    echo "❌ 前端门户: 无法访问"
fi

echo ""
echo "🌐 访问地址:"
echo "================================"
echo "🏠 用户门户: http://localhost/"
echo "🔧 管理后台: http://localhost/admin/"
echo "📋 Swagger文档: http://localhost/swagger/"
echo "📖 ReDoc文档: http://localhost/redoc/"

echo ""
echo "✅ 所有服务启动完成!"
EOF

chmod +x /opt/ai-platform/start_all_services.sh

# 运行启动脚本
/opt/ai-platform/start_all_services.sh
```

### 5.2 前端功能测试
```bash
# 创建前端测试脚本
cat > test_frontend.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台前端功能测试脚本
"""
import requests
import time
import subprocess

BASE_URL = 'http://localhost'

def test_frontend_pages():
    """测试前端页面"""
    pages = [
        ('/', '用户门户'),
        ('/admin/', '管理后台'),
        ('/swagger/', 'Swagger文档'),
        ('/redoc/', 'ReDoc文档'),
    ]
    
    print("🌐 前端页面测试")
    print("=" * 40)
    
    for path, name in pages:
        try:
            response = requests.get(f'{BASE_URL}{path}', timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: 可访问 ({response.status_code})")
            else:
                print(f"⚠️ {name}: 响应码 {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: 无法访问 - {e}")

def test_api_endpoints():
    """测试API端点"""
    endpoints = [
        '/api/data/status/',
        '/api/algorithm/status/',
        '/api/model/status/',
        '/api/service/status/',
    ]
    
    print("\n🔗 API端点测试")
    print("=" * 40)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'{BASE_URL}{endpoint}', timeout=10)
            if response.status_code in [200, 401]:  # 401表示需要认证，但API正常
                print(f"✅ {endpoint}: 正常")
            else:
                print(f"⚠️ {endpoint}: 响应码 {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: 无法访问 - {e}")

def test_nginx_status():
    """测试Nginx状态"""
    print("\n🔧 Nginx服务状态")
    print("=" * 40)
    
    try:
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'nginx'], 
                              capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            print("✅ Nginx服务: 运行中")
        else:
            print("❌ Nginx服务: 未运行")
    except Exception as e:
        print(f"❌ Nginx服务检查失败: {e}")

def main():
    print("🧪 AI中台前端集成测试")
    print("=" * 50)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(3)
    
    test_nginx_status()
    test_frontend_pages()
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🎉 前端测试完成!")
    print("\n📋 测试总结:")
    print("   请查看上述结果确保所有服务正常运行")
    print("\n🌐 快速访问链接:")
    print(f"   用户门户: {BASE_URL}/")
    print(f"   管理后台: {BASE_URL}/admin/")
    print(f"   API文档: {BASE_URL}/swagger/")

if __name__ == '__main__':
    main()
EOF

chmod +x test_frontend.py

# 运行前端测试
python test_frontend.py
```

## 6. 📊 部署验证清单

### ✅ 前端功能验证
- [ ] 用户门户页面正常加载
- [ ] 平台状态检查正常
- [ ] API文档链接可访问
- [ ] 登录功能正常工作

### ✅ Nginx配置验证  
- [ ] 静态文件正常服务
- [ ] API代理正常工作
- [ ] 管理后台可访问
- [ ] CORS配置正确

### ✅ 集成测试验证
- [ ] 前后端API通信正常
- [ ] 用户认证流程完整
- [ ] 错误处理机制正常
- [ ] 响应时间可接受

## 7. 🛠️ 故障排除

### 常见问题解决

#### Nginx配置错误
```bash
# 检查配置语法
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 重新加载配置
sudo systemctl reload nginx
```

#### 前端页面无法加载
```bash
# 检查文件权限
ls -la /opt/ai-platform/frontend/portal/build/

# 修复权限
sudo chown -R www-data:www-data /opt/ai-platform/frontend/
```

#### API代理失败
```bash
# 检查后端服务
curl http://127.0.0.1:8000/api/

# 检查Nginx代理配置
sudo nginx -T | grep -A 10 "location /api/"
```

### 性能优化
```bash
# 启用Gzip压缩
sudo tee -a /etc/nginx/sites-available/ai-platform << 'EOF'

# Gzip 压缩配置
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_proxied any;
gzip_comp_level 6;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/json
    application/javascript
    application/xml+rss
    application/atom+xml
    image/svg+xml;
EOF

sudo systemctl reload nginx
```

## 📝 总结

完成前端部署后，您将拥有：

- ✅ 现代化的用户门户界面
- ✅ 完整的管理后台系统
- ✅ 高性能的Nginx反向代理
- ✅ 静态文件服务优化
- ✅ API集成和测试界面

### 下一步
继续进行 [API集成测试](./03_api_integration.md)

---
*文档创建时间: 2025年1月*  
*适用系统: Ubuntu 24.04 LTS*  
*Node.js版本: 20 LTS*
