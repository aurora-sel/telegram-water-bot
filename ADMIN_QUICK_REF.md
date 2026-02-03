# 👨‍💼 管理员命令快速参考

## ⚡ 5 分钟快速设置

### 1️⃣ 获取你的 Telegram ID

在 Telegram 中向 **@userinfobot** 发送 `/start`

你会看到类似信息：
```
You are: 123456789
```

复制这个数字 → `123456789`

### 2️⃣ 设置环境变量（Koyeb）

**Koyeb 仪表板 → 应用 → Settings → Environment variables**

添加新变量：
- **Name:** `ADMIN_IDS`
- **Value:** `123456789`

点击 **Save** → **Redeploy**

### 3️⃣ 验证设置

等待 2-3 分钟部署完成后，在 Telegram 中发送：

```
/admin_stats
```

✅ **有响应** = 设置成功！
❌ **无权限** = 设置失败（见故障排查）

---

## 📋 管理员命令列表

| 命令 | 用途 | 示例 |
|------|------|------|
| `/admin_stats` | 查看统计 | `/admin_stats` |
| `/blacklist` | 拉黑用户 | `/blacklist 987654321 spam` |
| `/unblacklist` | 解黑用户 | `/unblacklist 987654321` |
| `/user_info` | 查看用户 | `/user_info 987654321` |

---

## 🔍 常见故障排查

### ❌ 显示"无权限"

**原因 1：还未 Redeploy**
```
→ 点击 Koyeb Redeploy，等待 2-3 分钟
```

**原因 2：ID 错误**
```
→ 再次向 @userinfobot 确认你的 ID
→ 确保没有输入错误
```

**原因 3：格式有空格**
```
❌ ADMIN_IDS=123456789, 987654321  （有空格）
✅ ADMIN_IDS=123456789,987654321   （无空格）
```

**原因 4：环境变量未保存**
```
→ Koyeb Settings 中检查 ADMIN_IDS 值
→ 确认有保存和 Redeploy
```

### ✅ 验证成功的标志

在 Koyeb 日志中看到：
```
[配置] ✅ 管理员 ID 配置成功: [123456789]
```

---

## 👥 多个管理员

用逗号分隔，**无空格**：

```
ADMIN_IDS=123456789,987654321,555666777
```

---

## 🔐 安全建议

- ✅ 定期用 `/admin_stats` 检查黑名单
- ✅ 如果需要，用 `/unblacklist` 解除拉黑
- ✅ 不要分享你的 ID 给不信任的人

---

## 📖 详细文档

→ [ADMIN_SETUP.md](ADMIN_SETUP.md) - 完整管理员配置指南

---

**提示：** 管理员功能是完全可选的。不配置 ADMIN_IDS 也可以正常使用所有用户功能。
