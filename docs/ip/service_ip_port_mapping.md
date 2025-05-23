# 服务 IP 与端口映射规划 (预设)

## 概述

本文档列出了项目中主要服务及其建议的 IP 地址（或分配策略）和端口号。
IP 地址通常会从 `ip_address_ranges.md` 中定义的相应池中分配，或者是 Kubernetes Service IP。

**IP 地址说明:**

*   `<K8S_SERVICE_IP>`: 表示由 Kubernetes 分配的 ClusterIP。
*   `<K8S_NODE_IP>`: 表示 Kubernetes 节点的 IP 地址。
*   `<LB_VIP>`: 表示负载均衡器的虚拟 IP 地址。
*   `<DEDICATED_IP_X>`: 表示从预留 IP 池中分配的特定静态 IP。

## 系统层

| 服务             | 组件/实例        | 建议 IP / 分配方式    | 默认端口 | 规划端口 | 备注                                     |
| ---------------- | ---------------- | --------------------- | -------- | -------- | ---------------------------------------- |
| **Kubernetes**   | API Server       | `<K8S_MASTER_IP>` / `<LB_VIP>` | 6443     | 6443     | 高可用集群可能使用 LB VIP                  |
|                  | etcd             | `<K8S_MASTER_IP>`     | 2379, 2380 | 2379, 2380 | 客户端端口, Peer 端口                     |
|                  | Kubelet          | `<K8S_NODE_IP>`       | 10250    | 10250    |                                          |
| **Nginx**        | 反向代理实例     | `<LB_VIP>` / `<DEDICATED_IP_X>` | 80, 443  | 80, 443  | 对外暴露 HTTP/HTTPS 服务                 |
| **Harbor**       | Harbor Core      | `<K8S_SERVICE_IP>` / `<DEDICATED_IP_X>` | 80, 443  | 8085, 8443 | 建议通过 Ingress 或 LB 暴露，端口可自定义 |
|                  | Notary Server    |                       | 4443     | 4443     |                                          |
|                  | Trivy            |                       | 8080     |          | (内部)                                   |
| **ELK Stack**    | Elasticsearch    | `<K8S_SERVICE_IP>` / `<DEDICATED_IP_X>` | 9200, 9300 | 9200, 9300 | HTTP, Transport                           |
|                  | Logstash         | `<K8S_SERVICE_IP>`    | 5044, 9600 | 5044, 9600 | Beats input, Web API                     |
|                  | Kibana           | `<K8S_SERVICE_IP>` / `<DEDICATED_IP_X>` | 5601     | 5601     | 通过 Ingress 或 LB 暴露                  |
| **Prometheus**   | Server           | `<K8S_SERVICE_IP>` / `<DEDICATED_IP_X>` | 9090     | 9090     | 通过 Ingress 或 LB 暴露                  |
|                  | Alertmanager     | `<K8S_SERVICE_IP>`    | 9093     | 9093     |                                          |
| **Grafana**      | Server           | `<K8S_SERVICE_IP>` / `<DEDICATED_IP_X>` | 3000     | 3000     | 通过 Ingress 或 LB 暴露                  |
| **MinIO**        | Server           | `<K8S_SERVICE_IP>` / `<DEDICATED_IP_X>` | 9000     | 9000     | API 端口                                 |
|                  | Console          |                       | 9001     | 9001     | (新版本可能合并或不同)                   |
| **PostgreSQL**   | (系统数据库)     | `<DEDICATED_IP_X>`    | 5432     | 5432     | 用于 Harbor, Keycloak 等系统组件           |
| **Keycloak**     | Server           | `<K8S_SERVICE_IP>` / `<DEDICATED_IP_X>` | 8080, 8443 | 8180, 8543 | 建议通过 Ingress/LB 暴露，避免与 Tomcat 冲突 |
| **Hashicorp Vault**| Server           | `<DEDICATED_IP_X>`    | 8200     | 8200     |                                          |

## 核心服务层

