#!/usr/bin/env python
"""
简化的迁移脚本，直接使用Django来创建迁移
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_local')

# 添加当前路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置Django
django.setup()

if __name__ == "__main__":
    try:
        print("=== 创建数据库迁移 ===")
        
        # 创建迁移
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        print("\n=== 应用数据库迁移 ===")
        # 应用迁移
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("\n=== 迁移完成 ===")
        
    except Exception as e:
        print(f"迁移过程中出现错误: {e}")
        sys.exit(1)
