# PowerShell API测试脚本
Write-Host "🚀 开始API测试" -ForegroundColor Green
Write-Host "=" * 50

$baseUrl = "http://127.0.0.1:8000"

# 测试端点列表
$endpoints = @(
    "/",
    "/api/",
    "/api/auth/",
    "/api/algorithm/",
    "/api/data/",
    "/api/model/", 
    "/api/service/",
    "/swagger/",
    "/redoc/"
)

foreach ($endpoint in $endpoints) {
    $url = $baseUrl + $endpoint
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 10 -UseBasicParsing
        $statusCode = $response.StatusCode
        if ($statusCode -eq 200) {
            Write-Host "✅ $endpoint : $statusCode" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $endpoint : $statusCode" -ForegroundColor Yellow
        }
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode) {
            Write-Host "⚠️  $endpoint : $statusCode" -ForegroundColor Yellow
        } else {
            Write-Host "❌ $endpoint : 连接失败" -ForegroundColor Red
        }
    }
}

Write-Host "`n✅ API测试完成" -ForegroundColor Green
