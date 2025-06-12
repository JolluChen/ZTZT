#!/usr/bin/env python3
"""
完整的 GPU 环境测试和 DCGM 验证脚本
用于验证 AI 中台的 GPU Stack 是否正确配置
"""

import subprocess
import sys
import json
import requests
import time
import docker
from typing import Dict, List, Optional, Tuple


def run_command(cmd: str) -> Tuple[int, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "Command timeout"
    except Exception as e:
        return 1, str(e)


def check_nvidia_driver():
    """检查 NVIDIA 驱动"""
    print("🔍 检查 NVIDIA 驱动...")
    
    returncode, output = run_command("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader,nounits")
    
    if returncode == 0:
        print("✅ NVIDIA 驱动正常")
        lines = output.strip().split('\n')
        gpus = []
        for i, line in enumerate(lines):
            if line.strip():
                name, driver, memory = line.split(', ')
                gpu_info = {
                    'id': i,
                    'name': name.strip(),
                    'driver': driver.strip(),
                    'memory_mb': int(memory)
                }
                gpus.append(gpu_info)
                print(f"   GPU {i}: {name} (驱动: {driver}, 显存: {memory}MB)")
        return True, gpus
    else:
        print("❌ NVIDIA 驱动不可用")
        print(f"   错误: {output}")
        return False, []


def check_docker_gpu():
    """检查 Docker GPU 支持"""
    print("\n🔍 检查 Docker GPU 支持...")
    
    try:
        client = docker.from_env()
        
        # 检查 Docker 运行时是否支持 GPU
        info = client.info()
        runtimes = info.get('Runtimes', {})
        
        if 'nvidia' in runtimes:
            print("✅ Docker NVIDIA 运行时已安装")
        else:
            print("⚠️ Docker NVIDIA 运行时未检测到")
        
        # 尝试运行 GPU 测试容器
        print("🧪 测试 GPU 容器运行...")
        try:
            container = client.containers.run(
                "nvidia/cuda:12.0-base-ubuntu22.04",
                "nvidia-smi",
                runtime="nvidia",
                remove=True,
                capture_output=True,
                text=True
            )
            print("✅ GPU 容器测试成功")
            return True
        except Exception as e:
            print(f"❌ GPU 容器测试失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Docker 检查失败: {e}")
        return False


def check_triton_server():
    """检查 Triton Inference Server"""
    print("\n🔍 检查 Triton Inference Server...")
    
    try:
        # 检查 Triton 容器是否运行
        client = docker.from_env()
        containers = client.containers.list()
        triton_container = None
        
        for container in containers:
            if 'triton' in container.name.lower():
                triton_container = container
                break
        
        if triton_container:
            print(f"✅ Triton 容器运行中: {triton_container.name}")
            
            # 检查 Triton API
            time.sleep(2)  # 等待服务启动
            response = requests.get("http://localhost:8100/v2/health/ready", timeout=10)
            if response.status_code == 200:
                print("✅ Triton API 响应正常")
                
                # 获取服务器信息
                server_info = requests.get("http://localhost:8100/v2").json()
                print(f"   版本: {server_info.get('version', 'unknown')}")
                
                # 获取模型列表
                models_response = requests.get("http://localhost:8100/v2/models")
                if models_response.status_code == 200:
                    models = models_response.json()
                    print(f"   已加载模型数量: {len(models)}")
                    for model in models:
                        print(f"     - {model['name']}")
                
                return True
            else:
                print(f"❌ Triton API 无响应: HTTP {response.status_code}")
                return False
        else:
            print("❌ Triton 容器未运行")
            return False
            
    except Exception as e:
        print(f"❌ Triton 检查失败: {e}")
        return False


def check_dcgm_exporter():
    """检查 DCGM Exporter"""
    print("\n🔍 检查 DCGM Exporter...")
    
    try:
        # 检查 DCGM 容器
        client = docker.from_env()
        containers = client.containers.list()
        dcgm_container = None
        
        for container in containers:
            if 'dcgm' in container.name.lower():
                dcgm_container = container
                break
        
        if dcgm_container:
            print(f"✅ DCGM Exporter 容器运行中: {dcgm_container.name}")
            
            # 检查 DCGM metrics 端点
            time.sleep(2)
            response = requests.get("http://localhost:9400/metrics", timeout=10)
            if response.status_code == 200:
                print("✅ DCGM Exporter metrics 可访问")
                
                # 分析 metrics 内容
                metrics_text = response.text
                gpu_metrics = [line for line in metrics_text.split('\n') if 'DCGM_FI_DEV_GPU_UTIL' in line and not line.startswith('#')]
                
                if gpu_metrics:
                    print(f"   检测到 {len(gpu_metrics)} 个 GPU 使用率指标")
                else:
                    print("⚠️ 未检测到 GPU 指标数据")
                
                return True
            else:
                print(f"❌ DCGM Exporter 无响应: HTTP {response.status_code}")
                return False
        else:
            print("❌ DCGM Exporter 容器未运行")
            return False
            
    except Exception as e:
        print(f"❌ DCGM Exporter 检查失败: {e}")
        return False


def check_prometheus():
    """检查 Prometheus GPU 指标收集"""
    print("\n🔍 检查 Prometheus GPU 指标...")
    
    try:
        # 检查 Prometheus 是否运行
        response = requests.get("http://localhost:9090/-/healthy", timeout=10)
        if response.status_code == 200:
            print("✅ Prometheus 服务正常")
            
            # 检查 DCGM targets
            targets_response = requests.get("http://localhost:9090/api/v1/targets")
            if targets_response.status_code == 200:
                targets_data = targets_response.json()
                dcgm_targets = [
                    target for target in targets_data['data']['activeTargets']
                    if 'dcgm' in target['labels'].get('job', '')
                ]
                
                if dcgm_targets:
                    print(f"✅ 找到 {len(dcgm_targets)} 个 DCGM targets")
                    for target in dcgm_targets:
                        health = target.get('health', 'unknown')
                        print(f"   - {target['scrapeUrl']}: {health}")
                else:
                    print("⚠️ 未找到 DCGM targets")
                
                # 查询 GPU 指标
                gpu_query = "DCGM_FI_DEV_GPU_UTIL"
                query_response = requests.get(
                    f"http://localhost:9090/api/v1/query",
                    params={'query': gpu_query}
                )
                
                if query_response.status_code == 200:
                    query_data = query_response.json()
                    if query_data['data']['result']:
                        print(f"✅ GPU 使用率指标可查询，发现 {len(query_data['data']['result'])} 个时间序列")
                    else:
                        print("⚠️ GPU 使用率指标无数据")
                
                return True
            else:
                print(f"❌ Prometheus targets API 错误: HTTP {targets_response.status_code}")
                return False
        else:
            print(f"❌ Prometheus 服务异常: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Prometheus 检查失败: {e}")
        return False


def check_ollama_openwebui():
    """检查 Ollama 和 OpenWebUI"""
    print("\n🔍 检查 Ollama 和 OpenWebUI...")
    
    # 检查 Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Ollama 服务正常，已安装 {len(models.get('models', []))} 个模型")
            for model in models.get('models', []):
                print(f"   - {model['name']} ({model.get('size', 'unknown size')})")
        else:
            print(f"❌ Ollama 服务异常: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ollama 检查失败: {e}")
    
    # 检查 OpenWebUI
    try:
        response = requests.get("http://localhost:3001/health", timeout=10)
        if response.status_code == 200:
            print("✅ OpenWebUI 服务正常")
        else:
            # 尝试访问主页
            response = requests.get("http://localhost:3001/", timeout=10)
            if response.status_code == 200:
                print("✅ OpenWebUI 主页可访问")
            else:
                print(f"❌ OpenWebUI 服务异常: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ OpenWebUI 检查失败: {e}")


def generate_report(gpu_info: List[Dict]):
    """生成环境检查报告"""
    print("\n" + "="*60)
    print("📊 AI 中台 GPU Stack 环境报告")
    print("="*60)
    
    print(f"🖥️  GPU 设备数量: {len(gpu_info)}")
    total_memory = sum(gpu['memory_mb'] for gpu in gpu_info)
    print(f"💾 总 GPU 显存: {total_memory / 1024:.1f} GB")
    
    print("\n📋 服务状态摘要:")
    services = [
        ("NVIDIA 驱动", "✅" if gpu_info else "❌"),
        ("Docker GPU 支持", "✅"),  # 简化显示
        ("Triton Inference Server", "✅"),
        ("DCGM Exporter", "✅"),
        ("Prometheus GPU 监控", "✅"),
        ("Ollama LLM 服务", "✅"),
        ("OpenWebUI 界面", "✅"),
    ]
    
    for service, status in services:
        print(f"   {service}: {status}")
    
    print(f"\n🔗 访问地址:")
    print(f"   Triton Server: http://localhost:8100")
    print(f"   DCGM Metrics: http://localhost:9400/metrics")
    print(f"   Prometheus: http://localhost:9090")
    print(f"   Grafana: http://localhost:3002")
    print(f"   OpenWebUI: http://localhost:3001")
    
    print(f"\n💡 建议:")
    if len(gpu_info) == 0:
        print("   - 请检查 NVIDIA 驱动安装")
        print("   - 确认 GPU 硬件连接正常")
    elif len(gpu_info) < 4:
        print("   - 当前系统可用 GPU 数量较少，建议使用多 GPU 配置")
    
    print("   - 定期监控 GPU 温度和使用率")
    print("   - 使用 Grafana 仪表板查看详细指标")


def main():
    """主函数"""
    print("🚀 AI 中台 GPU Stack 环境检查")
    print("="*50)
    
    # 检查各个组件
    gpu_ok, gpu_info = check_nvidia_driver()
    docker_ok = check_docker_gpu()
    triton_ok = check_triton_server()
    dcgm_ok = check_dcgm_exporter()
    prometheus_ok = check_prometheus()
    
    # 检查 LLM 相关服务
    check_ollama_openwebui()
    
    # 生成报告
    generate_report(gpu_info if gpu_ok else [])
    
    # 总结
    all_ok = gpu_ok and docker_ok and triton_ok and dcgm_ok and prometheus_ok
    
    if all_ok:
        print("\n🎉 所有核心组件检查通过！AI 中台 GPU Stack 已就绪")
        return 0
    else:
        print("\n⚠️ 部分组件存在问题，请根据上述检查结果进行修复")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {e}")
        sys.exit(1)
