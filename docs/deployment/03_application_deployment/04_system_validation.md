# 🔍 AI中台 - 系统验证与测试 (Ubuntu 24.04 LTS)

## 📋 文档概述

本文档提供AI中台应用部署后的系统验证和测试程序，确保整个平台的可靠性、性能和安全性。

> **⏱️ 预计验证时间**: 2-3小时  
> **🎯 部署目标**: 全系统功能验证和性能测试

## 🎯 验证目标

### ✅ 核心功能验证
- Django应用完整性测试
- 四大平台API功能验证
- 数据库连接和操作测试
- 用户认证和权限验证

### ✅ 性能验证
- API响应时间测试
- 并发用户负载测试
- 数据库性能基准测试
- 内存和CPU使用监控

### ✅ 安全验证
- JWT令牌安全测试
- API访问控制验证
- 数据传输加密测试
- 防护机制验证

## 📋 系统验证检查清单

### 1️⃣ 基础环境验证

```bash
# 创建验证脚本目录
mkdir -p ~/ai_platform_validation
cd ~/ai_platform_validation

# 创建环境验证脚本
cat > environment_check.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台基础环境验证脚本
验证系统环境和依赖项
"""

import sys
import subprocess
import requests
import json
from datetime import datetime
import os
import psutil

class EnvironmentValidator:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {'passed': 0, 'failed': 0}
        }
    
    def log_test(self, test_name, status, details=""):
        """记录测试结果"""
        result = {
            'test': test_name,
            'status': 'PASS' if status else 'FAIL',
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results['tests'].append(result)
        
        if status:
            self.results['summary']['passed'] += 1
            print(f"✅ {test_name}: PASS")
        else:
            self.results['summary']['failed'] += 1
            print(f"❌ {test_name}: FAIL - {details}")
        
        if details:
            print(f"   详情: {details}")
    
    def check_python_version(self):
        """检查Python版本"""
        version = sys.version_info
        required_version = (3, 10)
        
        if version >= required_version:
            self.log_test(
                "Python版本检查", 
                True, 
                f"Python {version.major}.{version.minor}.{version.micro}"
            )
        else:
            self.log_test(
                "Python版本检查", 
                False, 
                f"需要Python 3.10，当前: {version.major}.{version.minor}"
            )
    
    def check_system_resources(self):
        """检查系统资源"""
        # 检查内存
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        
        if memory_gb >= 4:
            self.log_test(
                "系统内存检查", 
                True, 
                f"可用内存: {memory_gb:.1f}GB"
            )
        else:
            self.log_test(
                "系统内存检查", 
                False, 
                f"内存不足，建议4GB+，当前: {memory_gb:.1f}GB"
            )
        
        # 检查磁盘空间
        disk = psutil.disk_usage('/')
        disk_gb = disk.free / (1024**3)
        
        if disk_gb >= 10:
            self.log_test(
                "磁盘空间检查", 
                True, 
                f"可用空间: {disk_gb:.1f}GB"
            )
        else:
            self.log_test(
                "磁盘空间检查", 
                False, 
                f"磁盘空间不足，建议10GB+，当前: {disk_gb:.1f}GB"
            )
    
    def check_services(self):
        """检查关键服务状态"""
        services = [
            ('postgresql', 'PostgreSQL数据库'),
            ('nginx', 'Nginx Web服务器'),
            ('redis-server', 'Redis缓存服务')
        ]
        
        for service, name in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip() == 'active':
                    self.log_test(f"{name}服务状态", True, "服务运行正常")
                else:
                    self.log_test(f"{name}服务状态", False, "服务未启动或异常")
            except Exception as e:
                self.log_test(f"{name}服务状态", False, str(e))
    
    def check_network_connectivity(self):
        """检查网络连接"""
        try:
            response = requests.get('http://localhost:8000/health/', timeout=10)
            if response.status_code == 200:
                self.log_test("Django应用连接", True, "应用响应正常")
            else:
                self.log_test("Django应用连接", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("Django应用连接", False, str(e))
        
        try:
            response = requests.get('http://localhost/admin/', timeout=10)
            if response.status_code in [200, 302]:
                self.log_test("Nginx代理连接", True, "代理服务正常")
            else:
                self.log_test("Nginx代理连接", False, f"HTTP状态码: {response.status_code}")
        except Exception as e:
            self.log_test("Nginx代理连接", False, str(e))
    
    def run_all_tests(self):
        """运行所有验证测试"""
        print("🔍 开始AI中台基础环境验证...")
        print("=" * 50)
        
        self.check_python_version()
        self.check_system_resources()
        self.check_services()
        self.check_network_connectivity()
        
        print("\n" + "=" * 50)
        print(f"📊 验证完成 - 通过: {self.results['summary']['passed']}, 失败: {self.results['summary']['failed']}")
        
        # 保存结果
        with open('environment_validation_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return self.results['summary']['failed'] == 0

if __name__ == "__main__":
    validator = EnvironmentValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)
EOF

# 运行环境验证
python3 environment_check.py
```

