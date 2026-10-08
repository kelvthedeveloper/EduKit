#!/bin/bash
# 开发环境一键初始化脚本
# 用途：安装依赖、准备本地开发环境

set -e

echo "=== EduKit 开发环境初始化 ==="

# 检查 Node / pnpm
if ! command -v pnpm &> /dev/null; then
    echo "安装 pnpm..."
    corepack enable pnpm || npm install -g pnpm
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "请先安装 Python 3.11+"
    exit 1
fi

# 根目录安装依赖
echo "安装前端依赖 (pnpm)..."
pnpm install

# 后端依赖
if [ -d "./backend" ]; then
    echo "创建 Python 虚拟环境..."
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    echo "安装 Python 依赖..."
    pip install -r requirements.txt
    cd ..
fi

# 环境变量文件
if [ ! -f .env ]; then
    echo "复制 .env.example 到 .env"
    cp .env.example .env
fi

echo ""
echo "初始化完成！下一步："
echo "  1. 编辑 .env 填写必要配置"
echo "  2. 启动基础设施：docker compose up -d postgres redis minio"
echo "  3. 执行数据库迁移：./scripts/migrate.sh"
echo "  4. 插入种子数据：./scripts/seed.sh"
echo "  5. 启动开发：pnpm dev"
