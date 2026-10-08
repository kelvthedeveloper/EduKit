#!/bin/bash
# 学校服务器更新脚本
# 用途：拉取最新镜像并平滑重启服务

set -e

echo "=== EduKit 学校服务器更新 ==="

# 进入脚本所在目录
cd "$(dirname "$0")/.."

# 拉取最新代码
echo "拉取最新配置..."
# TODO: git pull 或下载最新配置

# 拉取最新镜像
echo "拉取最新 Docker 镜像..."
docker compose pull

# 执行数据库迁移
echo "执行数据库迁移..."
docker compose run --rm backend python manage.py migrate

# 收集静态文件
echo "收集静态文件..."
docker compose run --rm backend python manage.py collectstatic --noinput

# 平滑重启服务
echo "重启服务..."
docker compose up -d

echo "更新完成！"
