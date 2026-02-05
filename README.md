# 🤖 Telegram 喝水提醒机器人

一个功能完整的 Telegram Bot，用于追踪个人饮水并提供定时提醒。支持多用户并发使用，每个用户拥有独立的调度系统和数据隔离。

## ✨ 核心特性

### 多用户隔离
- 每个用户的设置、提醒间隔和饮水记录完全独立
- 基于 Telegram `user_id` 的数据分离
- 支持无限用户并发使用

### 动态调度中心
- 为每个用户创建独立的 APScheduler Job
- 用户记录饮水后自动重置该用户的提醒任务
- 提醒间隔从最后一次饮水时间开始计算

### 时区支持
- UTC 时间统一存储，支持任意时区偏移
- 用户可设置活跃提醒时段（如 08:00 ~ 22:00）
- 到达活跃时段结束时自动推送当日总结报告

### 智能反馈
- 记录时实时显示今日进度百分比
- 根据进度提供个性化鼓励语
- 达成目标时自动庆祝

### 🆕 梯度提醒功能（v2.3）
- **智能提醒力度调整**
  - 根据用户未喝水的时长，自动提升提醒强度
  - 梯度 1: X 分钟未喝水（标准提醒）
  - 梯度 2: 2X 分钟未喝水（增强提醒）
  - 梯度 3: 3X 分钟未喝水（高级提醒）
  - 梯度 4+: 4X+ 分钟未喝水（紧急提醒）

- **管理员自定义**
  - 管理员可自定义各梯度的提醒文案
  - 默认每次提醒为统一文案："💧 是时候喝水了！"
  - 可通过命令修改特定梯度的文案
  - 可一键重置为默认配置

### 🆕 每日通知功能（v2.1）
- **每日开始通知** 🌅
  - 在用户设置的开始时间发送
  - 提醒用户今日目标
  - 附带鼓励语

- **每日结束报告** 📋
  - 在用户设置的结束时间发送
  - 显示今日饮水总量与目标对比
  - 与昨日数据对比分析
  - 鼓励用户保持或进步

### 🆕 用户管理功能（v2.0）
- **用户数据管理**
  - `/reset` - 重置自己的所有饮水记录
  - `/stop_today` - 停止今天的提醒
  - `/disable_forever` - 永久禁用提醒
  - `/enable` - 重新启用提醒

### 🆕 管理员功能（v2.0）
- **管理员权限**（需在环境变量中配置 ADMIN_IDS）
  - `/admin_help` - 显示所有管理员命令
  - `/admin_stats` - 查看全局统计（用户数、活跃度）
  - `/blacklist` - 拉黑用户（禁止使用机器人）
  - `/unblacklist` - 解除拉黑
  - `/user_info` - 查看用户详细信息和统计
  - `/set_reminder_messages` - 自定义梯度提醒文案（🆕 v2.3）
  - `/update_msg` - 更新单个梯度的提醒文案（🆕 v2.3）
  - `/reset_reminder_messages` - 重置提醒文案为默认（🆕 v2.3）
  
  **快速开始：** 📖 查看 [ADMIN_SETUP.md](ADMIN_SETUP.md) 了解如何配置管理员
  
- **自动清理**
  - 检测 7 天未交互的用户
  - 发送警告信息给用户
  - 24 小时后自动删除未反应用户的所有数据

### 🆕 自动保活（v2.0）
- 防止云平台（Render）自动休眠
- 支持 UptimeRobot 集成
- HTTP 健康检查端点（/health 和 /status）

## 🛠 技术栈

- **Python 3.10+** - 编程语言
- **aiogram 3.x** - Telegram Bot 框架（异步）
- **APScheduler** - 任务调度引擎
- **PostgreSQL** - 关系数据库
- **asyncpg** - 异步 PostgreSQL 驱动
- **Docker** - 容器化部署
- **Koyeb** - 云平台部署（推荐）

## 📦 项目结构

```
water-reminder-bot/
├── main.py              # 核心机器人逻辑
├── database.py          # 数据库操作模块
├── config.py            # 配置和常量
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 镜像配置
├── .env.example         # 环境变量示例
├── .gitignore           # Git 忽略文件
└── README.md            # 此文件
```

## 🚀 快速开始

### 1. 本地开发环境

#### 1.1 克隆或下载项目
```bash
cd water-reminder-bot
```

#### 1.2 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 1.3 安装依赖
```bash
pip install -r requirements.txt
```

#### 1.4 配置环境变量
```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件，填入你的配置
# 必须项：
# - TELEGRAM_TOKEN: 从 BotFather 获取的 Bot Token
# - DATABASE_URL: PostgreSQL 连接字符串
```

#### 1.5 启动本地 PostgreSQL（如果还未安装）

