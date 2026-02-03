"""
配置模块 (config.py)
存储机器人的全局配置和常量。
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ==================== Telegram Bot 配置 ====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("错误: 环境变量 TELEGRAM_TOKEN 未设置。请在 Koyeb 中配置此环境变量。")

# ==================== Webhook 配置 ====================
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
# Webhook URL 可选，用于 Webhook 模式

# ==================== 数据库配置 ====================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("错误: 环境变量 DATABASE_URL 未设置。请在 Koyeb 中配置此环境变量。")

# ==================== 应用配置 ====================
APP_PORT = int(os.getenv("PORT", 8080))  # Koyeb 默认使用 8080 端口
APP_HOST = "0.0.0.0"  # 监听所有网卡

# ==================== 管理员配置 ====================
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")  # 格式：123456789,987654321
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip()] if ADMIN_IDS_STR else []

# ==================== 保活配置（防止自动休眠）====================
UPTIMEROBOT_URL = os.getenv("UPTIMEROBOT_URL")  # UptimeRobot 监控 URL（可选）
# 如果设置此 URL，机器人会在后台定期 ping 以保持应用在线

# ==================== 业务常量 ====================

# 默认用户设置
DEFAULT_DAILY_GOAL = 2500  # ml
DEFAULT_INTERVAL = 60  # 分钟
DEFAULT_START_TIME = "08:00"
DEFAULT_END_TIME = "22:00"
DEFAULT_TIMEZONE = 8  # UTC+8

# 智能评价阈值
EVALUATION_THRESHOLDS = {
    "low": 0.5,      # 低于 50% 鼓励
    "medium": 0.8,   # 50% ~ 80% 中等提醒
    "high": 1.0,     # 80% ~ 100% 接近目标
    "excellent": 1.0  # 达到或超过目标
}

# 鼓励语
ENCOURAGEMENT_MESSAGES = {
    "low": [
        "💪 离目标还有段距离，喝一小口也是进步！",
        "🌟 每一滴都很珍贵，继续加油！",
        "💧 多喝水，改善体质，从现在开始！"
    ],
    "medium": [
        "👍 已经完成一半啦，再接再厉！",
        "🎯 距离目标越来越近，坚持住！",
        "⏳ 还需要再喝一点就完成了！"
    ],
    "high": [
        "🚀 你离目标很近了，冲刺吧！",
        "✨ 马上就要达成了，再加油一点！"
    ]
}

# 完成语
COMPLETION_MESSAGES = [
    "🎉 成就达成！你现在的身体水分充盈！",
    "🏆 目标完成！你是饮水小卫士！",
    "💯 完美！今天的饮水目标已达成！",
    "⭐ 太棒了！保持这个好习惯！"
]

# API 端点
API_ENDPOINTS = {
    "get_me": "https://api.telegram.org/bot{token}/getMe",
    "set_webhook": "https://api.telegram.org/bot{token}/setWebhook",
    "delete_webhook": "https://api.telegram.org/bot{token}/deleteWebhook",
}
