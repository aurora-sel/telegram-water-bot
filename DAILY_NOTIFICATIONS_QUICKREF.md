# 🚀 每日通知快速参考

## 功能概览

```
每天 08:00 ──→ 🌅 "新的一天，开始喝水吧！"
       ↓
   用户全天记录饮水
       ↓
每天 22:00 ──→ 📋 "今日成果总结 + 与昨天对比"
```

---

## 消息示例

### 开始通知 (08:00)
```
🌅 新的一天开始了！

📊 今日目标: 2000 ml

💪 新的一天，新的开始！让我们一起喝水吧！

直接发送数字（如 200）记录饮水量
```

### 结束报告 (22:00) - 已达成
```
📋 今日喝水报告

🎯 目标: 2000 ml
💧 实际: 2500 ml
📊 完成度: 125%
状态: ✅ 已达成

🎉 与昨日对比
📈 比昨天多喝了 300ml，继续保持！
（昨日: 2200 ml）

🌙 你太棒了！今天已经养成了很好的饮水习惯！
```

### 结束报告 - 未达成
```
📋 今日喝水报告

🎯 目标: 2000 ml
💧 实际: 1800 ml
📊 完成度: 90%
状态: ❌ 未达成

💪 与昨日对比
📈 比昨天多喝了 200ml，继续加油！
（昨日: 1600 ml）

🌙 今天虽然没达成，但你已经在进步了！明天继续加油！
```

---

## 用户命令速查表

| 命令 | 作用 | 对通知的影响 |
|------|------|-----------|
| `/start` | 启动机器人 | ✅ 创建通知 |
| `/time 08:00 22:00` | 设置活跃时段 | 🔄 更新通知时间 |
| `/stop_today` | 停止今天提醒 | ⏸️ 今天无通知 |
| `/disable_forever` | 永久禁用 | ❌ 停止所有通知 |
| `/enable` | 重新启用 | ✅ 恢复通知 |

---

## 配置检查清单

用户收不到通知？按顺序检查：

- [ ] 1. 执行过 `/start` 吗？
  ```
  /start
  ```

- [ ] 2. 时区设置正确吗？
  ```
  /timezone 8     # 北京时间
  /timezone 0     # 伦敦
  /timezone -5    # 纽约
  ```

- [ ] 3. 活跃时段设置正确吗？
  ```
  /time 08:00 22:00
  ```

- [ ] 4. 是否被禁用了？
  ```
  /enable         # 重新启用
  ```

- [ ] 5. 是否被拉入黑名单了？
  ```
  /start 会提示"已被禁用"
  ```

---

## 开发者速查表

### 核心函数调用链

```
用户输入 /start
    ↓
cmd_start()
    ↓
create_reminder_job()           # 定时提醒
create_daily_start_notification() # 每日开始
create_daily_end_report()       # 每日结束
```

### 数据库查询

```python
# 获取指定日期的饮水量
await db.get_daily_total(user_id, days_ago=0, timezone=8)  # 今天
await db.get_daily_total(user_id, days_ago=1, timezone=8)  # 昨天
```

### Job 管理

```python
# Job ID 规则
f"daily_start_{user_id}"   # 开始通知
f"daily_end_{user_id}"     # 结束报告
f"reminder_{user_id}"      # 定时提醒

# 查看所有 Job
scheduler.get_jobs()

# 手动触发任务
scheduler.reschedule_job(job_id, trigger=...)
```

---

## 关键特性

### ✅ 时区意识
- 所有时间都考虑用户时区
- 支持 UTC±XX:XX 的任何时区

### ✅ 数据准确
- 日期范围：用户本地时间 00:00 ~ 24:00
- 支持补录功能（`/back` 命令）
- 与昨日对比基于相同的时区逻辑

### ✅ 自动同步
- 修改 `/time` 后自动更新通知时间
- 禁用/启用时自动创建/销毁 Job
- 无需手动重启

### ✅ 容错处理
- 黑名单用户无法创建通知
- 禁用用户的通知自动停止
- 消息发送失败自动重试（APScheduler 机制）

---

## 文件导航

| 文件 | 用途 |
|------|------|
| [DAILY_NOTIFICATIONS.md](DAILY_NOTIFICATIONS.md) | 详细功能说明 |
| [DAILY_NOTIFICATIONS_TESTING.md](DAILY_NOTIFICATIONS_TESTING.md) | 测试场景 |
| main.py | 核心实现 |
| database.py | 数据库函数 |
| config.py | 消息配置 |

---

## 常见问题

### Q: 为什么昨天数据计算错误？
**A:** 检查时区设置
```
/timezone 8     # 根据实际情况调整
```

### Q: 怎样立即查看结束报告？
**A:** 手动执行 `/time` 重新生成 Job，可以添加调试代码手动调用

### Q: 支持自定义消息吗？
**A:** 是的，在 `config.py` 中修改：
- `ENCOURAGEMENT_MESSAGES` - 开始通知的鼓励语
- `COMPLETION_MESSAGES` - 结束报告的完成语

### Q: 新用户首次加入，何时收到开始通知？
**A:** 下一个开始时间点（不是立即发送）

### Q: 如何禁用某个用户的通知？
**A:** 管理员执行
```
/blacklist 用户ID 原因
```

---

## 版本更新日志

### v2.1 (2026-02-04)
✨ **新增**：每日通知功能
- 每日开始通知 🌅
- 每日结束报告 📋
- 昨日对比分析

🔧 **改进**：
- 新增 `db.get_daily_total()` 函数
- 自动 Job 管理（创建/更新/删除）
- 完整的文档和测试场景

---

## 支持

有问题？检查这些资源：
1. 📖 [DAILY_NOTIFICATIONS.md](DAILY_NOTIFICATIONS.md) - 完整说明
2. 🧪 [DAILY_NOTIFICATIONS_TESTING.md](DAILY_NOTIFICATIONS_TESTING.md) - 测试场景
3. 📋 本文件 - 快速参考
4. 💬 [ADMIN_SETUP.md](ADMIN_SETUP.md) - 管理员功能

