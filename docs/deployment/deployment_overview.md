# AI 中台 - 系统层部署概览

本文档是 AI 中台系统层部署系列文档的概览。具体部署文档如下：

- **[0. 操作系统安装 (Ubuntu 22.04 LTS)](./00_os_installation_ubuntu.md)**: 指导完成基础操作系统的安装和配置。
- **[1. 容器化平台部署](./01_container_platform_setup.md)**: 指导 Docker 和 Kubernetes 集群的安装与配置。
- **[2. Kubernetes 网络配置](./02_kubernetes_networking.md)**: 详细说明 Kubernetes 的网络插件 (CNI) 和 Ingress 控制器的配置。
- **[3. Kubernetes 存储系统部署](./03_storage_systems_kubernetes.md)**: 涵盖镜像仓库、监控数据存储、日志系统、对象存储和关系型数据库在 Kubernetes 环境下的部署。
- **[4. Kubernetes 资源管理](./04_resource_management_kubernetes.md)**: 介绍资源可视化工具 (如 Grafana) 和 GPU 资源管理插件的部署。
- **[5. 核心数据库建立与连接](./05_database_setup.md)**: 指导 PostgreSQL, MongoDB, 和 Weaviate 数据库的建立与连接。
- **[6. Django 与 RESTful API 环境配置](./06_django_rest_setup.md)**: 指导 Django 和 Django REST Framework 的配置与部署。
- **[8. Node.js 环境配置](./08_nodejs_setup.md)**: 指导 Node.js 环境的安装和前端开发环境的配置。

请按照顺序参考以上文档完成 AI 中台系统层的部署。

---

**后续步骤**:
完成系统层部署后，可以继续部署核心服务层和应用层。请参考相应的部署文档。

**重要提示**:
- 本系列文档提供的是通用安装指南和方向。具体命令和配置可能因您的环境和所选组件的特定版本而异。
- **务必参考各组件的官方文档**获取最准确和最新的安装说明。
- 在生产环境部署前，请在测试环境中充分验证所有组件的安装和配置。
- 持续关注各组件的许可证变化，确保合规性。
- 对于在中国大陆部署，请注意网络访问问题，可能需要使用国内的镜像源来加速下载和安装过程。