| 服务           | 组件/实例      | 建议 IP / 分配方式 | 默认端口 | 规划端口 | 备注                               |
| -------------- | -------------- | ------------------ | -------- | -------- | ---------------------------------- |
| **Django App** | (各应用实例)   | `<K8S_SERVICE_IP>` | 8000     | 8000+    | Gunicorn/Uvicorn 运行端口          |
| **PostgreSQL** | (应用主数据库) | `<DEDICATED_IP_X>` | 5432     | 15432    | 避免与系统 PostgreSQL 端口冲突     |
| **MongoDB**    | Mongod/Mongos  | `<DEDICATED_IP_X>` | 27017    | 27017    |                                    |
| **Weaviate**   | Server         | `<K8S_SERVICE_IP>` | 8080     | 8088     | 避免端口冲突, gRPC 50051           |
| **Redis**      | Server         | `<DEDICATED_IP_X>` | 6379     | 6379     |                                    |
| **Kafka**      | Brokers        | `<DEDICATED_IP_X>` | 9092     | 9092     | 客户端连接端口                     |
|                | Zookeeper      | `<DEDICATED_IP_X>` | 2181     | 2181     | (如果 Kafka 仍依赖外部 ZK)         |

## 应用层 (部分示例)

| 服务                      | 组件/实例                 | 建议 IP / 分配方式 | 默认端口 | 规划端口 | 备注                                     |
| ------------------------- | ------------------------- | ------------------ | -------- | -------- | ---------------------------------------- |
| **Apache Spark**          | Master UI                 | `<K8S_SERVICE_IP>` | 8080     | 18080    | 独立集群模式，避免端口冲突               |
|                           | Worker UI                 | `<K8S_NODE_IP>`    | 8081     | 18081    |                                          |
|                           | Driver/Executor           | (动态)             | (动态)   | (动态)   |                                          |
| **Apache Flink**          | JobManager Web UI         | `<K8S_SERVICE_IP>` | 8081     | 18088    | 避免端口冲突                             |
| **MLflow**                | Tracking Server           | `<K8S_SERVICE_IP>` | 5000     | 5001     | 避免与 Flask 开发端口冲突                |
| **Kubeflow Pipelines**    | API Server                | `<K8S_SERVICE_IP>` | 8888     | 8888     | (通常通过 Istio Gateway 暴露)            |
| **Triton Inference Server**| HTTP/GRPC                | `<K8S_SERVICE_IP>` | 8000,8001,8002 | 8000,8001,8002 | HTTP, GRPC, Metrics                    |
| **TorchServe**            | Inference/Management      | `<K8S_SERVICE_IP>` | 8080, 8081 | 8086, 8087 | Inference API, Management API            |
| **FastAPI Apps**          | (各应用实例)              | `<K8S_SERVICE_IP>` | 8000     | 8000+    | Uvicorn 运行端口                         |
| **Label Studio**          | Web UI                    | `<K8S_SERVICE_IP>` | 8080     | 8090     |                                          |
| **CVAT**                  | Web UI                    | `<K8S_SERVICE_IP>` | 8080     | 8091     |                                          |
| **Apache Superset**       | Web UI                    | `<K8S_SERVICE_IP>` | 8088     | 8088     |                                          |
| **ClickHouse**            | HTTP/Native               | `<DEDICATED_IP_X>` | 8123, 9000 | 8123, 9000 |                                          |
| **OpenWebUI**             | Web UI                    | `<K8S_SERVICE_IP>` | 3000     | 8092     | 默认3000，避免与 Grafana 冲突，或通过反向代理统一端口 |

## 用户交互层

| 服务           | 组件/实例      | 建议 IP / 分配方式 | 默认端口 | 规划端口 | 备注                               |
| -------------- | -------------- | ------------------ | -------- | -------- | ---------------------------------- |
| **React/Vue App** | (前端应用)   | `<LB_VIP>`         | 80/443   | 80/443   | 通过 Nginx 反向代理                  |

## 注意事项

*   `规划端口` 是建议的端口，如果默认端口可用且不冲突，也可以直接使用默认端口。
*   对于通过 Kubernetes Ingress 或 Service Mesh (如 Istio) 暴露的服务，外部访问端口由 Ingress Controller 或 Gateway 配置决定。
*   内部服务之间的通信，优先使用 Kubernetes Service DNS 名称。
*   安全性：确保只有必要的端口对外暴露，并配置好防火墙规则和网络策略。
*   高可用性：对于关键服务，考虑使用负载均衡和多副本部署。
