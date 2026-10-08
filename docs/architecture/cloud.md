# Cloud 云端架构

云端服务部署在公有云，负责跨学校的集中管理能力。

## 服务组件

- **前端 Web**：管理控制台、教育局/集团校视图
- **API Gateway**：统一认证、限流、路由
- **核心服务**：用户中心、组织管理、数据同步服务
- **分析服务**：数据仓库 (OLAP)、BI 报表、数据大屏
- **消息服务**：通知推送、短信、邮件网关

## 网络拓扑

```
Internet
   │
   ├─ CDN / WAF
   │
   ├─ Nginx (LB)
   │    ├─ Frontend (Next.js)
   │    └─ Backend API (Django)
   │         ├─ PostgreSQL (主从)
   │         ├─ Redis Cluster
   │         └─ S3 / MinIO
   └─ Sync Service (接收学校上报)
```
