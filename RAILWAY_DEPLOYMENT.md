# 🚂 Railway 部署指南 - 完整版

> **Railway 特点：** 超简洁界面，按使用量付费，有 $5 免费试用

## 📋 部署前准备

### 需要的信息

1. **Telegram Bot Token** - 从 BotFather 获取
2. **PostgreSQL 连接字符串** - 从 Neon 获取
3. **GitHub 仓库** - `water-reminder-bot`

---

## 🎯 快速部署（5 步，约 10 分钟）

### 步骤 1：创建 Railway 账户

1. 访问 https://railway.app
2. 点击 **"Login"** 或 **"Sign Up"**
3. 选择 **"GitHub"** 登录
4. 授权 Railway 访问 GitHub

✓ **完成时间：1 分钟**

---

### 步骤 2：创建新项目

1. 点击 **"New Project"**
2. 选择 **"Deploy from GitHub repo"**
3. 选择仓库 **`water-reminder-bot`**
4. 点击 **"Deploy"**

✓ **完成时间：1 分钟**

---

### 步骤 3：配置部署

Railway 会自动检测到 Dockerfile 并开始构建。

在部署过程中：
- 查看 **"Deployments"** 选项卡监控进度
- 正常时间：2-5 分钟

✓ **完成时间：5 分钟**

---

### 步骤 4：配置环境变量 ⭐ 关键

部署成功后配置环境变量：

1. 点击项目进入详情页
2. 找到你的应用（名称类似 `water-reminder-bot`）
3. 点击应用进入详情
4. 选择 **"Variables"** 标签
5. 添加两个变量：

**变量 1：**
```
Key:   TELEGRAM_TOKEN
Value: 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
```

**变量 2：**
```
Key:   DATABASE_URL
Value: postgresql://user:password@host:port/dbname?sslmode=require
```

6. 点击 "Add" 保存

✓ **完成时间：2 分钟**

---

### 步骤 5：重新部署

添加环境变量后需要重新部署才能生效：

1. 点击 **"Deployments"** 标签
2. 点击最新部署旁的 **"Redeploy"** 按钮
3. 等待新部署完成

✓ **完成时间：3 分钟**

---

## ✅ 验证部署成功

1. **检查应用状态**
   - 在 Railway 仪表板查看状态
   - 应显示 "Running" ✓

2. **获取应用 URL**
   - 点击应用
   - 在 "Deployment" 中查看公网 URL

3. **在 Telegram 中测试**
   ```
   /start
   ```
   - 收到欢迎消息 → **成功！** 🎉

---

## 🎨 Railway 仪表板功能

### 查看项目
- **Dashboard：** 项目概览
- **Services：** 列出所有服务
- **Deployments：** 部署历史

### 查看应用日志
1. 选择应用
2. 点击 **"Logs"** 标签
3. 查看实时日志

### 管理环境变量
1. 选择应用
2. 点击 **"Variables"** 标签
3. 添加/修改变量

### 查看应用详情
1. 选择应用
2. 点击 **"Settings"** 标签
3. 查看配置信息

---

## 💰 定价和免费试用

### 免费试用
- **$5 额度**
- **有效期：** 首月
- 用完后会停止服务（需升级）

### 按量付费
- **Web 应用：** $0.000231/小时（≈ $1.7/月）
- **数据库：** $0.000231/小时（≈ $1.7/月）
- **存储：** $0.00000417/GB/小时

### 典型费用
- Telegram Bot：~$3-5/月
- PostgreSQL 数据库：~$1-3/月
- **总计：~$5-8/月**

---

## ❓ 常见问题

### Q1: "Railway $5 免费试用用完了怎么办？"

**选项：**
1. 升级为付费账户（按量付费）
2. 删除应用，创建新账户（重新获得 $5）
3. 切换到其他平台（Render 完全免费）

### Q2: 部署失败

**查看错误：**
1. 点击 Deployments
2. 点击失败的部署
3. 查看 "Logs" 错误信息

**常见原因：**
- requirements.txt 不完整
- Dockerfile 有问题
- 环境变量缺失

### Q3: 机器人响应缓慢

**原因：** 可能在免费试用阶段被限流

**解决：** 升级为付费账户

### Q4: 如何更新应用？

**自动更新：**
```bash
git push origin main  # 推送到 GitHub
# Railway 会自动检测并重新部署
```

---

## 🔄 更新应用

Railway 支持自动部署：

```bash
# 修改代码
git add .
git commit -m "Update: description"
git push origin main

# Railway 自动部署
# 等待 2-5 分钟
```

---

## 📊 Railway vs Render vs Koyeb

| 功能 | Railway | Render | Koyeb |
|------|---------|--------|-------|
| 免费试用 | $5 | ✅ 完全免费 | ✅ 完全免费 |
| 长期免费 | ❌ | ✅ | ✅ |
| 按量付费 | ✅ | ❌ | ❌ |
| GitHub 集成 | ✅ | ✅ | ✅ |
| Docker | ✅ | ✅ | ✅ |
| UI 简洁度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 💡 Railway 最适合

- 想尝试一下（$5 试用）
- 接受付费的开发者
- 需要灵活的按量计费

---

## 🚀 快速开始

1. 访问 https://railway.app
2. 用 GitHub 登录
3. 创建项目并连接仓库
4. 添加环境变量
5. 重新部署

**总时间：约 10-15 分钟**

---

## 📚 相关文档

- **ALTERNATIVE_PLATFORMS.md** - 🌍 平台对比
- **RENDER_DEPLOYMENT.md** - ⭐ Render 指南（完全免费）
- **DEPLOYMENT_CHECKLIST.md** - ✓ 检查清单

---

**选择建议：**
- 💰 有预算？ → 选 Railway（按量付费，公平）
- 🆓 想完全免费？ → 选 Render
- ⏱️ 响应快？ → 选 Koyeb（如可用）

---

**祝部署顺利！**
