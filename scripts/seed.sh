#!/bin/bash
# 开发数据初始化 (种子数据)
# 用途：填充演示学校、用户、班级等测试数据

set -e

echo "=== 填充种子数据 ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

run_manage() {
    if docker compose ps --services --filter "status=running" | grep -q "^backend$"; then
        docker compose exec backend python manage.py "$@"
    else
        cd backend
        [ -f ".venv/bin/activate" ] && source .venv/bin/activate
        python manage.py "$@"
    fi
}

# 创建超级管理员 (如不存在)
echo "创建超级管理员 (如未配置)..."
# TODO: run_manage createsuperuser --noinput 或自定义命令

# 加载演示数据 fixture
echo "加载演示数据..."
# TODO: run_manage loaddata demo_school.json demo_users.json

echo "种子数据填充完成 ✓"
echo "默认管理员账号请查看 backend/fixtures/ 或使用 createsuperuser 手动创建"
