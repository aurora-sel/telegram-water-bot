# 🚀 Render 部署指南 - 完整版

> **推荐原因：** Render 是最接近 Koyeb 的替代品，完全免费，部署极其简单！

## 📋 部署前准备

### 需要准备的信息（与 Koyeb 相同）

1. **Telegram Bot Token**
   - 来源：BotFather
   - 格式：`1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh`

2. **PostgreSQL 连接字符串**
   - 推荐：Neon（https://neon.tech）
   - 格式：`postgresql://user:password@host:port/dbname?sslmode=require`

3. **GitHub 仓库**
   - 公开仓库 `water-reminder-bot`
   - 包含所有代码

---

## 🎯 快速部署（7 步，约 15 分钟）

### 步骤 1：创建 Render 账户

1. 访问 https://render.com
2. 点击 **"Sign up"**
3. 选择 **"Continue with GitHub"**
4. 授权 Render 访问你的 GitHub 账户
5. 授权成功后进入 Render 仪表板

✓ **完成时间：2 分钟**

---

### 步骤 2：连接 GitHub 仓库

1. 在 Render 仪表板，点击 **"New +"** 按钮
2. 选择 **"Web Service"**
3. 在 "Connect a repository" 部分，选择 **"water-reminder-bot"**
4. 如果仓库未显示，点击 "Configure account" 授权更多仓库
5. 选择仓库后点击 **"Connect"**

✓ **完成时间：2 分钟**

---

### 步骤 3：配置 Web Service

在创建表单中填写：

| 字段 | 值 | 说明 |
|------|-----|------|
| **Name** | `water-reminder-bot` | 服务名称（自动生成 URL） |
| **Environment** | `Docker` | 选择 Docker 构建 |
| **Region** | `Singapore` 或最近的区域 | 选择服务器位置 |
| **Branch** | `main` | 部署分支 |

> 💡 **提示：** 区域选择对 Telegram Bot 响应速度有影响

✓ **完成时间：1 分钟**

---

### 步骤 4：配置构建设置

向下滚动到 "Build Command" 部分：

- **Build Command（构建命令）:** 留空（不需要填写）
- **Start Command（启动命令）:** 已从 Dockerfile 自动读取

> Render 会自动读取 Dockerfile 中的配置

✓ **完成时间：1 分钟**

---

### 步骤 5：配置环境变量 ⭐ 关键步骤

1. 向下找到 **"Environment"** 部分
2. 点击 **"Add Environment Variable"**
3. 添加以下变量：

**第 1 个变量：**
```
Key:   TELEGRAM_TOKEN
Value: 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
```

**第 2 个变量：**
```
Key:   DATABASE_URL
Value: postgresql://user:password@host:port/dbname?sslmode=require
```

4. 每个变量后点击 "Add"

✓ **完成时间：2 分钟**

---

### 步骤 6：启动部署

1. 检查所有配置无误
2. 向下滚动到底部
3. 点击 **"Create Web Service"**
4. 等待部署开始

✓ **完成时间：1 分钟**

---

### 步骤 7：监控部署过程

部署进度页面会显示：

```
Building...          # 正在构建 Docker 镜像
Deploying...         # 正在部署应用
Running ✓            # 部署成功！
```

- **正常时间：** 2-5 分钟
- **可查看实时日志**

✓ **完成时间：5 分钟**

---

## ✅ 验证部署成功

部署完成后，你会看到：

1. **Render 仪表板**
   - 状态显示 "Live" ✓
   - 可看到应用的公网 URL（如：`https://water-reminder-bot-xxxxx.onrender.com`）

2. **在 Telegram 中测试**
   ```
   /start
   ```
   - 收到欢迎消息 → **部署成功！** 🎉

3. **功能测试**
   ```
   /settings          # 配置用户设置
   /record 250        # 记录 250ml 饮水
   /today             # 查看今日统计
   ```

---

## 🎨 Render 仪表板功能

### 查看应用信息
- **Name:** 应用名称（可修改）
- **URL:** 公网地址
- **Status:** 当前状态
- **Plan:** 付费计划（Free 是免费）

### 查看实时日志
1. 点击应用名称进入详情页
2. 选择 **"Logs"** 标签
3. 查看实时输出

### 配置环境变量
1. 点击应用名称进入详情页
2. 选择 **"Environment"** 标签
3. 修改或添加新变量

### 重启应用
1. 点击应用名称进入详情页
2. 选择 **"Settings"** 标签
3. 点击 **"Restart Service"**

---

## 📊 Render vs Koyeb 对比

