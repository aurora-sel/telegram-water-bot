# 🚀 水提醒机器人 v2.0 - 完整更新指南

**更新日期：** 2026-02-03  
**版本：** 从 v1.0 升级到 v2.0  
**状态：** ✅ 代码完成，准备部署

---

## 📋 本次更新概览

### 🆕 新增功能（3 大类）

#### 1️⃣ **管理员系统**
- 设置管理员权限
- 拉黑/解除拉黑用户
- 查看全局统计
- 查看用户详细信息

#### 2️⃣ **用户数据管理**
- 重置饮水记录
- 停止今日提醒
- 永久禁用提醒
- 重新启用提醒

#### 3️⃣ **自动清理系统**
- 检测 7 天未活动用户
- 发送警告信息
- 24 小时后删除数据

---

## 🔧 环境变量配置

### 新增环境变量

#### ADMIN_IDS（可选）
设置管理员权限

```env
# Koyeb 环境变量设置
ADMIN_IDS=123456789,987654321
```

**说明：**
- 多个 ID 用逗号分隔（无空格）
- 获取 ID：给 @userinfobot 发送消息
- 不设置则没有管理员

#### UPTIMEROBOT_URL（可选）
防止 Render 自动休眠

```env
# 不需要设置（保留为空）
UPTIMEROBOT_URL=
```

**说明：**
- 这是为了 UptimeRobot 集成准备
- 目前保留为空即可
- 详见 RENDER_AUTO_SLEEP_FIX.md

### 已有环境变量（必需）

| 变量 | 说明 | 示例 |
|------|------|------|
| `TELEGRAM_TOKEN` | Bot Token（必需） | `1234567890:ABCD...` |
| `DATABASE_URL` | PostgreSQL URL（必需） | `postgresql://...` |
| `PORT` | 监听端口 | `8080` |

---

## 📝 代码修改清单

### 已修改的文件

✅ **config.py**
- 新增 ADMIN_IDS 配置
- 新增 UPTIMEROBOT_URL 配置

✅ **database.py**
- Users 表新增 2 个字段：`last_interaction_time`, `is_disabled`
- 新增 Blacklist 表
- 新增 13 个新数据库函数

✅ **main.py**
- 新增 5 个用户命令（/reset, /stop_today, /disable_forever, /enable）
- 新增 5 个管理员命令（/admin_stats, /blacklist, /unblacklist, /user_info）
- 新增自动清理任务（cleanup_inactive_users）
- 所有命令都支持交互时间追踪和黑名单检查

✅ **.env.example**
- 新增环境变量说明

### 新建文档

✅ **FEATURE_UPDATE_2_0.md** - 详细的功能说明和部署指南

---

## 🚀 部署指南（3 步）

### 第 1 步：推送代码到 GitHub

```bash
cd d:\MyProjects\water-reminder-bot

# 查看修改
git status

# 提交代码
git add config.py database.py main.py .env.example FEATURE_UPDATE_2_0.md
git commit -m "Feature: Add admin system, user management, auto-cleanup v2.0"

# 推送到 GitHub
git push origin main
```

### 第 2 步：Koyeb 自动部署