### 2️⃣ 数据库验证

```bash
# 创建数据库验证脚本
cat > database_validation.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台数据库验证脚本
验证数据库连接、表结构和数据完整性
"""

import os
import sys
import django
import json
from datetime import datetime

# 设置Django环境
sys.path.append('/opt/ai_platform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User
from django.apps import apps

class DatabaseValidator:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {'passed': 0, 'failed': 0}
        }
    
    def log_test(self, test_name, status, details=""):
        """记录测试结果"""
        result = {
            'test': test_name,
            'status': 'PASS' if status else 'FAIL',
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results['tests'].append(result)
        
        if status:
            self.results['summary']['passed'] += 1
            print(f"✅ {test_name}: PASS")
        else:
            self.results['summary']['failed'] += 1
            print(f"❌ {test_name}: FAIL - {details}")
        
        if details:
            print(f"   详情: {details}")
    
    def check_database_connection(self):
        """检查数据库连接"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.log_test("数据库连接", True, f"PostgreSQL版本: {version}")
        except Exception as e:
            self.log_test("数据库连接", False, str(e))
    
    def check_migrations(self):
        """检查数据库迁移状态"""
        try:
            from django.core.management import execute_from_command_line
            from io import StringIO
            import contextlib
            
            # 捕获迁移检查输出
            output = StringIO()
            with contextlib.redirect_stdout(output):
                execute_from_command_line(['manage.py', 'showmigrations', '--plan'])
            
            migrations_output = output.getvalue()
            unapplied_count = migrations_output.count('[ ]')
            applied_count = migrations_output.count('[X]')
            
            if unapplied_count == 0:
                self.log_test(
                    "数据库迁移状态", 
                    True, 
                    f"所有迁移已应用 ({applied_count}个)"
                )
            else:
                self.log_test(
                    "数据库迁移状态", 
                    False, 
                    f"有{unapplied_count}个未应用的迁移"
                )
        except Exception as e:
            self.log_test("数据库迁移状态", False, str(e))
    
    def check_models(self):
        """检查模型完整性"""
        core_models = [
            'auth.User',
            'algorithm_platform.Algorithm',
            'data_platform.Dataset', 
            'model_platform.Model',
            'service_platform.Service'
        ]
        
        for model_path in core_models:
            try:
                model = apps.get_model(model_path)
                count = model.objects.count()
                self.log_test(
                    f"模型 {model_path}", 
                    True, 
                    f"表存在，记录数: {count}"
                )
            except Exception as e:
                self.log_test(f"模型 {model_path}", False, str(e))
    
    def check_admin_user(self):
        """检查管理员用户"""
        try:
            admin_users = User.objects.filter(is_superuser=True)
            if admin_users.exists():
                self.log_test(
                    "管理员用户", 
                    True, 
                    f"发现{admin_users.count()}个管理员用户"
                )
            else:
                self.log_test("管理员用户", False, "未找到管理员用户")
        except Exception as e:
            self.log_test("管理员用户", False, str(e))
    
    def check_database_performance(self):
        """检查数据库性能"""
        try:
            import time
            
            # 测试简单查询性能
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user;")
                result = cursor.fetchone()
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            if query_time < 100:  # 小于100ms
                self.log_test(
                    "数据库查询性能", 
                    True, 
                    f"查询时间: {query_time:.2f}ms"
                )
            else:
                self.log_test(
                    "数据库查询性能", 
                    False, 
                    f"查询时间过长: {query_time:.2f}ms"
                )
        except Exception as e:
            self.log_test("数据库查询性能", False, str(e))
    
    def run_all_tests(self):
        """运行所有数据库验证测试"""
        print("🗄️ 开始AI中台数据库验证...")
        print("=" * 50)
        
        self.check_database_connection()
        self.check_migrations()
        self.check_models()
        self.check_admin_user()
        self.check_database_performance()
        
        print("\n" + "=" * 50)
        print(f"📊 验证完成 - 通过: {self.results['summary']['passed']}, 失败: {self.results['summary']['failed']}")
        
        # 保存结果
        with open('database_validation_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return self.results['summary']['failed'] == 0

if __name__ == "__main__":
    validator = DatabaseValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)
EOF

# 运行数据库验证
python3 database_validation.py
```

