# 常用服务默认端口参考

## 概述

本文档提供一个常用服务及其标准/默认端口的参考列表，方便在进行网络规划时查阅。

## 常用端口列表

| 服务/协议         | 默认端口 | 传输协议 | 用途说明                         |
| ----------------- | -------- | -------- | -------------------------------- |
| HTTP              | 80       | TCP      | Web 服务                         |
| HTTPS             | 443      | TCP      | 安全 Web 服务                    |
| FTP               | 20, 21   | TCP      | 文件传输协议                     |
| SSH               | 22       | TCP      | 安全 Shell                       |
| Telnet            | 23       | TCP      | 远程登录 (不推荐)                |
| SMTP              | 25       | TCP      | 简单邮件传输协议                 |
| DNS               | 53       | TCP/UDP  | 域名系统                         |
| DHCP              | 67, 68   | UDP      | 动态主机配置协议                 |
| TFTP              | 69       | UDP      | 简单文件传输协议                 |
| NTP               | 123      | UDP      | 网络时间协议                     |
| SNMP              | 161, 162 | UDP      | 简单网络管理协议                 |
| LDAP              | 389      | TCP/UDP  | 轻量级目录访问协议               |
| LDAPS             | 636      | TCP      | LDAP over SSL                    |
| Microsoft DS      | 445      | TCP      | SMB over TCP (文件共享)          |
| Syslog            | 514      | UDP      | 系统日志                         |
| RDP               | 3389     | TCP      | 远程桌面协议 (Windows)           |
| **数据库相关**    |          |          |                                  |
| PostgreSQL        | 5432     | TCP      | PostgreSQL 数据库                |
| MySQL             | 3306     | TCP      | MySQL 数据库                     |
| MongoDB           | 27017    | TCP      | MongoDB 数据库                   |
| Redis             | 6379     | TCP      | Redis 缓存/数据库                |
| Oracle DB         | 1521     | TCP      | Oracle 数据库                    |
| Microsoft SQL Server | 1433    | TCP      | MS SQL Server 数据库             |
| **消息队列**      |          |          |                                  |
| Kafka             | 9092     | TCP      | Apache Kafka brokers             |
| RabbitMQ          | 5672     | TCP      | RabbitMQ AMQP port               |
| RabbitMQ Management| 15672    | TCP      | RabbitMQ 管理插件 UI             |
| Zookeeper         | 2181     | TCP      | Apache Zookeeper                 |
| **容器与编排**    |          |          |                                  |
| Docker Daemon API | 2375, 2376 | TCP    | Docker 引擎 API (2376 for TLS)   |
| Kubernetes API Server | 6443   | TCP    | Kubernetes API 服务              |
| etcd client       | 2379     | TCP      | etcd 客户端请求                  |
| etcd peer         | 2380     | TCP      | etcd 集群间通信                  |
| Kubelet API       | 10250    | TCP      | Kubelet API                      |
| Kube Proxy        | 10256    | TCP      | Kube Proxy 健康检查              |
| Calico Typha      | 5473     | TCP      | Calico Typha agent               |
| Flannel           | 8472     | UDP      | Flannel VXLAN overlay network    |
| **监控与日志**    |          |          |                                  |
| Prometheus        | 9090     | TCP      | Prometheus Server                |
| Alertmanager      | 9093     | TCP      | Prometheus Alertmanager          |
| Grafana           | 3000     | TCP      | Grafana Web UI                   |
| Elasticsearch HTTP| 9200     | TCP      | Elasticsearch REST API           |
| Elasticsearch Transport | 9300 | TCP    | Elasticsearch 节点间通信         |
| Kibana            | 5601     | TCP      | Kibana Web UI                    |
| Logstash Beats Input| 5044   | TCP      | Logstash Beats 输入插件          |
| **其他常用服务**  |          |          |                                  |
| Jenkins           | 8080     | TCP      | Jenkins CI/CD (默认)             |
| GitLab            | 80, 443  | TCP      | GitLab (通过 Nginx/Apache)       |
| SonarQube         | 9000     | TCP      | SonarQube Web UI                 |
| MinIO API         | 9000     | TCP      | MinIO S3 API                     |
| MinIO Console     | 9001     | TCP      | MinIO Web Console (新版可能变化) |
| Weaviate          | 8080     | TCP      | Weaviate REST API                |
| Weaviate gRPC     | 50051    | TCP      | Weaviate gRPC API                |
| MLflow Tracking   | 5000     | TCP      | MLflow Tracking Server           |
| Keycloak HTTP     | 8080     | TCP      | Keycloak (Wildfly/Quarkus)       |
| Keycloak HTTPS    | 8443     | TCP      | Keycloak (Wildfly/Quarkus)       |
| Hashicorp Vault   | 8200     | TCP      | Hashicorp Vault API              |

## 注意事项

*   这只是一个常用列表，并非详尽无遗。
*   某些服务可能使用多个端口或可配置为使用非标准端口。
*   在规划时，务必查阅特定服务的官方文档以获取最准确的端口信息。
*   出于安全考虑，不建议将所有服务的默认端口直接暴露到公网。
