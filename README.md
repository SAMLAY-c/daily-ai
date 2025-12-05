# RSS 情报监控系统

自动化RSS内容监控、AI分析和飞书数据推送系统。

## 功能特性

- 🔍 **多源RSS监控**: 支持YouTube、Bilibili、博客等多种RSS源
- 🎬 **智能媒体处理**: 自动下载视频音频并转录
- 🤖 **AI内容分析**: 使用Gemini进行深度内容分析和分类
- 📊 **数据推送**: 自动推送结构化数据到飞书多维表格
- 🚀 **自动化部署**: 支持GitHub Actions定时运行

## 本地开发

### 环境要求

- Python 3.10+
- FFmpeg
- Groq API Key
- Google Gemini API Key
- 飞书应用权限

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd rss-github
   ```

2. **创建虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **安装FFmpeg**
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg

   # Windows
   # 从 https://ffmpeg.org/download.html 下载
   ```

5. **配置环境变量**
   复制 `.env.example` 到 `.env` 并填入配置：
   ```bash
   cp .env.example .env
   ```

6. **运行程序**
   ```bash
   python main.py
   ```

## GitHub Actions 部署

### 1. 设置仓库密钥

在GitHub仓库的 Settings > Secrets and variables > Actions 中添加以下Repository Secrets：

#### 必需的密钥：

- `GOOGLE_API_KEY`: Google Gemini API密钥
- `GROQ_API_KEY`: Groq API密钥（用于语音转录）
- `FEISHU_APP_ID`: 飞书应用ID
- `FEISHU_APP_SECRET`: 飞书应用密钥
- `FEISHU_BITABLE_APP_TOKEN`: 飞书多维表格应用令牌
- `FEISHU_TABLE_ID`: 飞书表格ID
- `RSS_FEEDS`: RSS订阅源列表（逗号分隔）

#### RSS_FEEDS 格式示例：
```
http://47.83.6.113:1200/youtube/user/@tech-shrimp,http://47.83.6.113:1200/youtube/user/@AxtonLiu,https://rsshub.app/bilibili/user/video/2267573
```

### 2. GitHub Actions 功能

- **自动FFmpeg安装**: 工作流程会自动安装FFmpeg
- **定时运行**: 每小时自动执行一次
- **手动触发**: 支持手动运行
- **缓存优化**: 缓存pip依赖以提高运行速度
- **日志保存**: 保存执行日志7天

### 3. 工作流程文件

位于 `.github/workflows/rss-monitor.yml`，包含：

1. 代码检出
2. Python环境设置
3. FFmpeg安装和验证
4. 依赖安装
5. 环境变量配置
6. 运行主程序
7. 日志上传

## 配置说明

### RSS源配置

在 `.env` 文件中配置：
```
RSS_FEEDS=源1,源2,源3
```

### 测试模式

启用测试模式只处理第一个RSS源：
```
TEST_MODE=true
```

### 飞书配置

需要创建飞书应用并配置权限：
- 多维表格权限: `bitable:app`
- 应用权限: 查看、评论、编辑、管理

## 故障排除

### 常见问题

1. **FFmpeg错误**: 确保FFmpeg已正确安装
2. **API配额限制**: 检查Groq和Gemini API使用量
3. **飞书推送失败**: 验证飞书应用权限和表格字段配置
4. **YouTube 403错误**: 程序已内置重试机制，可自动处理

### 调试模式

启用详细日志：
```bash
export DEBUG=true
python main.py
```

## 项目结构

```
rss-github/
├── main.py              # 主程序入口
├── rss_manager.py       # RSS管理模块
├── media_handler.py     # 媒体处理模块
├── gemini_agent.py      # AI分析模块
├── feishu_pusher.py     # 飞书推送模块
├── requirements.txt     # Python依赖
├── .env.example        # 环境变量模板
├── .github/workflows/  # GitHub Actions配置
└── feishu_integration/ # 飞书管理工具
```

## 许可证

[MIT License](LICENSE)