### 3️⃣ API功能验证

```bash
# 创建API功能验证脚本
cat > api_validation.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台API功能验证脚本
验证所有API端点的功能和性能
"""

import requests
import json
import time
from datetime import datetime
import concurrent.futures
import statistics

class APIValidator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'performance': [],
            'summary': {'passed': 0, 'failed': 0}
        }
    
    def log_test(self, test_name, status, details=""):
        """记录测试结果"""
        result = {
            'test': test_name,
            'status': 'PASS' if status else 'FAIL',
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results['tests'].append(result)
        
        if status:
            self.results['summary']['passed'] += 1
            print(f"✅ {test_name}: PASS")
        else:
            self.results['summary']['failed'] += 1
            print(f"❌ {test_name}: FAIL - {details}")
        
        if details:
            print(f"   详情: {details}")
    
    def log_performance(self, endpoint, response_time, status_code):
        """记录性能数据"""
        perf_data = {
            'endpoint': endpoint,
            'response_time_ms': response_time,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
        self.results['performance'].append(perf_data)
    
    def authenticate(self):
        """获取JWT令牌"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/token/",
                json={
                    "username": "admin",
                    "password": "admin123"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                self.log_test("JWT认证", True, "成功获取访问令牌")
                return True
            else:
                self.log_test("JWT认证", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("JWT认证", False, str(e))
            return False
    
    def test_endpoint(self, endpoint, method="GET", data=None):
        """测试单个API端点"""
        try:
            start_time = time.time()
            
            if method == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}")
            elif method == "POST":
                response = self.session.post(f"{self.base_url}{endpoint}", json=data)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            self.log_performance(endpoint, response_time, response.status_code)
            
            if response.status_code in [200, 201]:
                self.log_test(
                    f"API {endpoint}", 
                    True, 
                    f"响应时间: {response_time:.2f}ms"
                )
                return True
            else:
                self.log_test(
                    f"API {endpoint}", 
                    False, 
                    f"HTTP状态码: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(f"API {endpoint}", False, str(e))
            return False
    
    def test_core_apis(self):
        """测试核心API端点"""
        core_endpoints = [
            "/health/",
            "/api/algorithm/",
            "/api/data/", 
            "/api/model/",
            "/api/service/",
            "/api/auth/user/",
            "/admin/",
            "/swagger/",
            "/redoc/"
        ]
        
        for endpoint in core_endpoints:
            self.test_endpoint(endpoint)
    
    def test_crud_operations(self):
        """测试CRUD操作"""
        # 测试创建操作
        test_data = {
            "name": "测试算法",
            "description": "API验证测试算法",
            "version": "1.0.0"
        }
        
        # 尝试创建
        if self.test_endpoint("/api/algorithm/", "POST", test_data):
            # 测试列表查询
            self.test_endpoint("/api/algorithm/")
    
    def test_performance_benchmarks(self):
        """执行性能基准测试"""
        endpoint = "/api/algorithm/"
        test_count = 10
        
        response_times = []
        
        for i in range(test_count):
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append((end_time - start_time) * 1000)
            except:
                continue
        
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            if avg_time < 200:  # 平均响应时间小于200ms
                self.log_test(
                    "API性能基准测试", 
                    True, 
                    f"平均响应时间: {avg_time:.2f}ms (最小: {min_time:.2f}ms, 最大: {max_time:.2f}ms)"
                )
            else:
                self.log_test(
                    "API性能基准测试", 
                    False, 
                    f"平均响应时间过长: {avg_time:.2f}ms"
                )
        else:
            self.log_test("API性能基准测试", False, "无法获取有效的响应时间数据")
    
    def test_concurrent_access(self):
        """测试并发访问"""
        endpoint = "/api/algorithm/"
        concurrent_users = 5
        
        def make_request():
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                return response.status_code == 200
            except:
                return False
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrent_users)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            success_count = sum(results)
            if success_count >= concurrent_users * 0.8:  # 80%成功率
                self.log_test(
                    "并发访问测试", 
                    True, 
                    f"{success_count}/{concurrent_users} 请求成功"
                )
            else:
                self.log_test(
                    "并发访问测试", 
                    False, 
                    f"成功率过低: {success_count}/{concurrent_users}"
                )
        except Exception as e:
            self.log_test("并发访问测试", False, str(e))
    
    def run_all_tests(self):
        """运行所有API验证测试"""
        print("🔗 开始AI中台API功能验证...")
        print("=" * 50)
        
        if not self.authenticate():
            print("❌ 认证失败，跳过需要认证的测试")
        
        self.test_core_apis()
        self.test_crud_operations()
        self.test_performance_benchmarks()
        self.test_concurrent_access()
        
        print("\n" + "=" * 50)
        print(f"📊 验证完成 - 通过: {self.results['summary']['passed']}, 失败: {self.results['summary']['failed']}")
        
        # 保存结果
        with open('api_validation_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return self.results['summary']['failed'] == 0

if __name__ == "__main__":
    validator = APIValidator()
    success = validator.run_all_tests()
    
    # 生成性能报告
    if validator.results['performance']:
        print("\n📈 API性能统计:")
        endpoints = {}
        for perf in validator.results['performance']:
            endpoint = perf['endpoint']
            if endpoint not in endpoints:
                endpoints[endpoint] = []
            endpoints[endpoint].append(perf['response_time_ms'])
        
        for endpoint, times in endpoints.items():
            avg_time = statistics.mean(times)
            print(f"   {endpoint}: 平均 {avg_time:.2f}ms")
    
    import sys
    sys.exit(0 if success else 1)
EOF

# 运行API验证
python3 api_validation.py
```

