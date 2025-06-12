# AI 中台增强功能开发实施规划：GPU Stack, 推理加速与 OpenWebUI

## 1. 引言

### 1.1. 文档目的
本文档是《AI 中台产品开发文档 (增强版)》的配套开发实施细则，旨在为研发团队提供关于 GPU Stack 建设、模型推理加速集成（以 NVIDIA Triton Inference Server 为核心）以及 OpenWebUI 部署与集成的详细技术指引和行动计划。本文档将具体化产品需求，明确开发步骤、技术选型、配置要点、预期成果和验证标准。

### 1.2. 范围
*   **GPU Stack 实现**: Kubernetes 集成、资源监控、调度配置。
*   **模型推理加速**: Triton Inference Server 部署、模型仓库管理、模型优化流程集成、服务接口封装。
*   **OpenWebUI 集成**: OpenWebUI 部署、后端 LLM 服务连接、用户认证（初步探讨）。

### 1.3. 关联文档
*   AI 中台产品开发文档 (增强版) (`docs/development/product_development_document_enhanced.md`)
*   项目现有架构文档 (如有)
*   Kubernetes 集群文档
*   NVIDIA GPU Operator, Triton, OpenWebUI 官方文档

## 2. GPU Stack 实施规划

目标：构建稳定、高效、可监控的 GPU 资源管理和调度能力。

### 2.1. 前提条件
*   可用的 Kubernetes 集群 (版本需与 NVIDIA GPU Operator 兼容)。
*   集群节点已安装 NVIDIA 物理 GPU 卡。
*   集群管理员权限。
*   网络可访问 NVIDIA 驱动和相关镜像仓库。

### 2.2. Kubernetes 集成步骤

#### 2.2.1. 安装 NVIDIA GPU Operator
*   **选型**: 采用 NVIDIA GPU Operator，它能自动化管理 NVIDIA GPU 驱动、Kubernetes 设备插件、容器运行时等。
*   **步骤**:
    1.  查阅官方文档，确认与当前 K8s 版本兼容的 GPU Operator 版本。
        *   参考: [NVIDIA GPU Operator Compatibility](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/platform-support.html)
    2.  添加 Helm 仓库:
        ```bash
        helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
        helm repo update
        ```
    3.  创建 Namespace (例如 `gpu-operator`):
        ```bash
        kubectl create ns gpu-operator
        ```
    4.  通过 Helm 安装 GPU Operator:
        ```bash
        helm install --wait --generate-name \
             -n gpu-operator --create-namespace \
             nvidia/gpu-operator
        ```
        *   注意：根据实际环境可能需要配置特定参数，如私有镜像仓库、驱动版本等。
    5.  验证安装：检查 `gpu-operator` namespace 下的 Pods 是否都正常运行。
        ```bash
        kubectl get pods -n gpu-operator
        ```
        检查节点是否已正确标记 GPU 资源:
        ```bash
        kubectl describe node <gpu-node-name> | grep nvidia.com/gpu
        ```

#### 2.2.2. 节点配置与验证
*   GPU Operator 会自动为 GPU 节点打上标签，如 `nvidia.com/gpu.present=true`。
*   验证设备插件是否正常工作，确保 Pod 可以请求到 `nvidia.com/gpu` 资源。

### 2.3. GPU 资源监控与告警

#### 2.3.1. 集成 DCGM Exporter
*   GPU Operator 通常会包含或可以配置部署 `dcgm-exporter` (Data Center GPU Manager Exporter) 用于暴露 GPU 指标给 Prometheus。
*   **步骤**:
    1.  确认 `dcgm-exporter` 是否已由 GPU Operator 部署并正常运行。
    2.  配置 Prometheus 抓取 `dcgm-exporter` 的 metrics 端点。这通常通过 ServiceMonitor (如果使用 Prometheus Operator) 或直接修改 Prometheus 配置文件完成。
        ```yaml
        # Prometheus scrape_configs 示例
        - job_name: 'dcgm-exporter'
          kubernetes_sd_configs:
            - role: endpoints
              namespaces:
                names: ['gpu-operator'] # 根据实际 dcgm-exporter 部署的 namespace 修改
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_label_app_kubernetes_io_name]
              action: keep
              regex: dcgm-exporter
            - source_labels: [__meta_kubernetes_endpoint_port_name]
              action: keep
              regex: metrics # 确认 dcgm-exporter service 的 metrics 端口名
        ```
