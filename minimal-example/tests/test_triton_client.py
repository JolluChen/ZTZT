#!/usr/bin/env python3
"""
Triton Inference Server 客户端测试脚本
用于测试部署在 Triton 上的模型推理功能
"""

import numpy as np
import requests
import json
import time
import argparse
from typing import Dict, Any, List


class TritonClient:
    """简化的 Triton HTTP 客户端"""
    
    def __init__(self, server_url: str = "http://localhost:8100"):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
    
    def is_server_ready(self) -> bool:
        """检查服务器是否就绪"""
        try:
            response = self.session.get(f"{self.server_url}/v2/health/ready")
            return response.status_code == 200
        except Exception as e:
            print(f"服务器连接失败: {e}")
            return False
    
    def get_server_metadata(self) -> Dict[str, Any]:
        """获取服务器元数据"""
        response = self.session.get(f"{self.server_url}/v2")
        return response.json()
    
    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """获取模型元数据"""
        response = self.session.get(f"{self.server_url}/v2/models/{model_name}")
        return response.json()
    
    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有可用模型"""
        response = self.session.get(f"{self.server_url}/v2/models")
        return response.json()
    
    def infer(self, model_name: str, inputs: List[Dict], outputs: List[Dict]) -> Dict[str, Any]:
        """执行推理"""
        payload = {
            "inputs": inputs,
            "outputs": outputs
        }
        
        response = self.session.post(
            f"{self.server_url}/v2/models/{model_name}/infer",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            raise Exception(f"推理失败: {response.status_code} - {response.text}")
        
        return response.json()


def test_simple_python_model(client: TritonClient):
    """测试简单的 Python 模型"""
    model_name = "simple-python-model"
    
    print(f"\n=== 测试模型: {model_name} ===")
    
    # 检查模型是否可用
    try:
        metadata = client.get_model_metadata(model_name)
        print(f"模型元数据: {json.dumps(metadata, indent=2)}")
    except Exception as e:
        print(f"获取模型元数据失败: {e}")
        return
    
    # 准备测试数据
    input_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    
    # 构造推理请求
    inputs = [{
        "name": "INPUT",
        "shape": list(input_data.shape),
        "datatype": "FP32",
        "data": input_data.tolist()
    }]
    
    outputs = [{
        "name": "OUTPUT"
    }]
    
    # 执行推理
    try:
        start_time = time.time()
        result = client.infer(model_name, inputs, outputs)
        end_time = time.time()
        
        print(f"推理用时: {(end_time - start_time) * 1000:.2f} ms")
        print(f"输入数据: {input_data}")
        
        if "outputs" in result and len(result["outputs"]) > 0:
            output_data = np.array(result["outputs"][0]["data"])
            print(f"输出数据: {output_data}")
            print(f"预期输出: {np.square(input_data)}")
            
            # 验证结果
            expected = np.square(input_data)
            if np.allclose(output_data, expected):
                print("✅ 推理结果正确!")
            else:
                print("❌ 推理结果不正确!")
        else:
            print("❌ 未收到输出数据")
            
    except Exception as e:
        print(f"推理失败: {e}")


def benchmark_model(client: TritonClient, model_name: str, num_requests: int = 100):
    """对模型进行性能基准测试"""
    print(f"\n=== 性能测试: {model_name} (请求数: {num_requests}) ===")
    
    # 准备测试数据
    input_data = np.random.random((10,)).astype(np.float32)
    
    inputs = [{
        "name": "INPUT",
        "shape": list(input_data.shape),
        "datatype": "FP32",
        "data": input_data.tolist()
    }]
    
    outputs = [{"name": "OUTPUT"}]
    
    # 执行基准测试
    times = []
    success_count = 0
    
    for i in range(num_requests):
        try:
            start_time = time.time()
            result = client.infer(model_name, inputs, outputs)
            end_time = time.time()
            
            times.append((end_time - start_time) * 1000)  # 转换为毫秒
            success_count += 1
            
            if (i + 1) % 10 == 0:
                print(f"已完成 {i + 1}/{num_requests} 个请求")
                
        except Exception as e:
            print(f"请求 {i + 1} 失败: {e}")
    
    # 计算统计信息
    if times:
        avg_time = np.mean(times)
        min_time = np.min(times)
        max_time = np.max(times)
        p50_time = np.percentile(times, 50)
        p95_time = np.percentile(times, 95)
        p99_time = np.percentile(times, 99)
        throughput = success_count / (sum(times) / 1000)  # 请求/秒
        
        print(f"\n性能统计:")
        print(f"  成功请求: {success_count}/{num_requests}")
        print(f"  平均延迟: {avg_time:.2f} ms")
        print(f"  最小延迟: {min_time:.2f} ms")
        print(f"  最大延迟: {max_time:.2f} ms")
        print(f"  P50 延迟: {p50_time:.2f} ms")
        print(f"  P95 延迟: {p95_time:.2f} ms")
        print(f"  P99 延迟: {p99_time:.2f} ms")
        print(f"  吞吐量: {throughput:.2f} 请求/秒")


def main():
    parser = argparse.ArgumentParser(description="Triton Inference Server 测试客户端")
    parser.add_argument("--server-url", default="http://localhost:8100", 
                       help="Triton 服务器 URL")
    parser.add_argument("--benchmark", action="store_true", 
                       help="执行性能基准测试")
    parser.add_argument("--num-requests", type=int, default=100,
                       help="基准测试的请求数量")
    
    args = parser.parse_args()
    
    # 创建客户端
    client = TritonClient(args.server_url)
    
    # 检查服务器状态
    print("检查 Triton 服务器状态...")
    if not client.is_server_ready():
        print("❌ Triton 服务器未就绪，请检查服务器是否正在运行")
        return
    
    print("✅ Triton 服务器就绪")
    
    # 获取服务器信息
    try:
        server_metadata = client.get_server_metadata()
        print(f"服务器版本: {server_metadata.get('version', 'Unknown')}")
    except Exception as e:
        print(f"获取服务器信息失败: {e}")
    
    # 列出可用模型
    try:
        models = client.list_models()
        print(f"\n可用模型: {[model['name'] for model in models]}")
    except Exception as e:
        print(f"获取模型列表失败: {e}")
        return
    
    # 测试简单 Python 模型
    test_simple_python_model(client)
    
    # 可选的性能基准测试
    if args.benchmark:
        benchmark_model(client, "simple-python-model", args.num_requests)


if __name__ == "__main__":
    main()
