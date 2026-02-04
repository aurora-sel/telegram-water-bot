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
import aiohttp

from database import db
from config import TELEGRAM_TOKEN, APP_HOST, APP_PORT, ENCOURAGEMENT_MESSAGES, COMPLETION_MESSAGES, ADMIN_IDS, UPTIMEROBOT_URL

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


def is_admin(user_id: int) -> bool:
    """检查用户是否为管理员"""
    return user_id in ADMIN_IDS


async def is_user_blacklisted(user_id: int) -> bool:
    """检查用户是否被加入黑名单"""
    return await db.is_in_blacklist(user_id)


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
        # 检查用户是否被黑名单或禁用
        if await is_user_blacklisted(user_id):
            logger.info(f"[调度] 用户 {user_id} 在黑名单中，跳过创建 Job")
            return
        
        # 获取用户设置
        user = await db.get_or_create_user(user_id)
        
        # 检查用户是否禁用提醒
        if user.get("is_disabled", 0):
            logger.info(f"[调度] 用户 {user_id} 已禁用提醒，跳过创建 Job")
            return
        
        interval_min = user["interval_min"]
        timezone = user["timezone"]
        
        # 如果已存在同用户的 Job，先删除
        job_id = f"reminder_{user_id}"
        try:
            scheduler.remove_job(job_id)
        except Exception:
            # Job 不存在，忽略错误
            pass
        
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
    
    # 更新最后交互时间
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此机器人。")
        return
    
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
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
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
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
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
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
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
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
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
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
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
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
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
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此功能。")
        return
    
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
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
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


# /reset 命令 - 重置用户数据
@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    """重置自己的所有饮水数据"""
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
    try:
        await db.reset_user_data(user_id)
        await message.answer(
            "🔄 <b>数据已重置</b>\n\n"
            "您的所有饮水记录已被删除，账户设置已保留。\n"
            "提醒将继续运行。",
            parse_mode="HTML"
        )
        logger.info(f"[重置] 用户 {user_id} 重置了自己的数据")
    except Exception as e:
        await message.answer(f"❌ 重置失败: {e}")


# /stop_today 命令 - 停止今日提醒
@dp.message(Command("stop_today"))
async def cmd_stop_today(message: Message):
    """停止今天的提醒，明天自动恢复"""
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
    try:
        # 移除用户的 Job
        job_id = f"reminder_{user_id}"
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass
        
        # 将用户从活跃 Job 字典中移除
        active_jobs.pop(user_id, None)
        
        # 计算明天的恢复时间（明天的开始时间）
        user = await db.get_user(user_id)
        if user:
            start_h, start_m = map(int, user['start_time'].split(":"))
            now = datetime.utcnow()
            user_tz = user['timezone']
            user_now = now + timedelta(hours=user_tz)
            
            # 计算明天开始时间
            tomorrow_start = (user_now + timedelta(days=1)).replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            # 转换回 UTC
            tomorrow_start_utc = tomorrow_start - timedelta(hours=user_tz)
            
            # 创建恢复任务（明天开始时间自动恢复）
            async def resume_reminder():
                await create_reminder_job(user_id)
                logger.info(f"[自动恢复] 用户 {user_id} 的提醒在明天已自动恢复")
            
            resume_job_id = f"resume_reminder_{user_id}"
            try:
                scheduler.remove_job(resume_job_id)
            except Exception:
                pass
            
            scheduler.add_job(
                resume_reminder,
                trigger=CronTrigger(year=tomorrow_start_utc.year, month=tomorrow_start_utc.month, 
                                   day=tomorrow_start_utc.day, hour=tomorrow_start_utc.hour, 
                                   minute=tomorrow_start_utc.minute),
                id=resume_job_id,
                replace_existing=True
            )
        
        await message.answer(
            "🛑 <b>今日提醒已停止</b>\n\n"
            "✨ 明天开始时间将自动恢复提醒\n"
            "或者使用 /start 立即重新启动。",
            parse_mode="HTML"
        )
        logger.info(f"[停止] 用户 {user_id} 停止了今日提醒，已安排明日自动恢复")
    except Exception as e:
        await message.answer(f"❌ 操作失败: {e}")
        logger.error(f"[错误] /stop_today 失败 (用户 {user_id}): {e}")


