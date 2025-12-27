import requests
import os
import time
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

class InterviewFieldCreator:
    def __init__(self):
        self.app_id = os.getenv("INTERVIEW_APP_ID")
        self.app_secret = os.getenv("INTERVIEW_APP_SECRET")
        self.app_token = os.getenv("INTERVIEW_BITABLE_APP_TOKEN")
        self.table_id = os.getenv("INTERVIEW_TABLE_ID")
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

        field_data = {
            "field_name": field_name,
            "type": field_type
        }

        # 为单选和多选字段添加选项
        if options and field_type in [3, 4]:  # 单选(3)或多选(4)
            field_data["property"] = {
                "options": [{"name": option} for option in options]
            }

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

    def create_all_fields(self, auto_confirm=False):
        """创建所有面试记录字段"""
        print("🚀 开始创建面试记录多维表格字段...")

        # 定义要创建的字段
        fields_config = [
            # === 基础信息区 ===
            {
                "name": "题目/话题",
                "type": 1,  # 单行文本
                "category": "基础信息区",
                "description": "面试题目的核心描述"
            },
            {
                "name": "涉及产品/公司",
                "type": 4,  # 多选
                "category": "基础信息区",
                "description": "题目涉及的主要公司或产品",
                "options": ["京东", "美团", "腾讯", "抖音", "阿里", "百度", "字节跳动", "拼多多", "快手", "小红书", "其他"]
            },
            {
                "name": "业务类型",
                "type": 3,  # 单选
                "category": "基础信息区",
                "description": "业务所属类型",
                "options": ["电商", "社交", "工具", "O2O", "内容", "金融", "游戏", "教育", "医疗", "出行", "其他"]
            },
            {
                "name": "创建时间",
                "type": 5,  # 日期
                "category": "基础信息区",
                "description": "记录创建的日期"
            },

            # === 深度解析区 ===
            {
                "name": "表层现象 (Phenomenon)",
                "type": 1,  # 单行文本
                "category": "深度解析区",
                "description": "描述看到的事实"
            },
            {
                "name": "战略意图 (Strategic Intent)",
                "type": 4,  # 多选
                "category": "深度解析区",
                "description": "企业的战略目的",
                "options": ["流量获取（拉新/促活）", "防御/护城河", "变现/营收", "生态闭环", "品牌建设", "技术布局", "用户留存", "其他"]
            },
            {
                "name": "核心商业逻辑 (Core Logic)",
                "type": 1,  # 单行文本
                "category": "深度解析区",
                "description": "一句话概括本质"
            },
            {
                "name": "关键支撑/资源 (Key Resources)",
                "type": 1,  # 单行文本
                "category": "深度解析区",
                "description": "做成这件事的底牌是什么"
            },
            {
                "name": "批判性思考/风险点 (Critical Thinking)",
                "type": 1,  # 单行文本
                "category": "深度解析区",
                "description": "反直觉的观点或难点"
            },

            # === 方法论沉淀区 ===
            {
                "name": "涉及思维模型",
                "type": 4,  # 多选
                "category": "方法论沉淀区",
                "description": "题目涉及的商业思维模型",
                "options": [
                    "高频打低频", "网络效应", "边际成本", "供需关系", "围魏救赵",
                    "单位经济模型(UE)", "用户体验五要素", "漏斗模型", "飞轮效应",
                    "长尾理论", "破窗效应", "马太效应", "灰度创新", "第一性原理",
                    "SWOT分析", "波士顿矩阵", "波特五力", "其他"
                ]
            },

            # === 面试备战区 ===
            {
                "name": "考察能力项",
                "type": 4,  # 多选
                "category": "面试备战区",
                "description": "本题考察的核心能力",
                "options": [
                    "商业敏感度", "战略视野", "用户同理心", "数据分析能力",
                    "资源整合能力", "产品思维", "运营思维", "技术理解",
                    "市场洞察", "沟通表达", "逻辑思维", "创新思维", "其他"
                ]
            },
            {
                "name": "回答金句/关键词",
                "type": 1,  # 单行文本
                "category": "面试备战区",
                "description": "面试时必须说出来的得分词"
            },
            {
                "name": "AI分析结果",
                "type": 1,  # 单行文本
                "category": "面试备战区",
                "description": "AI助手生成的深度分析和建议"
            },
            {
                "name": "难度评级",
                "type": 3,  # 单选
                "category": "面试备战区",
                "description": "题目难度评估",
                "options": ["⭐ 入门", "⭐⭐ 基础", "⭐⭐⭐ 中等", "⭐⭐⭐⭐ 进阶", "⭐⭐⭐⭐⭐ 困难"]
            },
            {
                "name": "掌握程度",
                "type": 3,  # 单选
                "category": "面试备战区",
                "description": "个人对题目的掌握程度",
                "options": ["🔴 未掌握", "🟡 了解", "🟢 熟悉", "🔵 精通"]
            }
        ]

        # 按类别分组显示
        categories = {}
        for field in fields_config:
            category = field["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(field)

        print(f"\n📋 将创建以下面试记录字段:")
        for category, fields in categories.items():
            print(f"\n🔸 {category}:")
            for field in fields:
                type_names = {1: "单行文本", 2: "数字", 3: "单选", 4: "多选", 5: "日期", 15: "超链接", 23: "附件"}
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

        print(f"\n🎉 面试记录字段创建完成！")
        print(f"   ✅ 成功创建: {success_count} 个字段")
        print(f"   ❌ 创建失败: {failed_count} 个字段")

def main():
    import sys
    auto_confirm = "--auto-confirm" in sys.argv

    creator = InterviewFieldCreator()
    creator.create_all_fields(auto_confirm=auto_confirm)

if __name__ == "__main__":
    main()