#### 2.3.2. Grafana Dashboard
*   **步骤**:
    1.  导入 NVIDIA 官方提供的或社区贡献的 Grafana Dashboard for DCGM。
        *   例如 Dashboard ID: `12239` (NVIDIA DCGM Exporter Dashboard)
    2.  根据实际指标名称和需求调整 Dashboard。
    3.  关键监控指标：GPU 使用率、显存使用率、GPU 温度、功耗、SM Clock、Memory Clock、PCIe 带宽。
#### 2.3.3. 告警规则
*   在 Prometheus 中配置基于 DCGM 指标的告警规则。
*   **示例告警**:
    *   GPU 温度过高。
    *   GPU 使用率持续过低/过高。
    *   GPU 显存不足。
    *   GPU 发生 Xid 错误。

### 2.4. GPU 调度策略
*   **Pod 资源请求**: 在 Pod spec 中通过 `resources.limits` 请求 GPU:
    ```yaml
    apiVersion: v1
    kind: Pod
    metadata:
      name: gpu-pod-example
    spec:
      containers:
        - name: cuda-container
          image: nvidia/cuda:12.2.0-base-ubuntu22.04
          command: ["sleep", "3600"]
          resources:
            limits:
              nvidia.com/gpu: 1 # 请求1个GPU
      restartPolicy: OnFailure
    ```
*   **MIG (Multi-Instance GPU) 配置 (如适用)**:
    *   如果 GPU 支持 MIG 且需要细粒度切分，需通过 GPU Operator 配置 MIG 策略。
    *   Pod 请求特定 MIG 实例。
*   **优先级和抢占**: 结合 Kubernetes 的 PriorityClass 实现高优先级任务优先获得 GPU。
*   **Taints 和 Tolerations**: 可以使用 Taints 标记 GPU 节点，仅允许特定 Pod 调度上去。

### 2.5. 测试与验证
*   部署一个简单的 CUDA 应用 Pod，验证其能成功分配并使用 GPU。
*   运行 GPU benchmarks (如 `cuda-samples`) 验证 GPU 性能。
*   检查 Grafana Dashboard 数据是否正确显示。
*   触发告警测试。

## 3. 模型推理加速实施规划 (NVIDIA Triton)

目标：部署高性能、可扩展的推理服务，支持多种模型框架和优化。

### 3.1. 前提条件
*   GPU Stack 已成功部署并可用。
*   Docker 环境。
*   模型文件 (原始格式或已优化格式)。
*   网络可访问 Triton Server 镜像 (如 `nvcr.io/nvidia/tritonserver`)。

### 3.2. Triton Inference Server 部署

#### 3.2.1. 部署方式
*   **推荐**: Kubernetes Deployment + Service。
*   **步骤**:
    1.  创建 Deployment YAML 文件:
        ```yaml
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: triton-inference-server
          labels:
            app: triton
        spec:
          replicas: 1 # 根据需求调整
          selector:
            matchLabels:
              app: triton
          template:
            metadata:
              labels:
                app: triton
            spec:
              containers:
              - name: triton
                image: nvcr.io/nvidia/tritonserver:<xx.yy>-py3 # 选择合适的版本标签
                resources:
                  limits:
                    nvidia.com/gpu: 1 # 请求GPU资源
                ports:
                - containerPort: 8000 # HTTP
                - containerPort: 8001 # gRPC
                - containerPort: 8002 # Metrics
                volumeMounts:
                - name: model-repository
                  mountPath: /models
                args:
                - tritonserver
                - --model-repository=/models
                # - --model-control-mode=poll # 或者 explicit
                # - --repository-poll-secs=30 # 如果是 poll 模式
              volumes:
              - name: model-repository
                persistentVolumeClaim: # 或者 hostPath, emptyDir 等，推荐 PVC
                  claimName: triton-model-repo-pvc
        ```
    2.  创建 PersistentVolumeClaim (PVC) 用于模型仓库 (如果使用 PVC)。
    3.  创建 Service YAML 文件暴露 Triton 端口:
        ```yaml
        apiVersion: v1
        kind: Service
        metadata:
          name: triton-service
          labels:
            app: triton
        spec:
          selector:
            app: triton
          ports:
          - name: http
            port: 8000
            targetPort: 8000
          - name: grpc
            port: 8001
            targetPort: 8001
          - name: metrics
            port: 8002
            targetPort: 8002
          type: LoadBalancer # 或者 ClusterIP, NodePort
        ```
    4.  部署 `kubectl apply -f <deployment.yaml> -f <service.yaml>`。
    5.  验证 Pod 运行状态和 Service 可访问性。

