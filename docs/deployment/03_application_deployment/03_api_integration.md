# ⭐ AI中台 - API集成测试指南 (Ubuntu 24.04 LTS)

本文档指导如何进行AI中台API系统的集成测试，确保前后端协作正常，API功能完整可用。

> **⚠️ 重要提示**: 请确保后端和前端应用都已成功部署并正常运行。

## ⏱️ 预计测试时间
- **环境验证**: 15分钟
- **基础API测试**: 30分钟  
- **认证系统测试**: 30分钟
- **平台API测试**: 45分钟
- **性能基线测试**: 30分钟
- **总计**: 2.5-3小时

## 🎯 测试目标
✅ 四大平台API功能验证  
✅ JWT认证系统完整性  
✅ API文档可用性测试  
✅ 错误处理机制验证  
✅ 性能基线建立

## 📋 前置条件检查

```bash
# 1. 验证后端服务
curl -f http://127.0.0.1:8000/admin/ && echo "✅ 后端服务正常"

# 2. 验证前端服务
curl -f http://localhost/ && echo "✅ 前端服务正常"

# 3. 验证数据库连接
cd /opt/ai-platform/backend
source /opt/ai-platform/ai-platform-env/bin/activate
python manage.py check

# 4. 验证必要工具
python -c "import requests, json; print('✅ 测试工具就绪')"
```

## 1. 📋 基础API测试

