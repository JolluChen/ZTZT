#!/usr/bin/env python3
"""
GPU 环境测试脚本
用于验证 NVIDIA GPU 环境配置是否正确
"""

import subprocess
import sys
import json
import requests
import time
from typing import Dict, List, Optional


def run_command(cmd: str) -> tuple[int, str]:
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
        for i, line in enumerate(lines):
            if line.strip():
                name, driver, memory = line.split(', ')
                print(f"   GPU {i}: {name} (驱动: {driver}, 显存: {memory}MB)")
        return True
    else:
        print("❌ NVIDIA 驱动不可用")
        print(f"   错误: {output}")
        return False


def check_docker_gpu():
    """检查 Docker GPU 支持"""
    print("\n🔍 检查 Docker GPU 支持...")
    
    # 检查 Docker 信息
    returncode, output = run_command("docker info")
    if returncode != 0:
        print("❌ Docker 不可用")
        return False
    
    if "nvidia" in output.lower():
        print("✅ Docker 支持 NVIDIA GPU")
        
        # 测试 GPU 容器
        print("   测试 GPU 容器...")
        returncode, output = run_command("docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi -L")
        
        if returncode == 0:
            print("✅ GPU 容器测试成功")
            gpu_lines = [line for line in output.split('\n') if 'GPU' in line]
            for line in gpu_lines:
                print(f"   {line.strip()}")
            return True
        else:
            print("❌ GPU 容器测试失败")
            print(f"   错误: {output}")
            return False
    else:
        print("❌ Docker 不支持 NVIDIA GPU")
        print("   请安装 NVIDIA Container Toolkit")
        return False


def check_triton_service():
    """检查 Triton 服务"""
    print("\n🔍 检查 Triton Inference Server...")
    
    triton_url = "http://localhost:8100"
    
    try:
        # 检查服务健康状态
        response = requests.get(f"{triton_url}/v2/health/ready", timeout=10)
        
        if response.status_code == 200:
            print("✅ Triton 服务正常运行")
            
            # 获取服务器信息
            try:
                info_response = requests.get(f"{triton_url}/v2", timeout=5)
                if info_response.status_code == 200:
                    info = info_response.json()
                    print(f"   版本: {info.get('version', 'Unknown')}")
                    print(f"   扩展: {', '.join(info.get('extensions', []))}")
            except Exception:
                pass
            
            # 获取模型列表
            try:
                models_response = requests.get(f"{triton_url}/v2/models", timeout=5)
                if models_response.status_code == 200:
                    models = models_response.json()
                    print(f"   已加载模型数量: {len(models)}")
                    for model in models[:3]:  # 显示前3个模型
                        print(f"   - {model['name']} (版本: {model.get('versions', 'N/A')})")
            except Exception:
                pass
            
            return True
        else:
            print(f"❌ Triton 服务响应异常: {response.status_code}")
            return False
    
    except requests.ConnectionError:
        print("❌ 无法连接到 Triton 服务")
        print("   请确保 Triton 服务正在运行: docker compose up -d triton-server")
        return False
    except Exception as e:
        print(f"❌ Triton 服务检查失败: {e}")
        return False


def check_ollama_service():
    """检查 Ollama 服务"""
    print("\n🔍 检查 Ollama 服务...")
    
    ollama_url = "http://localhost:11434"
    
    try:
        # 检查服务状态
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        
        if response.status_code == 200:
            print("✅ Ollama 服务正常运行")
            
            models = response.json().get('models', [])
            print(f"   已安装模型数量: {len(models)}")
            
            for model in models[:5]:  # 显示前5个模型
                name = model.get('name', 'Unknown')
                size = model.get('size', 0)
                size_gb = size / (1024**3) if size > 0 else 0
                print(f"   - {name} ({size_gb:.1f}GB)")
            
            return True
        else:
            print(f"❌ Ollama 服务响应异常: {response.status_code}")
            return False
    
    except requests.ConnectionError:
        print("❌ 无法连接到 Ollama 服务")
        print("   请确保 Ollama 服务正在运行: docker compose up -d ollama")
        return False
    except Exception as e:
        print(f"❌ Ollama 服务检查失败: {e}")
        return False