### 3.3. 模型仓库 (Model Repository) 设置与管理

*   **目录结构**:
    ```
    <model-repository-path>/
      <model-name>/
        [config.pbtxt]
        <version>/
          <model-definition-file>
      <another-model-name>/
        [config.pbtxt]
        <version>/
          <model-definition-file>
        <another-version>/
          <model-definition-file>
    ```
*   **`config.pbtxt`**: 模型配置文件，定义模型平台、输入输出、实例组、动态批处理等。
    *   示例 (TensorRT):
        ```protobuf
        name: "my_tensorrt_model"
        platform: "tensorrt_plan"
        max_batch_size: 8
        input [
          {
            name: "input_tensor"
            data_type: TYPE_FP32
            dims: [ 3, 224, 224 ]
          }
        ]
        output [
          {
            name: "output_tensor"
            data_type: TYPE_FP32
            dims: [ 1000 ]
          }
        ]
        instance_group [
          {
            count: 1
            kind: KIND_GPU
          }
        ]
        ```
*   **模型管理**:
    *   **加载模式**:
        *   `NONE`: 启动时加载所有模型。
        *   `EXPLICIT`: 仅加载启动参数 `--load-model` 指定的模型，或通过 API 控制加载/卸载。
        *   `POLL`: 定期扫描模型仓库，自动加载/更新/卸载模型 (通过 `--model-control-mode=poll` 和 `--repository-poll-secs` 控制)。
    *   **版本策略**: `config.pbtxt` 中可定义版本策略 (最新、特定、全部)。
    *   **存储**: 模型仓库可位于共享文件系统 (NFS)、云存储 (S3, GCS, Azure Blob - Triton 支持直接读取) 或 PVC。

### 3.4. 模型优化流程集成

#### 3.4.1. TensorRT 优化
*   **流程**:
    1.  将原始模型 (ONNX, TensorFlow SavedModel, PyTorch via ONNX) 转换为 TensorRT Plan (`.plan` 或 `.engine` 文件)。
    2.  使用 `trtexec` 工具或 TensorRT API 进行转换。
    3.  关键参数：精度模式 (FP32, FP16, INT8)、工作空间大小、批处理大小。
    4.  INT8 量化需要校准数据集。
*   **集成**:
    *   在模型中台的部署流程中增加 TensorRT 转换步骤。
    *   脚本化转换过程，输出 `.plan` 文件到 Triton 模型仓库对应版本目录。

#### 3.4.2. ONNX Runtime 优化
*   **流程**:
    1.  确保模型为 ONNX 格式。
    2.  ONNX Runtime 本身支持多种执行提供程序 (Execution Providers, EP)，如 CUDA EP, TensorRT EP。
    3.  在 `config.pbtxt` 中为 ONNX 模型配置 EP:
        ```protobuf
        platform: "onnxruntime_onnx"
        # ...
        parameters: {
          key: "execution_providers",
          value: { string_value: "CUDAExecutionProvider" } # 或者 "TensorRTExecutionProvider"
        }
        ```
    4.  ONNX Runtime 也提供图优化工具。
*   **集成**:
    *   模型中台确保模型能导出为 ONNX。
    *   部署时在 `config.pbtxt` 中配置合适的 EP。

### 3.5. API 集成与服务中台封装
*   Triton 提供 HTTP/REST 和 gRPC API 接口。
*   **服务中台**:
    *   封装 Triton 的 API，提供统一的、更上层的服务接口给应用开发者。
    *   处理认证、授权、限流、计费等。
    *   可能需要进行请求/响应格式的转换。
*   **客户端**: Triton 提供 Python/C++/Java 客户端库。

### 3.6. 测试与验证
*   使用 Triton 客户端发送推理请求到部署的模型，验证结果正确性。
*   性能测试：测量延迟和吞吐量，对比优化前后效果。
*   监控 Triton metrics 端点 (`/metrics`)，检查 `nv_inference_request_duration_us`, `nv_inference_queue_duration_us`, `nv_inference_count` 等指标。

