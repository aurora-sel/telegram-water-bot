"""
数据库操作模块 (database.py)
提供用户配置和饮水记录的数据库管理功能。
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import asyncpg
import asyncio

# 从环境变量获取数据库 URL（Koyeb 部署时使用）
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/water_reminder")

# 处理 asyncpg 兼容性：将 psycopg2 URL 转换为 asyncpg 格式
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

Base = declarative_base()


# ==================== 数据库模型 ====================

class User(Base):
    """用户配置表"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True)  # Telegram 用户 ID
    daily_goal = Column(Integer, default=2500)  # 每日目标饮水量 (ml)
    interval_min = Column(Integer, default=60)  # 提醒间隔 (分钟)
    start_time = Column(String(5), default="08:00")  # 活跃时段开始
    end_time = Column(String(5), default="22:00")  # 活跃时段结束
    timezone = Column(Integer, default=8)  # 时区偏移 (如 +8)
    last_remind_time = Column(DateTime, nullable=True)  # 上一次提醒时间 (UTC)
    last_interaction_time = Column(DateTime, default=datetime.utcnow)  # 上一次交互时间（用于检测过期用户）
    is_disabled = Column(Integer, default=0)  # 是否禁用提醒（1 = 禁用，0 = 启用）
    created_at = Column(DateTime, default=datetime.utcnow)  # 账户创建时间
    
    # 关系映射
    records = relationship("Record", back_populates="user", cascade="all, delete-orphan")


class Record(Base):
    """饮水记录表"""
    __tablename__ = "records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # 记录 ID
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)  # 用户 ID
    amount = Column(Integer, nullable=False)  # 饮水量 (ml)
    created_at = Column(DateTime, default=datetime.utcnow)  # 记录时间 (UTC)
    
    # 关系映射
    user = relationship("User", back_populates="records")


# ==================== 异步数据库操作类 ====================

