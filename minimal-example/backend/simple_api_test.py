#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的API测试脚本
"""
import requests
import json
import sys

# API基础URL
BASE_URL = 'http://127.0.0.1:8000'

def test_api_endpoints():
    print("🚀 开始API测试")
    print("=" * 50)
    
    # 检查服务器状态
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ 服务器状态: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        return
    
    # 测试API根端点
    endpoints_to_test = [
        '/api/',
        '/api/auth/',
        '/api/algorithm/',
        '/api/data/',
        '/api/model/',
        '/api/service/',
        '/swagger/',
        '/redoc/'
    ]
    
    for endpoint in endpoints_to_test:
        url = BASE_URL + endpoint
        try:
            response = requests.get(url, timeout=10)
            if response.status_code in [200, 301, 302]:
                print(f"✅ {endpoint}: {response.status_code}")
            else:
                print(f"⚠️  {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: 连接失败 - {e}")
    
    # 测试用户注册
    print("\n🔍 测试用户注册...")
    register_data = {
        "username": "testuser123",
        "email": "test123@example.com", 
        "password": "testpass123",
        "password_confirm": "testpass123"
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/auth/register/', json=register_data)
        print(f"  注册结果: {response.status_code}")
        if response.status_code != 201:
            print(f"  响应内容: {response.text[:200]}")
    except Exception as e:
        print(f"  注册失败: {e}")
    
    print("\n✅ API测试完成")

if __name__ == '__main__':
    test_api_endpoints()