## 4. OpenWebUI 集成规划

目标：提供一个用户友好的 Web 界面，用于与部署在中台的 LLM 进行交互。

### 4.1. 前提条件
*   至少一个 LLM 已通过 Triton (或其他兼容后端) 成功部署并提供服务接口。
*   Docker 环境。
*   网络可访问 OpenWebUI 镜像。

### 4.2. OpenWebUI 部署

*   **方式**: Docker Compose 或 Kubernetes Deployment。
*   **Docker Compose 示例 (`docker-compose.yml`)**:
    ```yaml
    version: '3.8'
    services:
      open-webui:
        image: ghcr.io/open-webui/open-webui:main # 或特定版本
        container_name: open-webui
        ports:
          - "3000:8080" # 将容器的8080端口映射到主机的3000端口
        volumes:
          - ./open-webui-data:/app/backend/data # 持久化数据
        environment:
          # - 'OPENAI_API_KEY=your_openai_api_key' # 如果直接连接OpenAI
          # - 'OPENAI_API_BASE_URL=http://<triton-or-llm-service-host>:<port>/v1' # 指向Triton的OpenAI兼容API
          - 'OLLAMA_BASE_URL=http://<ollama-host>:<port>' # 如果使用Ollama作为后端
          # 根据实际后端配置环境变量
        restart: unless-stopped
    ```
    *   **注意**: OpenWebUI 的端口映射和数据卷挂载。
    *   **重要**: 环境变量配置，特别是 `OPENAI_API_BASE_URL` (如果 Triton 部署的 LLM 提供了 OpenAI 兼容的 API) 或 `OLLAMA_BASE_URL` (如果通过 Ollama 代理或直接使用 Ollama)。
*   **Kubernetes 部署**: 类似 Triton，创建 Deployment 和 Service。

### 4.3. 后端 LLM 服务连接

*   **OpenAI 兼容接口**:
    *   如果 LLM 服务 (如通过 Triton 部署的 vLLM 或 TensorRT-LLM 后端) 暴露了 OpenAI 兼容的 API (通常在 `/v1/chat/completions`, `/v1/models` 等路径)。
    *   在 OpenWebUI 的环境变量或 Web UI 管理界面中配置 `OPENAI_API_BASE_URL` 指向该服务地址。
    *   API Key 可能需要根据后端服务的要求配置。
*   **Ollama 后端**:
    *   如果 LLM 通过 Ollama 部署，配置 `OLLAMA_BASE_URL`。
    *   OpenWebUI 可以直接与 Ollama 通信拉取模型、进行推理。
*   **其他后端**: OpenWebUI 支持多种后端，查阅其官方文档配置。
*   **模型管理**:
    *   在 OpenWebUI 的管理员设置中，可以拉取和管理后端可用的模型。
    *   用户可以在界面上选择不同的模型进行对话。

### 4.4. 用户认证与授权 (初步探讨)

*   **OpenWebUI 内建认证**: OpenWebUI 支持本地用户注册和登录。
*   **与中台统一认证**:
    *   **方案1 (OAuth2/OIDC Proxy)**: 在 OpenWebUI 前面放置一个支持 OAuth2/OIDC 的反向代理 (如 `oauth2-proxy`)，代理将用户认证请求重定向到中台的身份提供者 (IdP)。认证成功后，代理将用户信息（如 JWT）传递给 OpenWebUI。OpenWebUI 可能需要定制以解析和信任这些信息。
    *   **方案2 (Header-based Authentication)**: 如果中台的 API Gateway 或反向代理可以注入认证后的用户信息到请求头，OpenWebUI 或其后端适配器可以读取这些请求头进行用户识别。
    *   **方案3 (OpenWebUI 插件/定制)**: 探索 OpenWebUI 是否支持插件化认证或通过定制代码集成中台的认证 SDK。
*   **当前阶段**: 初期可以先使用 OpenWebUI 的内建用户管理。后续迭代再考虑与中台统一认证的深度集成。

### 4.5. 定制化 (可选)
*   **品牌化**: 替换 Logo、调整主题颜色等 (如果 OpenWebUI 支持)。
*   **功能裁剪**: 根据需求隐藏或禁用某些 OpenWebUI 功能。

