#!/usr/bin/env python3
"""
Dify 验证码问题修复脚本
这个脚本将彻底解决 Dify 管理员验证码界面的问题
"""
import psycopg2
import os
import sys
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'ai_user',
    'password': 'ai_password',
    'database': 'dify'
}

def connect_db():
    """连接到 PostgreSQL 数据库"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def reset_dify_setup(conn):
    """重置 Dify 设置状态"""
    cursor = conn.cursor()
    
    print("1. 清理设置表...")
    # 删除现有的设置记录
    cursor.execute("DELETE FROM dify_setups;")
    
    print("2. 重置管理员账户...")
    # 更新管理员账户，确保状态正确
    cursor.execute("""
        UPDATE accounts 
        SET 
            password = crypt('admin123456', gen_salt('bf')),
            status = 'active',
            is_setup = true,
            setup_at = NOW()
        WHERE email = 'admin@example.com';
    """)
    
    print("3. 确保租户状态正确...")
    # 确保租户状态正常
    cursor.execute("""
        UPDATE tenants 
        SET status = 'normal'
        WHERE name = 'admin''s Workspace';
    """)
    
    conn.commit()
    cursor.close()
    
    print("✅ 数据库状态重置完成")

def check_current_status(conn):
    """检查当前状态"""
    cursor = conn.cursor()
    
    print("\n📊 当前状态检查:")
    
    # 检查设置表
    cursor.execute("SELECT COUNT(*) FROM dify_setups;")
    setup_count = cursor.fetchone()[0]
    print(f"- 设置表记录数: {setup_count}")
    
    # 检查管理员账户
    cursor.execute("""
        SELECT email, status, is_setup, setup_at 
        FROM accounts 
        WHERE email = 'admin@example.com';
    """)
    admin = cursor.fetchone()
    if admin:
        print(f"- 管理员账户: {admin[0]}, 状态: {admin[1]}, 已设置: {admin[2]}")
    else:
        print("- ❌ 未找到管理员账户")
    
    # 检查租户
    cursor.execute("SELECT name, status FROM tenants;")
    tenants = cursor.fetchall()
    print(f"- 租户数量: {len(tenants)}")
    for tenant in tenants:
        print(f"  - {tenant[0]}: {tenant[1]}")
    
    cursor.close()

def main():
    """主函数"""
    print("🔧 Dify 验证码问题修复工具")
    print("=" * 50)
    
    # 连接数据库
    conn = connect_db()
    if not conn:
        print("❌ 无法连接到数据库，请确保 PostgreSQL 容器正在运行")
        sys.exit(1)
    
    try:
        # 检查当前状态
        check_current_status(conn)
        
        # 询问是否继续
        response = input("\n是否继续修复? (y/N): ")
        if response.lower() != 'y':
            print("取消操作")
            return
        
        # 执行修复
        reset_dify_setup(conn)
        
        # 再次检查状态
        print("\n修复后状态:")
        check_current_status(conn)
        
        print("\n✅ 修复完成！")
        print("\n📋 接下来的步骤:")
        print("1. 重启 Dify 容器")
        print("2. 访问 http://192.168.110.88")
        print("3. 使用邮箱: admin@example.com")
        print("4. 使用密码: admin123456")
        
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
