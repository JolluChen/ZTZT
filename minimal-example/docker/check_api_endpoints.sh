#!/bin/bash

echo "🔍 Dify API 端点检查"
echo "===================="

BASE_URL="http://192.168.110.88"

echo "📋 检查核心 API 端点:"
echo "----------------------"

# 检查 setup 状态
echo -n "Setup 状态: "
setup_response=$(curl -s ${BASE_URL}/console/api/setup)
if echo "$setup_response" | grep -q "finished"; then
    echo "✅ 已完成设置"
else
    echo "❌ 设置未完成: $setup_response"
fi

# 检查系统特性
echo -n "系统特性: "
if curl -s ${BASE_URL}/console/api/system-features >/dev/null; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

# 检查登录端点方法
echo -n "登录端点 (GET): "
login_get=$(curl -s -I ${BASE_URL}/console/api/login 2>/dev/null | head -1)
if echo "$login_get" | grep -q "405"; then
    echo "✅ 正确拒绝 GET (期望 POST)"
else
    echo "❌ 异常响应: $login_get"
fi

echo -n "登录端点 (POST): "
login_post=$(curl -s -X POST -H "Content-Type: application/json" -d '{}' -I ${BASE_URL}/console/api/login 2>/dev/null | head -1)
if echo "$login_post" | grep -q "400"; then
    echo "✅ 接受 POST (需要有效数据)"
elif echo "$login_post" | grep -q "200"; then
    echo "✅ 接受 POST"
else
    echo "❌ 异常响应: $login_post"
fi

echo ""
echo "🌐 检查前端页面:"
echo "----------------"

# 检查登录页面
echo -n "登录页面: "
if curl -s ${BASE_URL}/signin >/dev/null; then
    echo "✅ 可访问"
else
    echo "❌ 无法访问"
fi

# 检查主页
echo -n "主页: "
home_status=$(curl -s -I ${BASE_URL}/ 2>/dev/null | head -1)
if echo "$home_status" | grep -q "200\|307"; then
    echo "✅ 正常"
else
    echo "❌ 异常: $home_status"
fi

echo ""
echo "🔧 建议的解决方案:"
echo "----------------"
echo "1. 405 错误是正常的 - 说明登录端点只接受 POST 方法"
echo "2. 前端 JavaScript 可能在页面加载时错误地发送了 GET 请求"
echo "3. 这通常不影响实际登录功能，只是控制台警告"
echo "4. 清除浏览器缓存可能会解决这个问题"
echo ""
echo "🎯 测试登录:"
echo "管理员邮箱: admin@dify.ai"
echo "管理员密码: admin123456"
