# 🔧 Koyeb TCP 健康检查错误 - 修复指南

## 问题描述

**错误消息：** `TCP health check failed on port 8080`

**原因：** 应用没有在 8080 端口上启动 HTTP 服务器，只使用 Telegram 长轮询。Koyeb 需要 HTTP 服务器来进行健康检查。

---

## ✅ 已完成的修复

### 1. main.py 代码修改

添加了一个简单的 aiohttp HTTP 服务器，提供以下端点：

```python
GET / → 返回 "OK"（健康检查）
GET /health → 返回 "OK"（健康检查）
GET /status → 返回 JSON 格式的应用状态
```

**关键改进：**
- ✅ 同时运行 HTTP 服务器和 Telegram Bot 长轮询
- ✅ 应用启动时立即监听 8080 端口
- ✅ HTTP 服务器与 Bot 运行在同一个 asyncio 事件循环中
- ✅ 优雅关闭时正确清理资源

### 2. Dockerfile 修改

**改进点：**
- ✅ 添加了 `curl` 用于健康检查
- ✅ 更新了 HEALTHCHECK 以真实 HTTP 请求检查
- ✅ 使用 `ENTRYPOINT + CMD` 形式确保正确处理信号
- ✅ 改进的关闭流程

---

## 🚀 如何部署（修复版本）

### 第 1 步：更新本地文件

确保你的本地文件已更新为最新版本：
- `main.py` - 包含 HTTP 服务器代码
- `Dockerfile` - 更新的健康检查

### 第 2 步：推送到 GitHub

```bash
cd water-reminder-bot
git add .
git commit -m "Fix: Add HTTP server for Koyeb health checks"
git push origin main
```

### 第 3 步：重新部署到 Koyeb

1. 访问 Koyeb Dashboard
2. 选择你的应用
3. 点击 "Redeploy from main" 或 "Redeploy"
4. 等待新部署完成

### 第 4 步：验证部署

在 Koyeb 仪表板中：
- ✓ 应用状态应显示 "Healthy" （不是 "Unhealthy"）
- ✓ Deployment 日志中应看到 `[HTTP服务器] 已启动，监听 0.0.0.0:8080`

---

## 🧪 如何验证修复成功

### 方法 1：检查应用状态
在 Koyeb 仪表板：
1. 选择应用
2. 查看 "Health" 状态
3. 应该显示 "Healthy" ✓

### 方法 2：查看日志
在 Koyeb 仪表板：
1. 选择应用
2. 进入 "Logs" 标签
3. 查看是否有：
   ```
   [HTTP服务器] 已启动，监听 0.0.0.0:8080
   ```

### 方法 3：测试 HTTP 端点
```bash
# 获取你的应用 URL（从 Koyeb 仪表板）
curl https://your-app-url.onrender.com/health
# 应返回: OK

curl https://your-app-url.onrender.com/status
# 应返回: {"status": "running", "bot": "active", ...}
```

### 方法 4：测试 Telegram Bot
1. 打开 Telegram
2. 找到你的机器人
3. 发送 `/start`
4. 应该收到欢迎消息

---

## 📋 技术细节

### HTTP 服务器实现

```python
async def health_check(request):
    """健康检查端点 - 返回 200 OK"""
    return web.Response(text="OK", status=200)

async def run_http_server():
    """运行 HTTP 服务器"""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, APP_HOST, APP_PORT)
    await site.start()
    
    logger.info(f"[HTTP服务器] 已启动，监听 {APP_HOST}:{APP_PORT}")
    return runner
```

### 并发运行

```python
async def main():
    # 启动 HTTP 服务器
    http_runner = await run_http_server()
    
    try:
        # 启动 Telegram Bot 长轮询
        await dp.start_polling(bot, ...)
    finally:
        # 优雅关闭
        await http_runner.cleanup()
```

---

## 🔄 工作流程

```
应用启动
    ↓
启动 HTTP 服务器（监听 8080）
    ↓
启动 Telegram Bot 长轮询
    ↓
Koyeb 健康检查请求 → HTTP 服务器 → 返回 200 OK
    ↓
应用标记为 "Healthy" ✓
    ↓
Bot 开始接收消息并响应
```

---

## ⚠️ 常见问题

### Q1: 部署后仍显示 "Unhealthy"

**解决步骤：**
1. 等待 40 秒（HEALTHCHECK start-period）
2. 检查日志中是否有错误
3. 验证 TELEGRAM_TOKEN 和 DATABASE_URL 是否正确
4. 查看应用日志找具体错误

### Q2: 机器人无响应

**可能原因：**
1. 应用已启动但 Bot 长轮询失败
2. Telegram Token 不正确

**解决：**
1. 检查日志中是否有错误消息
2. 验证 TELEGRAM_TOKEN 是否正确
3. 重新部署

### Q3: HTTP 端点返回 404

**原因：** 应用路由配置错误

**解决：** 查看日志确认 HTTP 服务器已启动

### Q4: 应用在部署后立即崩溃

**可能原因：**
1. 环境变量缺失
2. 数据库连接失败

**解决：**
1. 检查 Koyeb 环境变量配置
2. 验证 DATABASE_URL 是否正确

---

## 🎯 预期行为

### 部署过程

```
Building... ✓
Pushing... ✓
Starting... ✓
[启动] 初始化数据库... ✓
[启动] 启动 APScheduler... ✓
[启动] Telegram 机器人已启动 ✓
[HTTP服务器] 已启动，监听 0.0.0.0:8080 ✓
[轮询] 启动长轮询模式... ✓

→ 应用状态：Healthy ✓
```

### 应用运行时

```
收到 Telegram 消息 → Bot 处理 → 返回响应
HTTP 健康检查 → 返回 OK ✓
```

---

## 📝 变更日志

### 修复前
- ❌ 没有 HTTP 服务器
- ❌ Koyeb 无法进行健康检查
- ❌ 部署失败，显示 "TCP health check failed"

### 修复后
- ✅ 添加 aiohttp HTTP 服务器
- ✅ 实现 `/health` 和 `/status` 端点
- ✅ HTTP 服务器与 Bot 并发运行
- ✅ 改进的 Dockerfile 和健康检查
- ✅ 正确的信号处理和资源清理

---

## 🔗 相关链接

- [Koyeb 文档 - 健康检查](https://docs.koyeb.com)
- [aiohttp 文档](https://docs.aiohttp.org)
- [Telegram Bot API](https://core.telegram.org/bots)

---

## ✅ 检查清单（部署前）

- [ ] main.py 已更新（包含 HTTP 服务器）
- [ ] Dockerfile 已更新（改进的健康检查）
- [ ] 所有文件已推送到 GitHub
- [ ] TELEGRAM_TOKEN 已在 Koyeb 中配置
- [ ] DATABASE_URL 已在 Koyeb 中配置
- [ ] 开始新的部署

---

**修复完成！现在重新部署应该能解决问题。** ✓

如有任何问题，查看 Koyeb 仪表板的 "Logs" 部分获取详细错误信息。
