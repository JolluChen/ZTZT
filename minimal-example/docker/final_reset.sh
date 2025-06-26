#!/bin/bash
# Dify 最终重置脚本

echo "🔧 执行 Dify 最终重置..."

# 1. 重置数据库状态
echo "📊 重置数据库状态..."
docker exec ai_platform_postgres psql -U ai_user -d dify -c "
-- 确保设置表显示完成状态
DELETE FROM dify_setups;
INSERT INTO dify_setups (version, setup_at) VALUES ('0.6.13', NOW());

-- 清理和重建账户
DELETE FROM tenant_account_joins;
DELETE FROM accounts;
DELETE FROM tenants;

-- 创建租户
INSERT INTO tenants (id, name, status, created_at, updated_at) 
VALUES (gen_random_uuid(), 'Default Workspace', 'normal', NOW(), NOW());

-- 创建管理员账户（无密码，用于跳过验证）
INSERT INTO accounts (id, name, email, status, initialized_at, created_at, updated_at) 
VALUES (gen_random_uuid(), 'Admin', 'admin@dify.ai', 'active', NOW(), NOW(), NOW());

-- 关联账户和租户
INSERT INTO tenant_account_joins (id, tenant_id, account_id, role, invited_by, created_at, updated_at)
SELECT gen_random_uuid(), t.id, a.id, 'owner', a.id, NOW(), NOW()
FROM tenants t, accounts a 
WHERE t.name = 'Default Workspace' AND a.email = 'admin@dify.ai';
"

# 2. 重启所有服务
echo "🔄 重启所有 Dify 服务..."
cd /home/lsyzt/ZTZT/minimal-example/docker
docker compose -f dify-docker-compose.yml restart

# 3. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 20

# 4. 验证状态
echo "✅ 验证系统状态..."
curl -s "http://192.168.110.88/console/api/setup"
echo ""

echo "🎯 完成！请尝试以下操作："
echo "1. 清除浏览器缓存"
echo "2. 访问：http://192.168.110.88"
echo "3. 或直接访问：http://192.168.110.88/signin"
echo "4. 如果仍显示验证码，请尝试无痕模式访问"
