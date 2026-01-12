# Wicked Stock Trading Tool

股票交易计划管理系统 - 基于 Dify AI 的智能交易助手

## 功能特性

- 🤖 **AI 交易助手**：集成 Dify 聊天机器人，智能生成交易计划
- 📊 **计划管理**：存储、查看、管理股票交易计划
- 🌟 **重点关注**：标记重要股票，自动置顶显示
- 📚 **版本控制**：同一股票支持多版本交易计划
- 🔒 **权限保护**：密码保护敏感操作
- 🎨 **现代化 UI**：折叠式卡片、渐变背景、流畅动画

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置应用

```bash
cp config.yaml.example config.yaml
```

编辑 `config.yaml`，配置以下内容：

```yaml
# 应用密码（用于保护交易计划保存和星标功能）
app:
  save_password: "YOUR_PASSWORD_HERE"

# Dify 聊天机器人 URL
dify:
  chatbot_url: "https://udify.app/chatbot/YOUR_CHATBOT_ID"

# 邮件提醒（可选）
alerts:
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    from_address: "your-email@gmail.com"
    to_address: "your-email@gmail.com"
    password: "YOUR_EMAIL_PASSWORD"
```

### 3. 运行应用

```bash
python app.py
```

访问：http://localhost:8888

## 使用说明

### 查看交易计划

- 左侧列表显示所有保存的交易计划
- 点击卡片标题展开/收起详情
- 点击"查看详情"按钮查看完整计划
- 点击"历史版本"查看同一股票的所有版本

### 使用 AI 助手

1. 点击右侧"解锁"按钮，输入密码
2. 与 Dify AI 对话，生成交易计划
3. 复制 AI 生成的交易计划
4. 粘贴到下方文本框
5. 点击"保存交易计划"

### 重点关注

- 解锁后，点击计划左侧的星标按钮 ⭐
- 星标计划会自动置顶并高亮显示
- 再次点击取消关注

## 技术栈

- **后端**：Flask + Python 3
- **数据库**：SQLite
- **前端**：原生 JavaScript + CSS
- **AI**：Dify 聊天机器人

## 数据库迁移

如果需要添加新字段，使用迁移脚本：

```bash
python migrate_db.py
```

## 安全提示

⚠️ **重要**：

1. 不要将 `config.yaml` 提交到 Git
2. 使用强密码保护应用
3. 不要在生产环境使用 debug 模式
4. 定期备份数据库文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