### 1.1 创建综合API测试脚本
```bash
cd /opt/ai-platform
cat > api_integration_test.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台API集成测试套件
"""
import requests
import json
import time
import sys
from datetime import datetime

class APITester:
    def __init__(self, base_url='http://localhost'):
        self.base_url = base_url
        self.api_url = f'{base_url}/api'
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_test(self, test_name, status, details=''):
        """记录测试结果"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        status_icon = '✅' if status else '❌'
        print(f"[{timestamp}] {status_icon} {test_name}")
        
        if details:
            print(f"    {details}")
        
        if status:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {details}")
        
        print()
    
    def test_server_health(self):
        """测试服务器健康状态"""
        print("🔍 1. 服务器健康状态测试")
        print("=" * 40)
        
        # 测试前端页面
        try:
            response = self.session.get(self.base_url, timeout=10)
            self.log_test("前端页面访问", 
                         response.status_code == 200,
                         f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("前端页面访问", False, f"错误: {e}")
        
        # 测试管理后台
        try:
            response = self.session.get(f'{self.base_url}/admin/', timeout=10)
            self.log_test("管理后台访问", 
                         response.status_code == 200,
                         f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("管理后台访问", False, f"错误: {e}")
        
        # 测试API文档
        for doc_type in ['swagger', 'redoc']:
            try:
                response = self.session.get(f'{self.base_url}/{doc_type}/', timeout=10)
                self.log_test(f"{doc_type.upper()}文档访问", 
                             response.status_code == 200,
                             f"状态码: {response.status_code}")
            except Exception as e:
                self.log_test(f"{doc_type.upper()}文档访问", False, f"错误: {e}")
    
    def test_authentication(self):
        """测试认证系统"""
        print("🔐 2. 认证系统测试")
        print("=" * 40)
        
        # 测试用户注册
        test_user = {
            'username': f'testuser_{int(time.time())}',
            'email': f'test_{int(time.time())}@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        try:
            response = self.session.post(
                f'{self.api_url}/auth/register/', 
                json=test_user,
                timeout=10
            )
            self.log_test("用户注册", 
                         response.status_code in [200, 201],
                         f"状态码: {response.status_code}")
            
            if response.status_code in [200, 201]:
                self.test_user = test_user
        except Exception as e:
            self.log_test("用户注册", False, f"错误: {e}")
            return
        
        # 测试用户登录
        try:
            login_data = {
                'username': test_user['username'],
                'password': test_user['password']
            }
            response = self.session.post(
                f'{self.api_url}/auth/token/', 
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access' in data:
                    self.auth_token = data['access']
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    self.log_test("用户登录", True, "JWT Token获取成功")
                else:
                    self.log_test("用户登录", False, "JWT Token未返回")
            else:
                self.log_test("用户登录", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("用户登录", False, f"错误: {e}")
        
        # 测试Token验证
        if self.auth_token:
            try:
                response = self.session.get(f'{self.api_url}/auth/me/', timeout=10)
                self.log_test("Token验证", 
                             response.status_code == 200,
                             f"状态码: {response.status_code}")
            except Exception as e:
                self.log_test("Token验证", False, f"错误: {e}")
    
    def test_platform_apis(self):
        """测试四大平台API"""
        print("🚀 3. 平台API测试")
        print("=" * 40)
        
        platforms = [
            ('data', '数据平台'),
            ('algorithm', '算法平台'),
            ('model', '模型平台'),
            ('service', '服务平台')
        ]
        
        for platform_key, platform_name in platforms:
            # 测试状态端点
            try:
                response = self.session.get(
                    f'{self.api_url}/{platform_key}/status/', 
                    timeout=10
                )
                self.log_test(f"{platform_name}状态检查", 
                             response.status_code == 200,
                             f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'status' in data:
                        self.log_test(f"{platform_name}状态响应", 
                                     data.get('status') == 'active',
                                     f"状态: {data.get('status')}")
            except Exception as e:
                self.log_test(f"{platform_name}状态检查", False, f"错误: {e}")
    
    def test_api_performance(self):
        """测试API性能"""
        print("⚡ 4. API性能测试")
        print("=" * 40)
        
        # 测试响应时间
        endpoints = [
            ('/admin/', '管理后台'),
            ('/api/data/status/', '数据平台API'),
            ('/api/algorithm/status/', '算法平台API'),
            ('/swagger/', 'Swagger文档')
        ]
        
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f'{self.base_url}{endpoint}', timeout=10)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                self.log_test(f"{name}响应时间", 
                             response_time < 2000,  # 2秒内
                             f"{response_time:.0f}ms")
            except Exception as e:
                self.log_test(f"{name}响应时间", False, f"错误: {e}")
    
    def test_error_handling(self):
        """测试错误处理"""
        print("🛡️ 5. 错误处理测试")
        print("=" * 40)
        
        # 测试404错误
        try:
            response = self.session.get(f'{self.api_url}/nonexistent/', timeout=10)
            self.log_test("404错误处理", 
                         response.status_code == 404,
                         f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("404错误处理", False, f"错误: {e}")
        
        # 测试未授权访问
        temp_headers = self.session.headers.copy()
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        
        try:
            response = self.session.get(f'{self.api_url}/auth/me/', timeout=10)
            self.log_test("未授权访问处理", 
                         response.status_code == 401,
                         f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("未授权访问处理", False, f"错误: {e}")
        
        # 恢复headers
        self.session.headers.update(temp_headers)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 AI中台API集成测试套件")
        print("=" * 50)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标服务: {self.base_url}")
        print()
        
        # 运行测试
        self.test_server_health()
        self.test_authentication()
        self.test_platform_apis()
        self.test_api_performance()
        self.test_error_handling()
        
        # 输出测试结果
        print("📊 测试结果汇总")
        print("=" * 50)
        print(f"✅ 通过: {self.test_results['passed']}")
        print(f"❌ 失败: {self.test_results['failed']}")
        print(f"📈 成功率: {self.test_results['passed']/(self.test_results['passed']+self.test_results['failed'])*100:.1f}%")
        
        if self.test_results['errors']:
            print("\n❌ 失败详情:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        print("\n🎉 测试完成!")
        
        # 返回测试结果
        return self.test_results['failed'] == 0

if __name__ == '__main__':
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
EOF

chmod +x api_integration_test.py
```

