#!/bin/bash
# 数据库迁移脚本
# 用途：在开发或生产环境执行 Django migrations

set -e

echo "=== 执行数据库迁移 ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 尝试在 Docker 中执行
if docker compose ps --services --filter "status=running" | grep -q "^backend$"; then
    echo "通过 Docker Compose 执行迁移..."
    docker compose exec backend python manage.py makemigrations
    docker compose exec backend python manage.py migrate
else
    # 本地执行
    echo "本地执行迁移..."
    if [ -d "./backend" ]; then
        cd backend
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        fi
        python manage.py makemigrations
        python manage.py migrate
    else
        echo "未找到 backend 目录"
        exit 1
    fi
fi

echo "迁移完成 ✓"
