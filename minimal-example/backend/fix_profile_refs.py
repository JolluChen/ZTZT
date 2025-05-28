#!/usr/bin/env python3
"""
修复UserProfile引用问题的脚本
将所有 user.userprofile 引用改为 user.profile
"""

import os
import re
import glob

def find_and_replace_profile_refs(directory):
    """查找并替换profile引用"""
    python_files = glob.glob(os.path.join(directory, '**', '*.py'), recursive=True)
    
    patterns = [
        (r'\.userprofile\b', '.profile'),  # .userprofile -> .profile
        (r'user\.userprofile', 'user.profile'),  # user.userprofile -> user.profile
    ]
    
    fixed_files = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_files.append(file_path)
                print(f"✅ 修复了文件: {file_path}")
        
        except Exception as e:
            print(f"❌ 处理文件 {file_path} 时出错: {e}")
    
    return fixed_files

def main():
    """主函数"""
    print("🔧 开始修复UserProfile引用...")
    
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    apps_dir = os.path.join(current_dir, 'apps')
    
    if not os.path.exists(apps_dir):
        print("❌ 未找到apps目录")
        return
    
    fixed_files = find_and_replace_profile_refs(apps_dir)
    
    if fixed_files:
        print(f"\n✅ 总共修复了 {len(fixed_files)} 个文件")
    else:
        print("\n✅ 没有发现需要修复的UserProfile引用")

if __name__ == "__main__":
    main()