### 1.2 创建API压力测试脚本
```bash
cat > api_stress_test.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台API压力测试脚本
"""
import requests
import threading
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class StressTester:
    def __init__(self, base_url='http://localhost', max_workers=10):
        self.base_url = base_url
        self.api_url = f'{base_url}/api'
        self.max_workers = max_workers
        self.results = []
    
    def single_request(self, endpoint, request_id):
        """单个请求测试"""
        start_time = time.time()
        try:
            response = requests.get(f'{self.base_url}{endpoint}', timeout=10)
            end_time = time.time()
            
            return {
                'id': request_id,
                'endpoint': endpoint,
                'status_code': response.status_code,
                'response_time': (end_time - start_time) * 1000,
                'success': response.status_code == 200,
                'timestamp': datetime.now()
            }
        except Exception as e:
            end_time = time.time()
            return {
                'id': request_id,
                'endpoint': endpoint,
                'status_code': 0,
                'response_time': (end_time - start_time) * 1000,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def run_stress_test(self, endpoint, num_requests=50, concurrent_users=10):
        """运行压力测试"""
        print(f"🔥 压力测试: {endpoint}")
        print(f"请求数量: {num_requests}, 并发用户: {concurrent_users}")
        print("=" * 50)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # 提交所有任务
            futures = [
                executor.submit(self.single_request, endpoint, i) 
                for i in range(num_requests)
            ]
            
            # 收集结果
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                # 实时显示进度
                if len(results) % 10 == 0:
                    print(f"进度: {len(results)}/{num_requests}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析结果
        self.analyze_results(results, total_time, endpoint)
        return results
    
    def analyze_results(self, results, total_time, endpoint):
        """分析测试结果"""
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            median_response_time = statistics.median(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = median_response_time = 0
        
        success_rate = len(successful_requests) / len(results) * 100
        requests_per_second = len(results) / total_time
        
        print(f"\n📊 {endpoint} 测试结果:")
        print(f"   总请求数: {len(results)}")
        print(f"   成功请求: {len(successful_requests)}")
        print(f"   失败请求: {len(failed_requests)}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   总耗时: {total_time:.2f}秒")
        print(f"   QPS: {requests_per_second:.2f}")
        print(f"   平均响应时间: {avg_response_time:.2f}ms")
        print(f"   最小响应时间: {min_response_time:.2f}ms")
        print(f"   最大响应时间: {max_response_time:.2f}ms")
        print(f"   中位响应时间: {median_response_time:.2f}ms")
        
        if failed_requests:
            print(f"\n❌ 失败请求详情:")
            for req in failed_requests[:5]:  # 只显示前5个失败请求
                error = req.get('error', f"HTTP {req['status_code']}")
                print(f"   - 请求{req['id']}: {error}")
        
        print()

def main():
    print("🚀 AI中台API压力测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = StressTester()
    
    # 测试不同端点
    test_cases = [
        ('/', '前端首页', 30, 5),
        ('/admin/', '管理后台', 20, 3),
        ('/api/data/status/', '数据平台API', 40, 8),
        ('/api/algorithm/status/', '算法平台API', 40, 8),
        ('/swagger/', 'Swagger文档', 20, 3),
    ]
    
    for endpoint, name, requests, concurrent in test_cases:
        print(f"\n🎯 测试 {name}")
        tester.run_stress_test(endpoint, requests, concurrent)
        time.sleep(2)  # 测试间隔
    
    print("🎉 压力测试完成!")

if __name__ == '__main__':
    main()
EOF

chmod +x api_stress_test.py
```

## 2. 🔐 认证系统专项测试

