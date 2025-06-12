#!/usr/bin/env python3
"""
AI 中台增强版综合验证脚本
验证所有服务是否正常运行并提供快速诊断
"""

import requests
import subprocess
import time
import json
import sys
from typing import Dict, List, Optional


class AIPllatformValidator:
    """AI 中台验证器"""
    
    def __init__(self):
        self.services = {
            "Django 后端": "http://localhost:8000",
            "前端界面": "http://localhost:3000",
            "Triton 推理": "http://localhost:8100",
            "OpenWebUI": "http://localhost:3001",
            "Grafana": "http://localhost:3002",
            "Prometheus": "http://localhost:9090",
            "MinIO": "http://localhost:9001"
        }
        
        self.api_endpoints = {
            "API 根路径": "http://localhost:8000/",
            "Swagger 文档": "http://localhost:8000/swagger/",
            "API 健康检查": "http://localhost:8000/api/health/",
            "用户认证": "http://localhost:8000/api/auth/",
        }
        
        self.results = {}
    
    def check_service(self, name: str, url: str, timeout: int = 5) -> Dict:
        """检查单个服务状态"""
        try:
            response = requests.get(url, timeout=timeout)
            return {
                "status": "success" if response.status_code == 200 else "warning",
                "code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "error": None
            }
        except requests.ConnectionError:
            return {
                "status": "error",
                "code": None,
                "response_time": None,
                "error": "连接失败"
            }
        except requests.Timeout:
            return {
                "status": "error",
                "code": None,
                "response_time": None,
                "error": "请求超时"
            }
        except Exception as e:
            return {
                "status": "error",
                "code": None,
                "response_time": None,
                "error": str(e)
            }
    
    def check_docker_services(self) -> Dict:
        """检查 Docker 服务状态"""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                try:
                    services = []
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            service = json.loads(line)
                            services.append({
                                "name": service.get("Service", "Unknown"),
                                "state": service.get("State", "Unknown"),
                                "status": service.get("Status", "Unknown")
                            })
                    
                    return {
                        "status": "success",
                        "services": services,
                        "error": None
                    }
                except json.JSONDecodeError:
                    # 如果 JSON 解析失败，尝试解析普通格式
                    lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                    services = []
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 4:
                            services.append({
                                "name": parts[0],
                                "state": parts[3] if len(parts) > 3 else "Unknown",
                                "status": " ".join(parts[4:]) if len(parts) > 4 else "Unknown"
                            })
                    
                    return {
                        "status": "success",
                        "services": services,
                        "error": None
                    }
            else:
                return {
                    "status": "error",
                    "services": [],
                    "error": result.stderr
                }
        
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "services": [],
                "error": "Docker 命令超时"
            }
        except Exception as e:
            return {
                "status": "error",
                "services": [],
                "error": str(e)
            }
    
    def check_triton_models(self) -> Dict:
        """检查 Triton 模型状态"""
        try:
            response = requests.get("http://localhost:8100/v2/models", timeout=10)
            if response.status_code == 200:
                models = response.json()
                return {
                    "status": "success",
                    "count": len(models),
                    "models": [{"name": m["name"], "versions": m.get("versions", [])} for m in models],
                    "error": None
                }
            else:
                return {
                    "status": "error",
                    "count": 0,
                    "models": [],
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "count": 0,
                "models": [],
                "error": str(e)
            }
    
    def check_ollama_models(self) -> Dict:
        """检查 Ollama 模型状态"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "status": "success",
                    "count": len(models),
                    "models": [{"name": m.get("name", "Unknown"), "size": m.get("size", 0)} for m in models],
                    "error": None
                }
            else:
                return {
                    "status": "error",
                    "count": 0,
                    "models": [],
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "count": 0,
                "models": [],
                "error": str(e)
            }
    
    def run_comprehensive_check(self):
        """运行综合检查"""
        print("🤖 AI 中台增强版 - 综合验证")
        print("=" * 60)
        
        # 检查 Docker 服务
        print("\n🐳 检查 Docker 服务状态...")
        docker_result = self.check_docker_services()
        self.results["Docker 服务"] = docker_result
        
        if docker_result["status"] == "success":
            print("✅ Docker 服务正常")
            running_services = [s for s in docker_result["services"] if "running" in s["state"].lower()]
            print(f"   运行中的服务: {len(running_services)}/{len(docker_result['services'])}")
            
            for service in docker_result["services"]:
                status_icon = "✅" if "running" in service["state"].lower() else "❌"
                print(f"   {status_icon} {service['name']}: {service['state']}")
        else:
            print("❌ Docker 服务检查失败")
            print(f"   错误: {docker_result['error']}")
        
        # 检查 Web 服务
        print("\n🌐 检查 Web 服务...")
        for name, url in self.services.items():
            result = self.check_service(name, url)
            self.results[name] = result
            
            if result["status"] == "success":
                print(f"✅ {name}: 正常 ({result['response_time']:.2f}s)")
            elif result["status"] == "warning":
                print(f"⚠️ {name}: 响应异常 (HTTP {result['code']})")
            else:
                print(f"❌ {name}: {result['error']}")
        
        # 检查 API 端点
        print("\n🔌 检查 API 端点...")
        for name, url in self.api_endpoints.items():
            result = self.check_service(name, url)
            self.results[name] = result
            
            if result["status"] == "success":
                print(f"✅ {name}: 正常")
            else:
                print(f"❌ {name}: {result['error'] if result['error'] else f'HTTP {result['code']}'}")
        
        # 检查 Triton 模型
        print("\n🔥 检查 Triton 模型...")
        triton_models = self.check_triton_models()
        self.results["Triton 模型"] = triton_models
        
        if triton_models["status"] == "success":
            print(f"✅ Triton 模型: {triton_models['count']} 个模型已加载")
            for model in triton_models["models"][:3]:  # 显示前3个
                print(f"   - {model['name']} (版本: {model['versions']})")
        else:
            print(f"❌ Triton 模型检查失败: {triton_models['error']}")
        
        # 检查 Ollama 模型
        print("\n🐪 检查 Ollama 模型...")
        ollama_models = self.check_ollama_models()
        self.results["Ollama 模型"] = ollama_models
        
        if ollama_models["status"] == "success":
            print(f"✅ Ollama 模型: {ollama_models['count']} 个模型已安装")
            for model in ollama_models["models"][:3]:  # 显示前3个
                size_gb = model['size'] / (1024**3) if model['size'] > 0 else 0
                print(f"   - {model['name']} ({size_gb:.1f}GB)")
        else:
            print(f"❌ Ollama 模型检查失败: {ollama_models['error']}")
    
    def generate_summary(self):
        """生成验证摘要"""
        print("\n" + "=" * 60)
        print("📊 验证摘要")
        print("=" * 60)
        
        total_checks = len(self.results)
        successful_checks = sum(1 for r in self.results.values() 
                               if isinstance(r, dict) and r.get("status") == "success")
        
        print(f"总检查项: {total_checks}")
        print(f"成功项: {successful_checks}")
        print(f"失败项: {total_checks - successful_checks}")
        print(f"成功率: {successful_checks/total_checks*100:.1f}%")
        
        # 关键服务状态
        print("\n🔑 关键服务状态:")
        key_services = ["Django 后端", "Triton 推理", "OpenWebUI"]
        for service in key_services:
            if service in self.results:
                result = self.results[service]
                status = "✅" if result.get("status") == "success" else "❌"
                print(f"   {status} {service}")
        
        # 访问地址
        if successful_checks > 0:
            print("\n🌐 可用服务地址:")
            for name, url in self.services.items():
                if name in self.results and self.results[name].get("status") == "success":
                    print(f"   - {name}: {url}")
        
        # 故障排除建议
        failed_services = [name for name, result in self.results.items() 
                          if isinstance(result, dict) and result.get("status") != "success"]
        
        if failed_services:
            print("\n🔧 故障排除建议:")
            
            if "Docker 服务" in failed_services:
                print("   - 检查 Docker 是否正在运行: docker --version")
                print("   - 启动服务: ./start.sh")
            
            if any("Triton" in service for service in failed_services):
                print("   - 检查 GPU 支持: python test_gpu_environment.py")
                print("   - 重启 Triton: docker compose restart triton-server")
            
            if any("Ollama" in service for service in failed_services):
                print("   - 启动 Ollama: docker compose up -d ollama")
                print("   - 下载模型: docker compose exec ollama ollama pull qwen2:0.5b")
            
            print("   - 查看详细日志: docker compose logs [service-name]")
        
        # 最终状态
        if successful_checks == total_checks:
            print("\n🎉 所有检查通过！AI 中台增强版运行正常。")
        elif successful_checks >= total_checks * 0.8:
            print("\n⚠️ 大部分服务正常，部分服务需要注意。")
        else:
            print("\n❌ 多个服务存在问题，请检查部署配置。")


def main():
    validator = AIPllatformValidator()
    
    try:
        validator.run_comprehensive_check()
        validator.generate_summary()
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断验证")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 验证过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
