# 飞书集成模块

本文件夹包含所有与飞书多维表格集成相关的脚本和工具。

## 文件说明

### 核心模块
- **`feishu_pusher.py`** - 主要的飞书推送模块，负责将AI分析结果推送到飞书表格
- **`gemini_agent.py`** - Gemini AI分析模块（位于项目根目录）

### 管理工具
- **`create_feishu_fields.py`** - 创建飞书表格字段
- **`update_business_field.py`** - 更新字段类型（如商业潜力字段改为星星显示）
- **`delete_specific_fields.py`** - 删除指定字段
- **`clear_feishu_table.py`** - 清空表格数据

## 使用方法

### 1. 创建/更新字段结构
```bash
# 创建所有字段
python feishu_integration/create_feishu_fields.py --auto-confirm

# 更新商业潜力字段为星星显示
python feishu_integration/update_business_field.py

# 删除不需要的字段
python feishu_integration/delete_specific_fields.py --auto-confirm
```

### 2. 清空数据
```bash
# 清空表格中所有记录
python feishu_integration/clear_feishu_table.py --auto-confirm
```

### 3. 在主程序中使用
```python
from feishu_integration.feishu_pusher import FeishuPusher

pusher = FeishuPusher()
pusher.push_record(raw_data, ai_analysis)
```

## 字段结构

### 基础元数据
- 新闻标题
- 原文链接
- 来源渠道
- 作者账号
- 发布日期
- 收藏日期（主字段）

### 技术与属性
- 所属领域
- AI模型
- 使用成本

### AI深度分析
- 一句话摘要
- 核心亮点
- 模式创新
- 商业潜力（星星显示）
- 完整转录
- AI对话分析

## 环境要求

确保 `.env` 文件中包含以下飞书相关配置：
```
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_BITABLE_APP_TOKEN=your_table_token
FEISHU_TABLE_ID=your_table_id
```