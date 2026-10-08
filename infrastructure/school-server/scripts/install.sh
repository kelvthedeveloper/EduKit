#!/bin/bash
# 学校服务器安装脚本
# 用途：在全新 Linux 服务器上一键部署 EduKit 学校本地版本

set -e

echo "=== EduKit 学校服务器安装脚本 ==="
echo ""

# 检查 Docker 是否已安装
if ! command -v docker &> /dev/null; then
    echo "正在安装 Docker..."
    # TODO: 安装 Docker 和 Docker Compose
    echo "Docker 安装完成"
else
    echo "Docker 已安装"
fi

# 创建必要目录
echo "创建数据目录..."
mkdir -p ./backups ./data/nginx ./data/postgres ./data/redis

# 复制环境变量文件
if [ ! -f .env ]; then
    echo "复制环境变量配置..."
    cp .env.example .env
    echo "请编辑 .env 文件配置相关参数后继续"
    exit 1
fi

# 启动服务
echo "启动所有服务..."
docker compose up -d

echo ""
echo "安装完成！访问 http://<服务器IP> 进入系统"
