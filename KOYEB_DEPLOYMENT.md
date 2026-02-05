# Koyeb 部署指南

## ✅ 部署前检查清单

### 1️⃣ 准备环境变量

在 Koyeb 部署前，确保有以下信息：

| 环境变量 | 说明 | 获取方式 |
|---------|------|--------|
| `TELEGRAM_TOKEN` | Telegram Bot Token | 从 @BotFather 获取 |
| `DATABASE_URL` | PostgreSQL 数据库连接字符串 | 从数据库服务获取 |

#### DATABASE_URL 格式

```
postgresql://username:password@host:port/database_name
```

**示例：**
```
postgresql://user123:MyPassword@db.example.com:5432/water_bot_db
```

### 2️⃣ PostgreSQL 数据库准备

在 Koyeb 或外部数据库服务中创建数据库：

- **数据库名称：** 自定义（如 `water_bot_db`）
- **用户名/密码：** 创建专用用户
- **端口：** 通常 5432（如使用其他端口，在 DATABASE_URL 中指定）

验证连接：
```bash
# 在本地测试数据库连接
psql "postgresql://username:password@host:port/database_name"
```

### 3️⃣ Koyeb 部署步骤

#### 第一步：连接 Git 仓库

1. 登录 [Koyeb 控制台](https://app.koyeb.com)
2. 点击 **Create Service** → **Git Repository**
3. 选择你的 GitHub 仓库
4. 确保分支为 `main`

#### 第二步：配置环境变量

1. 在 **Environment** 标签页中，点击 **Add variable**
2. 添加以下变量：

| Key | Value |
|-----|-------|
| `TELEGRAM_TOKEN` | 你的 Bot Token |
| `DATABASE_URL` | `postgresql://user:pass@host:port/db` |

**重要：** 不要在 VALUE 中添加引号

#### 第三步：启动配置

- **Builder:** Docker
- **Dockerfile path:** `./Dockerfile`
- **Exposed ports:** 8080 (HTTP)
- **Command:** `python main.py`

#### 第四步：部署

点击 **Create Service** 开始部署。

---

## 🔍 验证部署成功

### 查看日志

1. 在 Koyeb 仪表板中打开你的服务
2. 点击 **Runtime logs** 标签
3. 查找以下成功指示：

```
[启动] 初始化数据库...
[DB] ✅ 数据库连接池初始化成功
[DB] ✅ 所有表初始化完成
[启动] ✅ 数据库初始化成功
[启动] 🎉 Telegram Bot 已就绪！开始接收消息...
```

### 测试 Bot

1. 在 Telegram 中找到你的 Bot
2. 发送 `/start` 命令
3. Bot 应该回复欢迎消息

---

## ❌ 部署失败排查

### 错误：Application exited with code 1

**原因 1：DATABASE_URL 未设置或格式错误**

查看日志中是否出现：
```
[DB] ❌ DATABASE_URL 未正确配置！
[DB] 当前值: (未设置或使用默认值)
```

**解决：**
1. 回到 Koyeb 仪表板
2. 点击 **Settings** → **Environment variables**
3. 确保 `DATABASE_URL` 正确设置
4. 重新部署服务

**原因 2：数据库连接失败**

日志可能显示：
```
asyncpg.exceptions.PostgresError: ...
```

**解决：**
1. 验证 DATABASE_URL 格式正确
2. 检查数据库服务器是否在线
3. 验证用户名/密码正确
4. 验证数据库名称存在
5. 如果使用防火墙，确保允许 Koyeb IP 访问数据库

**原因 3：TELEGRAM_TOKEN 未设置**

日志可能显示：
```
aiogram.exceptions.RestrictedWithinBot: ...
```

**解决：**
1. 确保 `TELEGRAM_TOKEN` 环境变量已设置
2. 验证 Token 值正确（不含引号）
3. 重新部署服务

---

## 📊 梯度提醒功能（v2.3+）

部署成功后，管理员可以自定义梯度提醒文案：

```
/set_reminder_messages    - 查看当前梯度提醒配置
/update_msg <级别> <文案> - 修改指定级别的提醒文案
/reset_reminder_messages  - 恢复默认提醒文案
```

**示例：**
```
/update_msg 1 💧 该喝水了，朋友！
/update_msg 4 🚨 严重脱水预警！请立即喝水！
```

---

## 📞 需要帮助？

如果部署仍失败，收集以下信息并查看：

1. **完整错误日志** - 从 Koyeb Runtime logs 复制整个输出
2. **环境变量检查** - 确认 `TELEGRAM_TOKEN` 和 `DATABASE_URL` 已设置
3. **本地测试** - 在本地运行 `python check_env.py` 测试环境变量

```bash
python check_env.py
```

此命令会检查：
- ✅ `TELEGRAM_TOKEN` 是否设置
- ✅ `DATABASE_URL` 是否设置
- ✅ 数据库连接是否正常

---

## 🚀 重新部署

如果需要重新部署（更改环境变量或代码）：

1. 更新 Git 仓库（代码更改）或 Koyeb 环境变量
2. 在 Koyeb 仪表板中点击 **Deploy** 或 **Redeploy**
3. 等待部署完成
4. 查看日志确认成功

---

**最后更新：** v2.3（包含梯度提醒功能）
