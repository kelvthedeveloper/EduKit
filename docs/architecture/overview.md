# 架构总览

本文档描述 EduKit 系统的整体架构设计。

## 概要

EduKit 采用 **云边协同 (Cloud + Edge)** 双端架构：

- **Cloud 云端**：集中管理多所学校的数据汇总、报表分析、系统升级推送
- **School Server 学校本地端**：部署在学校局域网内，提供离线可用的教学管理服务
- **同步机制**：两端通过安全的同步协议保持数据一致性

## 技术栈

| 层级 | 技术 |
|-----|------|
| 前端 | Next.js 14 (App Router) + TypeScript + Tailwind CSS |
| 后端 | Django 4 + Django REST Framework + Celery |
| 数据库 | PostgreSQL 15 + Redis 7 |
| 对象存储 | MinIO (本地) / S3 (云端) |
| 部署 | Docker + Docker Compose + Nginx |
