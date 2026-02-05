#!/usr/bin/env python3
"""
快速启动诊断脚本 - 在 Koyeb 部署前运行此脚本检查配置
"""

import os
import sys

print("🔍 启动诊断检查...\n")

# 1. 检查必须的环境变量
print("📋 检查环境变量：")
required = {
    "TELEGRAM_TOKEN": "从 @BotFather 获取",
    "DATABASE_URL": "PostgreSQL 连接字符串"
}

missing = []
for var, desc in required.items():
    val = os.getenv(var)
    if val:
        display = val[:20] + "..." if len(val) > 20 else val
        print(f"  ✅ {var}: 已设置")
    else:
        print(f"  ❌ {var}: 未设置 ({desc})")
        missing.append(var)

if missing:
    print(f"\n❌ 缺少 {len(missing)} 个必要环境变量！")
    print("\n在 Koyeb 部署中设置这些变量：")
    for var in missing:
        print(f"  - {var}")
    sys.exit(1)

print("\n✅ 所有环境变量已设置！")
print("🚀 应用可以启动")
