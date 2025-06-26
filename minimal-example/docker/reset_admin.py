#!/usr/bin/env python3
"""
Dify 管理员账户重置脚本
"""
import os
import sys
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text
from urllib.parse import quote

def reset_admin_account():
    """重置管理员账户"""
    
    # 从环境变量获取数据库配置
    db_user = os.getenv('DB_USERNAME', 'ai_user')
    db_password = os.getenv('DB_PASSWORD', 'ai_password')
    db_host = os.getenv('DB_HOST', 'ai_platform_postgres')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_DATABASE', 'dify')
    
    # 管理员账户信息
    admin_email = 'admin@example.com'
    admin_password = 'admin123456'
    
    try:
        # 构建数据库连接
        encoded_password = quote(db_password)
        db_url = f'postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}'
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # 删除现有的管理员账户
            conn.execute(text("DELETE FROM accounts WHERE email = :email"), {"email": admin_email})
            
            # 生成密码哈希
            password_hash = generate_password_hash(admin_password)
            
            # 插入新的管理员账户
            insert_sql = text("""
                INSERT INTO accounts (id, email, password, status, created_at, updated_at, name, avatar)
                VALUES (
                    gen_random_uuid(),
                    :email,
                    :password_hash,
                    'active',
                    NOW(),
                    NOW(),
                    'Admin',
                    ''
                )
            """)
            
            conn.execute(insert_sql, {
                "email": admin_email,
                "password_hash": password_hash
            })
            
            conn.commit()
            
            print(f"✅ 管理员账户重置成功!")
            print(f"📧 邮箱: {admin_email}")
            print(f"🔑 密码: {admin_password}")
            print(f"🌐 登录地址: http://192.168.110.88")
            
    except Exception as e:
        print(f"❌ 重置失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_admin_account()
