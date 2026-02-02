# 📦 Koyeb 部署指导 - 完整版本

## 项目清理完成 ✓

您的项目已经清理完毕，所有非必要文件已删除，现在已准备好部署到 Koyeb。

### 项目文件结构

```
water-reminder-bot/
├── .dockerignore              # Docker 忽略文件
├── .env.example              # 环境变量示例（不在源码中存储实际值）
├── .gitignore                # Git 忽略文件
├── config.py                 # 配置模块 - 使用环境变量
├── database.py               # 数据库操作模块
├── Dockerfile                # Docker 容器配置
├── main.py                   # 主程序入口
├── README.md                 # 项目说明
├── requirements.txt          # Python 依赖列表
├── KOYEB_DEPLOY.md          # 详细部署指南
└── DEPLOYMENT_CHECKLIST.md  # 部署检查清单
```

## 关键改进

### ✓ 环境变量配置
- 所有敏感信息（Token、密码等）都使用 `os.getenv()` 从环境变量读取
- 不在源码中存储任何真实的环境变量值
- `config.py` 中添加了必要的环境变量验证
- 如果 `TELEGRAM_TOKEN` 或 `DATABASE_URL` 缺失，程序会明确报错

### ✓ 项目简化
- 删除了所有测试文件（`test_*.py`）
- 删除了临时文档文件
- 删除了开发工具脚本
- 保留了所有必要的生产环境文件

### ✓ 部署就绪
- Dockerfile 已优化
- `.dockerignore` 已配置
- 所有依赖已列在 `requirements.txt`

## 快速开始 - 3 步部署

### 步骤 1：准备信息

在部署前，请准备好以下信息：

1. **Telegram Bot Token**
   - 打开 Telegram，搜索 `@BotFather`
   - 发送 `/newbot`
   - 按照提示创建机器人
   - 记录获得的 Token

2. **PostgreSQL 数据库**
   - 推荐使用 **Neon**（免费）：https://neon.tech
   - 或 **Supabase**：https://supabase.com
   - 获取完整的连接字符串，格式如：
     ```
     postgresql://user:password@host:port/dbname?sslmode=require
     ```

3. **GitHub 账户和仓库**
   - 创建 GitHub 仓库
   - 将代码推送到仓库（公开）

### 步骤 2：Koyeb 配置

1. **访问 Koyeb**：https://app.koyeb.com

2. **创建应用**
   - 点击 "Create" → "Create App"
   - 选择 "GitHub"
   - 授权并选择仓库 `water-reminder-bot`
   - 分支选择 `main`

3. **构建配置**
   - Builder：`Dockerfile`
   - Dockerfile path：`./Dockerfile`
   - Port：`8080`

4. **环境变量配置（最重要！）**
   
   点击 "Add Env Variables" 并添加：

   ```
   TELEGRAM_TOKEN = 你的Bot Token
   DATABASE_URL = postgresql://user:password@host:port/dbname?sslmode=require
   ```

   > ⚠️ **重要** 
   > - 不要在代码中存储这些值
   > - 只在 Koyeb 仪表板中配置

### 步骤 3：部署

1. 检查所有配置无误
2. 点击 "Deploy"
3. 等待部署完成（3-5 分钟）
4. 在 Telegram 中测试机器人

## 环境变量详解

### 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `TELEGRAM_TOKEN` | Telegram Bot Token | `1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh` |
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql://user:pass@host:port/db?sslmode=require` |

### 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `PORT` | 应用监听端口 | `8080` |
| `WEBHOOK_URL` | Webhook 回调地址（可不配置） | - |

## 验证部署

部署完成后，验证机器人是否正常工作：

```
1. 打开 Telegram
2. 找到你创建的机器人
3. 发送 /start
4. 如果收到欢迎消息，表示部署成功 ✓
5. 测试 /settings 和 /record 命令
```

## 常见问题

### Q1: 部署失败，显示"Build Error"
A: 检查 GitHub 仓库是否包含所有必要文件

### Q2: 机器人无响应
A: 
- 检查 TELEGRAM_TOKEN 是否正确
- 检查数据库连接是否正常
- 查看 Koyeb 应用日志

### Q3: "Environment variable TELEGRAM_TOKEN not found"
A: 
- 进入 Koyeb 仪表板
- 找到你的应用
- 重新添加环境变量
- 重启应用

### Q4: 数据库连接失败
A:
- 验证 DATABASE_URL 格式是否正确
- 确认数据库服务在线
- 检查网络连接

## 更新应用

要更新应用，只需修改代码并推送到 GitHub：

```bash
# 修改代码
git add .
git commit -m "Update: description"
git push origin main

# Koyeb 会自动检测并重新部署
# 无需手动操作
```

## 重要提示

### 🔒 安全建议
1. **永远不要在代码中硬编码敏感信息**
   - ✓ 正确：使用环境变量
   - ✗ 错误：在 Python 文件中写死 Token

2. **环境变量管理**
   - 使用 Koyeb 内置的环境变量管理
   - 定期更新和轮换 Token

3. **数据库安全**
   - 使用强密码
   - 启用 SSL/TLS 连接
   - 定期备份

### 📝 相关文档
- 详细指南：[KOYEB_DEPLOY.md](KOYEB_DEPLOY.md)
- 检查清单：[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- 项目说明：[README.md](README.md)

## 获取帮助

- **Koyeb 文档**：https://docs.koyeb.com
- **Telegram Bot API**：https://core.telegram.org/bots
- **PostgreSQL**：https://www.postgresql.org/docs

---

## 部署流程图

```
准备信息
    ↓
获取 Token 和数据库 URL
    ↓
推送代码到 GitHub
    ↓
Koyeb 创建应用
    ↓
配置构建（Dockerfile）
    ↓
配置环境变量 ← ⚠️ 关键步骤
    ↓
部署
    ↓
等待完成（3-5 分钟）
    ↓
在 Telegram 中测试
    ↓
部署完成 ✓
```

---

祝部署顺利！如有问题，请参考相关文档或 Koyeb 官方文档。