# /disable_forever 命令 - 永久禁用提醒
@dp.message(Command("disable_forever"))
async def cmd_disable_forever(message: Message):
    """永久禁用提醒"""
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
    try:
        await db.set_user_disabled(user_id, True)
        
        # 移除用户的 Job
        job_id = f"reminder_{user_id}"
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass
        
        active_jobs.pop(user_id, None)
        
        await message.answer(
            "🚫 <b>提醒已永久禁用</b>\n\n"
            "您可以继续记录饮水，但不会收到自动提醒。\n"
            "使用 /enable 重新启用提醒。",
            parse_mode="HTML"
        )
        logger.info(f"[禁用] 用户 {user_id} 永久禁用了提醒")
    except Exception as e:
        await message.answer(f"❌ 操作失败: {e}")


# /enable 命令 - 启用提醒
@dp.message(Command("enable"))
async def cmd_enable(message: Message):
    """重新启用提醒"""
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此命令。")
        return
    
    try:
        await db.set_user_disabled(user_id, False)
        await create_reminder_job(user_id)
        
        await message.answer(
            "✅ <b>提醒已启用</b>\n\n"
            "您将按照设置的间隔接收提醒。",
            parse_mode="HTML"
        )
        logger.info(f"[启用] 用户 {user_id} 启用了提醒")
    except Exception as e:
        await message.answer(f"❌ 操作失败: {e}")


# ==================== 管理员命令 ====================

# /admin_stats 命令 - 管理员查看统计
@dp.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message):
    """查看全局统计（仅管理员）"""
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    if not is_admin(user_id):
        await message.answer("❌ 您没有权限执行此命令。")
        return
    
    try:
        all_users = await db.get_all_users()
        total_users = len(all_users)
        disabled_users = sum(1 for u in all_users if u.get("is_disabled", 0))
        active_users = total_users - disabled_users
        
        stats_text = (
            f"👨‍💼 <b>管理员统计</b>\n\n"
            f"总用户数: {total_users}\n"
            f"活跃用户: {active_users}\n"
            f"禁用用户: {disabled_users}\n"
        )
        
        await message.answer(stats_text, parse_mode="HTML")
        logger.info(f"[管理] 管理员 {user_id} 查看统计")
    except Exception as e:
        await message.answer(f"❌ 查询失败: {e}")


# /blacklist 命令 - 管理员拉黑用户
@dp.message(Command("blacklist"))
async def cmd_blacklist(message: Message):
    """拉黑用户（仅管理员）"""
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    if not is_admin(user_id):
        await message.answer("❌ 您没有权限执行此命令。")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("用法: /blacklist [用户ID] [原因]\n例如: /blacklist 123456789 垃圾用户")
        return
    
    try:
        target_id = int(args[1])
        reason = " ".join(args[2:]) if len(args) > 2 else ""
        
        await db.add_to_blacklist(target_id, reason)
        
        # 删除用户的 Job
        job_id = f"reminder_{target_id}"
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass
        
        active_jobs.pop(target_id, None)
        
        await message.answer(f"✅ 已拉黑用户 {target_id}")
        logger.info(f"[管理] 管理员 {user_id} 拉黑了用户 {target_id}，原因: {reason}")
    except ValueError:
        await message.answer("❌ 用户 ID 必须是数字")
    except Exception as e:
        await message.answer(f"❌ 操作失败: {e}")


