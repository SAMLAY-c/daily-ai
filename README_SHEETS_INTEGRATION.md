# 飞书电子表格集成说明

## 📋 当前配置状态

✅ **已完成的配置：**

1. **应用凭证配置**：
   - App ID: `cli_a9c39287a439dbde`
   - App Secret: `CRjhghFBklHmRxRd5ZfGgbiKqo26aiiA`

2. **电子表格信息**：
   - 表格链接: `https://pcnlp18cy9bm.feishu.cn/sheets/HEmPsc9poh9A6XtEVx9ctALmnld`
   - 表格标题: `项目`
   - 工作表标题: `boss直聘 agent`
   - 工作表ID: `47d5b8`

3. **权限验证**：
   - ✅ 应用已获得电子表格访问权限
   - ✅ Token 获取成功
   - ✅ 数据读取功能正常

## ⚠️ 当前限制

**数据写入功能**：
- 目前可以成功读取电子表格数据
- 写入功能遇到权限限制（403 Forbidden）
- 这可能是因为应用需要更高级别的写入权限

## 🛠️ 解决方案

### 方案1：添加写入权限
1. 登录飞书开发者后台
2. 进入应用 `cli_a9c39287a439dbde`
3. 在「权限管理」中添加以下权限：
   - `sheets:spreadsheet` (查看、评论、编辑和管理电子表格)

### 方案2：使用多维表格
1. 创建一个新的多维表格
2. 修改 `.env` 文件中的配置
3. 使用原有的 `feishu_pusher.py` (已经支持多维表格)

### 方案3：手动CSV导出
1. 将数据保存为CSV文件
2. 手动导入到飞书电子表格

## 📁 文件说明

- `feishu_pusher.py` - 原有的多维表格推送器（推荐）
- `sheets_feishu_pusher.py` - 电子表格推送器（读取功能正常）
- `.env` - 配置文件（已更新为电子表格配置）

## 🔧 测试命令

```bash
# 测试电子表格连接和读取
python3 sheets_feishu_pusher.py

# 测试多维表格连接（如果改用多维表格）
python3 -c "from feishu_pusher import FeishuPusher; FeishuPusher().get_tenant_token()"
```

## 💡 建议

**推荐使用多维表格**：
- API更稳定，权限更清晰
- 支持复杂的数据结构
- 更适合结构化数据存储

如果需要继续使用电子表格，建议：
1. 联系飞书技术支持确认写入权限
2. 或者定期手动导入CSV数据

---

*最后更新：2025-12-22*