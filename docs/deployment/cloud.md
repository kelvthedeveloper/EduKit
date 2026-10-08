# 云端部署文档

Cloud 端生产部署指南。

## 部署前检查

- [ ] 域名解析完成，SSL 证书就绪
- [ ] 对象存储 (S3 / MinIO) Bucket 创建完成
- [ ] 邮件 / 短信网关开通
- [ ] 数据库服务器参数优化完成

## 推荐拓扑

- 前端：CDN + 多可用区 Next.js
- API：K8s Deployment + HPA，至少 2 副本
- 数据库：PostgreSQL 主从 + PITR
- Redis：3 节点哨兵 / Cluster
- 监控：Prometheus + Grafana + Alertmanager

## 发布流程

1. CI 通过镜像构建并推送到仓库
2. 预发环境执行冒烟测试
3. 灰度 10% 流量
4. 全量发布
5. 监控 30 分钟