# /unblacklist 命令 - 管理员解除拉黑
@dp.message(Command("unblacklist"))
async def cmd_unblacklist(message: Message):
    """解除拉黑（仅管理员）"""
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    if not is_admin(user_id):
        await message.answer("❌ 您没有权限执行此命令。")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("用法: /unblacklist [用户ID]\n例如: /unblacklist 123456789")
        return
    
    try:
        target_id = int(args[1])
        await db.remove_from_blacklist(target_id)
        await message.answer(f"✅ 已解除对用户 {target_id} 的拉黑")
        logger.info(f"[管理] 管理员 {user_id} 解除了对用户 {target_id} 的拉黑")
    except ValueError:
        await message.answer("❌ 用户 ID 必须是数字")
    except Exception as e:
        await message.answer(f"❌ 操作失败: {e}")


# /user_info 命令 - 管理员查看用户信息
# /admin_help 命令 - 显示所有管理员命令
@dp.message(Command("admin_help"))
async def cmd_admin_help(message: Message):
    """显示所有管理员命令"""
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    if not is_admin(user_id):
        await message.answer("❌ 您没有权限执行此命令。")
        return
    
    help_text = (
        "🔑 <b>管理员命令列表</b>\n\n"
        "📊 <b>/admin_stats</b>\n"
        "查看全局统计数据\n\n"
        "🚫 <b>/blacklist</b> [用户ID] [原因(可选)]\n"
        "禁用用户账号\n"
        "例如: /blacklist 123456789 垃圾消息\n\n"
        "✅ <b>/unblacklist</b> [用户ID]\n"
        "取消禁用用户账号\n"
        "例如: /unblacklist 123456789\n\n"
        "👤 <b>/user_info</b> [用户ID]\n"
        "查看特定用户的详细信息\n"
        "例如: /user_info 123456789\n\n"
        "🔑 <b>/admin_help</b>\n"
        "显示此帮助信息"
    )
    
    await message.answer(help_text, parse_mode="HTML")
    logger.info(f"[管理员] 用户 {user_id} 查看了管理员命令")