### 2.1 JWT认证流程测试
```bash
cat > auth_test.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台认证系统专项测试
"""
import requests
import json
import time
from datetime import datetime, timedelta

class AuthTester:
    def __init__(self, base_url='http://localhost'):
        self.base_url = base_url
        self.api_url = f'{base_url}/api'
        self.session = requests.Session()
    
    def test_user_registration(self):
        """测试用户注册"""
        print("👤 用户注册测试")
        print("=" * 30)
        
        # 测试有效注册
        valid_user = {
            'username': f'testuser_{int(time.time())}',
            'email': f'test_{int(time.time())}@example.com',
            'password': 'ValidPass123!',
            'password_confirm': 'ValidPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        try:
            response = self.session.post(
                f'{self.api_url}/auth/register/',
                json=valid_user,
                timeout=10
            )
            print(f"✅ 有效用户注册: {response.status_code}")
            if response.status_code in [200, 201]:
                self.test_user = valid_user
                return True
            else:
                print(f"   响应: {response.text}")
        except Exception as e:
            print(f"❌ 用户注册失败: {e}")
        
        # 测试无效注册 (密码不匹配)
        invalid_user = {
            'username': f'testuser2_{int(time.time())}',
            'email': f'test2_{int(time.time())}@example.com',
            'password': 'ValidPass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        try:
            response = self.session.post(
                f'{self.api_url}/auth/register/',
                json=invalid_user,
                timeout=10
            )
            if response.status_code == 400:
                print("✅ 密码不匹配验证: 正确拒绝")
            else:
                print(f"⚠️ 密码不匹配验证: 状态码 {response.status_code}")
        except Exception as e:
            print(f"❌ 无效注册测试失败: {e}")
        
        return True
    
    def test_token_authentication(self):
        """测试Token认证"""
        print("\n🔑 Token认证测试")
        print("=" * 30)
        
        if not hasattr(self, 'test_user'):
            print("❌ 需要先完成用户注册测试")
            return False
        
        # 测试获取Token
        login_data = {
            'username': self.test_user['username'],
            'password': self.test_user['password']
        }
        
        try:
            response = self.session.post(
                f'{self.api_url}/auth/token/',
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access' in data and 'refresh' in data:
                    self.access_token = data['access']
                    self.refresh_token = data['refresh']
                    print("✅ Token获取成功")
                    print(f"   Access Token长度: {len(self.access_token)}")
                    print(f"   Refresh Token长度: {len(self.refresh_token)}")
                else:
                    print("❌ Token响应格式错误")
                    return False
            else:
                print(f"❌ Token获取失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Token获取异常: {e}")
            return False
        
        # 测试Token使用
        headers = {'Authorization': f'Bearer {self.access_token}'}
        try:
            response = self.session.get(
                f'{self.api_url}/auth/me/',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print("✅ Token验证成功")
                print(f"   用户名: {user_data.get('username')}")
                print(f"   邮箱: {user_data.get('email')}")
            else:
                print(f"❌ Token验证失败: {response.status_code}")
        except Exception as e:
            print(f"❌ Token使用异常: {e}")
        
        return True
    
    def test_token_refresh(self):
        """测试Token刷新"""
        print("\n🔄 Token刷新测试")
        print("=" * 30)
        
        if not hasattr(self, 'refresh_token'):
            print("❌ 需要先完成Token认证测试")
            return False
        
        try:
            response = self.session.post(
                f'{self.api_url}/auth/token/refresh/',
                json={'refresh': self.refresh_token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access' in data:
                    new_access_token = data['access']
                    print("✅ Token刷新成功")
                    print(f"   新Token长度: {len(new_access_token)}")
                    
                    # 验证新Token
                    headers = {'Authorization': f'Bearer {new_access_token}'}
                    verify_response = self.session.get(
                        f'{self.api_url}/auth/me/',
                        headers=headers,
                        timeout=10
                    )
                    
                    if verify_response.status_code == 200:
                        print("✅ 新Token验证成功")
                    else:
                        print("❌ 新Token验证失败")
                else:
                    print("❌ Token刷新响应格式错误")
            else:
                print(f"❌ Token刷新失败: {response.status_code}")
                print(f"   响应: {response.text}")
        except Exception as e:
            print(f"❌ Token刷新异常: {e}")
    
    def test_invalid_credentials(self):
        """测试无效凭据"""
        print("\n🛡️ 无效凭据测试")
        print("=" * 30)
        
        # 测试错误密码
        invalid_login = {
            'username': self.test_user['username'] if hasattr(self, 'test_user') else 'nonexistent',
            'password': 'WrongPassword123!'
        }
        
        try:
            response = self.session.post(
                f'{self.api_url}/auth/token/',
                json=invalid_login,
                timeout=10
            )
            
            if response.status_code == 401:
                print("✅ 错误密码验证: 正确拒绝")
            else:
                print(f"⚠️ 错误密码验证: 状态码 {response.status_code}")
        except Exception as e:
            print(f"❌ 错误密码测试失败: {e}")
        
        # 测试不存在的用户
        nonexistent_login = {
            'username': 'nonexistent_user_12345',
            'password': 'SomePassword123!'
        }
        
        try:
            response = self.session.post(
                f'{self.api_url}/auth/token/',
                json=nonexistent_login,
                timeout=10
            )
            
            if response.status_code == 401:
                print("✅ 不存在用户验证: 正确拒绝")
            else:
                print(f"⚠️ 不存在用户验证: 状态码 {response.status_code}")
        except Exception as e:
            print(f"❌ 不存在用户测试失败: {e}")
    
    def run_all_tests(self):
        """运行所有认证测试"""
        print("🔐 AI中台认证系统专项测试")
        print("=" * 50)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        success = True
        success &= self.test_user_registration()
        success &= self.test_token_authentication()
        success &= self.test_token_refresh()
        self.test_invalid_credentials()
        
        print("\n🎉 认证系统测试完成!")
        return success

if __name__ == '__main__':
    tester = AuthTester()
    tester.run_all_tests()
EOF

chmod +x auth_test.py
```

