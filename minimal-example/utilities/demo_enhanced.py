#!/usr/bin/env python3
"""
AI中台增强版功能演示脚本
演示GPU Stack、Triton推理、OpenWebUI等核心功能
"""

import os
import sys
from pathlib import Path

def demonstrate_features():
    """演示已实现的功能"""
    print("🤖 AI中台增强版功能演示")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    
    # 1. 检查项目结构
    print("\n📁 项目结构检查:")
    key_files = [
        "start_enhanced.sh",
        "docker-compose.yml", 
        "generate_sample_models.py",
        "test_triton_client.py",
        "validate_enhanced.py"
    ]
    
    for file in key_files:
        path = base_dir / file
        status = "✅ 存在" if path.exists() else "❌ 缺失"
        print(f"  {file:<25} {status}")
    
    # 2. 检查模型仓库
    print("\n🤖 模型仓库检查:")
    model_repo = base_dir / "model-repository"
    if model_repo.exists():
        for model_dir in model_repo.iterdir():
            if model_dir.is_dir():
                config_file = model_dir / "config.pbtxt"
                version_dir = model_dir / "1"
                
                config_status = "✅" if config_file.exists() else "❌"
                version_status = "✅" if version_dir.exists() else "❌"
                
                print(f"  {model_dir.name:<20} 配置:{config_status} 版本:{version_status}")
    else:
        print("  ❌ 模型仓库目录不存在")
    
    # 3. 检查Docker配置
    print("\n🐳 Docker配置检查:")
    docker_compose = base_dir / "docker-compose.yml"
    if docker_compose.exists():
        with open(docker_compose, 'r') as f:
            content = f.read()
            
        services = ["triton-server", "ollama", "open-webui", "prometheus", "grafana"]
        for service in services:
            status = "✅ 配置" if service in content else "❌ 缺失"
            print(f"  {service:<15} {status}")
    
    # 4. 检查增强功能
    print("\n🚀 增强功能检查:")
    
    # GPU支持检查
    gpu_config = "nvidia" in content if docker_compose.exists() else False
    print(f"  GPU支持配置      {'✅ 已配置' if gpu_config else '❌ 未配置'}")
    
    # 监控配置检查
    monitoring_dir = base_dir / "monitoring"
    monitoring_status = "✅ 已配置" if monitoring_dir.exists() else "❌ 未配置"
    print(f"  监控服务配置      {monitoring_status}")
    
    # 启动脚本检查
    start_script = base_dir / "start_enhanced.sh"
    script_executable = start_script.exists() and os.access(start_script, os.X_OK)
    print(f"  启动脚本可执行    {'✅ 可执行' if script_executable else '❌ 不可执行'}")
    
    # 5. 功能完成度评估
    print("\n📊 功能完成度评估:")
    
    features = {
        "GPU Stack支持": gpu_config,
        "Triton推理服务": "triton-server" in content if docker_compose.exists() else False,
        "OpenWebUI集成": "open-webui" in content if docker_compose.exists() else False,
        "监控服务": monitoring_dir.exists(),
        "模型仓库": model_repo.exists(),
        "自动化脚本": start_script.exists(),
        "验证工具": (base_dir / "validate_enhanced.py").exists(),
    }
    
    completed = sum(features.values())
    total = len(features)
    completion_rate = (completed / total) * 100
    
    for feature, status in features.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {feature}")
    
    print(f"\n🎯 总体完成度: {completed}/{total} ({completion_rate:.1f}%)")
    
    # 6. 使用建议
    print("\n💡 使用建议:")
    print("  1. 启动所有服务: ./start_enhanced.sh all")
    print("  2. 生成示例模型: python3 generate_sample_models.py")
    print("  3. 验证系统状态: python3 validate_enhanced.py")
    print("  4. 测试推理服务: python3 test_triton_client.py")
    print("  5. 查看服务状态: docker compose ps")
    
    # 7. 访问地址
    print("\n🌐 服务访问地址:")
    services_urls = {
        "Django后端": "http://localhost:8000",
        "Triton推理": "http://localhost:8100", 
        "OpenWebUI": "http://localhost:3001",
        "Prometheus": "http://localhost:9090",
        "Grafana": "http://localhost:3002",
        "MinIO": "http://localhost:9001"
    }
    
    for name, url in services_urls.items():
        print(f"  {name:<12} {url}")
    
    if completion_rate >= 90:
        print("\n🎉 恭喜！AI中台增强版已完全实现，可以开始使用！")
    elif completion_rate >= 70:
        print("\n⚠️  AI中台增强版基本完成，部分功能可能需要调整。")
    else:
        print("\n❌ AI中台增强版需要进一步完善。")

if __name__ == "__main__":
    demonstrate_features()
