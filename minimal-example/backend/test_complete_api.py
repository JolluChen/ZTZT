#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的API测试脚本
测试所有平台的API端点功能
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# 添加Django项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# API基础URL
BASE_URL = 'http://127.0.0.1:8000'
API_URL = f'{BASE_URL}/api'

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        
    def test_user_registration(self):
        """测试用户注册"""
        print("🔍 测试用户注册...")
        
        # 生成唯一用户名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_data = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        try:
            response = self.session.post(f'{API_URL}/auth/register/', json=user_data)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 201:
                print("  ✅ 用户注册成功")
                return user_data
            else:
                print(f"  ❌ 用户注册失败: {response.text}")
                return None
        except Exception as e:
            print(f"  ❌ 请求失败: {e}")
            return None
    
    def test_user_login(self, username, password):
        """测试用户登录"""
        print("🔍 测试用户登录...")
        
        login_data = {
            "username": username,
            "password": password
        }
        
        try:
            response = self.session.post(f'{API_URL}/auth/login/', json=login_data)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                self.refresh_token = data.get('refresh')
                
                # 设置认证头
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                
                print("  ✅ 用户登录成功")
                print(f"  Access Token: {self.access_token[:50]}...")
                return True
            else:
                print(f"  ❌ 用户登录失败: {response.text}")
                return False
        except Exception as e:
            print(f"  ❌ 请求失败: {e}")
            return False
    
    def test_user_profile(self):
        """测试用户资料"""
        print("🔍 测试用户资料...")
        
        try:
            response = self.session.get(f'{API_URL}/auth/profile/')
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                profile_data = response.json()
                print("  ✅ 获取用户资料成功")
                print(f"  用户名: {profile_data.get('username')}")
                print(f"  邮箱: {profile_data.get('email')}")
                return True
            else:
                print(f"  ❌ 获取用户资料失败: {response.text}")
                return False
        except Exception as e:
            print(f"  ❌ 请求失败: {e}")
            return False
    
    def test_algorithm_platform(self):
        """测试算法平台API"""
        print("🔍 测试算法平台...")
        
        endpoints = [
            ('algorithms/', 'GET', '算法列表'),
            ('executions/', 'GET', '执行记录'),
            ('results/', 'GET', '结果列表')
        ]
        
        for endpoint, method, description in endpoints:
            try:
                url = f'{API_URL}/algorithm/{endpoint}'
                response = self.session.get(url)
                print(f"  {description}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"    ✅ {description}获取成功")
                else:
                    print(f"    ❌ {description}获取失败: {response.text}")
            except Exception as e:
                print(f"    ❌ {description}请求失败: {e}")
    
    def test_data_platform(self):
        """测试数据平台API"""
        print("🔍 测试数据平台...")
        
        endpoints = [
            ('datasets/', 'GET', '数据集列表'),
            ('storage/', 'GET', '存储列表'),
            ('pipelines/', 'GET', '数据管道')
        ]
        
        for endpoint, method, description in endpoints:
            try:
                url = f'{API_URL}/data/{endpoint}'
                response = self.session.get(url)
                print(f"  {description}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"    ✅ {description}获取成功")
                else:
                    print(f"    ❌ {description}获取失败: {response.text}")
            except Exception as e:
                print(f"    ❌ {description}请求失败: {e}")
    
    def test_model_platform(self):
        """测试模型平台API"""
        print("🔍 测试模型平台...")
        
        endpoints = [
            ('models/', 'GET', '模型列表'),
            ('deployments/', 'GET', '部署列表'),
            ('experiments/', 'GET', '实验列表')
        ]
        
        for endpoint, method, description in endpoints:
            try:
                url = f'{API_URL}/model/{endpoint}'
                response = self.session.get(url)
                print(f"  {description}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"    ✅ {description}获取成功")
                else:
                    print(f"    ❌ {description}获取失败: {response.text}")
            except Exception as e:
                print(f"    ❌ {description}请求失败: {e}")
    
    def test_service_platform(self):
        """测试服务平台API"""
        print("🔍 测试服务平台...")
        
        endpoints = [
            ('services/', 'GET', '服务列表'),
            ('monitors/', 'GET', '监控列表'),
            ('configs/', 'GET', '配置列表')
        ]
        
        for endpoint, method, description in endpoints:
            try:
                url = f'{API_URL}/service/{endpoint}'
                response = self.session.get(url)
                print(f"  {description}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"    ✅ {description}获取成功")
                else:
                    print(f"    ❌ {description}获取失败: {response.text}")
            except Exception as e:
                print(f"    ❌ {description}请求失败: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始API功能测试")
        print("=" * 60)
        
        # 1. 测试用户注册
        user_data = self.test_user_registration()
        if not user_data:
            print("❌ 用户注册失败，使用默认管理员账户")
            user_data = {"username": "admin", "password": "admin"}
        
        print("-" * 60)
        
        # 2. 测试用户登录
        login_success = self.test_user_login(
            user_data["username"], 
            user_data.get("password", "admin")
        )
        if not login_success:
            print("❌ 无法登录，跳过需要认证的测试")
            return
        
        print("-" * 60)
        
        # 3. 测试用户资料
        self.test_user_profile()
        
        print("-" * 60)
        
        # 4. 测试各平台API
        self.test_algorithm_platform()
        print("-" * 30)
        self.test_data_platform()
        print("-" * 30)
        self.test_model_platform()
        print("-" * 30)
        self.test_service_platform()
        
        print("=" * 60)
        print("🎉 API测试完成")

def main():
    """主函数"""
    print("📋 最小化AI平台 - API功能测试")
    print(f"🌐 服务器地址: {BASE_URL}")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查服务器是否运行
    try:
        response = requests.get(BASE_URL, timeout=5)
        print("✅ Django服务器运行正常")
    except Exception as e:
        print(f"❌ 无法连接到Django服务器: {e}")
        print("请确保Django服务器在运行: python manage.py runserver")
        return
    
    print()
    
    # 运行API测试
    tester = APITester()
    tester.run_all_tests()

if __name__ == '__main__':
    main()
