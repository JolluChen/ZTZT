#!/usr/bin/env python3
"""
Triton 模型管理工具
用于管理 Triton Inference Server 的模型仓库
"""

import os
import json
import shutil
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Optional


class TritonModelManager:
    """Triton 模型管理器"""
    
    def __init__(self, model_repo_path: str = "./model-repository", 
                 triton_url: str = "http://localhost:8100"):
        self.model_repo_path = Path(model_repo_path)
        self.triton_url = triton_url.rstrip('/')
        
    def create_model_directory(self, model_name: str, version: str = "1") -> Path:
        """创建模型目录结构"""
        model_path = self.model_repo_path / model_name
        version_path = model_path / version
        
        model_path.mkdir(parents=True, exist_ok=True)
        version_path.mkdir(parents=True, exist_ok=True)
        
        return model_path
    
    def create_python_model_template(self, model_name: str, 
                                   input_name: str = "INPUT",
                                   output_name: str = "OUTPUT",
                                   input_shape: List[int] = [-1],
                                   output_shape: List[int] = [-1],
                                   datatype: str = "FP32",
                                   max_batch_size: int = 16) -> None:
        """创建 Python 模型模板"""
        
        model_path = self.create_model_directory(model_name)
        
        # 创建 config.pbtxt
        config_content = f'''name: "{model_name}"
backend: "python"
max_batch_size: {max_batch_size}

input [
  {{
    name: "{input_name}"
    data_type: TYPE_{datatype}
    dims: {input_shape}
  }}
]

output [
  {{
    name: "{output_name}"
    data_type: TYPE_{datatype}
    dims: {output_shape}
  }}
]

instance_group [
  {{
    count: 1
    kind: KIND_CPU
  }}
]

dynamic_batching {{
  max_queue_delay_microseconds: 100
}}'''
        
        with open(model_path / "config.pbtxt", "w") as f:
            f.write(config_content)
        
        # 创建 model.py 模板
        model_py_content = f'''import json
import numpy as np
import triton_python_backend_utils as pb_utils


class TritonPythonModel:
    """
    {model_name} 模型实现
    """

    def initialize(self, args):
        """模型初始化"""
        self.model_config = model_config = json.loads(args['model_config'])
        
        output_config = pb_utils.get_output_config_by_name(
            model_config, "{output_name}")
        self.output_dtype = pb_utils.triton_string_to_numpy(
            output_config['data_type'])

    def execute(self, requests):
        """执行推理"""
        responses = []

        for request in requests:
            # 获取输入
            input_tensor = pb_utils.get_input_tensor_by_name(request, "{input_name}")
            input_data = input_tensor.as_numpy()
            
            # TODO: 在这里实现您的模型逻辑
            # 当前示例：简单的恒等变换
            output_data = input_data.astype(self.output_dtype)
            
            # 创建输出
            output_tensor = pb_utils.Tensor("{output_name}", output_data)
            inference_response = pb_utils.InferenceResponse(
                output_tensors=[output_tensor])
            responses.append(inference_response)

        return responses

    def finalize(self):
        """模型清理"""
        print(f'{model_name} 模型清理完成')'''
        
        with open(model_path / "1" / "model.py", "w") as f:
            f.write(model_py_content)
        
        print(f"✅ Python 模型模板已创建: {model_path}")
    
    def create_onnx_model_template(self, model_name: str,
                                 onnx_file_path: str,
                                 input_name: str = "input",
                                 output_name: str = "output",
                                 input_shape: List[int] = [-1, 3, 224, 224],
                                 output_shape: List[int] = [-1, 1000],
                                 datatype: str = "FP32",
                                 max_batch_size: int = 8) -> None:
        """创建 ONNX 模型配置"""
        
        model_path = self.create_model_directory(model_name)
        
        # 复制 ONNX 文件
        if os.path.exists(onnx_file_path):
            shutil.copy2(onnx_file_path, model_path / "1" / "model.onnx")
        else:
            print(f"⚠️ ONNX 文件不存在: {onnx_file_path}")
        
        # 创建 config.pbtxt
        config_content = f'''name: "{model_name}"
platform: "onnxruntime_onnx"
max_batch_size: {max_batch_size}

input [
  {{
    name: "{input_name}"
    data_type: TYPE_{datatype}
    dims: {input_shape}
  }}
]

output [
  {{
    name: "{output_name}"
    data_type: TYPE_{datatype}
    dims: {output_shape}
  }}
]

instance_group [
  {{
    count: 1
    kind: KIND_GPU
  }}
]

optimization {{
  execution_accelerators {{
    gpu_execution_accelerator : [
      {{
        name : "tensorrt"
        parameters {{ key: "precision_mode" value: "FP16" }}
        parameters {{ key: "max_workspace_size_bytes" value: "1073741824" }}
      }}
    ]
  }}
}}'''
        
        with open(model_path / "config.pbtxt", "w") as f:
            f.write(config_content)
        
        print(f"✅ ONNX 模型配置已创建: {model_path}")
    
    def list_models(self) -> List[str]:
        """列出本地模型"""
        if not self.model_repo_path.exists():
            return []
        
        models = []
        for item in self.model_repo_path.iterdir():
            if item.is_dir() and (item / "config.pbtxt").exists():
                models.append(item.name)
        
        return models
    
    def validate_model(self, model_name: str) -> bool:
        """验证模型配置"""
        model_path = self.model_repo_path / model_name
        
        if not model_path.exists():
            print(f"❌ 模型目录不存在: {model_path}")
            return False
        
        config_file = model_path / "config.pbtxt"
        if not config_file.exists():
            print(f"❌ 配置文件不存在: {config_file}")
            return False
        
        # 检查版本目录
        version_dirs = [d for d in model_path.iterdir() 
                       if d.is_dir() and d.name.isdigit()]
        if not version_dirs:
            print(f"❌ 没有找到版本目录")
            return False
        
        print(f"✅ 模型 {model_name} 配置正确")
        return True
    
    def get_triton_models(self) -> Optional[List[Dict]]:
        """获取 Triton 服务器上的模型列表"""
        try:
            response = requests.get(f"{self.triton_url}/v2/models")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 获取 Triton 模型列表失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 连接 Triton 服务器失败: {e}")
            return None
    
    def load_model(self, model_name: str) -> bool:
        """加载模型到 Triton"""
        try:
            response = requests.post(f"{self.triton_url}/v2/repository/models/{model_name}/load")
            if response.status_code == 200:
                print(f"✅ 模型 {model_name} 加载成功")
                return True
            else:
                print(f"❌ 模型 {model_name} 加载失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 加载模型失败: {e}")
            return False
    
    def unload_model(self, model_name: str) -> bool:
        """从 Triton 卸载模型"""
        try:
            response = requests.post(f"{self.triton_url}/v2/repository/models/{model_name}/unload")
            if response.status_code == 200:
                print(f"✅ 模型 {model_name} 卸载成功")
                return True
            else:
                print(f"❌ 模型 {model_name} 卸载失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 卸载模型失败: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Triton 模型管理工具")
    parser.add_argument("--repo-path", default="./model-repository", 
                       help="模型仓库路径")
    parser.add_argument("--triton-url", default="http://localhost:8100",
                       help="Triton 服务器 URL")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 列出模型
    subparsers.add_parser("list", help="列出本地模型")
    
    # 列出 Triton 上的模型
    subparsers.add_parser("list-triton", help="列出 Triton 服务器上的模型")
    
    # 创建 Python 模型
    create_python_parser = subparsers.add_parser("create-python", help="创建 Python 模型模板")
    create_python_parser.add_argument("model_name", help="模型名称")
    create_python_parser.add_argument("--input-name", default="INPUT", help="输入张量名称")
    create_python_parser.add_argument("--output-name", default="OUTPUT", help="输出张量名称")
    create_python_parser.add_argument("--max-batch-size", type=int, default=16, help="最大批处理大小")
    
    # 创建 ONNX 模型
    create_onnx_parser = subparsers.add_parser("create-onnx", help="创建 ONNX 模型配置")
    create_onnx_parser.add_argument("model_name", help="模型名称")
    create_onnx_parser.add_argument("onnx_file", help="ONNX 文件路径")
    create_onnx_parser.add_argument("--input-name", default="input", help="输入张量名称")
    create_onnx_parser.add_argument("--output-name", default="output", help="输出张量名称")
    create_onnx_parser.add_argument("--max-batch-size", type=int, default=8, help="最大批处理大小")
    
    # 验证模型
    validate_parser = subparsers.add_parser("validate", help="验证模型配置")
    validate_parser.add_argument("model_name", help="模型名称")
    
    # 加载模型
    load_parser = subparsers.add_parser("load", help="加载模型到 Triton")
    load_parser.add_argument("model_name", help="模型名称")
    
    # 卸载模型
    unload_parser = subparsers.add_parser("unload", help="从 Triton 卸载模型")
    unload_parser.add_argument("model_name", help="模型名称")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = TritonModelManager(args.repo_path, args.triton_url)
    
    if args.command == "list":
        models = manager.list_models()
        if models:
            print("本地模型:")
            for model in models:
                print(f"  📦 {model}")
        else:
            print("没有找到本地模型")
    
    elif args.command == "list-triton":
        models = manager.get_triton_models()
        if models:
            print("Triton 服务器上的模型:")
            for model in models:
                print(f"  🔥 {model['name']} (版本: {model.get('versions', 'N/A')})")
        else:
            print("无法获取 Triton 服务器上的模型")
    
    elif args.command == "create-python":
        manager.create_python_model_template(
            args.model_name,
            args.input_name,
            args.output_name,
            max_batch_size=args.max_batch_size
        )
    
    elif args.command == "create-onnx":
        manager.create_onnx_model_template(
            args.model_name,
            args.onnx_file,
            args.input_name,
            args.output_name,
            max_batch_size=args.max_batch_size
        )
    
    elif args.command == "validate":
        manager.validate_model(args.model_name)
    
    elif args.command == "load":
        manager.load_model(args.model_name)
    
    elif args.command == "unload":
        manager.unload_model(args.model_name)


if __name__ == "__main__":
    main()