| 功能 | Render | Koyeb |
|------|--------|-------|
| 免费层 | ✅ 完全免费 | ✅ 完全免费 |
| GitHub 集成 | ✅ | ✅ |
| Docker 支持 | ✅ | ✅ |
| PostgreSQL | ✅ | ✅ |
| 环境变量 | ✅ | ✅ |
| 自动 SSL | ✅ | ✅ |
| 自动部署 | ✅ | ✅ |
| 部署速度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| UI 友好度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🆘 常见问题

### Q1: 部署失败，显示 "Build failed"

**原因：** Docker 构建错误

**解决步骤：**
1. 点击应用进入详情页
2. 选择 "Logs" 查看错误信息
3. 查看错误是否与依赖相关
4. 检查 requirements.txt 是否完整
5. 重新推送到 GitHub，Render 会自动重新部署

### Q2: "Environment variable not found" 错误

**原因：** 环境变量配置不完整

**解决：**
1. 进入应用的 "Environment" 设置
2. 验证 TELEGRAM_TOKEN 和 DATABASE_URL 都已添加
3. 检查没有拼写错误
4. 点击 "Restart Service" 重启应用

### Q3: 机器人无响应

**解决步骤：**
1. **检查应用状态**
   - Render 仪表板显示 "Live" ✓

2. **查看日志**
   - 点击 "Logs" 查看错误

3. **验证 Token**
   - 确认 TELEGRAM_TOKEN 是否正确

4. **重启应用**
   - Settings → Restart Service

### Q4: 数据库连接失败

**原因：** DATABASE_URL 不正确

**解决：**
1. 验证连接字符串格式：
   ```
   postgresql://用户名:密码@主机:端口/数据库名?sslmode=require
   ```

2. 测试数据库连接
3. 确认数据库服务在线
4. 更新 DATABASE_URL，然后重启应用

### Q5: 免费层限制是什么？

**Render 免费层特性：**
- ✅ 无限应用数量
- ✅ 无限带宽
- ✅ 自动部署
- ⚠️ 15 分钟无请求会休眠
- ⚠️ 启动需要 50 秒

**对于 Telegram Bot 的影响：**
- 机器人处于活跃状态时正常工作
- 长期不用会进入休眠
- 重新启动需要等待 50 秒

**解决方案：**
- 升级到 Paid ($7/月)
- 或使用定时任务保持活跃

---

## 💳 付费计划（可选）

如果想要更好的性能：

| 功能 | Free | Starter | Plus |
|------|------|---------|------|
| **价格** | 免费 | $7/月 | $12/月 |
| **休眠** | 15 分钟 | ❌ 无 | ❌ 无 |
| **启动时间** | ~50 秒 | ~5 秒 | ~2 秒 |
| **计算** | 共享 | 1 CPU | 1 CPU |
| **内存** | 512 MB | 1 GB | 2 GB |

---

## 🔄 更新应用

修改代码后自动部署：

```bash
# 修改代码
git add .
git commit -m "Update: description"
git push origin main

# Render 会自动检测并部署
# 无需手动操作
```

---

## 🔐 安全建议

1. **环境变量安全**
   - 不在代码中硬编码敏感信息
   - 使用 Render 的环境变量管理

2. **定期检查**
   - 查看 Logs 中是否有异常
   - 监控应用性能

3. **备份数据**
   - 定期导出数据库备份
   - 特别是生产环境

---

## 📈 监控和维护

### 定期检查
- 应用状态（仪表板）
- 错误日志（Logs 选项卡）
- 数据库使用情况

### 性能优化
- 如果响应慢，考虑升级计划
- 优化数据库查询
- 检查日志找瓶颈

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| **ALTERNATIVE_PLATFORMS.md** | 🌍 平台对比 |
| **README.md** | 📖 项目说明 |
| **DEPLOYMENT_CHECKLIST.md** | ✓ 检查清单 |

---

## 🎯 部署总结

```
准备信息 (5 分钟)
    ↓
创建 Render 账户 (2 分钟)
    ↓
连接 GitHub (2 分钟)
    ↓
配置服务 (1 分钟)
    ↓
添加环境变量 (2 分钟) ← 关键！
    ↓
启动部署 (1 分钟)
    ↓
等待完成 (5 分钟)
    ↓
验证 Telegram (1 分钟)
    ↓
✓ 完成！
```

**总耗时：约 15-20 分钟**

---

## 🚀 立即开始

1. 访问 https://render.com
2. 用 GitHub 账户登录
3. 按照上面的 7 步操作
4. 享受免费的 Telegram Bot！

---

**祝部署顺利！如有问题，查看 Logs 中的错误信息。**

需要帮助？检查 [ALTERNATIVE_PLATFORMS.md](ALTERNATIVE_PLATFORMS.md) 中的其他选项。
