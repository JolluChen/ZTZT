#!/bin/bash

echo "🔧 Dify 前端缓存清理和重启脚本"
echo "================================="

echo "1. 重启 dify-web 容器..."
docker restart docker-dify-web-1

echo "2. 等待容器启动..."
sleep 10

echo "3. 验证服务状态..."
echo "   - 检查容器状态:"
docker ps | grep dify-web

echo "   - 测试API端点:"
if curl -s http://192.168.110.88/console/api/system-features >/dev/null; then
    echo "   ✅ API端点正常"
else
    echo "   ❌ API端点异常"
fi

echo "   - 测试重复路径重定向:"
if curl -I http://192.168.110.88/console/api/console/api/system-features 2>/dev/null | grep -q "301"; then
    echo "   ✅ 重复路径重定向正常"
else
    echo "   ❌ 重复路径重定向异常"
fi

echo ""
echo "📝 建议用户操作:"
echo "   1. 清除浏览器缓存 (Ctrl+Shift+Del)"
echo "   2. 强制刷新页面 (Ctrl+F5)"
echo "   3. 或使用无痕模式打开 http://192.168.110.88/"
echo ""
echo "🔍 如果控制台仍有错误，请检查:"
echo "   - 浏览器开发者工具的网络标签页"
echo "   - 是否还有缓存的旧版本 JavaScript 文件"
