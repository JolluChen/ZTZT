# AI 中台 - 部署概览

本文档是 AI 中台部署系列文档的概览，旨在引导您完成从基础设施到应用服务的完整部署流程。文档按照部署层级进行组织，请依次参考。

## 一、环境部署 (Environment Deployment)

本阶段主要完成 AI 中台运行所需的基础设施和底层环境的搭建。

- **[0. 操作系统安装 (Ubuntu 22.04 LTS)](./01_environment_deployment/00_os_installation_ubuntu.md)**: 指导完成基础操作系统的安装和初始配置。
- **[1. 容器化平台部署](./01_environment_deployment/01_container_platform_setup.md)**: 指导 Docker 和 Kubernetes (k8s) 集群的安装、配置及验证。
- **[2. Kubernetes 网络配置](./01_environment_deployment/02_kubernetes_networking.md)**: 详细说明 Kubernetes 的网络方案，包括 CNI 插件（如 Calico, Cilium）和 Ingress 控制器的选择与配置。
- **[3. Kubernetes 存储系统部署](./01_environment_deployment/03_storage_systems_kubernetes.md)**: 涵盖持久化存储方案（如 MinIO 对象存储、Harbor 镜像仓库）以及日志和监控数据存储的部署。
- **[4. Kubernetes 资源管理](./01_environment_deployment/04_resource_management_kubernetes.md)**: 介绍资源监控工具（如 Prometheus, Grafana）和 GPU 等特殊资源管理插件的部署与配置。

## 二、服务部署 (Server Deployment)

本阶段主要部署 AI 中台的核心后台服务、中间件及相关依赖。

- **[5. 核心数据库系统部署](./02_server_deployment/05_database_setup.md)**: 概览 PostgreSQL, MongoDB, Weaviate, Redis, Kafka 等数据库和消息队列的部署。
    - *详细的各数据库部署指南请参考 `./02_server_deployment/05_database_deployment/` 目录下的专项文档。*
- **[6. Django 与 RESTful API 环境配置](./02_server_deployment/06_django_rest_setup.md)**: 指导后端 Python Django 项目的搭建、Django REST Framework API 的配置与部署。
- **[7. 权限管理系统部署](./02_server_deployment/07_permission_management.md)**: 指导身份认证与授权系统（如 Keycloak）的部署和集成。
- **[8. Node.js 环境配置](./02_server_deployment/08_nodejs_setup.md)**: 指导 Node.js 运行环境的安装和前端项目（若有）开发环境的配置。

## 三、应用部署 (Application Deployment)

本阶段涉及具体的 AI 应用、数据处理流程、模型服务等上层应用的部署。

- *(具体文档链接待补充，请参考 `./03_application_deployment/` 目录下的相关文档)*

---

**后续步骤**:
完成所有层级的部署后，请进行全面的系统集成测试和联调。

**重要提示**:
- 本系列文档提供的是通用安装指南和方向。具体命令和配置可能因您的环境和所选组件的特定版本而异。
- **务必参考各组件的官方文档**获取最准确和最新的安装说明。
- 在生产环境部署前，请在测试环境中充分验证所有组件的安装和配置。
- 持续关注各组件的许可证变化，确保合规性。
- 对于在中国大陆部署，请注意网络访问问题，可能需要使用国内的镜像源来加速下载和安装过程。
