# EduKit

> 现代化、一站式的学校综合管理系统，支持云边协同离线部署。

EduKit（原名 EdiKit）是一套面向 K12 / 中职 / 培训机构的完整学校管理系统，涵盖 **教务、教学、考试、德育、财务、家校沟通** 等核心业务模块。系统采用 **云端 SaaS + 学校本地服务器** 的双端架构，既能满足集团化办学的数据集中管控，又能确保校园局域网环境下的稳定离线可用。

---

## ✨ 核心特性

| 模块 | 说明 |
|-----|------|
| 🏫 组织管理 | 多校区 / 年级 / 班级 / 教研组 全层级管理 |
| 👥 人员中心 | 学生、教师、家长、管理员统一身份与权限 |
| 📚 教学管理 | 课程、教材、课表、备课资源、作业 |
| 📝 考试与成绩 | 组卷、在线考试、阅卷、多维度成绩分析 |
| ✅ 考勤与德育 | 人脸识别考勤、日常行为、奖惩记录 |
| 💰 收费与财务 | 学费缴纳、发票、收支流水 |
| 📱 家校互通 | 微信 / 小程序 / APP 通知、作业、成长档案 |
| 🔄 云边同步 | 增量同步、冲突解决、断网可用 |
| 🔐 安全合规 | RBAC 权限、操作审计、敏感数据脱敏、等保 2.0 |

---

## 🏗️ 架构概述

```
                        ┌──────────────────────────────┐
                        │        Cloud 云端服务        │
                        │  SaaS / 教育局 / 集团校视角  │
                        │  ┌────────┐   ┌──────────┐  │
                        │  │Web/API │   │数据分析  │  │
                        │  └───┬────┘   └────┬─────┘  │
                        │      │ PostgreSQL  │         │
                        └──────┼─────────────┼─────────┘
                               │  HTTPS / mTLS
                               │  增量双向同步
          ┌────────────────────┴────────────────────┐
          │                                         │
┌─────────▼──────────┐              ┌───────────────▼──────────┐
│  School Server #1  │              │   School Server #N       │
│   学校 A 本地部署   │     ...      │   学校 N 本地部署        │
│ ┌──────┐ ┌───────┐ │              │ ┌──────┐  ┌────────────┐ │
│ │Nextjs│ │Django │ │              │ │Nextjs│  │Django+Celery│ │
│ └──┬───┘ └───┬───┘ │              │ └──┬───┘  └─────┬──────┘ │
│    │  Nginx  │     │              │    │  Nginx      │        │
│    └────┬────┘     │              │    └─────┬──────┘        │
│   PostgreSQL+Redis │              │  PostgreSQL + Redis      │
└────────────────────┘              └──────────────────────────┘
```

更多架构细节请查阅 `docs/architecture/`。

---

## 📦 技术栈

| 分类 | 技术选型 |
|-----|---------|
| 前端 | **Next.js 14** (App Router) + TypeScript + TailwindCSS + shadcn/ui |
| 移动端 | 微信小程序 / H5 (共享 API 层) |
| 后端 | **Django 4** + DRF + Celery + Pydantic |
| 数据库 | **PostgreSQL 15** + **Redis 7** |
| 对象存储 | MinIO (本地) / AWS S3 (云端) |
| 部署 | Docker + Docker Compose + Nginx |
| CI/CD | GitHub Actions |
| 代码规范 | ESLint / Prettier / Ruff / Black / isort |

---

## 🚀 快速开始 (开发环境)

### 前置条件

- Docker & Docker Compose (推荐)
- Node.js 20+ & pnpm 8+
- Python 3.11+
- Git

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd EduKit

# 2. 初始化环境变量
cp .env.example .env
# 按需编辑 .env

# 3. 启动所有依赖服务 + 应用
docker compose up -d

# 4. 执行数据库迁移 + 种子数据
./scripts/migrate.sh
./scripts/seed.sh

# 5. 访问
# 前端: http://localhost/
# API:  http://localhost/api/
# Admin: http://localhost/admin/
# MinIO: http://localhost:9001/  (minioadmin / minioadmin)
```

### 方式二：本地裸机开发

```bash
# 1. 初始化 (会自动创建 venv / 安装依赖 / 复制 .env)
./scripts/setup.sh        # Linux/macOS
# 或
.\scripts\setup.ps1       # Windows PowerShell

# 2. 仅启动依赖中间件
docker compose up -d postgres redis minio

# 3. 迁移 + 种子数据
./scripts/migrate.sh
./scripts/seed.sh

# 4. 启动前后端 (Turbo monorepo)
pnpm dev
# 前端: http://localhost:3000
# API:  http://localhost:8000
```

---

## 🏫 学校本地服务器部署

参考完整部署 SOP：[`docs/deployment/school-server.md`](docs/deployment/school-server.md)

```bash
# 在学校服务器上
cd infrastructure/school-server
cp .env.example .env   # 填写学校信息 / 同步密钥
./scripts/install.sh
./scripts/health-check.sh
```

---

## 📁 目录结构

```
EduKit/
├── frontend/                 # Next.js 前端 (待创建)
├── backend/                  # Django 后端 (待创建)
│
├── infrastructure/           # 基础设施 & 部署配置
│   ├── docker/               #   Dockerfile (frontend/backend/worker)
│   ├── nginx/                #   Nginx 配置 (cloud / school-server)
│   ├── cloud/                #   云端部署
│   └── school-server/        #   学校本地端 (compose + 运维脚本)
│
├── .github/workflows/        # CI/CD (ci / frontend / backend)
│
├── docs/                     # 项目文档
│   ├── architecture/         #   架构设计
│   ├── database/             #   数据库
│   ├── api/                  #   API 规范
│   ├── sync/                 #   云边同步协议
│   ├── security/             #   认证授权与审计
│   └── deployment/           #   部署文档
│
├── scripts/                  # 跨平台辅助脚本 (bash + powershell)
│
├── docker-compose.yml        # 开发环境编排
├── docker-compose.school.yml # 学校服务器生产编排
├── pnpm-workspace.yaml
├── turbo.json
└── README.md
```

---

## 🧪 开发命令速查

| 命令 | 说明 |
|------|------|
| `pnpm dev` | 启动前后端开发模式 (Turbo) |
| `pnpm lint` | 前端 Lint |
| `pnpm build` | 全量构建 |
| `pnpm test` | 前端测试 |
| `./scripts/migrate.sh` | Django 数据库迁移 |
| `./scripts/seed.sh` | 插入演示数据 |
| `./scripts/sync-test.sh` | 云边同步集成测试 |
| `docker compose logs -f backend` | 查看后端日志 |

---

## 🤝 贡献指南

(待补充：Branch Strategy / PR 规范 / Commit Conventions)

---

## 📄 License

(待选择 & 补充)