### 4️⃣ 前端验证

```bash
# 创建前端验证脚本
cat > frontend_validation.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台前端验证脚本
验证前端界面和用户交互功能
"""

import requests
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class FrontendValidator:
    def __init__(self, base_url="http://localhost"):
        self.base_url = base_url
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {'passed': 0, 'failed': 0}
        }
        self.driver = None
    
    def log_test(self, test_name, status, details=""):
        """记录测试结果"""
        result = {
            'test': test_name,
            'status': 'PASS' if status else 'FAIL',
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results['tests'].append(result)
        
        if status:
            self.results['summary']['passed'] += 1
            print(f"✅ {test_name}: PASS")
        else:
            self.results['summary']['failed'] += 1
            print(f"❌ {test_name}: FAIL - {details}")
        
        if details:
            print(f"   详情: {details}")
    
    def setup_driver(self):
        """设置Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # 无头模式
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.log_test("WebDriver初始化", True, "Chrome WebDriver已启动")
            return True
        except Exception as e:
            self.log_test("WebDriver初始化", False, str(e))
            return False
    
    def test_static_pages(self):
        """测试静态页面可访问性"""
        pages = [
            ("/", "主页"),
            ("/admin/", "管理后台"),
            ("/portal/", "用户门户"),
            ("/swagger/", "API文档"),
            ("/redoc/", "ReDoc文档")
        ]
        
        for path, name in pages:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                if response.status_code in [200, 302]:
                    self.log_test(f"{name}页面访问", True, f"HTTP状态码: {response.status_code}")
                else:
                    self.log_test(f"{name}页面访问", False, f"HTTP状态码: {response.status_code}")
            except Exception as e:
                self.log_test(f"{name}页面访问", False, str(e))
    
    def test_admin_interface(self):
        """测试Django管理界面"""
        if not self.driver:
            return
        
        try:
            self.driver.get(f"{self.base_url}/admin/")
            
            # 检查登录页面是否加载
            wait = WebDriverWait(self.driver, 10)
            login_form = wait.until(
                EC.presence_of_element_located((By.ID, "login-form"))
            )
            
            if login_form:
                self.log_test("Django管理界面加载", True, "登录页面正常显示")
                
                # 尝试登录
                username_field = self.driver.find_element(By.NAME, "username")
                password_field = self.driver.find_element(By.NAME, "password")
                
                username_field.send_keys("admin")
                password_field.send_keys("admin123")
                
                # 点击登录按钮
                login_button = self.driver.find_element(By.XPATH, "//input[@type='submit']")
                login_button.click()
                
                # 等待页面跳转
                time.sleep(2)
                
                # 检查是否成功登录
                if "Django 管理" in self.driver.title or "Django administration" in self.driver.title:
                    self.log_test("Django管理界面登录", True, "成功登录管理后台")
                else:
                    self.log_test("Django管理界面登录", False, "登录失败或页面异常")
            
        except Exception as e:
            self.log_test("Django管理界面测试", False, str(e))
    
    def test_user_portal(self):
        """测试用户门户界面"""
        if not self.driver:
            return
        
        try:
            self.driver.get(f"{self.base_url}/portal/")
            
            # 检查页面标题
            if "AI中台" in self.driver.title:
                self.log_test("用户门户加载", True, "页面标题正确")
            else:
                self.log_test("用户门户加载", False, f"页面标题异常: {self.driver.title}")
            
            # 检查关键元素
            try:
                navigation = self.driver.find_element(By.CLASS_NAME, "navigation")
                self.log_test("用户门户导航", True, "导航栏元素存在")
            except:
                self.log_test("用户门户导航", False, "未找到导航栏元素")
            
            try:
                main_content = self.driver.find_element(By.CLASS_NAME, "main-content")
                self.log_test("用户门户内容", True, "主要内容区域存在")
            except:
                self.log_test("用户门户内容", False, "未找到主要内容区域")
                
        except Exception as e:
            self.log_test("用户门户测试", False, str(e))
    
    def test_api_documentation(self):
        """测试API文档界面"""
        if not self.driver:
            return
        
        # 测试Swagger UI
        try:
            self.driver.get(f"{self.base_url}/swagger/")
            
            wait = WebDriverWait(self.driver, 10)
            swagger_ui = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "swagger-ui"))
            )
            
            if swagger_ui:
                self.log_test("Swagger UI加载", True, "Swagger界面正常显示")
            
        except Exception as e:
            self.log_test("Swagger UI测试", False, str(e))
        
        # 测试ReDoc
        try:
            self.driver.get(f"{self.base_url}/redoc/")
            
            wait = WebDriverWait(self.driver, 10)
            redoc_container = wait.until(
                EC.presence_of_element_located((By.ID, "redoc-container"))
            )
            
            if redoc_container:
                self.log_test("ReDoc界面加载", True, "ReDoc界面正常显示")
                
        except Exception as e:
            self.log_test("ReDoc界面测试", False, str(e))
    
    def test_responsive_design(self):
        """测试响应式设计"""
        if not self.driver:
            return
        
        viewports = [
            (1920, 1080, "桌面"),
            (768, 1024, "平板"),
            (375, 667, "手机")
        ]
        
        for width, height, device in viewports:
            try:
                self.driver.set_window_size(width, height)
                self.driver.get(f"{self.base_url}/portal/")
                
                # 等待页面加载
                time.sleep(2)
                
                # 检查页面是否正常显示
                body = self.driver.find_element(By.TAG_NAME, "body")
                if body.is_displayed():
                    self.log_test(f"{device}响应式设计", True, f"分辨率{width}x{height}正常显示")
                else:
                    self.log_test(f"{device}响应式设计", False, "页面显示异常")
                    
            except Exception as e:
                self.log_test(f"{device}响应式设计", False, str(e))
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
    
    def run_all_tests(self):
        """运行所有前端验证测试"""
        print("🎨 开始AI中台前端验证...")
        print("=" * 50)
        
        # 基础页面测试
        self.test_static_pages()
        
        # 如果可以设置WebDriver，则进行更详细的测试
        if self.setup_driver():
            self.test_admin_interface()
            self.test_user_portal()
            self.test_api_documentation()
            self.test_responsive_design()
            self.cleanup()
        else:
            print("⚠️ 无法初始化WebDriver，跳过浏览器自动化测试")
        
        print("\n" + "=" * 50)
        print(f"📊 验证完成 - 通过: {self.results['summary']['passed']}, 失败: {self.results['summary']['failed']}")
        
        # 保存结果
        with open('frontend_validation_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return self.results['summary']['failed'] == 0

if __name__ == "__main__":
    validator = FrontendValidator()
    success = validator.run_all_tests()
    
    import sys
    sys.exit(0 if success else 1)
EOF

# 如果需要浏览器测试，安装Selenium和Chrome
echo "如果需要完整的前端测试，请安装Selenium："
echo "pip install selenium"
echo "并确保已安装Chrome浏览器和ChromeDriver"

# 运行前端验证（不包含浏览器自动化）
python3 frontend_validation.py
```

