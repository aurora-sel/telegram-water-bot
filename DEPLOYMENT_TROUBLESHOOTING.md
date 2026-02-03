# 部署故障排查指南

## 问题: `application exited with code 0 instance stopped`

应用启动后立即停止，无输出错误信息。这通常由环境变量缺失或配置错误导致。

---

## 快速诊断

### 第 1 步：查看 Koyeb 日志

1. 访问 **Koyeb 仪表板** → 选择你的应用
2. 点击 **活动** (Activity) → **日志** (Logs)
3. 查看最近的启动日志，寻找包含以下内容的错误：

```
❌ 错误: 环境变量 TELEGRAM_TOKEN 未设置!
❌ 错误: 环境变量 DATABASE_URL 未设置!
```

### 第 2 步：检查必需的环境变量

必需变量（必须配置）：

| 变量名 | 说明 | 获取方式 |
|--------|------|--------|
| `TELEGRAM_TOKEN` | Bot Token | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `DATABASE_URL` | PostgreSQL URL | Koyeb Marketplace 或自己的 PostgreSQL 实例 |

可选变量：

| 变量名 | 说明 | 值示例 |
|--------|------|--------|
| `ADMIN_IDS` | 管理员 Telegram ID（逗号分隔）| `123456789,987654321` |
| `UPTIMEROBOT_URL` | 保活 Ping URL | 来自 UptimeRobot |
| `PORT` | HTTP 服务器端口 | `8080`（默认） |

---

## 完整解决步骤

### ✅ 方案 1: 配置环境变量（最常见）

#### 1.1 获取 TELEGRAM_TOKEN

```
1. 打开 Telegram，搜索 @BotFather
2. 发送 /newbot
3. 输入 Bot 名称（如：water-reminder）
4. 输入 Bot 用户名（如：water_reminder_bot，必须以 _bot 结尾）
5. 复制返回的 Token（形如：123456789:ABCdefGHIjklmnoPQRstUvWxyz）
```

#### 1.2 获取 DATABASE_URL

**方案 A：使用 Koyeb PostgreSQL（推荐）**
1. Koyeb 仪表板 → Marketplace
2. 搜索 PostgreSQL
3. 创建实例（免费套餐）
4. 复制连接字符串（形如：`postgresql://user:password@host:5432/db_name`）

**方案 B：使用自己的 PostgreSQL**
- URL 格式：`postgresql://user:password@host:5432/database_name`
- 确保数据库可从 Koyeb 访问（开放防火墙）

#### 1.3 在 Koyeb 中配置变量

1. Koyeb 仪表板 → 应用 → **设置** (Settings)
2. 找到 **环境变量** (Environment Variables)
3. 添加以下变量：

```
TELEGRAM_TOKEN=你的 Bot Token
DATABASE_URL=postgresql://user:password@host/db_name
```

4. 保存并点击 **部署** (Deploy)

---

### ✅ 方案 2: 验证数据库连接

如果仍然失败，检查数据库连接：

```bash
# 在本地测试数据库连接
psql "postgresql://user:password@host:5432/database_name"
```

常见错误：
- ❌ `connection refused` → 数据库服务未运行或地址错误
- ❌ `authentication failed` → 用户名/密码错误
- ❌ `database "xxx" does not exist` → 数据库不存在，需要创建

**解决方案：**
```bash
# 创建数据库（如果不存在）
createdb database_name
```

---

### ✅ 方案 3: 检查 PostgreSQL 白名单

如果使用远程 PostgreSQL，需要配置防火墙：

**Koyeb PostgreSQL 白名单：**
1. Koyeb 仪表板 → PostgreSQL 实例 → 网络设置
2. 添加 Koyeb 应用的 IP 范围到白名单
3. 重启应用

**自有 PostgreSQL：**
1. 检查 PostgreSQL 配置：`pg_hba.conf`
2. 确保允许来自 Koyeb 的连接
3. 如果使用云服务（AWS RDS、阿里云等），检查安全组设置

---

### ✅ 方案 4: 本地测试

在部署前，在本地测试应用：

```bash
# 1. 创建 .env 文件
cat > .env << EOF
TELEGRAM_TOKEN=your_token_here
DATABASE_URL=postgresql://user:password@host/db_name
EOF

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行应用
python main.py
```

预期输出：
```
[启动] 初始化数据库...
[启动] ✅ 数据库初始化成功
[启动] 启动 APScheduler...
[启动] ✅ APScheduler 启动成功
[HTTP服务器] ✅ 已启动，监听 0.0.0.0:8080
[启动] 🎉 Telegram Bot 已就绪！开始接收消息...
```

---

## 常见错误与解决

| 错误信息 | 原因 | 解决方案 |
|---------|------|--------|
| `TELEGRAM_TOKEN 未设置` | 环境变量配置错误 | 检查 Koyeb 环境变量配置 |
| `DATABASE_URL 未设置` | 数据库连接字符串缺失 | 在 Koyeb 中添加 DATABASE_URL |
| `connection refused` | PostgreSQL 不可达 | 检查数据库地址、防火墙、白名单 |
| `authentication failed` | 数据库用户名/密码错误 | 验证凭证，重新复制 DATABASE_URL |
| `port 8080 already in use` | 端口被占用 | 修改 PORT 环境变量 |

---

## 调试技巧

### 查看详细日志

```bash
# 在本地开启调试模式
export LOGLEVEL=DEBUG
python main.py
```

### 测试 Telegram 连接

```bash
# 验证 Token 有效性
curl https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe
```

应该返回 Bot 信息，形如：
```json
{
  "ok": true,
  "result": {
    "id": 123456789,
    "is_bot": true,
    "first_name": "water-reminder"
  }
}
```

---

## 成功部署的标志

✅ Koyeb 仪表板显示应用状态：**Healthy**

✅ 日志包含以下内容：
```
[启动] ✅ 数据库初始化成功
[启动] ✅ APScheduler 启动成功
[HTTP服务器] ✅ 已启动
[启动] 🎉 Telegram Bot 已就绪！
```

✅ Bot 能响应命令：在 Telegram 中发送 `/start` 命令给你的 Bot

---

## 获取帮助

1. **查看详细日志**：Koyeb 仪表板 → 活动 → 日志
2. **测试本地环境**：按照"方案 4"在本地运行
3. **验证环境变量**：确保变量名称完全匹配，不要多余空格
4. **检查 PostgreSQL 连接**：使用 `psql` 命令行工具测试

---

## 相关文档

- [Koyeb 文档](https://docs.koyeb.com/)
- [PostgreSQL 连接字符串](https://www.postgresql.org/docs/current/libpq-connect-string.html)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [aiogram 文档](https://docs.aiogram.dev/)
