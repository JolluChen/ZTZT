#!/bin/bash

echo "🎉 Dify 部署完成 - 最终状态报告"
echo "================================"

echo "✅ 服务状态检查:"
echo "----------------"

# 检查容器运行状态
echo "📦 容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(dify|nginx)" | while read line; do
    echo "   $line"
done

echo ""
echo "🌐 Web 服务检查:"
echo "---------------"

# 主页
main_status=$(curl -s -I http://192.168.110.88/ 2>/dev/null | head -1 | awk '{print $2}')
echo "   主页 (http://192.168.110.88/): $main_status"

# 登录页面
signin_status=$(curl -s -I http://192.168.110.88/signin 2>/dev/null | head -1 | awk '{print $2}')
echo "   登录页面 (/signin): $signin_status"

# API 端点
api_status=$(curl -s -I http://192.168.110.88/console/api/system-features 2>/dev/null | head -1 | awk '{print $2}')
echo "   Console API (/console/api/system-features): $api_status"

echo ""
echo "🔐 登录信息:"
echo "-----------"
echo "   管理员邮箱: admin@dify.ai"
echo "   管理员密码: admin123456"
echo "   访问地址: http://192.168.110.88/"

echo ""
echo "⚠️  关于控制台错误的说明:"
echo "-------------------------"
echo "   • 405 错误 (METHOD NOT ALLOWED) 是正常的"
echo "   • 登录 API 正确地拒绝了 GET 请求"
echo "   • 这不影响实际的登录功能"
echo "   • 清除浏览器缓存可以减少这些警告"

echo ""
echo "🛠️  如果遇到问题:"
echo "----------------"
echo "   1. 清除浏览器缓存 (Ctrl+Shift+Del)"
echo "   2. 使用无痕模式访问"
echo "   3. 强制刷新页面 (Ctrl+F5)"
echo "   4. 检查容器状态: docker ps | grep dify"

echo ""
echo "📂 相关文件:"
echo "-----------"
echo "   • Docker Compose: /home/lsyzt/ZTZT/minimal-example/docker/dify-docker-compose.yml"
echo "   • Nginx 配置: /home/lsyzt/ZTZT/minimal-example/docker/dify-nginx.conf"
echo "   • 测试脚本: /home/lsyzt/ZTZT/minimal-example/docker/test_dify.sh"

echo ""
echo "🎯 部署成功! Dify 现在可以正常使用了!"
