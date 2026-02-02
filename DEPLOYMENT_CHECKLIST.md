# 水提醒机器人 - 快速部署清单

## 环境变量配置清单

在 Koyeb 中部署前，确保已准备好以下环境变量：

### 必需环境变量

| 环境变量 | 示例值 | 来源 |
|---------|-------|------|
| `TELEGRAM_TOKEN` | `1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh` | BotFather 或 Telegram |
| `DATABASE_URL` | `postgresql://user:pass@host/dbname?sslmode=require` | Neon 或 PostgreSQL 提供商 |

### 可选环境变量

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `PORT` | `8080` | 应用监听端口 |
| `WEBHOOK_URL` | - | Webhook 模式下的回调 URL（可不配置） |

## 部署前检查清单

- [ ] GitHub 账户已创建
- [ ] Koyeb 账户已创建
- [ ] PostgreSQL 数据库已创建（推荐使用 Neon）
- [ ] Telegram Bot Token 已从 BotFather 获取
- [ ] 代码已推送到 GitHub 仓库（公开）
- [ ] `.env.example` 文件已准备好

## Koyeb 部署步骤

1. **访问 Koyeb** → https://app.koyeb.com
2. **创建应用** → "Create App"
3. **选择 GitHub** → 连接 GitHub 账户
4. **选择仓库** → `water-reminder-bot`
5. **选择构建方式** → "Dockerfile"
6. **配置环境变量** → 添加 `TELEGRAM_TOKEN` 和 `DATABASE_URL`
7. **部署** → 点击 "Deploy"

## 部署后验证

```bash
# 1. 在 Telegram 中找到你的机器人
# 2. 发送 /start 命令
# 3. 应该收到欢迎消息
# 4. 测试 /settings 命令
# 5. 测试 /record 250 记录饮水
```

## 必要的文件

项目中必须包含以下文件用于 Koyeb 部署：

```
water-reminder-bot/
├── main.py           # 核心程序（必需）
├── database.py       # 数据库模块（必需）
├── config.py         # 配置模块（必需）
├── requirements.txt  # Python 依赖（必需）
├── Dockerfile        # Docker 配置（必需）
├── .dockerignore     # Docker 忽略文件（推荐）
├── .env.example      # 环境变量示例（参考）
├── .gitignore        # Git 忽略文件
└── README.md         # 项目说明
```

## 常见错误及解决方案

### 错误：ModuleNotFoundError

**原因：** 缺少依赖或 `requirements.txt` 不完整

**解决：** 确认 `requirements.txt` 包含所有必需包

### 错误：TELEGRAM_TOKEN 环境变量未找到

**原因：** Koyeb 中没有配置环境变量

**解决：** 在 Koyeb 仪表板中添加 `TELEGRAM_TOKEN`

### 错误：数据库连接失败

**原因：** DATABASE_URL 不正确或数据库离线

**解决：**
1. 验证 DATABASE_URL 格式
2. 确认数据库服务在线
3. 测试连接字符串

### 错误：机器人无响应

**原因：** 应用已部署但无法连接到 Telegram API

**解决：**
1. 检查 Koyeb 应用日志
2. 验证 TELEGRAM_TOKEN 是否正确
3. 检查网络连接

## 获取必要的信息

### 获取 TELEGRAM_TOKEN

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按照提示填写机器人名称和用户名
4. BotFather 会返回 Token

示例 Token：
```
1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
```

### 获取 DATABASE_URL

使用 Neon（推荐）：
1. 访问 https://neon.tech
2. 创建账户并登录
3. 创建新项目
4. 复制 PostgreSQL 连接字符串

示例连接字符串：
```
postgresql://neondb_owner:password@ep-xxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
```

## 重要提示

⚠️ **安全提示：**
- 永远不要在代码中硬编码 TELEGRAM_TOKEN 或 DATABASE_URL
- 使用 Koyeb 的环境变量管理功能
- 定期检查 Koyeb 应用日志

## 更新应用

当需要更新应用时：

```bash
# 1. 修改本地代码
# 2. 提交到 GitHub
git add .
git commit -m "Update: description"
git push origin main

# 3. Koyeb 会自动部署新版本
# 无需手动操作
```

## 查看应用状态

在 Koyeb 仪表板中：

1. 选择你的应用
2. 查看 "Status" 指示器（应显示 "Running"）
3. 查看 "Logs" 了解应用运行情况
4. 查看 "Services" 查看部署详情

## 需要帮助？

- Koyeb 文档：https://docs.koyeb.com
- Telegram Bot API：https://core.telegram.org/bots
- PostgreSQL 文档：https://www.postgresql.org/docs