1. 进入 Koyeb 仪表板 (https://app.koyeb.com)
2. 选择你的应用
3. 应该会自动检测到新的推送并开始部署（或手动点 "Redeploy"）
4. 等待部署完成（通常 2-5 分钟）

### 第 3 步：配置管理员（可选）

1. 进入应用设置 → Environment
2. 添加或更新 `ADMIN_IDS` 环境变量
3. 输入你的 Telegram ID（从 @userinfobot 获取）
4. 点击 "Deploy" 重启应用

---

## ✅ 部署验证

部署后检查以下项目：

- [ ] 应用状态为 "Healthy"
- [ ] 日志中有 "[启动] 已注册过期用户清理任务" 消息
- [ ] 向机器人发送 `/start` 有正常响应
- [ ] 如果配置了 ADMIN_IDS，测试 `/admin_stats` 命令
- [ ] 测试新的用户命令（/reset, /disable_forever 等）

---

## 📚 命令速查

### 用户命令（普通用户可用）

| 命令 | 说明 |
|------|------|
| `/reset` | 重置饮水记录 |
| `/stop_today` | 停止今日提醒 |
| `/disable_forever` | 永久禁用提醒 |
| `/enable` | 重新启用提醒 |
| `/stats` | 查看统计数据 |
| `/settings` | 查看设置 |
| `/help` | 显示帮助 |

### 管理员命令（仅 ADMIN_IDS 中的用户）

| 命令 | 说明 |
|------|------|
| `/admin_stats` | 查看全局统计 |
| `/blacklist [ID] [原因]` | 拉黑用户 |
| `/unblacklist [ID]` | 解除拉黑 |
| `/user_info [ID]` | 查看用户信息 |

---

## 🔐 安全建议

### 管理员保护

```
❌ 不要：
- 泄露你的 Telegram ID 给他人
- 将 ADMIN_IDS 放在 .env 文件中提交到 GitHub

✅ 应该：
- 只在 Koyeb 环境变量中设置
- 定期检查黑名单日志
- 谨慎使用拉黑权限
```

### 数据保护

```
✅ 定期备份：
- 备份 PostgreSQL 数据库
- 特别是生产环境

✅ 监控：
- 检查应用日志
- 确保清理任务正常运行
```

---

## 🧪 测试用例

### 测试管理员功能

1. **配置管理员**
   ```bash
   # 在 Koyeb 中设置
   ADMIN_IDS=你的用户ID
   ```

2. **重启应用后测试**
   ```
   发送: /admin_stats
   期望: 显示用户统计信息
   ```

3. **拉黑测试用户**
   ```
   发送: /blacklist 测试ID 测试拉黑
   期望: 成功拉黑
   
   该用户无法使用任何命令
   ```

### 测试用户功能

```
/reset
期望: 饮水记录被清除，设置保留

/disable_forever
期望: 停止接收提醒

/enable
期望: 恢复提醒

/stop_today
期望: 今天不提醒，明天继续
```

### 测试自动清理（可选）

1. 创建测试用户账户
2. 等待 7 天（或修改代码为 1 分钟用于测试）
3. 观察清理日志

---

## 📖 详细文档

| 文档 | 说明 |
|------|------|
| **FEATURE_UPDATE_2_0.md** | 功能详细说明 |
| **README.md** | 项目说明（已更新） |
| **RENDER_AUTO_SLEEP_FIX.md** | 防止自动休眠 |
| **DEPLOYMENT_START_HERE.md** | 部署快速开始 |

---

## ⚠️ 常见问题

### Q1：管理员命令说没权限

**原因：** ADMIN_IDS 未设置或 ID 错误

**解决：**
1. 确认你的 Telegram ID（@userinfobot）
2. 在 Koyeb 中设置 ADMIN_IDS
3. 重启应用

### Q2：清理任务没执行

**原因：** 可能是时间设置的问题

**检查：**
1. 查看日志中的 "清理过期用户" 消息
2. 确保数据库连接正常
3. 确保 APScheduler 已启动

### Q3：用户被拉黑后无法解除

**解决：**
```
使用 /unblacklist [ID] 命令解除
该命令只有管理员可以使用
```

### Q4：如何修改清理的时间阈值

**方法：**
```python
# 在 main.py 中找到：
inactive_users = await db.get_inactive_users(days=7)

# 修改 7 为其他数字，如改为 3 天：
inactive_users = await db.get_inactive_users(days=3)
```

---

## 📊 版本对比

| 功能 | v1.0 | v2.0 |
|------|------|------|
| 基础提醒 | ✅ | ✅ |
| 饮水统计 | ✅ | ✅ |
| 时区支持 | ✅ | ✅ |
| 管理员系统 | ❌ | ✅ |
| 拉黑功能 | ❌ | ✅ |
| 用户禁用 | ❌ | ✅ |
| 自动清理 | ❌ | ✅ |
| 交互追踪 | ❌ | ✅ |
| HTTP 健康检查 | ✅ | ✅ |

---

## 🎉 总结

**本次更新：**
- ✅ 10 个新命令
- ✅ 3 个新数据库函数组
- ✅ 自动清理系统
- ✅ 管理员权限管理
- ✅ 用户数据完全控制

**兼容性：**
- ✅ 完全向后兼容
- ✅ 自动建表和迁移
- ✅ 无需备份数据库

**准备好了吗？** 按照 3 步部署指南，立即更新你的机器人！🚀

---

**需要帮助？** 查看各个详细文档或查看新增命令的日志输出。
