#!/bin/bash
# 云边同步集成测试脚本
# 用途：模拟 School Server <-> Cloud 同步，验证协议与冲突解决

set -e

echo "=== 云边同步模拟测试 ==="

# TODO:
# 1. 启动一组 cloud 服务 + 一组 school-server 服务 (docker compose profile)
# 2. 在 school 创建若干条业务记录
# 3. 触发一次上行同步，验证 cloud 已收到
# 4. 在 cloud 修改全局配置，触发一次下行同步
# 5. 制造冲突场景，验证 Conflict Resolver 行为
# 6. 输出测试报告

echo "占位：待实现同步测试流程"