**选项 A：使用 Docker（推荐）**
```bash
docker run -d \
  --name postgres_water_bot \
  -e POSTGRES_USER=water_user \
  -e POSTGRES_PASSWORD=water_pass \
  -e POSTGRES_DB=water_reminder \
  -p 5432:5432 \
  postgres:15-alpine
```

然后更新 `.env` 文件：
```
DATABASE_URL=postgresql://water_user:water_pass@localhost:5432/water_reminder
```

**选项 B：使用本地 PostgreSQL**
确保本地已安装 PostgreSQL，并创建数据库：
```sql
CREATE DATABASE water_reminder;
```

#### 1.6 启动机器人
```bash
python main.py
```

成功启动时应看到：
```
[启动] 初始化数据库...
[DB] 数据库连接池初始化成功
[DB] 表创建/检查完成
[启动] 启动 APScheduler...
[启动] Telegram 机器人已启动
[轮询] 启动长轮询模式...
```

### 2. 云平台部署

#### 推荐的部署平台

| 平台 | 难度 | 免费 | 推荐 |
|------|------|------|------|
| **Koyeb** | ⭐⭐ | ✅ 完全免费 | 推荐 |

**部署指南：**
- ☁️ **[Koyeb 部署指南](KOYEB_DEPLOY.md)** - 完整的部署步骤

#### 2.1 前置准备

1. **注册 Koyeb 账户** - https://koyeb.com
2. **获取 Telegram Bot Token**
   - 在 Telegram 中搜索 `@BotFather`
   - 输入 `/newbot` 创建新机器人
   - 复制获得的 Token
3. **获取 PostgreSQL 数据库**
   - 使用 **Neon** 免费层（推荐）- https://neon.tech
   - 或 **Supabase** - https://supabase.com
   - 或自行搭建 PostgreSQL 实例

#### 2.2 部署步骤概览