### 4.6. 测试与验证
*   用户可以成功注册/登录 OpenWebUI。
*   用户可以在 OpenWebUI 中看到并选择已配置的 LLM 模型。
*   用户可以与 LLM 进行正常的对话交互。
*   对话历史能正确保存和加载。
*   检查 OpenWebUI 容器日志和后端 LLM 服务日志，排查连接和推理问题。

## 5. 开发与集成时间线 (参考产品文档)

*   **阶段一: 基础设施搭建 (GPU & Triton)**
    *   GPU Operator 部署与验证。
    *   Triton Server 基础部署与验证。
    *   基础 GPU 监控 (DCGM + Prometheus + Grafana)。
*   **阶段二: 推理加速与模型部署集成**
    *   至少一个 CV 和一个 NLP 模型的优化 (TensorRT/ONNX) 并部署到 Triton。
    *   服务中台初步集成 Triton API。
*   **阶段三: OpenWebUI 集成**
    *   OpenWebUI 部署。
    *   OpenWebUI 连接到 Triton 部署的 LLM。
    *   基础用户访问和模型选择。
*   **阶段四: 测试、文档与发布**
    *   详细的测试计划和执行。
    *   完善所有相关开发和用户文档。

## 6. 开发者环境与工具
*   `kubectl`
*   `helm`
*   Docker Desktop (或等效工具)
*   IDE (VS Code, PyCharm等)
*   Python (用于编写测试脚本、模型转换脚本)
*   NVIDIA CUDA Toolkit (本地开发和模型转换可能需要)
*   TensorRT (本地开发和模型转换可能需要)
*   访问 Kubernetes 集群、镜像仓库、代码仓库的权限。

## 7. 故障排查与常见问题

### 7.1. GPU Stack
*   **问题**: GPU Operator Pod 启动失败。
    *   **排查**: 检查 K8s 版本兼容性、驱动版本、节点内核版本、安全策略 (如 PodSecurityPolicies 或 OPA Gatekeeper)。查看 Operator 日志。
*   **问题**: Pod 无法分配 GPU (`nvidia.com/gpu: 0/X`)。
    *   **排查**: 检查 NVIDIA device plugin 是否正常运行，节点是否有可用 GPU，Pod 的 resource request 是否正确。`kubectl describe node <node-name>`。
*   **问题**: DCGM Exporter 指标不显示。
    *   **排查**: 检查 Prometheus scrape 配置，网络策略是否允许 Prometheus 访问 exporter 端点，exporter Pod 日志。

### 7.2. Triton Inference Server
*   **问题**: Triton Server 启动失败。
    *   **排查**: 检查镜像版本、模型仓库路径和权限、GPU 分配。查看 Triton Pod 日志。
*   **问题**: 模型加载失败。
    *   **排查**: 检查模型仓库结构、`config.pbtxt` 配置是否正确、模型文件是否完整且与平台兼容 (如 TensorRT plan 与 GPU 架构)。Triton 启动日志会详细报告模型加载状态。
*   **问题**: 推理请求错误或性能不佳。
    *   **排查**: 检查请求格式、输入数据类型和形状是否与 `config.pbtxt` 定义一致。使用 Triton 的 `--log-verbose=1` 获取详细日志。分析性能瓶颈 (CPU, GPU, I/O)。

### 7.3. OpenWebUI
*   **问题**: OpenWebUI 无法连接后端 LLM。
    *   **排查**: 检查环境变量 (`OPENAI_API_BASE_URL`, `OLLAMA_BASE_URL` 等) 是否正确配置。网络连通性 (从 OpenWebUI 容器到 LLM 服务)。LLM 服务本身是否正常运行并暴露了正确的 API 端点。查看 OpenWebUI 容器日志。
*   **问题**: 模型列表为空或无法选择模型。
    *   **排查**: 确认后端 LLM 服务已正确配置并加载了模型。OpenWebUI 是否有权限访问模型的元数据接口 (如 `/v1/models`)。
*   **问题**: 用户登录或注册问题。
    *   **排查**: 检查 OpenWebUI 数据卷权限，数据库连接 (如果使用外部数据库)。

---
*文档版本: 1.0*
*创建日期: 2025-06-10*
