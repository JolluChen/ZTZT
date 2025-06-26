#!/bin/bash

echo "=== Dify 前端修复脚本 ==="
echo "正在修复前端API路径配置..."

# 停止并重新创建 dify-web 容器以清除所有缓存
echo "1. 停止 dify-web 容器..."
docker stop docker-dify-web-1

echo "2. 删除 dify-web 容器以清除缓存..."
docker rm docker-dify-web-1

echo "3. 重新创建 dify-web 容器..."
cd /home/lsyzt/ZTZT/minimal-example/docker
docker compose up -d dify-web

echo "4. 等待容器启动..."
sleep 15

echo "5. 检查容器状态..."
docker ps | grep dify-web

echo "6. 测试 API 端点..."
echo "Console API:"
curl -s http://192.168.110.88/console/api/system-features | jq '.enable_email_password_login'

echo ""
echo "V1 API:"
curl -s http://192.168.110.88/v1/ | jq '.api_version'

echo ""
echo "=== 修复完成 ==="
echo "请清理浏览器缓存并访问: http://192.168.110.88"
echo "如果仍有问题，请按 Ctrl+F5 强制刷新页面"
