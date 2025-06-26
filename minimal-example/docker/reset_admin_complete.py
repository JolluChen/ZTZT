#!/usr/bin/env python3
"""
重置Dify管理员账户的脚本
"""
import sys
import secrets
import base64
import hashlib
import uuid
from datetime import datetime

# 生成密码哈希
def create_password_hash(password):
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    salt_base64 = base64.b64encode(salt).decode('utf-8')
    password_hash_base64 = base64.b64encode(password_hash).decode('utf-8')
    return salt_base64, password_hash_base64

# 主函数
def main():
    password = 'admin123456'
    salt_base64, password_hash_base64 = create_password_hash(password)
    
    print(f"生成的密码哈希:")
    print(f"盐值: {salt_base64}")
    print(f"哈希: {password_hash_base64}")
    
    # 生成SQL命令
    sql_commands = f"""
-- 删除现有管理员账户
DELETE FROM accounts WHERE email = 'admin@example.com';

-- 删除现有租户账户关联
DELETE FROM tenant_account_joins WHERE account_id IN (
    SELECT id FROM accounts WHERE email = 'admin@example.com'
);

-- 创建新的管理员账户
INSERT INTO accounts (
    id, name, email, password, password_salt, status, 
    initialized_at, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'Admin',
    'admin@example.com',
    '{password_hash_base64}',
    '{salt_base64}',
    'active',
    NOW(),
    NOW(),
    NOW()
);

-- 确保租户存在并关联管理员
INSERT INTO tenant_account_joins (
    id, tenant_id, account_id, role, invited_by, 
    created_at, updated_at
) 
SELECT 
    gen_random_uuid(),
    t.id,
    a.id,
    'owner',
    a.id,
    NOW(),
    NOW()
FROM tenants t, accounts a 
WHERE a.email = 'admin@example.com' 
AND t.name = 'admin''s Workspace'
ON CONFLICT DO NOTHING;

-- 确保设置表有记录
INSERT INTO dify_setups (version, setup_at) 
VALUES ('0.6.13', NOW()) 
ON CONFLICT DO NOTHING;
"""
    
    print("\n以下SQL命令将重置管理员账户:")
    print(sql_commands)
    
    return sql_commands

if __name__ == "__main__":
    main()
