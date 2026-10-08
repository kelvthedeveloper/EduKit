#!/bin/bash
# 数据备份脚本
# 用途：备份 PostgreSQL 数据库、媒体文件到指定目录

set -e

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "=== EduKit 数据备份 ($TIMESTAMP) ==="

cd "$(dirname "$0")/.."

mkdir -p "$BACKUP_DIR"

# 备份数据库
echo "备份数据库..."
docker compose exec -T postgres pg_dump -U edukit edukit > "$BACKUP_DIR/db-$TIMESTAMP.sql"

# 备份媒体文件
echo "备份媒体文件..."
tar -czf "$BACKUP_DIR/media-$TIMESTAMP.tar.gz" -C ./data media 2>/dev/null || echo "媒体文件目录不存在，跳过"

# 清理过期备份
if [ -n "$BACKUP_RETENTION_DAYS" ]; then
    echo "清理 $BACKUP_RETENTION_DAYS 天前的备份..."
    find "$BACKUP_DIR" -name "*.sql" -mtime +"$BACKUP_RETENTION_DAYS" -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +"$BACKUP_RETENTION_DAYS" -delete
fi

echo "备份完成: $BACKUP_DIR/"
ls -lh "$BACKUP_DIR" | tail -5