**步骤 1：推送代码到 GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/water-reminder-bot.git
git push -u origin main
```

**步骤 2：在 Koyeb 上创建应用**
1. 登录 Koyeb Dashboard：https://app.koyeb.com
2. 点击 "Create" → "Create App"
3. 选择 "GitHub" 作为代码源
4. 授权并选择你的仓库 `water-reminder-bot`
5. 选择分支 `main`

**步骤 3：配置运行设置**
- **Builder**: Docker
- **Dockerfile path**: `./Dockerfile`
- **Port**: 8080

**步骤 4：配置环境变量（关键！）**
在 Koyeb 的 "Environment variables" 部分添加：

| 环境变量 | 值 | 说明 |
|---------|-----|------|
| `TELEGRAM_TOKEN` | 从 BotFather 获取的 Token | Telegram Bot Token |
| `DATABASE_URL` | PostgreSQL 连接字符串 | 数据库连接地址 |

**示例 DATABASE_URL:**
```
postgresql://user:password@host:5432/water_reminder
```

> ⚠️ **重要：** 环境变量必须在 Koyeb 中配置，不要写在源码里！

**步骤 5：部署**
1. 点击 "Deploy"
2. 等待部署完成（通常 3-5 分钟）
3. 获取应用的公网 URL

**步骤 6：验证部署**
在 Telegram 中与你的机器人互动：
```
/start
```

如果机器人响应，则部署成功！

> **详细指南：** 如需更多信息，请参考 [KOYEB_DEPLOY.md](KOYEB_DEPLOY.md)

---

### 🔴 部署遇到错误？

如果看到 `application exited with code 0 instance stopped` 或应用无法启动：

⚡ **快速修复（5 分钟）：**
1. 查看 **[快速修复指南](DEPLOYMENT_QUICK_FIX.md)** - 最常见的 3 个原因
2. 检查 Koyeb 环境变量是否正确设置（`TELEGRAM_TOKEN` 和 `DATABASE_URL`）
3. 点击 "Redeploy" 重新部署

🔧 **完整故障排查：**
- 详见 **[故障排查指南](DEPLOYMENT_TROUBLESHOOTING.md)**
- 包含数据库连接测试、日志查看、本地测试方法

---

## 📱 使用指南

### 基本命令

#### 记录饮水
```
直接发送数字 (如: 200)
```
记录 200ml 的饮水，机器人会显示今日进度和下一次提醒时间。

#### 补录历史记录
```
/back [水量] [分钟前]
例如: /back 300 30
```
补录 30 分钟前喝的 300ml 水。

### 个性化配置

#### 设置每日目标
```
/goal [数字]
例如: /goal 3000
```
设置每日饮水目标为 3000ml（默认 2500ml）

#### 设置时区
```
/timezone [数字]
例如: /timezone 8
```
设置时区为 UTC+8（中国）

| 时区 | 示例地区 |
|------|--------|
| -5 | 美国东部 |
| 0 | 英国/GMT |
| 1 | 中欧时间 |
| 8 | 中国/新加坡 |
| 9 | 日本 |

#### 设置活跃时段
```
/time [开始] [结束]
例如: /time 08:00 22:00
```
只在 08:00 ~ 22:00 时间段内发送提醒。到达结束时间时会自动推送当日总结。

#### 设置提醒间隔
```
/interval [分钟]
例如: /interval 60
```
设置提醒间隔为 60 分钟。每次记录饮水后该间隔会重置。

### 数据查询

#### 查看当前设置
```
/settings
```

#### 查看统计数据
```
/stats
```
显示今日进度和最近 7 天的趋势。包括智能鼓励语。

#### 显示帮助
```
/help
```

### 🆕 用户管理命令（v2.0）

#### 重置自己的数据
```
/reset
```
删除所有饮水记录，但保留用户设置（目标、间隔等）。

#### 停止今天的提醒
```
/stop_today
```
停止今天的自动提醒，明天继续正常。

#### 永久禁用提醒
```
/disable_forever
```
永久停止接收提醒，但可继续手动记录饮水。

#### 重新启用提醒
```
/enable
```
恢复被禁用的提醒功能。

### 🆕 管理员命令（v2.0）

> **前提条件：** 需在环境变量 `ADMIN_IDS` 中配置你的 Telegram ID

#### 查看全局统计
```
/admin_stats
```
查看总用户数、活跃用户数、禁用用户数。

#### 拉黑用户
```
/blacklist [用户ID] [原因]
例如: /blacklist 123456789 垃圾广告
```
禁止指定用户使用机器人。用户无法执行任何命令，数据保留。

#### 解除拉黑
```
/unblacklist [用户ID]
例如: /unblacklist 123456789
```
解除对用户的拉黑，用户恢复正常使用。

#### 查看用户信息
```
/user_info [用户ID]
例如: /user_info 123456789
```
查看用户的详细信息，包括：
- 用户设置（目标、间隔、时区、活跃时段）
- 提醒和黑名单状态
- 今日饮水量
- 账户创建时间和最后交互时间

#### 🆕 自定义梯度提醒文案（v2.3）

管理员可自定义不同"未喝水时长"梯度下的提醒文案。默认所有梯度都为统一文案："💧 是时候喝水了！"

**启动配置向导**
```
/set_reminder_messages
```
显示当前配置和修改指引。

**修改单个梯度的文案**
```
/update_msg [梯度] [新文案]
例如: /update_msg 1 💧 是时候喝水啦！
例如: /update_msg 3 👀 眼睛都要干掉了！再不喝水就完蛋了！
```

**梯度说明** (假设提醒间隔为 60 分钟)：
| 梯度 | 触发条件 | 用途 |
|------|--------|------|
| 1 | 60 分钟未喝水 | 标准提醒 |
| 2 | 120 分钟未喝水 | 增强提醒，用户开始忘记 |
| 3 | 180 分钟未喝水 | 高级提醒，用户可能忙碌 |
| 4+ | 240+ 分钟未喝水 | 紧急提醒，需要强调 |

**重置为默认配置**
```
/reset_reminder_messages
```
将所有梯度文案重置为默认值。

**完整示例**
```
# 设置梯度 1: 温和提醒
/update_msg 1 💧 该喝水了呢～

# 设置梯度 2: 中等提醒  
/update_msg 2 🌊 这么久没喝水呀？喝一口吧～

# 设置梯度 3: 加强提醒
/update_msg 3 😰 眼睛要干掉了！快喝水！

# 设置梯度 4: 紧急提醒
/update_msg 4 🚨 妹妹都干掉了！！立即喝水！

# 查看配置
/set_reminder_messages

# 全部恢复默认
/reset_reminder_messages
```

## 🗄 数据库架构

### Users 表
存储用户的个性化设置和状态

```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,                    -- Telegram 用户 ID
    daily_goal INTEGER DEFAULT 2500,               -- 每日目标 (ml)
    interval_min INTEGER DEFAULT 60,               -- 提醒间隔 (分钟)
    start_time VARCHAR(5) DEFAULT '08:00',         -- 活跃开始时间
    end_time VARCHAR(5) DEFAULT '22:00',           -- 活跃结束时间
    timezone INTEGER DEFAULT 8,                    -- 时区偏移
    last_remind_time TIMESTAMP NULL,               -- 上次提醒时间 (UTC)
    last_interaction_time TIMESTAMP DEFAULT NOW(), -- 最后交互时间（用于清理检测）
    is_disabled INTEGER DEFAULT 0,                 -- 提醒禁用状态
    created_at TIMESTAMP DEFAULT NOW()             -- 账户创建时间
);
```

### Records 表
存储所有饮水记录

```sql
CREATE TABLE records (
    id SERIAL PRIMARY KEY,                -- 记录 ID
    user_id BIGINT NOT NULL,              -- 关联用户 ID
    amount INTEGER NOT NULL,              -- 饮水量 (ml)
    created_at TIMESTAMP DEFAULT NOW()    -- 记录时间 (UTC)
);