## 3. 📊 自动化测试套件

### 3.1 创建测试运行器
```bash
cat > run_all_tests.sh << 'EOF'
#!/bin/bash

echo "🧪 AI中台完整测试套件"
echo "==========================================="
date
echo ""

# 设置环境
cd /opt/ai-platform
export PYTHONPATH=/opt/ai-platform/backend:$PYTHONPATH

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果跟踪
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${YELLOW}🔍 运行测试: $test_name${NC}"
    echo "----------------------------------------"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ $test_name: 通过${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ $test_name: 失败${NC}"
        ((TESTS_FAILED++))
    fi
    
    echo ""
    sleep 2
}

# 1. 基础环境检查
echo "🔧 1. 基础环境检查"
echo "----------------------------------------"

# 检查服务状态
if curl -s http://127.0.0.1:8000/admin/ > /dev/null; then
    echo "✅ Django后端服务: 运行中"
else
    echo "❌ Django后端服务: 未运行"
    echo "请先启动后端服务: cd /opt/ai-platform/backend && ./start_server.sh"
    exit 1
fi

if curl -s http://localhost/ > /dev/null; then
    echo "✅ 前端服务: 可访问"
else
    echo "❌ 前端服务: 无法访问"
    echo "请检查Nginx配置"
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx服务: 运行中"
else
    echo "⚠️ Nginx服务: 未运行"
fi

echo ""

# 2. 运行测试套件
run_test "API集成测试" "python api_integration_test.py"
run_test "认证系统测试" "python auth_test.py"
run_test "API压力测试" "python api_stress_test.py"

# 3. Django内置测试
echo "🧪 Django内置测试"
echo "----------------------------------------"
cd /opt/ai-platform/backend
source /opt/ai-platform/ai-platform-env/bin/activate

if python manage.py test --verbosity=2; then
    echo -e "${GREEN}✅ Django单元测试: 通过${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Django单元测试: 失败${NC}"
    ((TESTS_FAILED++))
fi

echo ""

# 4. 生成测试报告
echo "📊 测试结果汇总"
echo "==========================================="
echo "测试完成时间: $(date)"
echo "通过测试: $TESTS_PASSED"
echo "失败测试: $TESTS_FAILED"
echo "总测试数: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    SUCCESS_RATE=100
else
    SUCCESS_RATE=$(( TESTS_PASSED * 100 / (TESTS_PASSED + TESTS_FAILED) ))
    echo -e "${YELLOW}⚠️ 部分测试失败，成功率: ${SUCCESS_RATE}%${NC}"
fi

# 5. 生成测试报告文件
cat > test_report.json << EOL
{
    "test_date": "$(date -Iseconds)",
    "environment": "Ubuntu 24.04 LTS",
    "total_tests": $((TESTS_PASSED + TESTS_FAILED)),
    "passed": $TESTS_PASSED,
    "failed": $TESTS_FAILED,
    "success_rate": $SUCCESS_RATE,
    "services": {
        "django_backend": "$(curl -s http://127.0.0.1:8000/admin/ > /dev/null && echo 'running' || echo 'stopped')",
        "nginx": "$(systemctl is-active nginx)",
        "frontend": "$(curl -s http://localhost/ > /dev/null && echo 'accessible' || echo 'inaccessible')"
    }
}
EOL

echo ""
echo "📋 详细报告已保存到: test_report.json"
echo ""

# 返回适当的退出代码
if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
EOF

chmod +x run_all_tests.sh
```

## 4. 🚀 运行完整测试

### 4.1 执行测试套件
```bash
# 运行完整测试套件
./run_all_tests.sh

# 或者单独运行各个测试
echo "运行基础API测试..."
python api_integration_test.py

echo "运行认证系统测试..."
python auth_test.py

echo "运行压力测试..."
python api_stress_test.py
```

