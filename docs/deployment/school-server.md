# 学校本地服务器部署文档

学校端部署实施 SOP。

## 硬件与环境准备

1. 准备一台 Linux 服务器 (推荐 Ubuntu 22.04 LTS)
2. 配置静态 IP，接入学校局域网
3. 开放以下端口：80 (HTTP), 443 (HTTPS, 可选)
4. 可选：UPS 不间断电源

## 部署步骤

```bash
# 1. 拷贝安装包到服务器
scp edukit-school-server.tar.gz user@school-server:/tmp/

# 2. 解压并进入目录
tar xzf edukit-school-server.tar.gz && cd school-server

# 3. 复制环境变量并编辑
cp .env.example .env
nano .env

# 4. 一键安装
chmod +x scripts/*.sh
./scripts/install.sh

# 5. 验证
./scripts/health-check.sh
```

## 日常运维

- **每日**：检查备份是否成功 (`./scripts/backup.sh`)
- **每周**：执行一次健康检查，查看磁盘
- **每月**：应用系统安全补丁，更新 EduKit (如有新版本)