### 5️⃣ 综合系统验证

```bash
# 创建综合验证脚本
cat > system_validation.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台综合系统验证脚本
执行所有验证测试并生成综合报告
"""

import subprocess
import json
import os
from datetime import datetime
import time

class SystemValidator:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'validation_modules': [],
            'summary': {
                'total_tests': 0,
                'total_passed': 0,
                'total_failed': 0,
                'success_rate': 0
            }
        }
    
    def run_validation_module(self, module_name, script_file):
        """运行单个验证模块"""
        print(f"\n🔍 执行 {module_name} 验证...")
        print("-" * 40)
        
        try:
            # 运行验证脚本
            result = subprocess.run(
                ['python3', script_file],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 尝试读取结果文件
            result_file = script_file.replace('.py', '_results.json')
            module_results = None
            
            if os.path.exists(result_file):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        module_results = json.load(f)
                except:
                    pass
            
            module_data = {
                'module': module_name,
                'script': script_file,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0,
                'results': module_results,
                'timestamp': datetime.now().isoformat()
            }
            
            self.results['validation_modules'].append(module_data)
            
            if module_results:
                self.results['summary']['total_tests'] += module_results['summary']['passed'] + module_results['summary']['failed']
                self.results['summary']['total_passed'] += module_results['summary']['passed']
                self.results['summary']['total_failed'] += module_results['summary']['failed']
            
            if result.returncode == 0:
                print(f"✅ {module_name} 验证完成")
            else:
                print(f"❌ {module_name} 验证失败")
                if result.stderr:
                    print(f"错误信息: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {module_name} 验证超时")
            module_data = {
                'module': module_name,
                'script': script_file,
                'exit_code': -1,
                'success': False,
                'error': 'Validation timeout',
                'timestamp': datetime.now().isoformat()
            }
            self.results['validation_modules'].append(module_data)
        
        except Exception as e:
            print(f"💥 {module_name} 验证异常: {str(e)}")
            module_data = {
                'module': module_name,
                'script': script_file,
                'exit_code': -1,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.results['validation_modules'].append(module_data)
    
    def generate_html_report(self):
        """生成HTML验证报告"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI中台系统验证报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
        }}
        .summary-card .number {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
        .modules {{
            padding: 30px;
        }}
        .module {{
            margin-bottom: 30px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }}
        .module-header {{
            padding: 15px 20px;
            background: #e9ecef;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .module-header h3 {{
            margin: 0;
        }}
        .status-badge {{
            padding: 4px 12px;
            border-radius: 4px;
            color: white;
            font-size: 0.9em;
        }}
        .status-success {{ background-color: #28a745; }}
        .status-error {{ background-color: #dc3545; }}
        .module-content {{
            padding: 20px;
        }}
        .test-results {{
            margin-top: 15px;
        }}
        .test-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f8f9fa;
        }}
        .test-item:last-child {{
            border-bottom: none;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 AI中台系统验证报告</h1>
            <p>验证时间: {self.results['timestamp']}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>总测试数</h3>
                <div class="number">{self.results['summary']['total_tests']}</div>
            </div>
            <div class="summary-card">
                <h3>通过测试</h3>
                <div class="number success">{self.results['summary']['total_passed']}</div>
            </div>
            <div class="summary-card">
                <h3>失败测试</h3>
                <div class="number danger">{self.results['summary']['total_failed']}</div>
            </div>
            <div class="summary-card">
                <h3>成功率</h3>
                <div class="number {'success' if self.results['summary']['success_rate'] >= 90 else 'warning' if self.results['summary']['success_rate'] >= 70 else 'danger'}">{self.results['summary']['success_rate']:.1f}%</div>
            </div>
        </div>
        
        <div class="modules">
            <h2>验证模块详情</h2>
"""
        
        for module in self.results['validation_modules']:
            status_class = "status-success" if module['success'] else "status-error"
            status_text = "通过" if module['success'] else "失败"
            
            html_content += f"""
            <div class="module">
                <div class="module-header">
                    <h3>{module['module']}</h3>
                    <span class="status-badge {status_class}">{status_text}</span>
                </div>
                <div class="module-content">
                    <p><strong>脚本:</strong> {module['script']}</p>
                    <p><strong>退出代码:</strong> {module['exit_code']}</p>
                    <p><strong>执行时间:</strong> {module['timestamp']}</p>
"""
            
            if module.get('results') and module['results'].get('tests'):
                html_content += """
                    <div class="test-results">
                        <h4>测试结果详情:</h4>
"""
                for test in module['results']['tests']:
                    status_icon = "✅" if test['status'] == 'PASS' else "❌"
                    html_content += f"""
                        <div class="test-item">
                            <span>{status_icon} {test['test']}</span>
                            <span>{test['status']}</span>
                        </div>
"""
                html_content += "</div>"
            
            if module.get('error'):
                html_content += f"""
                    <div style="background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin-top: 10px;">
                        <strong>错误:</strong> {module['error']}
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="timestamp">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        with open('system_validation_report.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("📄 HTML验证报告已生成: system_validation_report.html")
    
    def run_all_validations(self):
        """运行所有系统验证"""
        print("🚀 开始AI中台综合系统验证...")
        print("=" * 60)
        
        validation_modules = [
            ("基础环境验证", "environment_check.py"),
            ("数据库验证", "database_validation.py"),
            ("API功能验证", "api_validation.py"),
            ("前端验证", "frontend_validation.py")
        ]
        
        start_time = time.time()
        
        for module_name, script_file in validation_modules:
            if os.path.exists(script_file):
                self.run_validation_module(module_name, script_file)
            else:
                print(f"⚠️ 跳过 {module_name} - 脚本文件不存在: {script_file}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 计算成功率
        if self.results['summary']['total_tests'] > 0:
            self.results['summary']['success_rate'] = (
                self.results['summary']['total_passed'] / 
                self.results['summary']['total_tests'] * 100
            )
        
        print("\n" + "=" * 60)
        print("📊 综合验证完成")
        print(f"⏱️ 总用时: {total_time:.1f}秒")
        print(f"📈 成功率: {self.results['summary']['success_rate']:.1f}%")
        print(f"✅ 通过测试: {self.results['summary']['total_passed']}")
        print(f"❌ 失败测试: {self.results['summary']['total_failed']}")
        
        # 生成报告
        with open('system_validation_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.generate_html_report()
        
        # 输出建议
        if self.results['summary']['success_rate'] >= 95:
            print("\n🎉 系统验证优秀！AI中台已准备好投入使用。")
        elif self.results['summary']['success_rate'] >= 80:
            print("\n👍 系统验证良好，建议检查失败的测试项目。")
        else:
            print("\n⚠️ 系统验证存在问题，请检查并修复失败的测试项目后重新验证。")
        
        return self.results['summary']['success_rate'] >= 80

if __name__ == "__main__":
    validator = SystemValidator()
    success = validator.run_all_validations()
    
    import sys
    sys.exit(0 if success else 1)
EOF

# 运行综合系统验证
python3 system_validation.py
```