### 4.2 查看测试报告
```bash
# 查看JSON格式测试报告
cat test_report.json | python -m json.tool

# 创建可读的测试报告
cat > generate_test_report.py << 'EOF'
#!/usr/bin/env python3
"""
生成可读的测试报告
"""
import json
from datetime import datetime

def generate_html_report():
    """生成HTML测试报告"""
    try:
        with open('test_report.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ 未找到测试报告文件，请先运行测试")
        return
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI中台测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        .header {{ text-align: center; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; border-radius: 5px; text-align: center; }}
        .success {{ background-color: #d4edda; color: #155724; }}
        .warning {{ background-color: #fff3cd; color: #856404; }}
        .danger {{ background-color: #f8d7da; color: #721c24; }}
        .info {{ background-color: #d1ecf1; color: #0c5460; }}
        .service-status {{ margin: 10px 0; padding: 10px; border-left: 4px solid #007bff; }}
        .running {{ border-left-color: #28a745; }}
        .stopped {{ border-left-color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 AI中台系统测试报告</h1>
            <p>测试时间: {data['test_date']}</p>
            <p>测试环境: {data['environment']}</p>
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <div class="metric {'success' if data['success_rate'] == 100 else 'warning' if data['success_rate'] >= 80 else 'danger'}">
                <h3>总体成功率</h3>
                <h2>{data['success_rate']}%</h2>
            </div>
            
            <div class="metric info">
                <h3>总测试数</h3>
                <h2>{data['total_tests']}</h2>
            </div>
            
            <div class="metric success">
                <h3>通过测试</h3>
                <h2>{data['passed']}</h2>
            </div>
            
            <div class="metric {'danger' if data['failed'] > 0 else 'success'}">
                <h3>失败测试</h3>
                <h2>{data['failed']}</h2>
            </div>
        </div>
        
        <div>
            <h3>🔧 服务状态</h3>
"""
    
    for service, status in data['services'].items():
        status_class = 'running' if status in ['running', 'active', 'accessible'] else 'stopped'
        status_icon = '✅' if status in ['running', 'active', 'accessible'] else '❌'
        service_name = {
            'django_backend': 'Django后端',
            'nginx': 'Nginx服务',
            'frontend': '前端服务'
        }.get(service, service)
        
        html_content += f"""
            <div class="service-status {status_class}">
                {status_icon} <strong>{service_name}</strong>: {status}
            </div>
"""
    
    html_content += """
        </div>
        
        <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
            <h3>📋 测试建议</h3>
"""
    
    if data['success_rate'] == 100:
        html_content += "<p>🎉 所有测试通过！系统运行正常。</p>"
    elif data['success_rate'] >= 80:
        html_content += "<p>⚠️ 大部分测试通过，建议检查失败的测试项。</p>"
    else:
        html_content += "<p>❌ 多项测试失败，建议详细检查系统配置。</p>"
    
    html_content += """
            <ul>
                <li>定期运行测试以确保系统稳定性</li>
                <li>关注API响应时间，确保用户体验</li>
                <li>检查日志文件以获取详细错误信息</li>
                <li>验证所有服务的运行状态</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    
    with open('test_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ HTML测试报告已生成: test_report.html")

if __name__ == '__main__':
    generate_html_report()
EOF

chmod +x generate_test_report.py
python generate_test_report.py
```

## 5. 📊 性能监控和指标