class DatabaseManager:
    """异步数据库管理器 - 为 APScheduler 和 aiogram 提供接口"""
    
    def __init__(self):
        self.pool = None
    
    async def init(self):
        """初始化数据库连接池"""
        try:
            # 验证 DATABASE_URL 环境变量
            if not DATABASE_URL or DATABASE_URL == "postgresql://user:password@localhost/water_reminder":
                print("[DB] ❌ DATABASE_URL 未正确配置！")
                print("[DB] 当前值: (未设置或使用默认值)")
                print("[DB] 请设置环境变量: DATABASE_URL=postgresql://username:password@host:port/dbname")
                raise ValueError("DATABASE_URL 环境变量未设置或格式不正确")
            
            # 创建 asyncpg 连接池
            # asyncpg 需要使用 postgresql:// 格式
            dsn = DATABASE_URL if DATABASE_URL.startswith("postgresql://") else f"postgresql://{DATABASE_URL}"
            
            # 隐藏密码后显示连接字符串
            safe_dsn = dsn.split("@")[1] if "@" in dsn else "unknown"
            print(f"[DB] 正在连接数据库: postgresql://***@{safe_dsn}")
            
            self.pool = await asyncpg.create_pool(
                dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            print("[DB] ✅ 数据库连接池初始化成功")
            
            # 建表
            await self._create_tables()
            print("[DB] ✅ 所有表初始化完成")
        except Exception as e:
            print(f"[DB] ❌ 初始化失败: {e}")
            print(f"[DB] 错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _create_tables(self):
        """创建数据库表并执行迁移"""
        try:
            async with self.pool.acquire() as conn:
                # 1. 创建主表
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        daily_goal INTEGER DEFAULT 2500,
                        interval_min INTEGER DEFAULT 60,
                        start_time VARCHAR(5) DEFAULT '08:00',
                        end_time VARCHAR(5) DEFAULT '22:00',
                        timezone INTEGER DEFAULT 8,
                        last_remind_time TIMESTAMP NULL,
                        last_interaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_disabled INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("[DB] users 表已就绪")
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS records (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                        amount INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("[DB] records 表已就绪")
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS blacklist (
                        user_id BIGINT PRIMARY KEY,
                        reason VARCHAR(255),
                        blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("[DB] blacklist 表已就绪")
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS reminder_messages (
                        user_id BIGINT PRIMARY KEY,
                        gradient_1 VARCHAR(255),
                        gradient_2 VARCHAR(255),
                        gradient_3 VARCHAR(255),
                        gradient_4 VARCHAR(255),
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("[DB] reminder_messages 表已就绪")
                
                # 2. 执行迁移：添加缺失的列（v2.0 升级）
                await self._migrate_schema(conn)
                
                # 3. 创建索引
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_records_user_id ON records(user_id)
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_records_created_at ON records(created_at)
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_last_interaction ON users(last_interaction_time)
                """)
                print("[DB] 表创建/迁移/索引完成")
        except Exception as e:
            print(f"[DB] ❌ 表创建失败: {e}")
            print(f"[DB] 错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _migrate_schema(self, conn):
        """数据库架构迁移 - 处理列的添加和修改"""
        try:
            # 首先检查 users 表是否存在
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """)
            
            if not table_exists:
                print("[DB] users 表不存在，跳过迁移")
                return
            
            # 检查 last_interaction_time 列是否存在
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'last_interaction_time'
                )
            """)
            
            if not result:
                print("[DB] 迁移: 添加 last_interaction_time 列...")
                await conn.execute("""
                    ALTER TABLE users 
                    ADD COLUMN last_interaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
                print("[DB] ✅ last_interaction_time 列已添加")
        except Exception as e:
            print(f"[DB] ⚠️  迁移 last_interaction_time 列失败: {e}")
        
        try:
            # 检查 is_disabled 列是否存在
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'is_disabled'
                )
            """)
            
            if not result:
                print("[DB] 迁移: 添加 is_disabled 列...")
                await conn.execute("""
                    ALTER TABLE users 
                    ADD COLUMN is_disabled INTEGER DEFAULT 0
                """)
                print("[DB] ✅ is_disabled 列已添加")
        except Exception as e:
            print(f"[DB] ⚠️  迁移 is_disabled 列失败: {e}")
        
        # 为 users 表添加 quiet_hours 列（免打扰时段，JSON 格式）
        try:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'quiet_hours'
                )
            """)
            
            if not result:
                print("[DB] 迁移: 添加 quiet_hours 列...")
                await conn.execute("""
                    ALTER TABLE users 
                    ADD COLUMN quiet_hours TEXT DEFAULT '[]'
                """)
                print("[DB] ✅ quiet_hours 列已添加")
        except Exception as e:
            print(f"[DB] ⚠️  迁移 quiet_hours 列失败: {e}")
        
        # 为 reminder_messages 表添加更多梯度列（gradient_5 到 gradient_99）
        try:
            # 检查 reminder_messages 表是否存在
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'reminder_messages'
                )
            """)
            
            if table_exists:
                # 添加梯度 5-99
                for i in range(5, 100):
                    column_name = f"gradient_{i}"
                    result = await conn.fetchval(f"""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = 'reminder_messages' AND column_name = '{column_name}'
                        )
                    """)
                    
                    if not result:
                        try:
                            await conn.execute(f"""
                                ALTER TABLE reminder_messages 
                                ADD COLUMN {column_name} VARCHAR(255)
                            """)
                            print(f"[DB] ✅ {column_name} 列已添加")
                        except Exception as e:
                            print(f"[DB] ⚠️  添加 {column_name} 列失败: {e}")
                            break  # 如果有一个失败，后面的可能都会失败
        except Exception as e:
            print(f"[DB] ⚠️  迁移 reminder_messages 梯度列失败: {e}")

    
    async def close(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
    
    # ==================== 用户操作 ====================
    
    async def get_or_create_user(self, user_id: int) -> Dict[str, Any]:
        """获取或创建用户配置"""
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            
            if not user:
                # 创建新用户
                await conn.execute(
                    """INSERT INTO users (user_id, daily_goal, interval_min, 
                       start_time, end_time, timezone) 
                       VALUES ($1, 2500, 60, '08:00', '22:00', 8)""",
                    user_id
                )
                user = await conn.fetchrow(
                    "SELECT * FROM users WHERE user_id = $1",
                    user_id
                )
            
            return dict(user)
    
    async def update_user_settings(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """更新用户设置"""
        async with self.pool.acquire() as conn:
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ["daily_goal", "interval_min", "start_time", "end_time", "timezone"]:
                    fields.append(f"{key} = ${len(values) + 1}")
                    values.append(value)
            
            if not fields:
                return await self.get_or_create_user(user_id)
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ${len(values)} RETURNING *"
            user = await conn.fetchrow(query, *values)
            return dict(user) if user else {}
    
    async def update_last_remind_time(self, user_id: int, remind_time: Optional[datetime] = None):
        """更新用户上次提醒时间"""
        remind_time = remind_time or datetime.utcnow()
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_remind_time = $1 WHERE user_id = $2",
                remind_time,
                user_id
            )
    
    # ==================== 记录操作 ====================
    
    async def add_record(self, user_id: int, amount: int, created_at: Optional[datetime] = None) -> Dict[str, Any]:
        """添加饮水记录"""
        created_at = created_at or datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            record_id = await conn.fetchval(
                """INSERT INTO records (user_id, amount, created_at) 
                   VALUES ($1, $2, $3) RETURNING id""",
                user_id,
                amount,
                created_at
            )
            
            record = await conn.fetchrow(
                "SELECT * FROM records WHERE id = $1",
                record_id
            )
            return dict(record)
    
    async def get_today_records(self, user_id: int, timezone: int = 0) -> List[Dict[str, Any]]:
        """获取今日记录（考虑时区）"""
        # 计算用户本地时间的今天的 UTC 时间范围
        now_utc = datetime.utcnow()
        today_start_local = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = today_start_local - timedelta(hours=timezone)
        today_end_utc = today_start_utc + timedelta(days=1)
        
        async with self.pool.acquire() as conn:
            records = await conn.fetch(
                """SELECT * FROM records 
                   WHERE user_id = $1 AND created_at >= $2 AND created_at < $3
                   ORDER BY created_at ASC""",
                user_id,
                today_start_utc,
                today_end_utc
            )
            return [dict(r) for r in records]
    
    async def get_last_record_time(self, user_id: int) -> Optional[datetime]:
        """获取最后一次饮水记录时间"""
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                """SELECT created_at FROM records 
                   WHERE user_id = $1 
                   ORDER BY created_at DESC LIMIT 1""",
                user_id
            )
            return record["created_at"] if record else None
    
    async def get_stats(self, user_id: int, days: int = 7, timezone: int = 0) -> Dict[str, Any]:
        """获取用户统计数据"""
        async with self.pool.acquire() as conn:
            # 今日数据
            today_records = await self.get_today_records(user_id, timezone)
            today_total = sum(r["amount"] for r in today_records)
            
            # 最近 N 天数据
            end_time_utc = datetime.utcnow()
            start_time_utc = end_time_utc - timedelta(days=days)
            
            daily_stats = await conn.fetch(
                """SELECT 
                   DATE(created_at AT TIME ZONE 'UTC' + INTERVAL '1 hour' * $3) as date,
                   SUM(amount) as total
                   FROM records
                   WHERE user_id = $1 AND created_at >= $2
                   GROUP BY DATE(created_at AT TIME ZONE 'UTC' + INTERVAL '1 hour' * $3)
                   ORDER BY date DESC""",
                user_id,
                start_time_utc,
                timezone
            )
            
            return {
                "today_total": today_total,
                "today_records": today_records,
                "daily_stats": [{"date": str(stat["date"]), "total": stat["total"]} 
                              for stat in daily_stats]
            }
    
    async def get_today_total(self, user_id: int, timezone: int = 0) -> int:
        """获取今日总饮水量"""
        records = await self.get_today_records(user_id, timezone)
        return sum(r["amount"] for r in records)
    
    async def get_daily_total(self, user_id: int, days_ago: int = 0, timezone: int = 0) -> int:
        """
        获取指定日期的饮水总量
        days_ago: 0 表示今天，1 表示昨天，2 表示前天，等等
        """
        async with self.pool.acquire() as conn:
            # 计算目标日期的 UTC 开始和结束时间
            now_utc = datetime.utcnow()
            user_tz_offset = timedelta(hours=timezone)
            user_now = now_utc + user_tz_offset
            
            target_date = (user_now - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)
            target_start_utc = target_date - user_tz_offset
            target_end_utc = target_start_utc + timedelta(days=1)
            
            result = await conn.fetchval(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM records
                   WHERE user_id = $1 AND created_at >= $2 AND created_at < $3""",
                user_id,
                target_start_utc,
                target_end_utc
            )
            
            return int(result) if result else 0
    
    # ==================== 用户禁用和删除 ====================
    
    async def update_last_interaction(self, user_id: int, interaction_time: Optional[datetime] = None):
        """更新用户最后交互时间"""
        interaction_time = interaction_time or datetime.utcnow()
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_interaction_time = $1 WHERE user_id = $2",
                interaction_time,
                user_id
            )
    
    async def set_user_disabled(self, user_id: int, disabled: bool = True) -> None:
        """设置用户禁用状态"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET is_disabled = $1 WHERE user_id = $2",
                1 if disabled else 0,
                user_id
            )
    
    async def is_user_disabled(self, user_id: int) -> bool:
        """检查用户是否被禁用"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT is_disabled FROM users WHERE user_id = $1",
                user_id
            )
            return bool(result) if result is not None else False
    
    async def reset_user_data(self, user_id: int) -> None:
        """重置用户数据（删除所有记录，但保留用户配置）"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM records WHERE user_id = $1",
                user_id
            )
    
    async def delete_user_completely(self, user_id: int) -> None:
        """完全删除用户及其所有数据"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM users WHERE user_id = $1",
                user_id
            )
    
    async def add_to_blacklist(self, user_id: int, reason: str = "") -> None:
        """将用户加入黑名单"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO blacklist (user_id, reason) VALUES ($1, $2)
                   ON CONFLICT (user_id) DO UPDATE SET reason = $2""",
                user_id,
                reason
            )
    
    async def remove_from_blacklist(self, user_id: int) -> None:
        """将用户从黑名单移除"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM blacklist WHERE user_id = $1",
                user_id
            )
    
    async def is_in_blacklist(self, user_id: int) -> bool:
        """检查用户是否在黑名单中"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT 1 FROM blacklist WHERE user_id = $1",
                user_id
            )
            return bool(result)
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户（仅管理员使用）"""
        async with self.pool.acquire() as conn:
            users = await conn.fetch("SELECT * FROM users ORDER BY user_id")
            return [dict(u) for u in users]
    
    async def get_inactive_users(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取超过 N 天未交互的用户"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        async with self.pool.acquire() as conn:
            users = await conn.fetch(
                "SELECT * FROM users WHERE last_interaction_time < $1 AND is_disabled = 0",
                cutoff_time
            )
            return [dict(u) for u in users]
    
    async def get_reminder_messages(self, user_id: int) -> Optional[Dict[int, str]]:
        """获取用户自定义的梯度提醒文案"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM reminder_messages WHERE user_id = $1",
                user_id
            )
            if result:
                messages = {}
                # 遍历所有可能的梯度列（gradient_1 到 gradient_99）
                for i in range(1, 100):
                    column_name = f'gradient_{i}'
                    if column_name in result and result[column_name]:
                        messages[i] = result[column_name]
                    elif i > 1 and i - 1 in messages:
                        # 如果某个梯度为空，但前一个梯度有值，继续检查
                        continue
                    else:
                        # 如果梯度为空且前面没有设置，停止
                        break
                return messages if messages else None
            return None
    
    async def set_reminder_messages(self, user_id: int, messages: Dict[int, str]) -> bool:
        """设置用户自定义的梯度提醒文案"""
        async with self.pool.acquire() as conn:
            # 首先确保记录存在
            await conn.execute("""
                INSERT INTO reminder_messages (user_id, updated_at)
                VALUES ($1, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
            """, user_id)
            
            # 然后更新所有梯度
            for gradient, text in messages.items():
                column_name = f"gradient_{gradient}"
                # 动态构建 UPDATE 语句
                await conn.execute(f"""
                    UPDATE reminder_messages
                    SET {column_name} = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $2
                """, text, user_id)
            
            return True
    
    async def reset_reminder_messages(self, user_id: int) -> bool:
        """重置用户的梯度提醒文案为默认配置"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM reminder_messages WHERE user_id = $1",
                user_id
            )
            return True

    async def get_quiet_hours(self, user_id: int) -> list:
        """获取用户的免打扰时段列表"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT quiet_hours FROM users WHERE user_id = $1",
                user_id
            )
            if result:
                try:
                    return json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    return []
            return []

    async def set_quiet_hours(self, user_id: int, hours: list) -> bool:
        """设置用户的免打扰时段（覆盖原有）"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET quiet_hours = $1 WHERE user_id = $2",
                json.dumps(hours),
                user_id
            )
            return True

    async def add_quiet_hour(self, user_id: int, start_time: str, end_time: str) -> bool:
        """添加一个免打扰时段"""
        try:
            quiet_hours = await self.get_quiet_hours(user_id)
            # 检查是否已存在相同时段
            for period in quiet_hours:
                if period.get("start") == start_time and period.get("end") == end_time:
                    return False  # 时段已存在
            # 添加新时段
            quiet_hours.append({"start": start_time, "end": end_time})
            # 按开始时间排序
            quiet_hours.sort(key=lambda x: x["start"])
            return await self.set_quiet_hours(user_id, quiet_hours)
        except Exception as e:
            logger.error(f"添加免打扰时段失败: {e}")
            return False

    async def remove_quiet_hour(self, user_id: int, start_time: str, end_time: str) -> bool:
        """删除一个免打扰时段"""
        try:
            quiet_hours = await self.get_quiet_hours(user_id)
            # 移除指定时段
            quiet_hours = [
                period for period in quiet_hours
                if not (period.get("start") == start_time and period.get("end") == end_time)
            ]
            return await self.set_quiet_hours(user_id, quiet_hours)
        except Exception as e:
            logger.error(f"删除免打扰时段失败: {e}")
            return False

    async def is_in_quiet_hours(self, user_id: int) -> bool:
        """检查当前时间是否在用户的免打扰时段内"""
        try:
            quiet_hours = await self.get_quiet_hours(user_id)
            if not quiet_hours:
                return False
            
            # 获取用户时区（如果有）
            async with self.pool.acquire() as conn:
                tz_str = await conn.fetchval(
                    "SELECT timezone FROM users WHERE user_id = $1",
                    user_id
                )
            
            # 使用用户时区或默认时区
            if tz_str:
                try:
                    tz = pytz.timezone(tz_str)
                except:
                    tz = pytz.UTC
            else:
                tz = pytz.UTC
            
            now = datetime.now(tz).strftime("%H:%M")
            
            for period in quiet_hours:
                start = period.get("start", "")
                end = period.get("end", "")
                if start <= now <= end:
                    return True
            return False
        except Exception as e:
            logger.error(f"检查免打扰时段失败: {e}")
            return False

# 全局数据库实例
db = DatabaseManager()