import requests
import os
import time
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

class FeishuFieldCreator:
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.app_token = os.getenv("FEISHU_BITABLE_APP_TOKEN")
        self.table_id = os.getenv("FEISHU_TABLE_ID")
        self.token = None
        self.token_expire_time = 0

    def get_tenant_token(self):
        """获取并缓存 Tenant Access Token"""
        if self.token and time.time() < self.token_expire_time:
            return self.token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        resp = requests.post(url, json=payload)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                self.token = data.get("tenant_access_token")
                self.token_expire_time = time.time() + data.get("expire", 7200) - 60
                return self.token
            else:
                print(f"❌ 获取 Token 失败: {data.get('msg')}")
                return None
        else:
            print(f"❌ 请求 Token 失败: {resp.text}")
            return None

    def create_field(self, field_name, field_type, options=None, description=None):
        """创建单个字段"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 构建字段数据 - 先尝试最简单的格式
        field_data = {
            "field_name": field_name,
            "type": field_type
        }

        # 为单选和多选字段添加选项
        if options and field_type in [3, 4]:  # 单选(3)或多选(4)
            field_data["property"] = {
                "options": [{"name": option} for option in options]
            }

        # 暂时不添加ui_type和description，先用最基础的格式测试

        # 生成唯一的客户端token
        params = {
            "client_token": str(uuid.uuid4())
        }

        try:
            resp = requests.post(url, headers=headers, params=params, json=field_data)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    field_id = data.get("data", {}).get("field", {}).get("field_id")
                    print(f"   ✅ 创建字段成功: {field_name} [ID: {field_id}]")
                    return True
                else:
                    print(f"   ❌ 创建字段 {field_name} 失败: {data.get('msg')}")
                    return False
            else:
                print(f"   ❌ 创建请求失败: {resp.text}")
                return False
        except Exception as e:
            print(f"   ❌ 创建字段时出错: {e}")
            return False

    def create_all_fields(self, auto_confirm=False, debug_single=False):
        """创建所有字段"""
        print("🚀 开始创建飞书多维表格字段...")

        # 定义要创建的字段
        fields_config = [
            # === 基础元数据 (Meta Info) ===
            {
                "name": "新闻标题",
                "type": 1,  # 多行文本
                "category": "基础元数据",
                "description": "内容的核心标题"
            },
            {
                "name": "原文链接",
                "type": 15,  # 超链接
                "category": "基础元数据",
                "description": "原始出处链接"
            },
            {
                "name": "视频链接",
                "type": 15,  # 超链接
                "category": "基础元数据",
                "description": "YouTube/Bilibili 等视频链接"
            },
            {
                "name": "来源渠道",
                "type": 3,  # 单选
                "category": "基础元数据",
                "description": "信息的来源平台",
                "options": [
                    "Twitter", "GitHub", "Arxiv", "HuggingFace",
                    "微信公众号", "官方博客", "YouTube", "Bilibili", "其他"
                ]
            },
            {
                "name": "作者账号",
                "type": 1,  # 多行文本
                "category": "基础元数据",
                "description": "关键KOL或机构名称"
            },
            {
                "name": "地域归属",
                "type": 3,  # 单选
                "category": "基础元数据",
                "description": "用于区分访问门槛和生态",
                "options": ["🌏 国外", "🇨🇳 国内", "未知"]
            },
            {
                "name": "发布日期",
                "type": 5,  # 日期
                "category": "基础元数据",
                "description": "信息的原始产生时间"
            },
            {
                "name": "收藏日期",
                "type": 5,  # 日期
                "category": "基础元数据",
                "description": "你入库的时间（自动生成）"
            },

            # === 技术与属性 (Tech & Attributes) ===
            {
                "name": "内容类型",
                "type": 3,  # 单选
                "category": "技术与属性",
                "description": "区分是学术研究还是应用工具",
                "options": ["📄 论文", "🛠️ 工具", "📰 新闻", "📦 模型", "💡 教程", "🎥 视频"]
            },
            {
                "name": "所属领域",
                "type": 4,  # 多选
                "category": "技术与属性",
                "description": "宏观技术领域",
                "options": ["LLM", "CV", "Audio", "Agent", "RAG", "机器人", "其他"]
            },
            {
                "name": "涉及技术",
                "type": 4,  # 多选
                "category": "技术与属性",
                "description": "微观技术栈关键词",
                "options": ["Transformer", "Diffusion", "RLHF", "LoRA", "Mamba", "其他"]
            },
            {
                "name": "AI模型",
                "type": 4,  # 多选
                "category": "技术与属性",
                "description": "该项目基于哪个基座模型",
                "options": [
                    "GPT-4", "Claude-3", "Llama-3", "Stable Diffusion",
                    "Gemini", "Midjourney", "Sora", "无", "其他"
                ]
            },
            {
                "name": "使用成本",
                "type": 3,  # 单选
                "category": "技术与属性",
                "description": "快速判断能否白嫖",
                "options": ["🆓 开源免费", "💰 商业付费", "💳 API计费", "🤝 免费试用", "未知"]
            },
            {
                "name": "核心关键词",
                "type": 4,  # 多选
                "category": "技术与属性",
                "description": "自动提取的Tag，用于搜索",
                "options": [
                    "AI", "机器学习", "深度学习", "自然语言处理", "计算机视觉",
                    "语音识别", "推荐系统", "自动驾驶", "机器人", "区块链",
                    "物联网", "云计算", "大数据", "开源", "商业化", "其他"
                ]
            },

            # === AI 深度分析 (AI Analysis) ===
            {
                "name": "一句话摘要",
                "type": 1,  # 多行文本
                "category": "AI深度分析",
                "description": "TL;DR，快速了解讲什么"
            },
            {
                "name": "核心亮点",
                "type": 1,  # 多行文本
                "category": "AI深度分析",
                "description": "解决了什么痛点？有什么突破？"
            },
            {
                "name": "模式创新",
                "type": 1,  # 多行文本
                "category": "AI深度分析",
                "description": "技术或商业模式上的新颖之处"
            },
            {
                "name": "商业潜力",
                "type": 1,  # 改为多行文本以支持星星显示
                "category": "AI深度分析",
                "description": "变现能力或行业颠覆性评分(⭐-⭐⭐⭐⭐⭐)"
            },
            {
                "name": "完整转录",
                "type": 1,  # 多行文本
                "category": "AI深度分析",
                "description": "视频字幕或网页全文的清洗版"
            },
            {
                "name": "AI对话分析",
                "type": 1,  # 多行文本
                "category": "AI深度分析",
                "description": "AI Agent对该内容的完整分析记录"
            }
        ]

        # 按类别分组显示
        categories = {}
        for field in fields_config:
            category = field["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(field)

        print(f"\n📋 将创建以下字段:")
        for category, fields in categories.items():
            print(f"\n🔸 {category}:")
            for field in fields:
                type_names = {1: "多行文本", 2: "数字", 3: "单选", 4: "多选", 5: "日期", 15: "超链接"}
                type_name = type_names.get(field["type"], "未知")
                print(f"   - {field['name']} ({type_name})")

        if auto_confirm:
            print(f"\n🤖 自动确认模式：开始创建 {len(fields_config)} 个字段")
        else:
            try:
                confirm = input(f"\n确认要创建这 {len(fields_config)} 个字段吗？(输入 'yes' 确认): ")
                if confirm.lower() != 'yes':
                    print("❌ 操作已取消")
                    return
            except EOFError:
                print("❌ 无法获取用户确认，操作已取消")
                return

        # 如果是调试模式，只创建一个字段
        if debug_single:
            test_field = fields_config[0]
            print(f"\n🔧 调试模式：只创建一个字段")
            if self.create_field(
                test_field["name"],
                test_field["type"],
                test_field.get("options"),
                test_field.get("description")
            ):
                print("✅ 调试成功，可以尝试创建所有字段")
            else:
                print("❌ 调试失败，请检查配置")
            return

        # 逐个创建字段
        print(f"\n🔨 开始创建字段...")
        success_count = 0
        failed_count = 0

        for i, field_config in enumerate(fields_config, 1):
            print(f"\n[{i}/{len(fields_config)}] 正在创建字段: {field_config['name']}")

            if self.create_field(
                field_config["name"],
                field_config["type"],
                field_config.get("options"),
                field_config.get("description")
            ):
                success_count += 1
            else:
                failed_count += 1

            # 避免请求过快，API 限制为 10 次/秒
            time.sleep(0.2)

        print(f"\n🎉 字段创建完成！")
        print(f"   ✅ 成功创建: {success_count} 个字段")
        print(f"   ❌ 创建失败: {failed_count} 个字段")

def main():
    import sys
    auto_confirm = "--auto-confirm" in sys.argv
    debug_single = "--debug" in sys.argv

    creator = FeishuFieldCreator()
    creator.create_all_fields(auto_confirm=auto_confirm, debug_single=debug_single)

if __name__ == "__main__":
    main()