def check_openwebui_service():
    """检查 OpenWebUI 服务"""
    print("\n🔍 检查 OpenWebUI 服务...")
    
    webui_url = "http://localhost:3001"
    
    try:
        response = requests.get(webui_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ OpenWebUI 服务正常运行")
            print(f"   访问地址: {webui_url}")
            return True
        else:
            print(f"❌ OpenWebUI 服务响应异常: {response.status_code}")
            return False
    
    except requests.ConnectionError:
        print("❌ 无法连接到 OpenWebUI 服务")
        print("   请确保 OpenWebUI 服务正在运行: docker compose up -d open-webui")
        return False
    except Exception as e:
        print(f"❌ OpenWebUI 服务检查失败: {e}")
        return False


def check_monitoring_services():
    """检查监控服务"""
    print("\n🔍 检查监控服务...")
    
    services = {
        "Prometheus": "http://localhost:9090",
        "Grafana": "http://localhost:3002"
    }
    
    all_ok = True
    
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} 服务正常运行")
                print(f"   访问地址: {url}")
            else:
                print(f"❌ {service_name} 服务响应异常: {response.status_code}")
                all_ok = False
        except requests.ConnectionError:
            print(f"❌ 无法连接到 {service_name} 服务")
            all_ok = False
        except Exception as e:
            print(f"❌ {service_name} 服务检查失败: {e}")
            all_ok = False
    
    return all_ok


def run_simple_triton_test():
    """运行简单的 Triton 推理测试"""
    print("\n🧪 运行 Triton 推理测试...")
    
    try:
        returncode, output = run_command("python test_triton_client.py --server-url http://localhost:8100")
        
        if returncode == 0:
            print("✅ Triton 推理测试成功")
            # 提取关键信息
            lines = output.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['推理用时', '推理结果正确', '成功请求']):
                    print(f"   {line.strip()}")
            return True
        else:
            print("❌ Triton 推理测试失败")
            print(f"   错误: {output}")
            return False
    
    except Exception as e:
        print(f"❌ 推理测试异常: {e}")
        return False


def generate_report(results: Dict[str, bool]):
    """生成测试报告"""
    print("\n" + "="*60)
    print("📊 GPU 环境测试报告")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"总测试项: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print("\n建议:")
    if not results.get("NVIDIA 驱动", False):
        print("  - 请安装 NVIDIA 显卡驱动")
    
    if not results.get("Docker GPU 支持", False):
        print("  - 请安装 NVIDIA Container Toolkit")
        print("    参考: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html")
    
    if not all(results.get(service, False) for service in ["Triton 服务", "Ollama 服务", "OpenWebUI 服务"]):
        print("  - 请启动相关服务: ./start.sh")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！AI 中台增强版已准备就绪。")
        print("\n🚀 快速开始:")
        print("  - 访问 OpenWebUI: http://localhost:3001")
        print("  - 访问 Triton 服务: http://localhost:8100")
        print("  - 访问 Grafana 监控: http://localhost:3002 (admin/admin123)")
    else:
        print("\n⚠️ 部分测试失败，请根据上述建议进行修复。")


def main():
    print("🤖 AI 中台增强版 - GPU 环境测试")
    print("="*60)
    
    results = {}
    
    # 基础环境检查
    results["NVIDIA 驱动"] = check_nvidia_driver()
    results["Docker GPU 支持"] = check_docker_gpu()
    
    # 服务检查
    results["Triton 服务"] = check_triton_service()
    results["Ollama 服务"] = check_ollama_service()
    results["OpenWebUI 服务"] = check_openwebui_service()
    results["监控服务"] = check_monitoring_services()
    
    # 功能测试
    if results["Triton 服务"]:
        results["Triton 推理测试"] = run_simple_triton_test()
    
    # 生成报告
    generate_report(results)


if __name__ == "__main__":
    main()
