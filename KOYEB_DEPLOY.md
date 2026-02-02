# Koyeb 部署指南

## 前置要求

- GitHub 账户
- Koyeb 账户（https://koyeb.com）
- Neon PostgreSQL 数据库实例（或其他 PostgreSQL 服务）
- Telegram Bot Token（从 BotFather 获取）

## 部署步骤

### 第一步：准备数据库

1. **创建 PostgreSQL 数据库**
   - 访问 [Neon](https://neon.tech) 或其他 PostgreSQL 服务
   - 创建一个新项目
   - 获取数据库连接字符串，格式如下：
     ```
     postgresql://user:password@host:port/dbname?sslmode=require
     ```

2. **记录数据库 URL**
   - 保存完整的数据库连接字符串，后续会用到

### 第二步：准备 Telegram Bot

1. **从 BotFather 获取 Token**
   - 在 Telegram 中搜索 @BotFather
   - 发送 `/newbot` 创建新机器人
   - 按照指示完成创建
   - 获取 Bot Token，格式如下：
     ```
     1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
     ```

### 第三步：上传代码到 GitHub

1. **创建 GitHub 仓库**
   - 登录 GitHub
   - 创建新仓库，名称如 `water-reminder-bot`

2. **上传项目代码**
   ```bash
   # 初始化 Git 仓库
   cd water-reminder-bot
   git init
   
   # 添加 remote
   git remote add origin https://github.com/your-username/water-reminder-bot.git
   
   # 提交代码
   git add .
   git commit -m "Initial commit"
   
   # 推送到 GitHub
   git branch -M main
   git push -u origin main
   ```

3. **确保 GitHub 仓库公开**
   - Settings → Visibility → Public

### 第四步：在 Koyeb 中创建应用

1. **访问 Koyeb 仪表板**
   - 登录 [Koyeb](https://app.koyeb.com)

2. **创建新应用**
   - 点击 "Create App"
   - 选择 "GitHub" 作为代码源
   - 选择你的仓库 `water-reminder-bot`
   - 选择分支：`main`
   - 点击 "Continue"

3. **配置构建设置**
   - **Builder:** 选择 "Dockerfile"
   - **Dockerfile path:** 保留默认 `Dockerfile`
   - 点击 "Continue"

4. **配置应用运行时**
   - **Instance type:** 选择 "Free" 或按需选择
   - **Port:** 保留 `8080`
   - 点击 "Continue"

### 第五步：配置环境变量

**重要：在此步骤配置所有环境变量**

1. **添加环境变量**
   
   点击 "Add Env Variables" 并添加以下变量：

   | 变量名 | 值 | 说明 |
   |--------|-----|------|
   | `TELEGRAM_TOKEN` | `your_bot_token_here` | 从 BotFather 获取的 Bot Token |
   | `DATABASE_URL` | `postgresql://...` | 从 Neon 或 PostgreSQL 获取的完整连接字符串 |
   | `PORT` | `8080` | 应用监听端口（默认值，无需修改） |

   示例：
   ```
   TELEGRAM_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
   DATABASE_URL=postgresql://user:password@host:port/dbname?sslmode=require
   PORT=8080
   ```

2. **验证环境变量**
   - 确保没有拼写错误
   - 特别检查 TELEGRAM_TOKEN 和 DATABASE_URL

### 第六步：部署应用

1. **启动部署**
   - 检查所有配置无误
   - 点击 "Deploy"
   - Koyeb 将自动构建 Docker 镜像并启动应用

2. **等待部署完成**
   - 部署通常需要 3-5 分钟
   - 可在 "Activity" 选项卡中查看部署日志

3. **验证应用状态**
   - 部署完成后，应用状态应显示为 "Healthy" 或 "Running"
   - 如显示其他状态，检查 "Logs" 选项卡中的错误信息

### 第七步：测试机器人

1. **在 Telegram 中测试**
   - 打开 Telegram
   - 搜索你创建的机器人
   - 发送 `/start` 命令
   - 应该收到欢迎消息

2. **测试功能**
   - 发送 `/settings` 配置个人设置
   - 发送 `/record 250` 记录饮水
   - 发送 `/today` 查看今日统计

### 常见问题解决

#### 问题 1：部署失败，显示"Build failed"

**解决方案：**
- 检查 GitHub 仓库是否包含所有必要文件：`main.py`, `database.py`, `config.py`, `requirements.txt`, `Dockerfile`
- 查看 "Logs" 中的具体错误信息
- 检查网络连接

#### 问题 2：机器人无响应

**解决方案：**
- 确认 TELEGRAM_TOKEN 是正确的
- 确认 DATABASE_URL 是可访问的
- 检查 Koyeb 中的应用日志
- 检查 Telegram API 连接

#### 问题 3：数据库连接错误

**解决方案：**
- 验证 DATABASE_URL 格式是否正确
- 确认数据库服务是否在线
- 如使用 Neon，确认 SSL 模式设置为 `require`
- 测试数据库连接字符串

#### 问题 4：环境变量未被加载

**解决方案：**
- 在 Koyeb 仪表板重新启动应用
- 检查环境变量是否正确设置
- 确认没有拼写错误

## 更新应用

1. **在本地修改代码**
   ```bash
   git add .
   git commit -m "Update: description of changes"
   git push origin main
   ```

2. **Koyeb 将自动部署**
   - Koyeb 会自动检测 GitHub 的推送
   - 触发新的构建和部署

## 监控和管理

### 查看应用日志
- 在 Koyeb 仪表板中点击应用
- 选择 "Logs" 选项卡
- 查看实时日志信息

### 扩展和优化
- 修改 Instance type 来调整计算资源
- 可在 Settings 中配置自动扩展

### 数据库管理
- 通过 Neon 仪表板管理数据库
- 可创建备份和恢复

## 安全建议

1. **不要在代码中硬编码敏感信息**
   - ✓ 好：使用环境变量
   - ✗ 坏：在 Python 文件中硬编码 Token

2. **保护环境变量**
   - 使用 Koyeb 的内置环境变量管理
   - 定期轮换 TELEGRAM_TOKEN

3. **数据库安全**
   - 使用强密码
   - 启用 SSL/TLS 连接
   - 定期备份数据

## 支持和反馈

- 遇到问题，查看 Koyeb 文档：https://docs.koyeb.com
- Telegram Bot API 文档：https://core.telegram.org/bots
- PostgreSQL 文档：https://www.postgresql.org/docs