### 5.1 创建性能监控脚本
```bash
cat > performance_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
AI中台性能监控脚本
"""
import psutil
import requests
import time
import json
from datetime import datetime

class PerformanceMonitor:
    def __init__(self, base_url='http://localhost'):
        self.base_url = base_url
        self.api_url = f'{base_url}/api'
        
    def get_system_metrics(self):
        """获取系统性能指标"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_api_metrics(self):
        """获取API性能指标"""
        endpoints = [
            '/',
            '/admin/',
            '/api/data/status/',
            '/api/algorithm/status/',
            '/swagger/'
        ]
        
        metrics = {}
        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = requests.get(f'{self.base_url}{endpoint}', timeout=10)
                end_time = time.time()
                
                metrics[endpoint] = {
                    'response_time': (end_time - start_time) * 1000,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
            except Exception as e:
                metrics[endpoint] = {
                    'response_time': 0,
                    'status_code': 0,
                    'success': False,
                    'error': str(e)
                }
        
        return metrics
    
    def run_monitoring(self, duration_minutes=5, interval_seconds=30):
        """运行性能监控"""
        print(f"🔍 开始性能监控 (持续{duration_minutes}分钟)")
        print("=" * 50)
        
        data_points = []
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            # 收集指标
            system_metrics = self.get_system_metrics()
            api_metrics = self.get_api_metrics()
            
            data_point = {
                'timestamp': datetime.now().isoformat(),
                'system': system_metrics,
                'api': api_metrics
            }
            
            data_points.append(data_point)
            
            # 实时显示
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"CPU: {system_metrics['cpu_percent']:.1f}%, "
                  f"内存: {system_metrics['memory_percent']:.1f}%, "
                  f"API响应: {api_metrics.get('/', {}).get('response_time', 0):.0f}ms")
            
            time.sleep(interval_seconds)
        
        # 保存数据
        with open('performance_data.json', 'w') as f:
            json.dump(data_points, f, indent=2)
        
        # 生成报告
        self.generate_performance_report(data_points)
        
        print("\n✅ 性能监控完成，数据已保存到 performance_data.json")
    
    def generate_performance_report(self, data_points):
        """生成性能报告"""
        if not data_points:
            return
        
        # 计算平均值
        avg_cpu = sum(d['system']['cpu_percent'] for d in data_points) / len(data_points)
        avg_memory = sum(d['system']['memory_percent'] for d in data_points) / len(data_points)
        
        # API响应时间统计
        api_stats = {}
        for endpoint in ['/', '/admin/', '/api/data/status/']:
            response_times = [
                d['api'].get(endpoint, {}).get('response_time', 0) 
                for d in data_points 
                if d['api'].get(endpoint, {}).get('success', False)
            ]
            
            if response_times:
                api_stats[endpoint] = {
                    'avg': sum(response_times) / len(response_times),
                    'min': min(response_times),
                    'max': max(response_times),
                    'count': len(response_times)
                }
        
        print(f"\n📊 性能报告摘要")
        print("=" * 30)
        print(f"平均CPU使用率: {avg_cpu:.1f}%")
        print(f"平均内存使用率: {avg_memory:.1f}%")
        
        print(f"\nAPI响应时间 (ms):")
        for endpoint, stats in api_stats.items():
            print(f"  {endpoint}: 平均{stats['avg']:.0f}, 最小{stats['min']:.0f}, 最大{stats['max']:.0f}")

if __name__ == '__main__':
    monitor = PerformanceMonitor()
    monitor.run_monitoring(duration_minutes=2, interval_seconds=10)  # 短时间测试
EOF

chmod +x performance_monitor.py
```

## 6. 📋 测试验证清单

### ✅ API功能验证
- [ ] 四大平台API端点响应正常
- [ ] API文档 (Swagger/ReDoc) 可访问
- [ ] JWT认证流程完整
- [ ] 用户注册登录功能正常
- [ ] 错误处理机制正确

### ✅ 性能验证
- [ ] API响应时间 < 500ms
- [ ] 并发用户支持 > 10
- [ ] 系统资源使用合理
- [ ] 错误率 < 5%

### ✅ 安全验证
- [ ] 未授权访问被正确拒绝
- [ ] Token验证机制正常
- [ ] 密码验证规则生效
- [ ] CORS配置正确

### ✅ 集成验证
- [ ] 前后端通信正常
- [ ] 数据库操作正常
- [ ] 静态文件服务正常
- [ ] 日志记录完整

## 📝 总结

API集成测试完成后，您将获得：

- ✅ 完整的API功能验证
- ✅ 认证系统可靠性确认
- ✅ 性能基线数据
- ✅ 自动化测试套件
- ✅ 详细的测试报告

### 下一步
继续进行 [系统验证](./04_system_validation.md)

---
*文档创建时间: 2025年1月*  
*适用系统: Ubuntu 24.04 LTS*  
*测试框架: Python requests + 自定义测试套件*
