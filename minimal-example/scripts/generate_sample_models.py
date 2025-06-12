#!/usr/bin/env python3
"""
简单 ONNX 模型生成器
用于创建演示用的 ONNX 模型
"""

import numpy as np
import onnx
from onnx import helper, TensorProto, mapping
import os


def create_simple_linear_model():
    """创建一个简单的线性模型"""
    
    # 定义输入
    input_tensor = helper.make_tensor_value_info(
        'input', TensorProto.FLOAT, [1, 10]
    )
    
    # 定义输出
    output_tensor = helper.make_tensor_value_info(
        'output', TensorProto.FLOAT, [1, 5]
    )
    
    # 创建权重张量
    weight_np = np.random.randn(10, 5).astype(np.float32)
    weight_tensor = helper.make_tensor(
        name='weight',
        data_type=TensorProto.FLOAT,
        dims=weight_np.shape,
        vals=weight_np.flatten()
    )
    
    # 创建偏置张量
    bias_np = np.random.randn(5).astype(np.float32)
    bias_tensor = helper.make_tensor(
        name='bias',
        data_type=TensorProto.FLOAT,
        dims=bias_np.shape,
        vals=bias_np.flatten()
    )
    
    # 创建 MatMul 节点
    matmul_node = helper.make_node(
        'MatMul',
        inputs=['input', 'weight'],
        outputs=['matmul_output'],
        name='matmul'
    )
    
    # 创建 Add 节点
    add_node = helper.make_node(
        'Add',
        inputs=['matmul_output', 'bias'],
        outputs=['output'],
        name='add'
    )
    
    # 创建图
    graph = helper.make_graph(
        nodes=[matmul_node, add_node],
        name='SimpleLinearModel',
        inputs=[input_tensor],
        outputs=[output_tensor],
        initializer=[weight_tensor, bias_tensor]
    )
    
    # 创建模型
    model = helper.make_model(graph, producer_name='simple-model-generator')
    model.opset_import[0].version = 11
    
    return model


def create_simple_cnn_model():
    """创建一个简单的 CNN 模型 (用于图像分类演示)"""
    
    # 定义输入 (batch_size, channels, height, width)
    input_tensor = helper.make_tensor_value_info(
        'input', TensorProto.FLOAT, [1, 3, 224, 224]
    )
    
    # 定义输出 (batch_size, num_classes)
    output_tensor = helper.make_tensor_value_info(
        'output', TensorProto.FLOAT, [1, 1000]
    )
    
    nodes = []
    initializers = []
    
    # 全局平均池化
    gap_node = helper.make_node(
        'GlobalAveragePool',
        inputs=['input'],
        outputs=['gap_output'],
        name='global_average_pool'
    )
    nodes.append(gap_node)
    
    # Flatten
    flatten_node = helper.make_node(
        'Flatten',
        inputs=['gap_output'],
        outputs=['flatten_output'],
        name='flatten',
        axis=1
    )
    nodes.append(flatten_node)
    
    # 全连接层权重
    fc_weight = np.random.randn(3, 1000).astype(np.float32) * 0.01
    fc_weight_tensor = helper.make_tensor(
        name='fc_weight',
        data_type=TensorProto.FLOAT,
        dims=fc_weight.shape,
        vals=fc_weight.flatten()
    )
    initializers.append(fc_weight_tensor)
    
    # 全连接层偏置
    fc_bias = np.zeros(1000).astype(np.float32)
    fc_bias_tensor = helper.make_tensor(
        name='fc_bias',
        data_type=TensorProto.FLOAT,
        dims=fc_bias.shape,
        vals=fc_bias.flatten()
    )
    initializers.append(fc_bias_tensor)
    
    # 全连接层
    fc_node = helper.make_node(
        'MatMul',
        inputs=['flatten_output', 'fc_weight'],
        outputs=['fc_output'],
        name='fc'
    )
    nodes.append(fc_node)
    
    # 添加偏置
    add_node = helper.make_node(
        'Add',
        inputs=['fc_output', 'fc_bias'],
        outputs=['output'],
        name='add_bias'
    )
    nodes.append(add_node)
    
    # 创建图
    graph = helper.make_graph(
        nodes=nodes,
        name='SimpleCNNModel',
        inputs=[input_tensor],
        outputs=[output_tensor],
        initializer=initializers
    )
    
    # 创建模型
    model = helper.make_model(graph, producer_name='simple-cnn-generator')
    model.opset_import[0].version = 11
    
    return model


