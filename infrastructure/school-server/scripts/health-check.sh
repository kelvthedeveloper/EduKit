#!/bin/bash
# 健康检查脚本
# 用途：检查各服务运行状态，异常时告警

set -e

cd "$(dirname "$0")/.."

echo "=== EduKit 服务器健康检查 $(date) ==="
echo ""

EXIT_CODE=0

check_service() {
    local name=$1
    if docker compose ps --services --filter "status=running" | grep -q "^$name$"; then
        echo "[OK]   $name - 运行中"
    else
        echo "[FAIL] $name - 未运行"
        EXIT_CODE=1
    fi
}

echo "--- Docker 服务状态 ---"
check_service "postgres"
check_service "redis"
check_service "backend"
check_service "worker"
check_service "frontend"
check_service "nginx"

echo ""
echo "--- HTTP 端点检查 ---"

# 检查前端
if curl -fsS http://localhost/ > /dev/null 2>&1; then
    echo "[OK]   前端页面 (http://localhost/)"
else
    echo "[FAIL] 前端页面"
    EXIT_CODE=1
fi

# 检查 API 健康检查端点
if curl -fsS http://localhost/api/health/ > /dev/null 2>&1; then
    echo "[OK]   API 健康检查 (http://localhost/api/health/)"
else
    echo "[WARN] API 健康检查端点 (可能未实现)"
fi

echo ""
echo "--- 磁盘使用 ---"
df -h | grep -E "^Filesystem|/$"

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "所有检查通过 ✓"
else
    echo "存在异常，请检查！"
fi

exit $EXIT_CODE
