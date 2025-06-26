#!/bin/bash

echo "🔍 Dify 服务健康检查"
echo "========================"

# 检查容器状态
echo "📦 检查容器状态..."
echo "Dify Web 容器:"
docker ps | grep dify-web | grep -q "Up" && echo "✅ dify-web 运行正常" || echo "❌ dify-web 未运行"

echo "Dify API 容器:"
docker ps | grep dify_api | grep -q "Up" && echo "✅ dify-api 运行正常" || echo "❌ dify-api 未运行"

echo "Dify Worker 容器:"
docker ps | grep dify_worker | grep -q "Up" && echo "✅ dify-worker 运行正常" || echo "❌ dify-worker 未运行"

echo "Nginx 容器:"
docker ps | grep dify-nginx | grep -q "Up" && echo "✅ nginx 运行正常" || echo "❌ nginx 未运行"

echo ""
echo "🌐 检查 Web 服务..."

# 检查主页
echo "主页 (http://192.168.110.88/):"
if curl -s -I http://192.168.110.88/ | grep -q "200\|307"; then
    echo "✅ 主页访问正常"
else
    echo "❌ 主页访问异常"
fi

# 检查应用页面
echo "应用页面 (http://192.168.110.88/apps):"
if curl -s -I http://192.168.110.88/apps | grep -q "200"; then
    echo "✅ 应用页面访问正常"
else
    echo "❌ 应用页面访问异常"
fi

# 检查 API
echo "Console API (http://192.168.110.88/console/api/system-features):"
if curl -s -I http://192.168.110.88/console/api/system-features | grep -q "200"; then
    echo "✅ Console API 访问正常"
else
    echo "❌ Console API 访问异常"
fi

# 检查静态资源
echo "Favicon (http://192.168.110.88/favicon.ico):"
if curl -s -I http://192.168.110.88/favicon.ico | grep -q "200"; then
    echo "✅ Favicon 访问正常"
else
    echo "❌ Favicon 访问异常"
fi

echo ""
echo "🔧 API 响应测试..."
echo "系统特性 API 响应:"
curl -s http://192.168.110.88/console/api/system-features | jq -r '.enable_marketplace, .enable_email_password_login' 2>/dev/null | head -2

echo ""
echo "📋 总结"
echo "========================"
echo "如果以上所有检查都显示 ✅，那么 Dify 已完全正常运行"
echo "访问地址: http://192.168.110.88/"
echo "管理员邮箱: admin@dify.ai"
echo "管理员密码: admin123456"