def save_model(model, filename):
    """保存模型到文件"""
    # 检查模型
    onnx.checker.check_model(model)
    
    # 保存模型
    onnx.save(model, filename)
    print(f"✅ 模型已保存到: {filename}")
    
    # 显示模型信息
    print(f"   模型大小: {os.path.getsize(filename) / 1024:.1f} KB")
    
    # 显示输入输出信息
    print("   输入:")
    for input_tensor in model.graph.input:
        shape = [dim.dim_value for dim in input_tensor.type.tensor_type.shape.dim]
        print(f"     {input_tensor.name}: {shape}")
    
    print("   输出:")
    for output_tensor in model.graph.output:
        shape = [dim.dim_value for dim in output_tensor.type.tensor_type.shape.dim]
        print(f"     {output_tensor.name}: {shape}")


def main():
    print("🤖 ONNX 模型生成器")
    print("="*50)
    
    # 确保目录存在
    os.makedirs("model-repository/simple-linear-model/1", exist_ok=True)
    os.makedirs("model-repository/simple-cnn-model/1", exist_ok=True)
    
    # 生成简单线性模型
    print("\n📊 生成简单线性模型...")
    linear_model = create_simple_linear_model()
    save_model(linear_model, "model-repository/simple-linear-model/1/model.onnx")
    
    # 生成线性模型配置
    linear_config = '''name: "simple-linear-model"
platform: "onnxruntime_onnx"
max_batch_size: 16

input [
  {
    name: "input"
    data_type: TYPE_FP32
    dims: [ 10 ]
  }
]

output [
  {
    name: "output"
    data_type: TYPE_FP32
    dims: [ 5 ]
  }
]

instance_group [
  {
    count: 1
    kind: KIND_CPU
  }
]

parameters: {
  key: "execution_providers"
  value: { string_value: "CPUExecutionProvider" }
}

dynamic_batching {
  max_queue_delay_microseconds: 100
}'''
    
    with open("model-repository/simple-linear-model/config.pbtxt", "w") as f:
        f.write(linear_config)
    
    # 生成简单 CNN 模型
    print("\n🖼️ 生成简单 CNN 模型...")
    cnn_model = create_simple_cnn_model()
    save_model(cnn_model, "model-repository/simple-cnn-model/1/model.onnx")
    
    # 生成 CNN 模型配置
    cnn_config = '''name: "simple-cnn-model"
platform: "onnxruntime_onnx"
max_batch_size: 4

input [
  {
    name: "input"
    data_type: TYPE_FP32
    dims: [ 3, 224, 224 ]
  }
]

output [
  {
    name: "output"
    data_type: TYPE_FP32
    dims: [ 1000 ]
  }
]

instance_group [
  {
    count: 1
    kind: KIND_CPU
  }
]

parameters: {
  key: "execution_providers"
  value: { string_value: "CPUExecutionProvider" }
}

dynamic_batching {
  max_queue_delay_microseconds: 100
}'''
    
    with open("model-repository/simple-cnn-model/config.pbtxt", "w") as f:
        f.write(cnn_config)
    
    print("\n🎉 模型生成完成！")
    print("\n📁 模型文件:")
    print("  - model-repository/simple-linear-model/1/model.onnx")
    print("  - model-repository/simple-cnn-model/1/model.onnx")
    
    print("\n🧪 测试建议:")
    print("  1. 启动 Triton 服务: docker compose up -d triton-server")
    print("  2. 验证模型加载: python manage_triton_models.py list-triton")
    print("  3. 运行推理测试: python test_triton_client.py")


if __name__ == "__main__":
    try:
        import onnx
        main()
    except ImportError:
        print("❌ 需要安装 onnx 库: pip install onnx")
        print("   或者直接使用预生成的示例模型")
