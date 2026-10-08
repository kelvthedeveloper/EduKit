#!/bin/bash
# 数据恢复脚本
# 用途：从指定备份文件恢复数据库和媒体文件
# 用法: ./restore.sh <备份文件路径>

set -e

if [ -z "$1" ]; then
    echo "用法: $0 <备份文件路径>"
    echo "示例: $0 ./backups/db-20240101-000000.sql"
    exit 1
fi

BACKUP_FILE="$1"

echo "=== EduKit 数据恢复 ==="
echo "警告：此操作将覆盖现有数据！"
read -p "确认继续？(y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

cd "$(dirname "$0")/.."

# 根据文件类型恢复
if [[ "$BACKUP_FILE" == *.sql ]]; then
    echo "恢复数据库..."
    docker compose exec -T postgres psql -U edukit edukit < "$BACKUP_FILE"
    echo "数据库恢复完成"
elif [[ "$BACKUP_FILE" == *.tar.gz ]]; then
    echo "恢复媒体文件..."
    tar -xzf "$BACKUP_FILE" -C ./data
    echo "媒体文件恢复完成"
else
    echo "不支持的文件格式"
    exit 1
fi

# 重启服务
echo "重启服务使更改生效..."
docker compose restart backend worker

echo "恢复完成！"
