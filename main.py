"""
主程序模块 (main.py)
Telegram 喝水提醒机器人的核心逻辑。
支持多用户独立调度，基于 aiogram 3.x 和 APScheduler。
支持 HTTP 健康检查用于云平台部署（Koyeb, Render 等）
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import re

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiohttp import web

from database import db
from config import TELEGRAM_TOKEN, APP_HOST, APP_PORT, ENCOURAGEMENT_MESSAGES, COMPLETION_MESSAGES

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== 全局对象 ====================
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()

# 存储所有活跃的用户提醒 Job ID，格式：{user_id: job_id}
active_jobs = {}


# ==================== 状态管理 ====================

class SettingsForm(StatesGroup):
    """用户设置表单状态"""
    waiting_for_goal = State()
    waiting_for_timezone = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()
    waiting_for_interval = State()


# ==================== 辅助函数 ====================

def get_user_local_time(timezone: int) -> datetime:
    """获取用户当前本地时间"""
    utc_now = datetime.utcnow()
    return utc_now + timedelta(hours=timezone)


def is_in_active_period(now: datetime, start_time_str: str, end_time_str: str) -> bool:
    """判断当前时间是否在活跃时段内"""
    try:
        # 解析时间字符串 HH:MM
        start_h, start_m = map(int, start_time_str.split(":"))
        end_h, end_m = map(int, end_time_str.split(":"))
        
        now_h, now_m = now.hour, now.minute
        now_minutes = now_h * 60 + now_m
        
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        
        # 处理跨越午夜的情况（如 22:00 ~ 08:00）
        if start_minutes < end_minutes:
            return start_minutes <= now_minutes < end_minutes
        else:
            return now_minutes >= start_minutes or now_minutes < end_minutes
    except:
        return True


async def create_reminder_job(user_id: int):
    """为用户创建一个独立的提醒 Job"""
    try:
        # 获取用户设置
        user = await db.get_or_create_user(user_id)
        
        interval_min = user["interval_min"]
        timezone = user["timezone"]
        
        # 如果已存在同用户的 Job，先删除
        job_id = f"reminder_{user_id}"
        if job_id in scheduler.get_jobs():
            scheduler.remove_job(job_id)
        
        # 创建异步任务函数
        async def send_reminder():
            """发送提醒给用户"""
            try:
                user_data = await db.get_or_create_user(user_id)
                user_local_time = get_user_local_time(user_data["timezone"])
                
                # 检查是否在活跃时段
                if not is_in_active_period(
                    user_local_time,
                    user_data["start_time"],
                    user_data["end_time"]
                ):
                    logger.info(f"[提醒] 用户 {user_id} 不在活跃时段，跳过提醒")
                    return
                
                # 获取今日进度
                today_total = await db.get_today_total(user_id, user_data["timezone"])
                daily_goal = user_data["daily_goal"]
                progress_percent = int((today_total / daily_goal) * 100) if daily_goal > 0 else 0
                
                # 构建提醒消息
                message_text = (
                    f"💧 <b>是时候喝水了！</b>\n\n"
                    f"📊 <b>今日进度</b>\n"
                    f"已喝: {today_total}ml / {daily_goal}ml ({progress_percent}%)\n"
                    f"还需: {max(0, daily_goal - today_total)}ml\n\n"
                    f"📝 <i>直接发送数字（如 200）记录饮水量</i>"
                )
                
                await bot.send_message(
                    user_id,
                    message_text,
                    parse_mode="HTML"
                )
                
                # 更新提醒时间
                await db.update_last_remind_time(user_id)
                logger.info(f"[提醒] 已发送给用户 {user_id}")
                
            except Exception as e:
                logger.error(f"[提醒] 发送给用户 {user_id} 失败: {e}")
        
        # 注册定时任务（每 interval_min 分钟执行一次）
        scheduler.add_job(
            send_reminder,
            trigger=CronTrigger(minute=f"*/{interval_min if interval_min >= 1 else 1}"),
            id=job_id,
            name=f"提醒_用户{user_id}",
            replace_existing=True,
            misfire_grace_time=30
        )
        
        active_jobs[user_id] = job_id
        logger.info(f"[调度] 为用户 {user_id} 创建提醒 Job (间隔 {interval_min} 分钟)")
        
    except Exception as e:
        logger.error(f"[调度] 创建 Job 失败 (用户 {user_id}): {e}")


async def reset_reminder_job(user_id: int):
    """重置用户的提醒 Job（用户记录饮水后调用）"""
    logger.info(f"[调度] 重置用户 {user_id} 的提醒 Job")
    await create_reminder_job(user_id)


# ==================== 消息处理器 ====================

# /start 命令
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """处理 /start 命令"""
    user_id = message.from_user.id
    
    # 创建或获取用户
    user = await db.get_or_create_user(user_id)
    
    # 为新用户创建提醒 Job
    if user_id not in active_jobs:
        await create_reminder_job(user_id)
    
    # 构建欢迎消息
    welcome_text = (
        "👋 <b>欢迎来到喝水提醒机器人！</b>\n\n"
        "🎯 <b>功能介绍</b>\n"
        "📝 直接发送数字记录饮水量 (如: 200)\n"
        "/goal [数字] - 设置每日目标 (ml)\n"
        "/interval [分钟] - 设置提醒间隔\n"
        "/timezone [数字] - 设置时区 (如: 8)\n"
        "/time [开始] [结束] - 设置活跃时段 (如: 08:00 22:00)\n"
        "/back [水量] [分钟前] - 补录饮水记录\n"
        "/stats - 查看统计数据\n"
        "/help - 显示帮助\n\n"
        f"📊 <b>您的当前设置</b>\n"
        f"目标: {user['daily_goal']}ml/天\n"
        f"提醒间隔: {user['interval_min']}分钟\n"
        f"时区: UTC+{user['timezone']}\n"
        f"活跃时段: {user['start_time']} ~ {user['end_time']}"
    )
    
    await message.answer(welcome_text, parse_mode="HTML")


# /help 命令
@dp.message(Command("help"))
async def cmd_help(message: Message):
    """处理 /help 命令"""
    help_text = (
        "🤖 <b>机器人命令列表</b>\n\n"
        "<b>📝 记录饮水</b>\n"
        "直接发送数字 (如: 200) - 记录 200ml\n"
        "/back [水量] [分钟前] - 补录 (如: /back 300 30)\n\n"
        "<b>⚙️ 个性化配置</b>\n"
        "/goal [数字] - 设置每日目标饮水量\n"
        "/interval [数字] - 设置提醒间隔 (分钟)\n"
        "/timezone [数字] - 设置时区 (如 8 表示 UTC+8)\n"
        "/time [开始] [结束] - 设置活跃时段\n\n"
        "<b>📊 数据查询</b>\n"
        "/stats - 查看今日进度和 7 日趋势\n\n"
        "<b>ℹ️ 其他</b>\n"
        "/settings - 查看当前设置\n"
        "/help - 显示此帮助"
    )
    await message.answer(help_text, parse_mode="HTML")


# /settings 命令
@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    """查看当前设置"""
    user_id = message.from_user.id
    user = await db.get_or_create_user(user_id)
    
    settings_text = (
        "⚙️ <b>您的当前设置</b>\n\n"
        f"🎯 每日目标: {user['daily_goal']} ml\n"
        f"⏱️ 提醒间隔: {user['interval_min']} 分钟\n"
        f"🌍 时区: UTC+{user['timezone']}\n"
        f"⏰ 活跃时段: {user['start_time']} ~ {user['end_time']}\n"
        f"📅 账户创建: {user['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await message.answer(settings_text, parse_mode="HTML")


# /goal 命令
@dp.message(Command("goal"))
async def cmd_goal(message: Message, state: FSMContext):
    """设置每日目标"""
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("用法: /goal [数字]\n例如: /goal 2500")
        return
    
    try:
        goal = int(args[1])
        if goal <= 0:
            await message.answer("❌ 目标必须大于 0")
            return
        
        user_id = message.from_user.id
        await db.update_user_settings(user_id, daily_goal=goal)
        
        await message.answer(f"✅ 已设置每日目标为 {goal}ml")
        logger.info(f"[设置] 用户 {user_id} 设置目标为 {goal}ml")
        
    except ValueError:
        await message.answer("❌ 请输入有效的数字")


# /interval 命令
@dp.message(Command("interval"))
async def cmd_interval(message: Message):
    """设置提醒间隔"""
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("用法: /interval [分钟]\n例如: /interval 60")
        return
    
    try:
        interval = int(args[1])
        if interval <= 0:
            await message.answer("❌ 间隔必须大于 0")
            return
        
        user_id = message.from_user.id
        await db.update_user_settings(user_id, interval_min=interval)
        
        # 重置提醒 Job
        await reset_reminder_job(user_id)
        
        await message.answer(f"✅ 已设置提醒间隔为 {interval}分钟")
        logger.info(f"[设置] 用户 {user_id} 设置提醒间隔为 {interval}分钟")
        
    except ValueError:
        await message.answer("❌ 请输入有效的数字")


# /timezone 命令
@dp.message(Command("timezone"))
async def cmd_timezone(message: Message):
    """设置时区"""
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("用法: /timezone [数字]\n例如: /timezone 8 (表示 UTC+8)")
        return
    
    try:
        tz = int(args[1])
        if tz < -12 or tz > 14:
            await message.answer("❌ 时区范围应为 -12 ~ 14")
            return
        
        user_id = message.from_user.id
        await db.update_user_settings(user_id, timezone=tz)
        
        await message.answer(f"✅ 已设置时区为 UTC+{tz}")
        logger.info(f"[设置] 用户 {user_id} 设置时区为 UTC+{tz}")
        
    except ValueError:
        await message.answer("❌ 请输入有效的数字")


# /time 命令
@dp.message(Command("time"))
async def cmd_time(message: Message):
    """设置活跃时段"""
    args = message.text.split()
    
    if len(args) < 3:
        await message.answer("用法: /time [开始时间] [结束时间]\n例如: /time 08:00 22:00")
        return
    
    try:
        start_time = args[1]
        end_time = args[2]
        
        # 验证时间格式
        if not re.match(r"^\d{2}:\d{2}$", start_time) or not re.match(r"^\d{2}:\d{2}$", end_time):
            await message.answer("❌ 时间格式不正确，请使用 HH:MM 格式")
            return
        
        user_id = message.from_user.id
        await db.update_user_settings(user_id, start_time=start_time, end_time=end_time)
        
        await message.answer(f"✅ 已设置活跃时段为 {start_time} ~ {end_time}")
        logger.info(f"[设置] 用户 {user_id} 设置活跃时段为 {start_time} ~ {end_time}")
        
    except Exception as e:
        await message.answer(f"❌ 设置失败: {e}")


# /back 命令 - 补录饮水
@dp.message(Command("back"))
async def cmd_back(message: Message):
    """补录饮水记录"""
    args = message.text.split()
    
    if len(args) < 3:
        await message.answer("用法: /back [水量] [分钟前]\n例如: /back 300 30")
        return
    
    try:
        amount = int(args[1])
        minutes_ago = int(args[2])
        
        if amount <= 0:
            await message.answer("❌ 水量必须大于 0")
            return
        
        if minutes_ago < 0:
            await message.answer("❌ 分钟数不能为负数")
            return
        
        user_id = message.from_user.id
        user = await db.get_or_create_user(user_id)
        
        # 计算记录时间（UTC）
        record_time = datetime.utcnow() - timedelta(minutes=minutes_ago)
        
        # 添加记录
        await db.add_record(user_id, amount, record_time)
        
        # 获取今日进度
        today_total = await db.get_today_total(user_id, user["timezone"])
        daily_goal = user["daily_goal"]
        progress_percent = int((today_total / daily_goal) * 100) if daily_goal > 0 else 0
        
        # 重置提醒 Job
        await reset_reminder_job(user_id)
        
        # 构建反馈消息
        feedback_text = (
            f"🥤 <b>补录成功！</b>\n\n"
            f"本次: {amount}ml\n"
            f"今日进度: {today_total}/{daily_goal}ml ({progress_percent}%)\n"
            f"距离目标还差: {max(0, daily_goal - today_total)}ml\n"
            f"⏱️ 下一场提醒已重置"
        )
        
        await message.answer(feedback_text, parse_mode="HTML")
        logger.info(f"[记录] 用户 {user_id} 补录 {minutes_ago}分钟前的 {amount}ml")
        
    except ValueError:
        await message.answer("❌ 请输入有效的数字")


# /stats 命令
@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """查看统计数据"""
    user_id = message.from_user.id
    user = await db.get_or_create_user(user_id)
    
    # 获取统计数据
    stats = await db.get_stats(user_id, days=7, timezone=user["timezone"])
    
    today_total = stats["today_total"]
    daily_goal = user["daily_goal"]
    progress_percent = int((today_total / daily_goal) * 100) if daily_goal > 0 else 0
    
    # 智能评价
    if progress_percent < 50:
        messages = ENCOURAGEMENT_MESSAGES["low"]
    elif progress_percent < 80:
        messages = ENCOURAGEMENT_MESSAGES["medium"]
    elif progress_percent < 100:
        messages = ENCOURAGEMENT_MESSAGES["high"]
    else:
        messages = COMPLETION_MESSAGES
    
    encouragement = messages[0] if messages else "继续加油！"
    
    # 构建统计消息
    stats_text = (
        f"📊 <b>今日数据</b>\n"
        f"已喝: {today_total}ml / {daily_goal}ml\n"
        f"进度: {progress_percent}%\n"
        f"还差: {max(0, daily_goal - today_total)}ml\n\n"
        f"{encouragement}\n\n"
        f"📈 <b>最近 7 天趋势</b>\n"
    )
    
    if stats["daily_stats"]:
        for stat in stats["daily_stats"]:
            date_str = stat["date"]
            total = stat["total"]
            goal_percent = int((total / daily_goal) * 100) if daily_goal > 0 else 0
            stats_text += f"{date_str}: {total}ml ({goal_percent}%)\n"
    else:
        stats_text += "暂无记录\n"
    
    await message.answer(stats_text, parse_mode="HTML")
    logger.info(f"[统计] 用户 {user_id} 查询统计数据")


# 处理数字输入 - 记录饮水
@dp.message(F.text.isdigit())
async def handle_water_input(message: Message):
    """处理数字输入，记录饮水量"""
    user_id = message.from_user.id
    
    try:
        amount = int(message.text)
        
        if amount <= 0:
            await message.answer("❌ 请输入大于 0 的数字")
            return
        
        if amount > 5000:
            await message.answer("⚠️ 输入值过大，请确认。如确实需要记录，请用 /back 命令")
            return
        
        # 获取用户设置
        user = await db.get_or_create_user(user_id)
        
        # 添加记录
        await db.add_record(user_id, amount)
        
        # 获取今日进度
        today_total = await db.get_today_total(user_id, user["timezone"])
        daily_goal = user["daily_goal"]
        progress_percent = int((today_total / daily_goal) * 100) if daily_goal > 0 else 0
        
        # 重置提醒 Job
        await reset_reminder_job(user_id)
        
        # 构建反馈消息
        feedback_text = (
            f"🥤 <b>记录成功！</b>\n\n"
            f"本次: {amount}ml\n"
            f"今日进度: {today_total}/{daily_goal}ml ({progress_percent}%)\n"
            f"距离目标还差: {max(0, daily_goal - today_total)}ml\n"
            f"⏱️ 下一场提醒已重置"
        )
        
        # 如果达成目标，添加庆祝语
        if progress_percent >= 100:
            feedback_text += f"\n\n{COMPLETION_MESSAGES[0]}"
        
        await message.answer(feedback_text, parse_mode="HTML")
        logger.info(f"[记录] 用户 {user_id} 记录了 {amount}ml")
        
    except Exception as e:
        logger.error(f"[记录] 处理用户 {user_id} 的输入失败: {e}")
        await message.answer(f"❌ 记录失败: {e}")


# 默认消息处理
@dp.message()
async def handle_unknown(message: Message):
    """处理未知消息"""
    await message.answer(
        "❓ 我不太明白你的意思。\n"
        "请输入数字记录饮水，或使用 /help 查看命令列表。"
    )


# ==================== 应用启动和关闭 ====================

async def on_startup():
    """应用启动事件"""
    logger.info("[启动] 初始化数据库...")
    await db.init()
    
    logger.info("[启动] 启动 APScheduler...")
    if not scheduler.running:
        scheduler.start()
    
    logger.info("[启动] Telegram 机器人已启动")
    
    # 加载所有活跃用户的 Job（可选，用于容器重启后恢复）
    # 由于内存存储，重启后需要用户重新触发
    logger.info("[启动] 机器人初始化完成")


async def on_shutdown():
    """应用关闭事件"""
    logger.info("[关闭] 停止 APScheduler...")
    if scheduler.running:
        scheduler.shutdown()
    
    logger.info("[关闭] 关闭数据库连接...")
    await db.close()
    
    await bot.session.close()
    logger.info("[关闭] 机器人已关闭")


# ==================== HTTP 服务器（用于健康检查和部署验证） ====================

async def health_check(request):
    """健康检查端点 - 返回 200 OK"""
    return web.Response(text="OK", status=200)


async def status_check(request):
    """状态检查端点 - 返回应用状态"""
    status = {
        "status": "running",
        "bot": "active",
        "timestamp": datetime.utcnow().isoformat()
    }
    return web.json_response(status)


def create_app():
    """创建 aiohttp Web 应用"""
    app = web.Application()
    
    # 添加路由（用于健康检查）
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', status_check)
    
    return app


async def run_http_server():
    """运行 HTTP 服务器"""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, APP_HOST, APP_PORT)
    await site.start()
    
    logger.info(f"[HTTP服务器] 已启动，监听 {APP_HOST}:{APP_PORT}")
    return runner


async def main():
    """主函数 - 同时运行 HTTP 服务器和 Telegram Bot"""
    # 注册启动和关闭事件
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # 启动 HTTP 服务器
    http_runner = await run_http_server()
    
    try:
        # 删除 Webhook（如果存在）并启动长轮询
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("[轮询] 启动长轮询模式...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"[错误] 主程序异常: {e}")
        raise
    finally:
        # 清理 HTTP 服务器
        await http_runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[关闭] 收到中止信号，正在关闭...")
    except Exception as e:
        logger.error(f"[错误] 应用崩溃: {e}")
