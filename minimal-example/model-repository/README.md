# Triton Inference Server 模型仓库说明

此目录用于存放 Triton Inference Server 的模型。

## 目录结构
```
model-repository/
└── model_name/
    ├── config.pbtxt       # 模型配置文件
    └── 1/                 # 版本目录
        └── model.onnx     # 模型文件
```

## 示例配置

对于测试，您可以添加一个简单的模型或使用 Triton 的示例模型。

目前为空目录，Triton Server 将启动但不加载任何模型。