## 📋 验证报告查看

```bash
# 查看验证结果
echo "📄 验证报告文件:"
ls -la *validation_results.json system_validation_report.html 2>/dev/null || echo "暂无验证报告文件"

# 如果有HTML报告，在浏览器中打开
if [ -f "system_validation_report.html" ]; then
    echo "🌐 在浏览器中查看详细报告:"
    echo "file://$(pwd)/system_validation_report.html"
fi

# 显示快速摘要
if [ -f "system_validation_results.json" ]; then
    echo "📊 验证结果摘要:"
    python3 -c "
import json
with open('system_validation_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    summary = data['summary']
    print(f'总测试数: {summary[\"total_tests\"]}')
    print(f'通过测试: {summary[\"total_passed\"]}')
    print(f'失败测试: {summary[\"total_failed\"]}')
    print(f'成功率: {summary[\"success_rate\"]:.1f}%')
"
fi
```

## 🔧 故障排除

### 常见问题解决

1. **数据库连接失败**
   ```bash
   # 检查PostgreSQL服务状态
   sudo systemctl status postgresql
   
   # 重启数据库服务
   sudo systemctl restart postgresql
   ```

2. **API响应超时**
   ```bash
   # 检查Django应用状态
   sudo systemctl status ai_platform
   
   # 查看应用日志
   sudo journalctl -u ai_platform -f
   ```

3. **前端页面无法访问**
   ```bash
   # 检查Nginx服务状态
   sudo systemctl status nginx
   
   # 重新加载Nginx配置
   sudo nginx -t && sudo systemctl reload nginx
   ```

## 📚 相关文档

- [AI中台部署概览](../deployment_overview.md)
- [后端应用部署](01_backend_deployment.md)
- [前端应用部署](02_frontend_deployment.md)
- [API集成测试](03_api_integration.md)
- [部署检查清单](05_deployment_checklist.md)

---

> **📝 注意**: 本文档基于Ubuntu 24.04 LTS环境编写，其他Linux发行版可能需要适当调整命令。