CREATE INDEX idx_records_user_id ON records(user_id);
CREATE INDEX idx_records_created_at ON records(created_at);
```

### 🆕 Blacklist 表（v2.0）
存储被拉黑的用户

```sql
CREATE TABLE blacklist (
    user_id BIGINT PRIMARY KEY,           -- 被拉黑的用户 ID
    reason VARCHAR(255),                  -- 拉黑原因
    blocked_at TIMESTAMP DEFAULT NOW()    -- 拉黑时间
);
```

### 🆕 Reminder Messages 表（v2.3）
存储管理员自定义的梯度提醒文案

```sql
CREATE TABLE reminder_messages (
    user_id BIGINT PRIMARY KEY,           -- 管理员用户 ID
    gradient_1 VARCHAR(255),              -- 梯度 1 的提醒文案
    gradient_2 VARCHAR(255),              -- 梯度 2 的提醒文案
    gradient_3 VARCHAR(255),              -- 梯度 3 的提醒文案
    gradient_4 VARCHAR(255),              -- 梯度 4 的提醒文案
    updated_at TIMESTAMP DEFAULT NOW()    -- 最后更新时间
);
```

## 🔧 多用户调度机制

### 核心设计

每个活跃用户拥有一个独立的 APScheduler Job：
- **Job ID**: `reminder_{user_id}`
- **触发器**: 基于 CronTrigger 的分钟间隔
- **执行条件**: 仅在用户设置的活跃时段内执行

### 重置流程

当用户记录一次饮水时：
1. 添加记录到数据库
2. 销毁该用户的旧 Job
3. 创建新的 Job，间隔从当前时间重新计算
4. 返回反馈消息

```python
# 伪代码
async def handle_water_input(amount):
    await db.add_record(user_id, amount)
    await reset_reminder_job(user_id)  # 销毁并重建 Job
    # 显示进度反馈
```

### 时区处理

所有时间统一以 UTC 存储，但在业务逻辑中转换：

```python
# 获取用户当前本地时间
user_local_time = get_user_local_time(timezone_offset)

# 检查是否在活跃时段
is_in_active_period(user_local_time, start_time, end_time)

# 转换今日日期范围
today_start_utc = now_utc - timedelta(hours=timezone_offset)
```

## 🔐 安全最佳实践

### 环境变量
- **永远不要**在代码中硬编码 `TELEGRAM_TOKEN` 或 `DATABASE_URL`
- 使用 `.env` 文件管理敏感信息
- Koyeb 部署时通过 Dashboard 设置环境变量

### 数据库
- 使用强密码
- 仅允许特定 IP 访问（若可能）
- 定期备份数据库

### Bot 安全
- 监控异常的 API 调用
- 限制命令执行频率（可选）
- 不存储用户的个人敏感信息

## 📊 日志和调试

### 本地调试
编辑 `main.py` 中的日志级别：
```python
logging.basicConfig(level=logging.DEBUG)  # 更详细的日志
```

### Koyeb 日志查看
1. 登录 Koyeb Dashboard
2. 进入应用 → "Logs"
3. 查看实时日志

### 常见问题

**Q: 机器人无响应**
- 检查 `TELEGRAM_TOKEN` 是否正确
- 查看 Koyeb 日志是否有错误

**Q: 数据库连接失败**
- 验证 `DATABASE_URL` 格式正确
- 确认数据库服务在线
- 检查防火墙和网络连接

**Q: 提醒不发送**
- 确认用户在活跃时段内
- 查看 APScheduler 日志
- 确认机器人有发送消息的权限

## 📈 性能优化

### 数据库索引
已创建的索引：
- `idx_records_user_id` - 加速用户查询
- `idx_records_created_at` - 加速时间范围查询

### 异步设计
- 使用 `asyncpg` 异步驱动
- 所有数据库操作非阻塞
- APScheduler 基于 AsyncIOScheduler

### 连接池
- 异步连接池：5-20 个并发连接
- 自动连接复用和回收

## 🤝 贡献指南

欢迎提交 Issue 和 PR！

## 📄 许可证

MIT License

## 🎯 未来计划

- [ ] 支持 Webhook 模式部署
- [ ] 添加数据导出功能
- [ ] 支持群组管理员功能
- [ ] 集成天气 API，根据天气调整提醒
- [ ] 支持语音消息提醒
- [ ] Web Dashboard 数据可视化

## 📞 支持

如有问题或建议，请：
1. 查看本 README 的常见问题部分
2. 提交 GitHub Issue
3. 联系开发者

---

**祝你使用愉快！🎉 记得多喝水，保持健康！💧**
