# 部署快速诊断清单

## 🔴 错误: `application exited with code 0 instance stopped`

这表示应用启动后立即停止。最常见的原因是 **环境变量配置错误**。

---

## ⚡ 3 分钟快速修复

### 步骤 1: 检查 Koyeb 环境变量（必做 ✅）

在 **Koyeb 仪表板** → 应用 → **设置** → **环境变量**，确认以下变量已设置：

```
TELEGRAM_TOKEN = 你的 Bot Token（来自 @BotFather）
DATABASE_URL = postgresql://user:password@host/db_name
```

⚠️ **常见错误：**
- 变量名拼写错误（应该是 `TELEGRAM_TOKEN`，不是 `TOKEN` 或 `BOT_TOKEN`）
- 值为空或包含引号（应该是纯文本，无引号）
- 复制时包含空格：`TELEGRAM_TOKEN = 123...`（前后有空格）

### 步骤 2: 重新部署

1. 保存环境变量后，点击 **保存** (Save)
2. 点击 **部署** (Deploy) 或 **Redeploy**
3. 等待 2-3 分钟

### 步骤 3: 查看日志

点击 **活动** (Activity) → **日志** (Logs)，查找以下之一：

✅ **成功标志**：
```
[启动] ✅ 数据库初始化成功
[启动] ✅ APScheduler 启动成功
[HTTP服务器] ✅ 已启动
[启动] 🎉 Telegram Bot 已就绪！
```

❌ **失败提示**（如果看到这些，按下面处理）：
```
❌ 错误: 环境变量 TELEGRAM_TOKEN 未设置!
❌ 错误: 环境变量 DATABASE_URL 未设置!
```

---

## 🔧 详细故障排查

### 如果仍未解决，按顺序检查：

#### A. TELEGRAM_TOKEN 问题

**获取方式：**
1. 打开 Telegram
2. 搜索 **@BotFather**，发送 `/start`
3. 发送 `/newbot`
4. 输入 Bot 名称：`Water Reminder` 或 `水提醒机器人`
5. 输入 Bot 用户名：`water_reminder_bot`（必须以 `_bot` 结尾）
6. 复制返回的 Token（形如：`123456789:ABCdefGHIjklmnoPQRstUvWxyz`）

**验证 Token：**
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

应返回：
```json
{
  "ok": true,
  "result": {
    "id": 123456789,
    "is_bot": true,
    "first_name": "Water Reminder"
  }
}
```

---

#### B. DATABASE_URL 问题

**获取方式（推荐 Koyeb PostgreSQL）：**
1. Koyeb 仪表板 → **Marketplace**
2. 搜索 **PostgreSQL**
3. 点击 **部署** (Deploy)
4. 选择 **免费** (Free)
5. 配置后，复制 **连接 URL**

**URL 格式检查：**
```
postgresql://username:password@hostname:5432/database_name
```

⚠️ **常见错误：**
- ❌ 缺少 `postgresql://` 前缀
- ❌ 密码包含特殊字符需要 URL 编码（如 `@` 变成 `%40`）
- ❌ 主机名错误或过期

**本地测试连接：**
```bash
psql "postgresql://user:password@host:5432/db"
# 如果连接成功，则 URL 正确
```

---

#### C. PostgreSQL 防火墙问题

如果数据库连接失败（"connection refused"），需要允许 Koyeb 访问：

**Koyeb PostgreSQL 白名单：**
1. Koyeb 仪表板 → PostgreSQL 实例 → **设置** (Settings)
2. 找到 **网络** (Network) → **添加 IP** (Add IP)
3. 输入你应用的 IP 或使用 `0.0.0.0/0`（允许所有）

**自有 PostgreSQL：**
- 云服务（AWS RDS、Azure、阿里云）：检查**安全组**或**防火墙规则**
- 本地 PostgreSQL：修改 `pg_hba.conf`

---

## 📋 完整诊断清单

| 项目 | 状态 | 说明 |
|------|------|------|
| TELEGRAM_TOKEN 已设置 | ✅/❌ | 在 Koyeb 环境变量中 |
| DATABASE_URL 已设置 | ✅/❌ | 在 Koyeb 环境变量中 |
| Token 格式正确 | ✅/❌ | 形如 `123:ABC` |
| DATABASE_URL 格式正确 | ✅/❌ | 形如 `postgresql://user:pass@host/db` |
| PostgreSQL 可访问 | ✅/❌ | 用 psql 测试连接 |
| 已点击部署 | ✅/❌ | Koyeb Redeploy |
| 应用状态为 Healthy | ✅/❌ | Koyeb 仪表板检查 |
| 日志显示成功信息 | ✅/❌ | 查看 Koyeb 日志 |

---

## 🎯 测试成功

应用部署成功的标志：

1. **Koyeb 仪表板** 应用状态：**Healthy** ✅
2. **日志显示**：`[启动] 🎉 Telegram Bot 已就绪！`
3. **Bot 可用**：在 Telegram 中对 Bot 发送 `/start` 有响应

```
你的 Bot 地址：https://t.me/你的bot用户名
```

---

## 🆘 仍需帮助？

查看完整诊断指南：
→ 打开 `DEPLOYMENT_TROUBLESHOOTING.md` 文件

---

## 最后一招：本地测试

如果仍不确定，在本地验证：

```bash
# 1. 创建 .env
cat > .env << EOF
TELEGRAM_TOKEN=你的token
DATABASE_URL=你的数据库url
EOF

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

预期看到：
```
[启动] 初始化数据库...
[启动] ✅ 数据库初始化成功
[启动] ✅ APScheduler 启动成功
[HTTP服务器] ✅ 已启动，监听 0.0.0.0:8080
[启动] 🎉 Telegram Bot 已就绪！
```

如果本地成功但 Koyeb 失败，则问题在 Koyeb 环境变量配置。