@dp.message(Command("user_info"))
async def cmd_user_info(message: Message):
    """查看用户信息（仅管理员）"""
    user_id = message.from_user.id
    await db.update_last_interaction(user_id)
    
    if not is_admin(user_id):
        await message.answer("❌ 您没有权限执行此命令。")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("用法: /user_info [用户ID]\n例如: /user_info 123456789")
        return
    
    try:
        target_id = int(args[1])
        user = await db.get_or_create_user(target_id)
        
        # 获取用户统计
        stats = await db.get_stats(target_id)
        today_total = stats["today_total"]
        
        # 获取用户黑名单状态
        is_blacklisted = await db.is_in_blacklist(target_id)
        
        info_text = (
            f"👤 <b>用户信息</b>\n\n"
            f"用户 ID: {user['user_id']}\n"
            f"每日目标: {user['daily_goal']} ml\n"
            f"提醒间隔: {user['interval_min']} 分钟\n"
            f"时区: UTC+{user['timezone']}\n"
            f"活跃时段: {user['start_time']} ~ {user['end_time']}\n"
            f"提醒状态: {'🚫 禁用' if user.get('is_disabled') else '✅ 启用'}\n"
            f"黑名单状态: {'❌ 已拉黑' if is_blacklisted else '✅ 正常'}\n"
            f"今日饮水: {today_total} ml\n"
            f"账户创建: {user['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"最后交互: {user['last_interaction_time'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await message.answer(info_text, parse_mode="HTML")
        logger.info(f"[管理] 管理员 {user_id} 查看了用户 {target_id} 的信息")
    except ValueError:
        await message.answer("❌ 用户 ID 必须是数字")
    except Exception as e:
        await message.answer(f"❌ 查询失败: {e}")


# 处理数字输入 - 记录饮水
@dp.message(F.text.isdigit())
async def handle_water_input(message: Message):
    """处理数字输入，记录饮水量"""
    user_id = message.from_user.id
    
    # 更新最后交互时间
    await db.update_last_interaction(user_id)
    
    # 检查黑名单
    if await is_user_blacklisted(user_id):
        await message.answer("❌ 您已被管理员禁用，无法使用此功能。")
        return
    
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

async def cleanup_inactive_users():
    """清理超过 7 天未交互的用户"""
    try:
        inactive_users = await db.get_inactive_users(days=7)
        for user_info in inactive_users:
            user_id = user_info["user_id"]
            try:
                # 发送最后提醒信息
                await bot.send_message(
                    user_id,
                    "👋 <b>账户即将清理</b>\n\n"
                    "由于您超过 7 天未与我们的机器人进行任何交互，"
                    "您的所有数据（喝水记录）将在 24 小时后被删除。\n\n"
                    "如需保留数据，请回复任何消息。",
                    parse_mode="HTML"
                )
                # 更新最后交互时间（给用户 24 小时反应时间）
                await db.update_last_interaction(user_id)
            except Exception as e:
                logger.warning(f"[清理] 无法发送消息给用户 {user_id}: {e}")
                # 用户可能已删除机器人或封禁了，直接删除
                await db.delete_user_completely(user_id)
                logger.info(f"[清理] 已删除用户 {user_id} 的所有数据（无法联系）")
    except Exception as e:
        logger.error(f"[清理] 清理过期用户任务失败: {e}")


async def on_startup():
    """应用启动事件"""
    try:
        logger.info("[启动] 初始化数据库...")
        await db.init()
        logger.info("[启动] ✅ 数据库初始化成功")
    except Exception as e:
        logger.error(f"[启动] ❌ 数据库初始化失败: {e}", exc_info=True)
        logger.error("[启动] 💡 诊断信息:")
        logger.error("[启动]   - 检查 DATABASE_URL 环境变量是否正确")
        logger.error("[启动]   - 检查 PostgreSQL 服务器是否在线")
        logger.error("[启动]   - 检查数据库是否存在且可访问")
        raise
    
    try:
        logger.info("[启动] 启动 APScheduler...")
        if not scheduler.running:
            scheduler.start()
        logger.info("[启动] ✅ APScheduler 启动成功")
    except Exception as e:
        logger.error(f"[启动] ❌ APScheduler 启动失败: {e}", exc_info=True)
        raise

    # 添加定时清理任务（每天 00:00 UTC 执行）
    scheduler.add_job(
        cleanup_inactive_users,
        trigger=CronTrigger(hour=0, minute=0),
        id="cleanup_inactive_users",
        name="清理过期用户",
        replace_existing=True,
        misfire_grace_time=300
    )
    logger.info("[启动] ✅ 已注册过期用户清理任务（每日 00:00 UTC 执行）")
    
    logger.info("[启动] Telegram 机器人已启动")
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
    try:
        app = create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, APP_HOST, APP_PORT)
        await site.start()
        
        logger.info(f"[HTTP服务器] ✅ 已启动，监听 {APP_HOST}:{APP_PORT}")
        return runner
    except Exception as e:
        logger.error(f"[HTTP服务器] ❌ 启动失败: {e}", exc_info=True)
        logger.error(f"[HTTP服务器] 💡 检查端口 {APP_PORT} 是否已被占用")
        raise


async def main():
    """主函数 - 同时运行 HTTP 服务器和 Telegram Bot"""
    # 注册启动和关闭事件
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    http_runner = None
    try:
        # 启动 HTTP 服务器
        logger.info("[HTTP服务器] 启动中...")
        http_runner = await run_http_server()
        logger.info("[HTTP服务器] ✅ 成功启动")
        
        # 删除 Webhook（如果存在）并启动长轮询
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("[轮询] 启动长轮询模式...")
        logger.info("[启动] 🎉 Telegram Bot 已就绪！开始接收消息...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"[错误] 主程序异常: {e}", exc_info=True)
        raise
    finally:
        # 清理 HTTP 服务器
        if http_runner:
            try:
                await http_runner.cleanup()
                logger.info("[关闭] HTTP 服务器已清理")
            except Exception as e:
                logger.warning(f"[关闭] HTTP 服务器清理失败: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[关闭] 收到中止信号，正在关闭...")
    except Exception as e:
        logger.error(f"[错误] 应用崩溃: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
