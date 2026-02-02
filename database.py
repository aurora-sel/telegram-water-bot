"""
数据库操作模块 (database.py)
提供用户配置和饮水记录的数据库管理功能。
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
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
            # 创建 asyncpg 连接池
            # asyncpg 需要使用 postgresql:// 格式
            dsn = DATABASE_URL if DATABASE_URL.startswith("postgresql://") else f"postgresql://{DATABASE_URL}"
            self.pool = await asyncpg.create_pool(
                dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            print("[DB] 数据库连接池初始化成功")
            
            # 建表
            await self._create_tables()
        except Exception as e:
            print(f"[DB] 初始化失败: {e}")
            raise
    
    async def _create_tables(self):
        """创建数据库表"""
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            daily_goal INTEGER DEFAULT 2500,
            interval_min INTEGER DEFAULT 60,
            start_time VARCHAR(5) DEFAULT '08:00',
            end_time VARCHAR(5) DEFAULT '22:00',
            timezone INTEGER DEFAULT 8,
            last_remind_time TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS records (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            amount INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_records_user_id ON records(user_id);
        CREATE INDEX IF NOT EXISTS idx_records_created_at ON records(created_at);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema)
            print("[DB] 表创建/检查完成")
    
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


# ==================== 全局数据库实例 ====================

db = DatabaseManager()
